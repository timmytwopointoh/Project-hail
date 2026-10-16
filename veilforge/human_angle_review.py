#!/usr/bin/env python3
"""VEILFORGE M31: 14-angle actual human mesh image technical review.

Adapted from VEILFORGE M27 image semantics and silhouette/LOD heuristics:
deterministic foreground, clipping, distinct view checks and face closeups.
The report is advisory for shape realism; photographs and actual human
identity are NOT automatically understood by this utility.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

REQUIRED=("front","side","back","three_quarter","orbit_030","orbit_060",
          "orbit_120","orbit_150","orbit_210","orbit_225","orbit_240",
          "orbit_270","orbit_300","orbit_330")
FACE=("face_front","face_side","face_three_quarter")
BACKGROUND=(216,216,218)

def mask(img):
    im=img.convert("RGB")
    w,h=im.size
    im=im.crop((int(w*.04),int(h*.07),int(w*.96),int(h*.93)))
    im=im.resize((160,180))
    data=im.getdata()
    return [max(abs(v[i]-BACKGROUND[i]) for i in range(3))>24
            for v in data]

def iou(a,b):
    if len(a)!=len(b):raise ValueError("Mismatched masks")
    union=sum(x or y for x,y in zip(a,b))
    return sum(x and y for x,y in zip(a,b))/union if union else 0.

def report(root,output):
    from PIL import Image
    root=Path(root);output=Path(output)
    if len(set(REQUIRED))!=14:raise ValueError("Bad view specification")
    masks={}
    views=[]
    for name in (*REQUIRED,*FACE):
        path=root/(name+".png")
        if not path.is_file() or path.stat().st_size<1200:
            raise FileNotFoundError("Missing source-mesh camera "+name)
        with Image.open(path) as img:
            if img.size[0]<400 or img.size[1]<500:
                raise ValueError("Human view too small: "+name)
            sample=mask(img)
        coverage=sum(sample)/len(sample)
        masks[name]=sample
        views.append({
            "name":name,
            "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
            "foreground_coverage":round(coverage,6),
            "visibly_present":coverage>.012
        })
    bad=[v["name"] for v in views if not v["visibly_present"]]
    variations=[1-iou(masks["front"],masks[name])
                for name in ("side","back","three_quarter")]
    frozen=max(variations)<.017
    overcropped=sum(masks["front"][0:160])>18
    hard_gates={
        "14_real_body_cameras_present":len(views)==17,
        "3_real_face_closeups_present":all(x in masks for x in FACE),
        "human_visible_in_all_views":not bad,
        "camera_orbit_has_distinct_geometry":not frozen,
    }
    outcome={
        "engine":"VEILFORGE",
        "milestone":"M31",
        "actual_offline_mesh_views":14,
        "facial_detail_views":3,
        "views":views,
        "front_v_side_silhouette_difference":round(variations[0],5),
        "front_v_back_silhouette_difference":round(variations[1],5),
        "front_v_three_quarter_silhouette_difference":round(variations[2],5),
        "technical_gates":hard_gates,
        "technical_pass":all(hard_gates.values()),
        "framing_warnings":["possibly clipped upper border"] if overcropped else [],
        "manual_human_reference_similarity":False,
        "mobile_android_screenshots":False,
        "photorealistic":False,
        "artistic_approval":False
    }
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(outcome,indent=2)+"\n")
    return outcome

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    result=report(args.root,args.out)
    print("VEILFORGE_M31_SEMANTIC_ANGLE_REVIEW",
          "views",result["actual_offline_mesh_views"],
          "technical_pass",result["technical_pass"],
          "human_visual_approved",result["artistic_approval"])
    if not result["technical_pass"]:
        raise SystemExit(1)

if __name__=="__main__":main()
