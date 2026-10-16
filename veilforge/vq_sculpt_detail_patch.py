#!/usr/bin/env python3
"""Generate a reproducible true high-resolution sculpted test surface.

The low/high grids share the exact UV atlas. High mesh actually contains
wave-displaced vertices (not a shader trick). This is a reference TEST
fixture of the general-purpose high-to-low mesh baker, not a character.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from engine import inspect_obj

def mesh(path,subdivisions,*,high,amplitude=.016):
    if not 4<=subdivisions<=128:raise ValueError("Invalid sculpt grid resolution")
    if not 0<amplitude<=.03:raise ValueError("Invalid sculpt strength")
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    lines=["# VEYLQUORIN source-generated reference geometry, meters, Y-up",
           "o high_detail_reference" if high else "o low_reference",
           "usemtl stone"]
    for z in range(subdivisions+1):
        for x in range(subdivisions+1):
            u=x/subdivisions;v=z/subdivisions
            envelope=(math.sin(math.pi*u)*math.sin(math.pi*v))**2
            y=amplitude*envelope*(
                .55*math.sin(13*math.pi*u)*math.sin(11*math.pi*v)+
                .45*math.sin(22*math.pi*u+.6)*math.sin(15*math.pi*v+.2)) if high else 0
            lines.append(f"v {u*2:.9f} {y:.9f} {v*2:.9f} .72 .67 .58")
    for z in range(subdivisions+1):
        for x in range(subdivisions+1):
            lines.append(f"vt {x/subdivisions:.9f} {z/subdivisions:.9f}")
    lines.append("vn 0 1 0")
    span=subdivisions+1
    for z in range(subdivisions):
        for x in range(subdivisions):
            a=z*span+x+1;b=a+1;c=a+span;d=c+1
            for i,j,k in ((a,d,b),(a,c,d)):
                lines.append(f"f {i}/{i}/1 {j}/{j}/1 {k}/{k}/1")
    path.write_text("\n".join(lines)+"\n",encoding="utf-8")
    return inspect_obj(path)

def build(out,*,low_segments=4,high_segments=40):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    low=out/"source_low.obj";high=out/"source_high.obj"
    low_qa=mesh(low,low_segments,high=False)
    high_qa=mesh(high,high_segments,high=True)
    if high_qa["triangles"]<=low_qa["triangles"]*20:
        raise ValueError("Fixture lacks higher-detail mesh")
    result={"schema_version":1,"milestone":"M30","source":"actual triangulated geometry",
            "low_triangles":low_qa["triangles"],"high_triangles":high_qa["triangles"],
            "low_sha256":hashlib.sha256(low.read_bytes()).hexdigest(),
            "high_sha256":hashlib.sha256(high.read_bytes()).hexdigest(),
            "manually_approved":False,"source_geometry_baked":False}
    (out/"sculpt_source_manifest.json").write_text(json.dumps(result,indent=2)+"\n")
    return result
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    r=build(a.out)
    print("VQ_M30_SCULPT_SOURCE_PASS",r["low_triangles"],r["high_triangles"])
if __name__=="__main__":main()
