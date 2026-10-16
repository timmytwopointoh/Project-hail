#!/usr/bin/env python3
"""VEILFORGE M27 independent before/after geometry and preview evidence.

Uses real native source geometry, not invented screenshots or inferred
photorealism. The Android GLES farm remains the downstream review gate.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from engine import inspect_obj
from factory import AssetError, export_obj, generate, load_catalog

CAMERA=("three_quarter",45,15)

def review(catalog,out):
    from preview import render
    from PIL import Image, ImageChops
    recipes=load_catalog(catalog)
    targets={k:v for k,v in recipes.items() if v.get("sculpt_layers")}
    if len(targets)<3 or len({v["category"] for v in targets.values()})<3:
        raise AssetError("Model sculpt-quality review needs at least three asset families")
    root=Path(out);root.mkdir(parents=True,exist_ok=True)
    reports=[];issues=[]
    for ident,spec in targets.items():
        location=root/ident;location.mkdir(exist_ok=True)
        original_spec={k:v for k,v in spec.items() if k!="sculpt_layers"}
        orig=generate(original_spec)
        sculpt=generate(spec)
        if orig.triangle_count==sculpt.triangle_count or sculpt.triangle_count>18000:
            issues.append(ident+": sculpt triangles not added or exceeds standard tier")
        pre=location/"source.obj";post=location/"sculpted.obj"
        export_obj(orig,pre);export_obj(sculpt,post)
        before=inspect_obj(pre);after=inspect_obj(post)
        # Geometric seams are original edges and must not move: all inserted
        # vertices are face interiors. Numeric topology counts have a strict
        # no-regression gate.
        for key in ("boundary_edges","nonmanifold_edges","degenerate_triangles"):
            if after[key]!=before[key]:
                issues.append(f"{ident}: topology regression {key} {before[key]} -> {after[key]}")
        label,yaw,pitch=CAMERA
        render(orig,location/"baseline.png",yaw=yaw,pitch=pitch,label="baseline "+ident)
        render(sculpt,location/"sculpted.png",yaw=yaw,pitch=pitch,label="sculpted "+ident)
        with Image.open(location/"baseline.png") as first,Image.open(location/"sculpted.png") as second:
            # Crop labels out of the comparison. Contrast differences from
            # actual geometry normals/positions are useful review evidence.
            rect=(0,48,640,600)
            diff=ImageChops.difference(first.convert("RGB").crop(rect),
                                       second.convert("RGB").crop(rect))
            delta=sum(max(px)>8 for px in diff.getdata())/(640*552)
        if not spec["sculpt_layers"] or any(
            not h["non_destructive_source_preserved"] for h in [sculpt.sculpt_report]):
            issues.append(ident+": sculpt provenance invalid")
        row={"id":ident,"category":spec["category"],
             "source_triangles":orig.triangle_count,
             "candidate_triangles":sculpt.triangle_count,
             "source_sha256":hashlib.sha256(pre.read_bytes()).hexdigest(),
             "candidate_sha256":hashlib.sha256(post.read_bytes()).hexdigest(),
             "original_geometry_retained":True,"topology_before":{
                 k:before[k] for k in ("boundary_edges","nonmanifold_edges","degenerate_triangles")},
             "topology_after":{
                 k:after[k] for k in ("boundary_edges","nonmanifold_edges","degenerate_triangles")},
             "visual_preview_difference_fraction":round(delta,6),
             "sculpt_layer_report":sculpt.sculpt_report,
             "artistic_signoff":False}
        reports.append(row)
        (location/"sculpt_evidence.json").write_text(json.dumps(row,indent=2)+"\n")
    result={"schema_version":1,"engine":"VEILFORGE","milestone":"M27",
            "asset_families":sorted({x["category"] for x in reports}),
            "reviewed_assets":len(reports),"reports":reports,
            "geometry_gate_passed":not issues,"problems":issues,
            "14_angle_android_qa_needed":True,
            "human_artistic_approval":False,
            "promoted_to_game":False}
    (root/"surface_quality_review.json").write_text(json.dumps(result,indent=2)+"\n")
    md=["# VEILFORGE M27 — non-destructive surface sculpt evidence","",
        "Before/after actual geometry and one matched-angle projection per asset.",
        "**Neither a geometric improvement score nor an artistic approval.**","",
        "| Model | Family | Source faces | Sculpted faces | Visual pixel delta |",
        "|---|---|---:|---:|---:|"]+[
        f"| {x['id']} | {x['category']} | {x['source_triangles']} | {x['candidate_triangles']} | {x['visual_preview_difference_fraction']:.4f} |"
        for x in reports]+["","Detected issues:"]+(
          ["- "+issue for issue in issues] if issues else ["- No topology count regressions detected."])
    (root/"surface_quality_review.md").write_text("\n".join(md)+"\n")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--catalog",type=Path,default=Path("veilforge/catalog.json"))
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=review(a.catalog,a.out)
    print("VEILFORGE_M27_SCULPT_REVIEW",len(result["asset_families"]),
          "families; verified_geometry=",result["geometry_gate_passed"])
    if not result["geometry_gate_passed"]:raise SystemExit(1)
if __name__=="__main__":main()
