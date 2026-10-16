#!/usr/bin/env python3
"""VEYLQUORIN M31: deterministic, non-overlapping, padded OBJ UV atlas.

Uses triangle-local charts arranged in two isolated triangular cells per
square. Intentionally preserves original 3D vertices/normals/materials and
separates UV seams; does not claim texture-stretch optimization, contiguous
organic UV islands, automatic correspondence to a separate high-poly mesh,
or final artistic approval.

Source OBJ is NEVER overwritten. Refuses insufficient texel density and
malformed faces rather than collapsing UV islands into one texel.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from engine import inspect_obj, read_obj

def plan(face_count,texture_size,padding):
    if type(face_count) is not int or not 1<=face_count<=150000:
        raise ValueError("Invalid source triangle count")
    if type(texture_size) is not int or texture_size not in (128,256,512,1024,2048,4096):
        raise ValueError("Atlas resolution must be a supported power of two")
    if type(padding) is not int or not 1<=padding<=8:
        raise ValueError("Atlas gutter must be 1-8 pixels")
    cells=math.ceil(face_count/2)
    side=math.ceil(math.sqrt(cells))
    pitch=texture_size/side
    # Preserve minimum 16px tile; two triangles need adequate usable area
    # after the outer mip gutter and diagonal isolation gap.
    if pitch<max(16,2*padding+8):
        raise ValueError("Insufficient texel density: increase atlas resolution")
    return {"side":side,"cell_pitch_pixels":pitch,"cell_count":cells,
            "island_count":face_count,"unused_cells":side*side-cells}

def unwrap(source,dest,*,texture_size=1024,padding=2):
    source=Path(source);dest=Path(dest)
    if source.resolve()==dest.resolve():
        raise ValueError("Never overwrite the source OBJ")
    if not source.is_file() or source.is_symlink():
        raise ValueError("Unsafe/missing source OBJ")
    v,old_uv,n,faces=read_obj(source)
    mesh=inspect_obj(source)
    spec=plan(len(faces),texture_size,padding)
    if mesh["degenerate_triangles"]:
        raise ValueError("Cannot UV-atlas source with collapsed 3D faces")
    # No existing topology, shading, or material definitions are altered.
    # Positive vertex and normal OBJ references are explicitly reconstructed
    # from the strict original triangle parser; no source indices are guessed.
    uv=[]
    face_lines=[]
    side=spec["side"]
    pitch=texture_size/side
    for fi,tri in enumerate(faces):
        cell=fi//2
        col,row=cell%side,cell//side
        x0=(col*pitch+padding)/texture_size
        y0=(row*pitch+padding)/texture_size
        x1=((col+1)*pitch-padding)/texture_size
        y1=((row+1)*pitch-padding)/texture_size
        gap=1/texture_size
        if fi%2==0:
            local=((x0,y0),(x1-gap,y0),(x0,y1-gap))
        else:
            local=((x1,y1),(x0+gap,y1),(x1,y0+gap))
        start=len(uv)
        uv.extend(local)
        corners=[]
        for k,ref in enumerate(tri):
            vi,_,ni=ref
            piece=f"{vi+1}/{start+k+1}"
            if ni is not None:piece+=f"/{ni+1}"
            corners.append(piece)
        face_lines.append("f "+" ".join(corners)+"\n")
    raw=source.read_text(encoding="utf-8").splitlines(keepends=True)
    result=[]
    written_uv=False
    face_index=0
    for line in raw:
        parts=line.partition("#")[0].strip().split()
        kind=parts[0] if parts else ""
        if kind=="vt":continue
        if kind=="f":
            if not written_uv:
                for x,y in uv:result.append(f"vt {x:.11f} {y:.11f}\n")
                written_uv=True
            result.append(face_lines[face_index]);face_index+=1
        else:result.append(line)
    if face_index!=len(faces):
        raise ValueError("OBJ face ordering changed unexpectedly")
    # Reused source geometry means original inspector topology must remain
    # identical. Each chart uses independent positive UV corner references.
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text("".join(result),encoding="utf-8")
    try:
        out=inspect_obj(dest)
        before=inspect_obj(source)
        fixed=("triangles","vertices_raw","vertices_welded","normals",
               "boundary_edges","nonmanifold_edges","degenerate_triangles",
               "duplicate_triangles","bounds_min","bounds_max")
        regress=[key for key in fixed if out[key]!=before[key]]
        if regress or out["uvs"]!=len(faces)*3 or out["uvs_outside_zero_one"]:
            raise ValueError("Atlas altered source geometry or has invalid UV coverage: "+str(regress))
        from vq_mesh_baker import uv_rows
        # This checks every triangle's UV orientation and nonzero area using
        # the same strict parser as the high-to-low mesh baker.
        uv_rows(dest)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    result={
        "schema_version":1,"engine":"VEYLQUORIN","milestone":"M31",
        "method":"padded triangle-local deterministic atlas",
        "source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
        "candidate_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
        "source_triangles":len(faces),"charts":len(faces),
        "texture_size":texture_size,"gutter_pixels":padding,
        "cell_pitch_pixels":round(pitch,4),"cells_per_side":side,
        "geometry_invariants_preserved":True,
        "original_uvs_replaced":True,
        "source_uv_atlas_tiling_preserved":False,
        "original_source_unmodified":True,
        "new_material_maps_required":True,
        "texture_stretch_optimized":False,
        "continuous_surface_islands_preserved":False,
        "compatible_with_unique_uv_high_low_baker":True,
        "production_approved":False,"android_emulator_verified":False,
        "manual_artistic_review_required":True}
    review=dest.parent/(dest.stem+"_atlas_report.json")
    review.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--obj",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--size",type=int,default=1024)
    p.add_argument("--padding",type=int,default=2)
    a=p.parse_args()
    m=unwrap(a.obj,a.out,texture_size=a.size,padding=a.padding)
    print("VQ_M31_UNIQUE_ATLAS_PASS",m["source_triangles"],
          "charts at",m["texture_size"],"pixels")
if __name__=="__main__":main()
