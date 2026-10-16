#!/usr/bin/env python3
"""VEILFORGE M29: strain/tearing QA on actually exported triangle-stream OBJ.

Source and posed OBJ must share all triangle vertices/materials. The audit
checks geometric edge stretch AND hip/torso leakage, detecting bad reference
poses that normal/mesh-topology checks alone mistakenly accepted. It does
not judge photographic attractiveness or replace human multi-angle review.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

def vertices(obj: Path):
    with obj.open(encoding="utf-8",errors="replace") as stream:
        for line in stream:
            if line.startswith("v "):
                values=tuple(float(x) for x in line.split()[1:7])
                if len(values)!=6 or not all(math.isfinite(v) for v in values):
                    raise ValueError("Nonfinite, uncolored or malformed OBJ vertex")
                yield values

def audit(source: Path, posed: Path, *, variant: str="tpose"):
    if variant not in ("tpose","relaxed"):
        raise ValueError("Expected T-pose or relaxed reference")
    left=vertices(source);right=vertices(posed)
    triangles=0
    extreme_faces=0
    strained_faces=0
    extreme_edges=0
    max_ratio=0.
    leaked_body=0
    protected_garments_shifted=0
    max_shift=0.
    while True:
        base=list(next(left,None) for _ in range(3))
        posed_tri=list(next(right,None) for _ in range(3))
        if all(p is None for p in base+posed_tri):
            break
        if any(p is None for p in base+posed_tri):
            raise ValueError("Triangle-stream cardinality differs")
        triangles+=1
        local=[]
        for p,q in zip(base,posed_tri):
            if p[3:]!=q[3:]:
                raise ValueError("Pose modified skin/eye/hair vertex material")
            delta=math.dist(p[:3],q[:3])
            max_shift=max(max_shift,delta)
            x,y,z=p[:3]
            if abs(x)<.405 and .95<y<1.62 and delta>.065:
                leaked_body+=1
            is_shorts=p[3]<.29 and p[4]<.28 and p[5]<.28 and y<1.68
            if is_shorts and delta>.000005:
                protected_garments_shifted+=1
        for i,j in ((0,1),(1,2),(2,0)):
            before=math.dist(base[i][:3],base[j][:3])
            after=math.dist(posed_tri[i][:3],posed_tri[j][:3])
            if before<1.e-6:
                raise ValueError("Baseline contains near-zero triangle edge")
            factor=max(after/before,before/max(after,1.e-8))
            local.append(factor)
            max_ratio=max(max_ratio,factor)
            if factor>10:extreme_edges+=1
        if max(local)>3:strained_faces+=1
        if max(local)>10:extreme_faces+=1
    if triangles<20:raise ValueError("No reference character triangles")
    # Grounded thresholds: this is a reference rig STRESS gate, not visual AI.
    # The current M29 experimental T-pose exceeds these and is deliberately
    # NOT approved while the same base model passes pure geometry/unit tests.
    geometry_ok=(extreme_faces<=15 and strained_faces<=250 and
                 leaked_body<=35 and protected_garments_shifted==0)
    return {
        "schema_version":1,
        "engine":"VEILFORGE",
        "iteration":"M29",
        "pose":variant,
        "triangles_evaluated":triangles,
        "triangle_faces_stretched_over_3x":strained_faces,
        "triangle_faces_stretched_over_10x":extreme_faces,
        "edges_stretched_over_10x":extreme_edges,
        "max_edge_stretch_ratio":round(max_ratio,5),
        "lower_torso_and_pelvis_vertices_displaced":leaked_body,
        "protected_garment_vertices_displaced":protected_garments_shifted,
        "max_vertex_displacement":round(max_shift,5),
        "geometric_stretch_accepted":geometry_ok,
        "manual_reference_likeness_approved":False,
        "photo_realistic":False,
        "auto_promoted":False,
        "recovery_priority":"rig segmentation and connected shoulder/hip deformation" if not geometry_ok else
                            "visual reference comparison pending",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--baseline",type=Path,required=True)
    p.add_argument("--posed",type=Path,required=True)
    p.add_argument("--variant",choices=("tpose","relaxed"),required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=audit(a.baseline,a.posed,variant=a.variant)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("VEILFORGE_M29_POSE_STRAIN",report["pose"],
          "accepted",report["geometric_stretch_accepted"],
          "stretched",report["triangle_faces_stretched_over_3x"],
          "body_leak",report["lower_torso_and_pelvis_vertices_displaced"])

if __name__=="__main__":
    main()
