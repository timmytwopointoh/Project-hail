#!/usr/bin/env python3
"""VEILFORGE M5: emulator screenshot visual diagnosis and bounded defect queue.

Processes actual, hashed Android screenshots. Detects missing camera changes,
clipped silhouettes, uneven foreground visibility, low-frequency detail, and
cross-view instability. Heuristics only, not AI aesthetic or photoreal grading.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from android_visual_qa import ROLES, VIEWS, BACKGROUND, dialog_overlay_fraction

def silhouette(image):
    im=image.convert("RGB")
    w,h=im.size
    # Reuse normalized central rectangle to exclude varying Android system bars.
    im=im.crop((int(w*.07),int(h*.08),int(w*.93),int(h*.92))).resize((192,192))
    px=list(im.getdata())
    mask=[max(abs(rgb[k]-BACKGROUND[k]) for k in range(3))>=35 for rgb in px]
    return mask,192,192

def outline_analysis(mask,width,height):
    pixels=sum(mask)
    if not pixels:
        return {"coverage":0,"touch_edge_ratio":0,"edge_crossings":0,
                "horizontal_asymmetry":0}
    # Count actual image silhouette contact along an inset margin, not phone UI.
    margin=3
    boundary=[i for i,v in enumerate(mask) if v and
              (i//width<margin or i//width>=height-margin or
               i%width<margin or i%width>=width-margin)]
    # Images can contain legitimate full-screen terrain; these metrics trigger
    # warnings only, never rejection without a semantic asset-type reference.
    left=sum(mask[y*width+x] for y in range(height) for x in range(width//2))
    right=pixels-left
    crossings=0
    y=height//2
    for x in range(1,width):
        if mask[y*width+x]!=mask[y*width+x-1]:crossings+=1
    return {"coverage":round(pixels/(width*height),5),
            "touch_edge_ratio":round(len(boundary)/max(pixels,1),5),
            "edge_crossings":crossings,
            "horizontal_asymmetry":round(abs(left-right)/pixels,5)}

def iou(a,b):
    if len(a)!=len(b):raise ValueError("Mismatched screenshot sizes")
    union=sum(x or y for x,y in zip(a,b))
    return sum(x and y for x,y in zip(a,b))/union if union else 0.

def diagnose(root,out,*,strict_provenance=True):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    reports=list(root.rglob("emulator_visual_qa.json"))
    roles={}
    problems=[];warnings=[];assets={}
    for path in reports:
        data=json.loads(path.read_text(encoding="utf-8"))
        role=data.get("role")
        if role not in ROLES or role in roles:
            problems.append("Unknown or duplicate emulator role "+str(role));continue
        roles[role]=path
        for entry in data.get("assets",[]):
            name=entry.get("asset")
            if name not in ROLES[role] or name in assets:
                problems.append("Unexpected or duplicate asset "+str(name));continue
            views=entry.get("views",[])
            if len(views)!=len(VIEWS):
                problems.append(name+": incomplete Android screenshot set");continue
            measurements=[];masks=[]
            for index,(meta,(yaw,pitch)) in enumerate(zip(views,VIEWS)):
                file=path.parent/meta.get("image","")
                if (meta.get("yaw"),meta.get("pitch"))!=(yaw,pitch):
                    problems.append(name+": mismatched camera specification");break
                if not file.is_file():
                    problems.append(name+": missing frame "+str(index));break
                if strict_provenance and hashlib.sha256(file.read_bytes()).hexdigest()!=meta.get("sha256"):
                    problems.append(name+": altered real emulator frame");break
                from PIL import Image
                with Image.open(file) as frame:
                    if dialog_overlay_fraction(frame)>=.70:
                        problems.append(name+": Android system ANR/modal covers the rendered model; invalid screenshot")
                        break
                    mask,w,h=silhouette(frame)
                masks.append(mask)
                measurements.append(outline_analysis(mask,w,h))
            if len(measurements)!=len(VIEWS):continue
            # A frozen viewer often has identical silhouettes for all angles.
            orbit=[1-iou(masks[0],other) for other in masks[1:]]
            maxdelta=max(orbit)
            unique_looks=sum(v>.03 for v in orbit)
            coverage=[m["coverage"] for m in measurements]
            if maxdelta<.02 or unique_looks<3:
                if name in ("scene","rolling_terrain"):
                    warnings.append({"asset":name,"subject":"silhouette",
                                     "reason":"Wide terrain/scene silhouette stable; verify material and camera movement from original framebuffer"})
                else:
                    problems.append(name+": frozen or insufficient distinct silhouettes")
            if max(coverage)<.004:
                problems.append(name+": missing visible asset across views")
            if max(m["touch_edge_ratio"] for m in measurements)>.10:
                warnings.append({"asset":name,"subject":"framing",
                                 "reason":"Foreground contacts crop boundary; verify if terrain or true clipping"})
            if min(coverage)<.006:
                warnings.append({"asset":name,"subject":"view_visibility",
                                 "reason":"At least one view has very little foreground; check culling/camera"})
            assets[name]={"role":role,"views":len(measurements),
                          "min_coverage":round(min(coverage),4),
                          "max_coverage":round(max(coverage),4),
                          "distinct_orbits":unique_looks,
                          "max_silhouette_change":round(maxdelta,4),
                          "mean_horizontal_asymmetry":round(
                              sum(m["horizontal_asymmetry"] for m in measurements)/len(measurements),4),
                          "framing_warnings":sum(m["touch_edge_ratio"]>.10 for m in measurements)}
    for role,expected in ROLES.items():
        if role not in roles:problems.append("Missing emulator role "+role)
        for name in expected:
            if name not in assets:problems.append("Missing audited asset "+name)
    backlog=[]
    for item in problems:
        backlog.append({"priority":"blocker","owner":"studio",
                        "source":"android-semantic-frames","action":item})
    for warn in warnings:
        backlog.append({"priority":"review","owner":"models",
                        "source":"android-semantic-frames","asset":warn["asset"],
                        "action":warn["reason"]})
    result={"schema_version":1,"engine":"VEILFORGE",
            "mode":"real-android-screenshot-shape-diagnostics",
            "roles":len(roles),"assets_scanned":len(assets),
            "frames_scanned":sum(x["views"] for x in assets.values()),
            "assets":assets,"problems":problems,"warnings":warnings,
            "technical_gate_passed":not problems,"repair_queue":backlog,
            "manual_artistic_review_required":True,
            "photorealism_verified":False,"hardware_performance_verified":False,
            "limitation":"Color-background threshold and silhouettes cannot detect all shading, anatomy, perceptual quality or intentional full-screen geometry."}
    (out/"semantic_visual_review.json").write_text(json.dumps(result,indent=2)+"\n")
    (out/"semantic_repair_queue.json").write_text(json.dumps(backlog,indent=2)+"\n")
    lines=["# VEILFORGE — Android screenshot semantic geometry diagnostics","",
           f"Android roles: {len(roles)}/{len(ROLES)}; actual source assets: {len(assets)};",
           f"Screenshot frames: {result['frames_scanned']}",
           f"Shape diagnostic gate: {'PASS' if not problems else 'FAIL'}",
           "","This does not certify photorealism or subjective quality.",
           "","## Blockers"]+["- "+p for p in problems]
    lines+=["","## Human-review warnings"]+["- "+x["asset"]+": "+x["reason"] for x in warnings]
    (out/"semantic_visual_review.md").write_text("\n".join(lines)+"\n")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=diagnose(args.root,args.out)
    print("VEILFORGE_EMULATOR_SEMANTIC",result["frames_scanned"],
          "frames; passed=",result["technical_gate_passed"],
          "warnings=",len(result["warnings"]))
    if not result["technical_gate_passed"]:raise SystemExit(1)
if __name__=="__main__":main()
