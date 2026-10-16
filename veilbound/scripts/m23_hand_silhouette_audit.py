#!/usr/bin/env python3
"""Offline preview rejection gate: four independently visible finger columns plus a thumb.
This is NOT proof of anatomical rig quality, Android visibility or photorealism.
"""
import argparse
import json
from pathlib import Path
from PIL import Image

FINGER_ROWS=(435,460,480)
THUMB_ROW=370

def skin_runs(image,y):
    im=image.convert("RGB")
    spans=[]
    for x in range(35,im.width-35):
        r,g,b=im.getpixel((x,y))
        if not (r<205 and g<180 and b<160):
            continue
        if spans and x<=spans[-1][1]+1:
            spans[-1][1]=x
        else:
            spans.append([x,x])
    return [[a,b] for a,b in spans if b-a+1>=12]

def audit(selected):
    sides={}
    passed=True
    for side in ("left","right"):
        image=selected/(side+"_hand_front.png")
        if not image.is_file():
            sides[side]={"error":"missing rendered hand closeup"}
            passed=False
            continue
        im=Image.open(image)
        rows={str(y):skin_runs(im,y) for y in FINGER_ROWS}
        thumb=skin_runs(im,THUMB_ROW)
        counts={y:len(spans) for y,spans in rows.items()}
        distinct=all(n==4 for n in counts.values())
        thumb_distinct=len(thumb)>=5
        passed=passed and distinct and thumb_distinct
        sides[side]={
            "finger_column_counts":counts,
            "finger_column_spans":rows,
            "thumb_row":THUMB_ROW,
            "thumb_row_column_count":len(thumb),
            "four_visible_fingers":distinct,
            "separate_thumb_silhouette":thumb_distinct,
        }
    return {
        "gate":"offline_front_visible_digit_silhouettes",
        "result":"pass" if passed else "reject_for_manual_rework",
        "digit_count_target":"four fingers plus one thumb per side",
        "human_visual_review_required":True,
        "android15_screenshot_review_required":True,
        "photo_realism_proven":False,
        "sides":sides,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--selected",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--fail-on-reject",action="store_true")
    args=p.parse_args()
    report=audit(args.selected)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"result":report["result"],
         "counts":{side:entry.get("finger_column_counts")
                   for side,entry in report["sides"].items()}},indent=2))
    return int(args.fail_on_reject and report["result"]!="pass")

if __name__=="__main__":
    raise SystemExit(main())
