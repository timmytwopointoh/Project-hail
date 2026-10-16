#!/usr/bin/env python3
"""VQ M33: bounded connected planar/near-planar OBJ UV charts.

Charts are welded-edge connected and material isolated. Each chart is projected
into one shared planar basis, checked for signed area, bounded stretch and
positive-area UV self-overlap, then packed at one common texel density with
explicit rectangular gutters. This is *not* a conformal unwrap of arbitrary
curved/folded surfaces, mip dilation or an artist-approved material bake.
"""
from __future__ import annotations
import argparse
from collections import defaultdict, deque
import hashlib
import json
import math
from pathlib import Path
from engine import inspect_obj, read_obj
from vq_brushes import _face_materials
from vq_uv_seams import seam_counts

MAX_FACES = 5000

def _sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))

def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))

def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

def _unit(v):
    length = math.sqrt(_dot(v, v))
    if not math.isfinite(length) or length < 1e-12:
        raise ValueError("Degenerate or nonfinite source triangle")
    return tuple(x/length for x in v)

def _area2(poly):
    return sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(poly, poly[1:]+poly[:1]))

def _clip_polygon(poly, a, b):
    """Clip a convex polygon to the left of oriented edge a->b."""
    def side(p):
        return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
    out = []
    for p, q in zip(poly, poly[1:]+poly[:1]):
        dp, dq = side(p), side(q)
        inside_p, inside_q = dp >= -1e-11, dq >= -1e-11
        if inside_p:
            out.append(p)
        if inside_p != inside_q:
            t = dp/(dp-dq)
            out.append((p[0]+t*(q[0]-p[0]), p[1]+t*(q[1]-p[1])))
    return out

def _check_no_overlap(triangles):
    """Detect *area* overlap, allowing shared vertices and shared edges."""
    boxes = [(min(p[0] for p in tri), min(p[1] for p in tri),
              max(p[0] for p in tri), max(p[1] for p in tri)) for tri in triangles]
    for i, left in enumerate(triangles):
        a = boxes[i]
        for j in range(i+1, len(triangles)):
            b = boxes[j]
            if min(a[2], b[2])-max(a[0], b[0]) <= 1e-10 or \
               min(a[3], b[3])-max(a[1], b[1]) <= 1e-10:
                continue
            poly = list(left)
            for k in range(3):
                poly = _clip_polygon(poly, triangles[j][k], triangles[j][(k+1)%3])
                if len(poly) < 3:
                    break
            if len(poly) >= 3 and abs(_area2(poly)) > 1e-9*min(abs(_area2(left)), abs(_area2(triangles[j]))):
                raise ValueError("Chart projection overlaps nonadjacent triangle interiors")

def _pack(charts, size, padding, scale):
    """Deterministic height-first shelf packing of padded chart rectangles."""
    order = sorted(range(len(charts)), key=lambda i: (-charts[i]["height"], -charts[i]["width"], i))
    x = y = row_h = 0
    places = {}
    for i in order:
        chart = charts[i]
        w = math.ceil(chart["width"]*scale) + 2*(padding+1)
        h = math.ceil(chart["height"]*scale) + 2*(padding+1)
        if w > size or h > size:
            return None
        if x+w > size:
            x, y, row_h = 0, y+row_h, 0
        if y+h > size:
            return None
        places[i] = (x+padding+1, y+padding+1)
        x += w
        row_h = max(row_h, h)
    return places

def unwrap(source, dest, *, texture_size=512, padding=4,
           max_angle_degrees=15.0, max_stretch=1.08):
    source, dest = Path(source), Path(dest)
    if source.resolve() == dest.resolve():
        raise ValueError("Never overwrite source OBJ")
    if not source.is_file() or source.is_symlink() or dest.is_symlink():
        raise ValueError("Missing or unsafe OBJ source/destination")
    if type(texture_size) is not int or texture_size not in (128, 256, 512, 1024, 2048, 4096):
        raise ValueError("Unsupported atlas resolution")
    if type(padding) is not int or not 2 <= padding <= 16:
        raise ValueError("Chart padding must be 2-16 pixels")
    if type(max_angle_degrees) not in (int, float) or not math.isfinite(max_angle_degrees) or not 1 <= max_angle_degrees <= 35:
        raise ValueError("Unsafe chart dihedral threshold")
    if type(max_stretch) not in (int, float) or not math.isfinite(max_stretch) or not 1 <= max_stretch <= 1.3:
        raise ValueError("Invalid stretch budget")
    verts, _, _, faces = read_obj(source)
    if not 1 <= len(faces) <= MAX_FACES:
        raise ValueError("Bounded chart face capacity exceeded")
    source_audit = inspect_obj(source)
    if source_audit["degenerate_triangles"] or source_audit["duplicate_triangles"] or source_audit["nonmanifold_edges"]:
        raise ValueError("Invalid source topology for connected charts")
    materials = _face_materials(source, len(faces))
    points = [[tuple(verts[c[0]][:3]) for c in f] for f in faces]
    normals = [_unit(_cross(_sub(p[1], p[0]), _sub(p[2], p[0]))) for p in points]
    keys = [[tuple(round(x, 6) for x in p) for p in tri] for tri in points]
    edges = defaultdict(list)
    for fi, tri in enumerate(keys):
        for k in range(3):
            edge = tuple(sorted((tri[k], tri[(k+1)%3])))
            edges[edge].append(fi)
    adjacency = [set() for _ in faces]
    for owners in edges.values():
        if len(owners) > 2:
            raise ValueError("Nonmanifold source edge")
        if len(owners) == 2:
            a, b = owners
            adjacency[a].add(b)
            adjacency[b].add(a)
    threshold = math.cos(math.radians(max_angle_degrees))
    assigned = set()
    charts = []
    for seed in range(len(faces)):
        if seed in assigned:
            continue
        group = []
        todo = deque([seed])
        assigned.add(seed)
        while todo:
            fi = todo.popleft()
            group.append(fi)
            for neighbor in sorted(adjacency[fi]):
                if neighbor in assigned or materials[fi] != materials[neighbor]:
                    continue
                if _dot(normals[fi], normals[neighbor]) < threshold or \
                   _dot(normals[seed], normals[neighbor]) < threshold:
                    continue
                assigned.add(neighbor)
                todo.append(neighbor)
        group.sort()
        normal = normals[seed]
        origin = points[seed][0]
        unique_points = {key: point for fi in group for key, point in zip(keys[fi], points[fi])}
        # Rotate each chart to a compact bounding rectangle. A fixed first-face
        # diagonal can waste half an atlas on a square grid and fail a real bake.
        # Edge-direction candidates preserve scale and triangle orientation.
        candidates = {}
        for fi in group:
            for k in range(3):
                direction = _sub(points[fi][(k+1)%3], points[fi][k])
                direction = tuple(direction[j]-_dot(direction, normal)*normal[j] for j in range(3))
                tangent = _unit(direction)
                # A tangent and its negative have identical box dimensions.
                if next(x for x in tangent if abs(x)>1e-8) < 0:
                    tangent = tuple(-x for x in tangent)
                candidates[tuple(round(x, 6) for x in tangent)] = tangent
        if len(candidates) > 128:
            # Stable sampling of diverse directions; never dependent on face order.
            ordered = sorted(candidates)
            candidates = {key: candidates[key] for key in
                          (ordered[(i*(len(ordered)-1))//127] for i in range(128))}
        best = None
        for tangent in candidates.values():
            bitangent = _cross(normal, tangent)
            coords = {}
            for key, point in unique_points.items():
                displacement = _sub(point, origin)
                coords[key] = (_dot(displacement, tangent), _dot(displacement, bitangent))
            xs = [uv[0] for uv in coords.values()]
            ys = [uv[1] for uv in coords.values()]
            width, height = max(xs)-min(xs), max(ys)-min(ys)
            score = (round(width*height, 9), round(max(width, height), 9),
                     tuple(round(x, 6) for x in tangent))
            if best is None or score < best[0]:
                best = (score, coords)
        coords = best[1]
        projected = []
        for fi in group:
            tri = [coords[k] for k in keys[fi]]
            signed = _area2(tri)
            if signed <= 1e-12:
                raise ValueError("Chart projection inverted or collapsed")
            stretch = 1/_dot(normal, normals[fi])
            if stretch > max_stretch + 1e-9:
                raise ValueError("Chart area stretch exceeds budget")
            projected.append(tri)
        _check_no_overlap(projected)
        lo_x = min(uv[0] for uv in coords.values())
        lo_y = min(uv[1] for uv in coords.values())
        hi_x = max(uv[0] for uv in coords.values())
        hi_y = max(uv[1] for uv in coords.values())
        charts.append({"faces": group, "coords": coords, "min_x": lo_x, "min_y": lo_y,
                       "width": hi_x-lo_x, "height": hi_y-lo_y,
                       "max_stretch": max(1/_dot(normal, normals[fi]) for fi in group),
                       "min_area": min(_area2(t)/2 for t in projected)})
    hi = texture_size / max(max(c["width"], c["height"]) for c in charts)
    lo = 0.0
    for _ in range(36):
        mid = (lo+hi)/2
        if _pack(charts, texture_size, padding, mid) is not None:
            lo = mid
        else:
            hi = mid
    scale = lo*(1-1e-9)
    placements = _pack(charts, texture_size, padding, scale)
    if placements is None or scale <= 0:
        raise ValueError("Atlas packing failed")
    min_area = min(c["min_area"]*scale*scale for c in charts)
    if min_area < 1:
        raise ValueError("Insufficient texel density for connected charts")
    face_uvs = [None]*len(faces)
    atlas_uvs = []
    for chart_index, chart in enumerate(charts):
        px, py = placements[chart_index]
        local_indices = {}
        for fi in chart["faces"]:
            ids = []
            for key in keys[fi]:
                if key not in local_indices:
                    u, v = chart["coords"][key]
                    uv = ((px+(u-chart["min_x"])*scale)/texture_size,
                          (py+(v-chart["min_y"])*scale)/texture_size)
                    if not all(0 <= c <= 1 for c in uv):
                        raise ValueError("Packed chart exceeds atlas")
                    atlas_uvs.append(uv)
                    local_indices[key] = len(atlas_uvs)
                ids.append(local_indices[key])
            face_uvs[fi] = ids
    output = []
    face_index = 0
    wrote_uv = False
    for line in source.read_text(encoding="utf-8").splitlines(keepends=True):
        tokens = line.partition("#")[0].strip().split()
        kind = tokens[0] if tokens else ""
        if kind == "vt":
            continue
        if kind == "f":
            if not wrote_uv:
                output.extend(f"vt {u:.11f} {v:.11f}\n" for u, v in atlas_uvs)
                wrote_uv = True
            corners = []
            for ref, ti in zip(faces[face_index], face_uvs[face_index]):
                vi, _, ni = ref
                corners.append(f"{vi+1}/{ti}"+(f"/{ni+1}" if ni is not None else ""))
            output.append("f "+" ".join(corners)+"\n")
            face_index += 1
        else:
            output.append(line)
    if face_index != len(faces):
        raise ValueError("Source face ordering changed")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("".join(output), encoding="utf-8")
    try:
        after = inspect_obj(dest)
        fixed = ("triangles", "vertices_raw", "vertices_welded", "normals", "boundary_edges",
                 "nonmanifold_edges", "degenerate_triangles", "duplicate_triangles", "bounds_min", "bounds_max")
        if any(after[k] != source_audit[k] for k in fixed) or after["uvs_outside_zero_one"]:
            raise ValueError("Connected atlas modified source geometry")
        from vq_mesh_baker import uv_rows
        uv_rows(dest)
        seams = seam_counts(dest)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    report = {"schema_version": 1, "engine": "VEYLQUORIN", "milestone": "M33",
              "method": "welded-edge connected near-planar material-isolated charts",
              "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
              "candidate_sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
              "source_triangles": len(faces), "charts": len(charts),
              "texture_size": texture_size, "gutter_pixels": padding,
              "world_to_texel_scale": round(scale, 6),
              "minimum_triangle_area_texels": round(min_area, 4),
              "maximum_area_stretch_ratio": round(max(c["max_stretch"] for c in charts), 6),
              "uv_seams": seams, "geometry_invariants_preserved": True,
              "source_unchanged": True, "original_uvs_replaced": True,
              "general_curved_surface_unwrap": False, "mip_gutter_dilation": False,
              "android_emulator_verified": False, "artistic_signoff": False,
              "production_approved": False}
    (dest.parent/(dest.stem+"_charts_report.json")).write_text(json.dumps(report, indent=2)+"\n")
    return report

def main():
    p = argparse.ArgumentParser(description="VQ bounded connected chart unwrap")
    p.add_argument("--obj", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--size", type=int, default=512)
    p.add_argument("--padding", type=int, default=4)
    p.add_argument("--angle", type=float, default=15.)
    a = p.parse_args()
    result = unwrap(a.obj, a.out, texture_size=a.size, padding=a.padding,
                    max_angle_degrees=a.angle)
    print("VQ_M33_CONNECTED_CHARTS_PASS", result["source_triangles"],
          "faces", result["charts"], "charts")

if __name__ == "__main__":
    main()
