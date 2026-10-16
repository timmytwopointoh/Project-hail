#!/usr/bin/env python3
"""VEILFORGE M31: reproducible numeric silhouette coaching, not visual identity AI.

Looks at actual exported T-pose OBJ vertices and measurements derived from
the user's generated T-pose reference. No reference-image bytes are placed in
GitHub, and no claim of photorealism or calibrated camera correspondence
can be made from this simplified orthographic comparison.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

DEFAULT_TARGET=Path(__file__).with_name("human_reference_targets.json")

def source_vertices(obj: Path):
    with obj.open("r",encoding="utf-8",errors="replace") as stream:
        for row in stream:
            if not row.startswith("v "):
                continue
            entries=row.split()
            if len(entries)<4:
                raise ValueError("Invalid OBJ geometry row")
            x,y,z=(float(v) for v in entries[1:4])
            if not all(map(math.isfinite,(x,y,z))):
                raise ValueError("Nonfinite source geometry")
            yield x,y,z

def evaluate(obj: Path,target: Path=DEFAULT_TARGET):
    spec=json.loads(target.read_text(encoding="utf-8"))
    if spec["schema_version"]!=1 or spec["pixels_in_repository"] is not False:
        raise ValueError("Reference provenance or schema invalid")
    points=list(source_vertices(obj))
    if len(points)<3000:
        raise ValueError("Must inspect a real complete human model")
    ys=[p[1] for p in points]
    max_y,min_y=max(ys),min(ys)
    height=max_y-min_y
    if height<.5 or not math.isfinite(height):
        raise ValueError("Source not a human-sized model")
    xmin=min(p[0] for p in points)
    xmax=max(p[0] for p in points)
    target_data=spec["normalized_target"]
    expected=target_data["arm_span_over_height"]
    armspan=(xmax-xmin)/height
    lines=[]
    for row in target_data["slices"]:
        top=row["top_fraction"]
        # Bin source vertices around the same normalized image-height level.
        # ±1.5% is wide enough for dense M28 skin topology, not a fitted
        # screen-projection silhouette with camera occlusion.
        band=[p[0] for p in points if abs((max_y-p[1])/height-top)<.015]
        if len(band)<9:
            lines.append({"region":row["name"],"source_sample_vertices":len(band),
                          "warning":"insufficient source vertices"})
            continue
        measured=(max(band)-min(band))/height
        target_width=row["width_over_height"]
        delta=measured-target_width
        lines.append({
            "region":row["name"],
            "reference_fraction_from_top":top,
            "target_width_over_height":target_width,
            "model_width_over_height":round(measured,5),
            "signed_difference":round(delta,5),
            "absolute_error":round(abs(delta),5),
            "source_sample_vertices":len(band),
            "review_needed":abs(delta)>.06
        })
    good=[x for x in lines if "absolute_error" in x]
    if len(good)<8:
        raise ValueError("Insufficient real model cross-sectional evidence")
    # Corrections are recommendations to the sculpt curriculum, not commands
    # that automatically mutate the fully playable hero or an unreviewed mesh.
    deviations=sorted(good,key=lambda r:r["absolute_error"],reverse=True)
    priorities=[{"region":x["region"],"error":x["absolute_error"],
                 "type":"too_wide" if x["signed_difference"]>0 else "too_narrow",
                 "owner":"silhouette_refinement",
                 "manual_visual_review_required":True}
                for x in deviations if x["review_needed"]]
    return {
        "schema_version":1,
        "engine":"VEILFORGE",
        "milestone":"M31",
        "source_obj_sha256":hashlib.sha256(obj.read_bytes()).hexdigest(),
        "target_json_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
        "reference_image":spec["reference_image"],
        "reference_pixels_in_repository":False,
        "compare_type":"orthographic_height-normalized_vertex_span",
        "source_vertices":len(points),
        "model_height_units":round(height,5),
        "target_armspan_over_height":expected,
        "model_armspan_over_height":round(armspan,5),
        "armspan_error":round(abs(armspan-expected),5),
        "cross_section_comparison":lines,
        "mean_absolute_cross_section_error":round(
            sum(r["absolute_error"] for r in good)/len(good),5),
        "manual_review_queue":priorities,
        "reference_camera_calibrated":False,
        "photorealism_verified":False,
        "artistic_approval":False,
        "safe_to_auto_promote":False
    }

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--obj",type=Path,required=True)
    a.add_argument("--target",type=Path,default=DEFAULT_TARGET)
    a.add_argument("--out",type=Path,required=True)
    v=a.parse_args()
    report=evaluate(v.obj,v.target)
    v.out.parent.mkdir(parents=True,exist_ok=True)
    v.out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print("VEILFORGE_M31_REFERENCE_FIT",
          "arm_ratio",report["model_armspan_over_height"],
          "silhouette_abs_error",report["mean_absolute_cross_section_error"],
          "review_regions",len(report["manual_review_queue"]),
          "art_approved",report["artistic_approval"])

if __name__=="__main__":
    main()
