#!/usr/bin/env python3
"""VEILFORGE asset inspection and deterministic PBR texture baker.

Builds reproducible *source assets*, never silently promotes an asset to a game.
No ML/photo-realism or physically-based renderer is claimed. No third-party
packages are needed. The PBR maps can be imported into Blender/glTF materials.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import zlib

MAX_ELEMENTS = 2_000_000
PROFILES = {
    "skin": {"base": (174, 119, 96), "metallic": 0, "roughness": 154, "variation": 13},
    "stone": {"base": (113, 119, 112), "metallic": 0, "roughness": 215, "variation": 31},
    "steel": {"base": (128, 144, 155), "metallic": 232, "roughness": 93, "variation": 18},
    "leather": {"base": (103, 68, 44), "metallic": 0, "roughness": 184, "variation": 24},
    "cloth": {"base": (59, 59, 67), "metallic": 0, "roughness": 205, "variation": 19},
}

class MeshError(ValueError):
    pass

def _finite(values):
    return all(math.isfinite(a) for a in values)

def _read_float(line, minimum):
    try:
        p = tuple(float(a) for a in line.split()[1:])
    except ValueError as error:
        raise MeshError("Non-numeric OBJ vertex") from error
    if len(p) < minimum or not _finite(p):
        raise MeshError("OBJ coordinate is invalid or nonfinite")
    return p

def _idx(value, count):
    if not value:
        return None
    try:
        i = int(value)
    except ValueError as error:
        raise MeshError("Invalid OBJ index") from error
    if i == 0 or abs(i) > count or (i > 0 and i > count):
        raise MeshError("OBJ index outside buffer")
    return (i - 1) if i > 0 else count + i

def read_obj(path: Path):
    """Parse triangle-only OBJ; position topology is independent of UV seams."""
    vertices, normals, texcoords, faces = [], [], [], []
    with path.open(encoding="utf-8") as inp:
        for lineno, line in enumerate(inp, 1):
            line = line.partition("#")[0].strip()
            if not line:
                continue
            kind = line.split(maxsplit=1)[0]
            if kind == "v":
                vertices.append(_read_float(line, 3))
            elif kind == "vn":
                normals.append(_read_float(line, 3))
            elif kind == "vt":
                texcoords.append(_read_float(line, 2))
            elif kind == "f":
                terms = line.split()[1:]
                if len(terms) != 3:
                    raise MeshError(f"OBJ must be triangulated (line {lineno})")
                tri = []
                for term in terms:
                    bits = term.split("/")
                    if len(bits) > 3 or not bits[0]:
                        raise MeshError(f"Bad face reference on line {lineno}")
                    vi = _idx(bits[0], len(vertices))
                    ui = _idx(bits[1], len(texcoords)) if len(bits) > 1 else None
                    ni = _idx(bits[2], len(normals)) if len(bits) > 2 else None
                    tri.append((vi, ui, ni))
                faces.append(tuple(tri))
            if max(len(vertices), len(normals), len(texcoords), len(faces)) > MAX_ELEMENTS:
                raise MeshError("Asset exceeds bounded inspector capacity")
    if not vertices or not faces:
        raise MeshError("No renderable triangle geometry")
    return vertices, texcoords, normals, faces

def inspect_obj(path: Path):
    vertices, uv, normals, faces = read_obj(path)
    edge_uses = {}
    duplicate_faces = set()
    repeat = 0
    bad = 0
    zero_normals = 0
    for normal in normals:
        if math.sqrt(sum(v*v for v in normal[:3])) < 0.25:
            zero_normals += 1
    for face in faces:
        p = [vertices[c[0]][:3] for c in face]
        a = tuple(p[1][k] - p[0][k] for k in range(3))
        b = tuple(p[2][k] - p[0][k] for k in range(3))
        cx = a[1]*b[2] - a[2]*b[1]
        cy = a[2]*b[0] - a[0]*b[2]
        cz = a[0]*b[1] - a[1]*b[0]
        if cx*cx + cy*cy + cz*cz < 1e-16:
            bad += 1
        # Geometry-only welded topology, so split UV seams are not false holes.
        keys = [tuple(round(v, 5) for v in point) for point in p]
        canon = tuple(sorted(keys))
        if canon in duplicate_faces:
            repeat += 1
        duplicate_faces.add(canon)
        for i in range(3):
            k = tuple(sorted((keys[i], keys[(i+1)%3])))
            edge_uses[k] = edge_uses.get(k, 0) + 1
    mins = [min(v[i] for v in vertices) for i in range(3)]
    maxs = [max(v[i] for v in vertices) for i in range(3)]
    boundary = sum(v == 1 for v in edge_uses.values())
    nonmanifold = sum(v > 2 for v in edge_uses.values())
    uvs_outside = sum(any(t < 0 or t > 1 for t in p[:2]) for p in uv)
    return {
        "schema_version": 1,
        "source": path.name,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "vertices_raw": len(vertices),
        "vertices_welded": len({tuple(round(v,5) for v in p[:3]) for p in vertices}),
        "uvs": len(uv),
        "normals": len(normals),
        "triangles": len(faces),
        "degenerate_triangles": bad,
        "duplicate_triangles": repeat,
        "boundary_edges": boundary,
        "nonmanifold_edges": nonmanifold,
        "watertight_welded_topology": boundary == 0 and nonmanifold == 0,
        "zero_normals": zero_normals,
        "uvs_outside_zero_one": uvs_outside,
        "bounds_min": [round(n, 6) for n in mins],
        "bounds_max": [round(n, 6) for n in maxs],
        "dimensions": [round(maxs[i]-mins[i], 6) for i in range(3)],
        "ready_for_game": False,
        "manual_visual_review_required": True,
    }

def _chunk(tag: bytes, payload: bytes):
    data = tag + payload
    return struct.pack(">I", len(payload)) + data + struct.pack(">I", zlib.crc32(data) & 0xffffffff)

def write_png(path: Path, width: int, height: int, channels: int, data: bytes):
    if channels not in (1, 3) or len(data) != width*height*channels:
        raise ValueError("Bad PNG channel buffer")
    color = 0 if channels == 1 else 2
    raw = b"".join(b"\x00" + data[y*width*channels:(y+1)*width*channels] for y in range(height))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" +
        _chunk(b"IHDR", struct.pack(">IIBBBBB", width,height,8,color,0,0,0)) +
        _chunk(b"IDAT", zlib.compress(raw, level=6)) + _chunk(b"IEND", b""))

def _noise(x: int, y: int, seed: int, period: int):
    # Smooth, deterministic, SEAMLESS 2D value noise: wraps at material edges.
    grid = 16
    period = max(2, period)
    fx = (x % period) * grid / period
    fy = (y % period) * grid / period
    ix, iy = int(fx), int(fy)
    sx, sy = fx - ix, fy - iy
    sx, sy = sx*sx*(3-2*sx), sy*sy*(3-2*sy)
    def h(a, b):
        a %= grid
        b %= grid
        z = (a * 374761393 + b * 668265263 + seed * 1442695041) & 0xffffffff
        z = ((z ^ (z >> 13)) * 1274126177) & 0xffffffff
        return ((z ^ (z >> 16)) & 65535) / 65535.0
    a = h(ix, iy)*(1-sx)+h(ix+1, iy)*sx
    b = h(ix, iy+1)*(1-sx)+h(ix+1, iy+1)*sx
    return a*(1-sy)+b*sy

def _clamp(v):
    return min(255, max(0, round(v)))

def bake_pbr(dest: Path, profile: str, size: int = 512, seed: int = 2026):
    """Emit deterministic source PBR maps. Normal approximation is tangent-space."""
    if profile not in PROFILES:
        raise ValueError("Unknown material profile")
    if size not in (128, 256, 512, 1024, 2048):
        raise ValueError("Texture dimension must be 128/256/512/1024/2048")
    dest.mkdir(parents=True, exist_ok=True)
    material = PROFILES[profile]
    n = size*size
    heights = bytearray(n)
    # Detail is stylized procedural noise, not a scan of real human skin.
    for y in range(size):
        for x in range(size):
            fine = _noise(x*2,y*2,seed+37,size*2)
            coarse = _noise(x,y,seed,size)
            heights[y*size+x] = _clamp(255*(.65*coarse+.35*fine))
    out = {"albedo": bytearray(n*3), "normal": bytearray(n*3),
           "roughness": bytearray(n), "metallic": bytearray(n),
           "ao": bytearray(n), "height": heights}
    for y in range(size):
        yp, yn = ((y-1)%size)*size, ((y+1)%size)*size
        for x in range(size):
            i = y*size+x
            h = heights[i]
            val = (h-128)/128
            base = material["base"]
            for c in range(3):
                out["albedo"][i*3+c] = _clamp(base[c] + val*material["variation"] + c*val*.7)
            out["roughness"][i] = _clamp(material["roughness"] + val*19)
            out["metallic"][i] = material["metallic"]
            out["ao"][i] = _clamp(235 + 20*val)
            dx = (heights[y*size+(x+1)%size]-heights[y*size+(x-1)%size])/255
            dy = (heights[yn+x]-heights[yp+x])/255
            nx,ny,nz = -dx*.9, -dy*.9, 1.0
            mag = math.sqrt(nx*nx+ny*ny+nz*nz)
            for c, v in enumerate((nx,ny,nz)):
                out["normal"][i*3+c] = _clamp((v/mag*.5+.5)*255)
    for name, data in out.items():
        write_png(dest/(name+".png"), size,size,3 if name in ("albedo","normal") else 1,data)
    manifest = {
        "schema_version": 1, "material": profile, "resolution": [size,size],
        "seed": seed, "workflow": "original deterministic procedural texture",
        "source_type": "procedural_not_photogrammetry",
        "maps": {name: {"file": name+".png", "color_space": "sRGB" if name=="albedo" else "linear"}
                 for name in out},
        "metallic_roughness_workflow": True,
        "tangent_space_normal": True,
        "reviewed_in_game": False,
    }
    (dest/"material.json").write_text(json.dumps(manifest, indent=2)+"\n",encoding="utf-8")
    return manifest

def main():
    p = argparse.ArgumentParser(description="Offline game-source asset baker and mesh QA")
    sub = p.add_subparsers(dest="command",required=True)
    q = sub.add_parser("inspect")
    q.add_argument("--obj",type=Path,required=True)
    q.add_argument("--out",type=Path,required=True)
    t = sub.add_parser("material")
    t.add_argument("--type",choices=sorted(PROFILES),required=True)
    t.add_argument("--out",type=Path,required=True)
    t.add_argument("--size",type=int,default=512)
    t.add_argument("--seed",type=int,default=2026)
    a = p.parse_args()
    if a.command=="inspect":
        result=inspect_obj(a.obj)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
        if result["degenerate_triangles"] > result["triangles"]*.02:
            raise SystemExit("QUALITY_GATE_FAIL: >2% zero-area triangles")
        print("VEILFORGE_MESH_AUDIT",json.dumps({
            k:result[k] for k in ("triangles","boundary_edges","nonmanifold_edges","degenerate_triangles")}))
    else:
        result=bake_pbr(a.out,a.type,a.size,a.seed)
        print("VEILFORGE_PBR_MAPS",result["material"],result["resolution"])
if __name__=="__main__":
    main()
