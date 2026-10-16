#!/usr/bin/env python3
"""VQ M33: real M32 adult-human geometry -> UV-isolated normal-baking studies.

This is an isolated TEST REGION for the authentic VQ M30 high-to-low baker.
It is not an artist-created UV unwrap or a replacement human. The original
M32 face / shoulder OBJ is immutable; all exported geometry is an explicit
independent sample with a PER-FACE packed UV diagnostic atlas. Real smooth
production UV islands, anatomical painting and a projection cage are pending.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from hashlib import sha256
import json
import math
from pathlib import Path

def unit(x):
    length=math.sqrt(sum(k*k for k in x))
    if not math.isfinite(length) or length<1e-10:
        raise ValueError("Invalid source skin normal")
    return tuple(k/length for k in x)

def cross(a,b):return (a[1]*b[2]-a[2]*b[1],
                       a[2]*b[0]-a[0]*b[2],
                       a[0]*b[1]-a[1]*b[0])
def sub(a,b):return tuple(a[k]-b[k] for k in range(3))
def key(p):return tuple(round(k,6) for k in p)
def length(p,q):return math.dist(p,q)
def mask(region,p):
    x,y,z=p
    if region=="face":
        return -0.18<x<0.18 and 2.35<y<2.52 and .09<z<.27
    if region=="shoulders":
        return .23<abs(x)<.53 and 1.82<y<2.10 and -.02<z<.22
    if region=="hands":
        # Right-hand-only UV baking diagnosis; mirrored left is not silently
        # treated as interchangeable with anatomical/nail geometry.
        return .46<x<.82 and .70<y<1.22 and -.09<z<.24
    if region=="feet":
        return .07<abs(x)<.45 and .02<y<.33 and -.14<z<.48
    raise ValueError("Unsupported anatomical region")

def read_source(path):
    """Bounded triangle-only OBJ reader, preserves source order and SHA."""
    path=Path(path)
    if path.suffix.lower()!=".obj" or not path.is_file() or path.is_symlink():
        raise ValueError("Expected a real source .obj file, never a symlink")
    if path.stat().st_size>110_000_000:raise ValueError("OBJ size cap exceeded")
    vertex=[];normals=[];faces=[]
    with path.open("r",encoding="utf-8") as stream:
        for line in stream:
            row=line.split()
            if not row:continue
            if row[0]=="v":
                if len(row)<7:raise ValueError("Require original VQ per-vertex skin colors")
                xyz=tuple(float(z) for z in row[1:4])
                rgb=tuple(float(z) for z in row[4:7])
                if not all(map(math.isfinite,xyz+rgb)):
                    raise ValueError("Nonfinite user source geometry or pigment")
                vertex.append((xyz,rgb))
            elif row[0]=="vn":
                nn=tuple(float(z) for z in row[1:4])
                normals.append(unit(nn))
            elif row[0]=="f":
                if len(row)!=4:raise ValueError("Only actual triangles accepted")
                f=[]
                for corner in row[1:]:
                    elements=corner.split("/")
                    vi=int(elements[0])-1
                    ni=int(elements[2])-1 if len(elements)>2 and elements[2] else None
                    if vi<0 or vi>=len(vertex):
                        raise ValueError("OBJ index outside original source")
                    if ni is not None and (ni<0 or ni>=len(normals)):
                        raise ValueError("OBJ normal index out of bounds")
                    f.append((vi,ni))
                faces.append(tuple(f))
                if len(faces)>130000:raise ValueError("Source exceeds VQ source budget")
    if not faces or not normals:
        raise ValueError("Actual human source triangles and normals required")
    return vertex,normals,faces

def is_skin(color):
    r,g,b=color
    return .36<r<.84 and .22<g<.64 and .16<b<.55 and r>g>b

def choose_faces(vertices,faces,region):
    selected=[]
    for f in faces:
        if all(mask(region,vertices[vi][0]) and is_skin(vertices[vi][1])
               for vi,_ in f):
            selected.append(f)
    if len(selected)<120:
        raise ValueError("Human anatomy zone has too few true skin faces")
    if len(selected)>6800:
        raise ValueError("Too many triangles for tiny UV bake diagnostic")
    return selected

def build(source,out,region):
    source=Path(source);out=Path(out)
    if out.resolve()==source.resolve() or source.resolve().is_relative_to(out.resolve()):
        raise ValueError("Never write candidate on source")
    verts,normals,faces=read_source(source)
    selected=choose_faces(verts,faces,region)
    # Normal averages and incident geometric resolution are evaluated from
    # original shared positions; disconnected OBJ vertex indices do not
    # artificially break a sculpt seam.
    sums=defaultdict(lambda:[0.,0.,0.])
    min_edge={}
    for f in selected:
        p=[verts[k][0] for k,_ in f]
        raw=cross(sub(p[1],p[0]),sub(p[2],p[0]))
        if sum(v*v for v in raw)<1e-17:continue
        for k,q in enumerate(p):
            group=key(q)
            for c in range(3):sums[group][c]+=raw[c]
            near=min(length(q,p[(k+1)%3]),length(q,p[(k+2)%3]))
            min_edge[group]=min(min_edge.get(group,1e9),near)
    surface={group:unit(values) for group,values in sums.items()}
    low=out/"source_skin_low.obj"
    high=out/"source_skin_high.obj"
    rows_low=["# VQ M33 actual source human region, diagnostic independent UV atlas",
              "o m33_original_skin_section","usemtl skin"]
    rows_high=["# VQ M33 same UV atlas, REAL bounded displacement of M32 source",
               "o m33_micro_sculpted_skin","usemtl skin"]
    count=len(selected)
    grid=math.ceil(math.sqrt(math.ceil(count/2)))
    if grid*grid*2<count:raise AssertionError("UV atlas cell budget")
    touched=0;max_disp=0.
    for index,f in enumerate(selected):
        cell=index//2
        row=cell//grid;col=cell%grid
        # IMPORTANT: cells need both *border gutters* and a *diagonal
        # gutter*. Two unrelated source faces may NOT share a UV diagonal:
        # raster texel centers can land exactly on it, causing ambiguous
        # overlaps in VQ's strict M30 baker. Here each triangle has a true
        # positive-width island separation and still fills >60% of UV0.
        margin=.025
        if index%2:
            pattern=((1-margin,1-margin),(2*margin,1-margin),
                     (1-margin,2*margin))
        else:
            pattern=((margin,margin),(1-2*margin,margin),
                     (margin,1-2*margin))
        for k,(vi,ni) in enumerate(f):
            p,rgb=verts[vi]
            group=key(p)
            n=surface.get(group,normals[ni] if ni is not None else None)
            if n is None:raise ValueError("Missing sampled face normal")
            # Gentle, deterministic microgeometry on original actual skin;
            # cap based on source edge length to protect narrow facial detail.
            dx,dy,dz=p
            wave=math.sin(dx*119+dy*29)*math.cos(dy*97+dz*47)
            amplitude=min(.0014,max(0.,min_edge.get(group,0.)*.08))
            displacement=amplitude*wave
            max_disp=max(max_disp,abs(displacement))
            if abs(displacement)>1e-8:touched+=1
            moved=tuple(p[d]+n[d]*displacement for d in range(3))
            u=(col+pattern[k][0])/grid
            v=(row+pattern[k][1])/grid
            for dest,position in ((rows_low,p),(rows_high,moved)):
                dest.append("v "+" ".join(f"{val:.9f}" for val in position)+
                            " "+" ".join(f"{val:.6f}" for val in rgb))
                dest.append(f"vt {u:.9f} {v:.9f}")
                dest.append("vn "+" ".join(f"{val:.9f}" for val in n))
        base=index*3+1
        for dest in (rows_low,rows_high):
            dest.append("f "+" ".join(f"{j}/{j}/{j}" for j in (base,base+1,base+2)))
    if touched<120 or max_disp<.00008:
        raise ValueError("Real human sculpt patch did not change geometrically")
    out.mkdir(parents=True,exist_ok=True)
    low.write_text("\n".join(rows_low)+"\n",encoding="utf-8")
    high.write_text("\n".join(rows_high)+"\n",encoding="utf-8")
    report={
        "schema_version":1,"engine":"VEYLQUORIN",
        "milestone":"M33","region":region,
        "source_obj_sha256":sha256(source.read_bytes()).hexdigest(),
        "source_faces":len(faces),"selected_real_human_faces":count,
        "low_faces":count,"high_faces":count,
        "atlas_grid_cells":[grid,grid],
        "atlas_method":"per-face two-triangles-per-cell with diagonal and exterior texel-safe UV gutters; diagnostic only, not production seam-aware unwrapping",
        "actual_skin_geometry_was_displaced":True,
        "displaced_corners":touched,
        "max_microsculpt_world_units":round(max_disp,8),
        "low_sha256":sha256(low.read_bytes()).hexdigest(),
        "high_sha256":sha256(high.read_bytes()).hexdigest(),
        "original_human_unchanged":True,
        "gameplay_character_modified":False,
        "face_likeness_verified":False,
        "whole_body_uv_atlas_created":False,
        "normal_baked":False,
        "production_approved":False
    }
    (out/"m33_skin_region_source_manifest.json").write_text(
        json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--obj",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--region",choices=("face","shoulders","hands","feet"),required=True)
    a=p.parse_args()
    info=build(a.obj,a.out,a.region)
    print("VQ_M33_ACTUAL_HUMAN_SKIN_REGION",
          info["region"],info["selected_real_human_faces"],
          "source_sha",info["source_obj_sha256"][:16],
          "source_unchanged",info["original_human_unchanged"])

if __name__=="__main__":
    main()
