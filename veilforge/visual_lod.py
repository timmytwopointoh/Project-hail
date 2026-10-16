#!/usr/bin/env python3
"""VEILFORGE M4 LOD visual regression check based on *real emulator frames*.

Architecture standard/mobile views are compared in the same camera positions
across DIFFERENT virtual devices. This is a conservative visual heuristic, not
perceptual similarity or artistic signoff, and no external reference is faked.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

BACKGROUND=(17,21,29)
PAIR=("ancient_gate_standard","ancient_gate_mobile")

def foreground(im):
    im=im.convert("RGB")
    w,h=im.size
    # Crop off Android navigation and system bars, which may be dark.
    im=im.crop((int(w*.07),int(h*.08),int(w*.93),int(h*.92))).resize((256,256))
    out=[]
    for r,g,b in im.getdata():
        out.append(max(abs(r-BACKGROUND[0]),abs(g-BACKGROUND[1]),abs(b-BACKGROUND[2]))>29 and
                   (max(r,g,b)-min(r,g,b)>7 or max(r,g,b)>85))
    return out

def iou(a,b):
    if len(a)!=len(b):raise ValueError("Bad silhouette dimension")
    intersection=sum(x and y for x,y in zip(a,b))
    union=sum(x or y for x,y in zip(a,b))
    return intersection/union if union else 0

def report(root,out):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    reports=list(root.rglob("emulator_visual_qa.json"))
    images={}
    for file in reports:
        record=json.loads(file.read_text())
        for asset in record["assets"]:
            if asset["asset"] in PAIR:
                images[asset["asset"]]=[(file.parent/v["image"],v["yaw"],v["pitch"]) for v in asset["views"]]
    if set(images)!=set(PAIR):
        raise ValueError("LOD comparisons require actual mobile and standard emulator captures")
    standard,mobile=(images[k] for k in PAIR)
    if len(standard)!=14 or len(mobile)!=14:
        raise ValueError("Need exactly 14 real frames at each LOD")
    from PIL import Image
    comparisons=[]
    for first,second in zip(standard,mobile):
        if first[1:]!=second[1:]:
            raise ValueError("LOD cameras must match exactly")
        with Image.open(first[0]) as a,Image.open(second[0]) as b:
            u,v=foreground(a),foreground(b)
            similarity=iou(u,v)
            comparisons.append({"yaw":first[1],"pitch":first[2],
                "silhouette_iou":round(similarity,4),
                "standard_coverage":round(sum(u)/len(u),4),
                "mobile_coverage":round(sum(v)/len(v),4)})
    summary={
        "schema_version":1,"pair":list(PAIR),"samples":len(comparisons),
        "mean_silhouette_iou":round(sum(c["silhouette_iou"] for c in comparisons)/len(comparisons),4),
        "min_silhouette_iou":round(min(c["silhouette_iou"] for c in comparisons),4),
        "views":comparisons,"captures_from_android_emulator":True,
        "quality_heuristic_only":True,"artistic_approval":False,
        "quality_warning":False}
    # Reference frames come from different Android emulators with different
    # display sizes. Use a deliberately conservative threshold until calibrated.
    summary["quality_warning"]=summary["mean_silhouette_iou"]<.35
    (out/"visual_lod_report.json").write_text(json.dumps(summary,indent=2)+"\n")
    (out/"visual_lod_report.md").write_text(
        "# VEILFORGE mobile-vs-standard screenshot silhouette comparison\n\n"+
        f"14 actual Android screenshots per LOD; mean IoU {summary['mean_silhouette_iou']:.3f}; "+
        f"min IoU {summary['min_silhouette_iou']:.3f}.\n\n"+
        ("**Potential silhouette regression: prioritize review.**\n" if summary["quality_warning"] else
         "Geometry silhouette roughly consistent under the conservative check.\n")+
        "\nStill requires artist and physical-device validation.\n")
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();x=report(a.root,a.out)
    print("VEILFORGE_ANDROID_LOD_COMPARE",x["mean_silhouette_iou"],"warning",x["quality_warning"])

if __name__=="__main__":
    main()
