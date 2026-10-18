#!/usr/bin/env python3
"""Independent manager of Android emulator evidence + scoped repair backlog.

Fail closed if any expected device, actual screenshot or required asset view is
missing; green geometry-only CI never counts as real Android visual QA.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from android_visual_qa import ROLES, VIEWS

def review(root,out,source_sha,apk_sha):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    findings=[];issues=[];repair=[]
    if len(source_sha)!=40 or len(apk_sha)!=64:
        raise ValueError("Invalid expected commit or APK checksum")
    for role,names in ROLES.items():
        matches=list(root.rglob("emulator_visual_qa.json"))
        matches=[p for p in matches if p.parent.name in (role,"veilforge-android-"+role)]
        if len(matches)!=1:
            issues.append(f"{role}: expected one isolated emulator report, found {len(matches)}")
            repair.append({"owner":"studio","priority":"blocker","subject":role,
                           "action":"Restore missing Android emulator QA worker/capture"})
            continue
        path=matches[0]
        try:
            r=json.loads(path.read_text())
            if (r.get("role")!=role or r.get("source_commit")!=source_sha or
                r.get("apk_sha256")!=apk_sha or r.get("device_android_api")!=35 or
                r.get("technical_visual_smoke_pass") is not True or
                r.get("material_textures_uploaded") is not True or
                r.get("screenshots_clear_of_modal_ui") is not True or
                r.get("texture_counts",{}).get("basecolor",0)<8 or
                r.get("texture_counts",{}).get("metallic_roughness",0)<8 or
                r.get("artistic_quality_approved") is not False or
                r.get("physical_device_qa_pass") is not False):
                issues.append(f"{role}: invalid device/checksum/approval attestations")
            assets=r.get("assets",[])
            if tuple(x.get("asset") for x in assets)!=names:
                issues.append(f"{role}: expected captured assets differ")
            count=0
            # Independent stale-frame detection across distinct assets.
            first_asset_by_sha={}
            for a in assets:
                name=a["asset"]
                if len(a.get("views",[]))!=len(VIEWS):
                    issues.append(f"{role}/{name}: not all 14 actual view frames present")
                if a.get("max_orbit_change",0)<.0006:
                    issues.append(f"{role}/{name}: camera orbit not visually detectable")
                # A delayed compositor replay can skip adjacent-frame checks.
                first_view_by_sha={}
                for index,v in enumerate(a["views"]):
                    count+=1
                    digest=v.get("sha256")
                    if isinstance(digest,str) and len(digest)==64:
                        prior_view=first_view_by_sha.setdefault(
                            digest,(index,v.get("yaw"),v.get("pitch")))
                        if prior_view[0]!=index:
                            kind=("adjacent" if index==prior_view[0]+1
                                  else "nonadjacent")
                            issues.append(
                                f"{role}/{name}: repeated {kind} screenshot: "
                                f"first yaw={prior_view[1]} pitch={prior_view[2]} "
                                f"replayed yaw={v.get('yaw')} pitch={v.get('pitch')} "
                                "(stale camera presentation)")
                    if isinstance(digest,str) and len(digest)==64:
                        prior=first_asset_by_sha.setdefault(
                            digest,(name,v.get("yaw"),v.get("pitch")))
                        if prior[0]!=name:
                            issues.append(
                                f"{role}: cross-asset identical screenshot: "
                                f"{prior[0]} yaw={prior[1]} pitch={prior[2]} "
                                f"and {name} yaw={v.get('yaw')} pitch={v.get('pitch')} "
                                "(stale asset presentation)")
                    # Require exact camera metadata and canonical screenshot path.
                    if index >= len(VIEWS):
                        issues.append(f"{role}/{name}: unexpected camera view index {index}")
                        continue
                    expected_yaw,expected_pitch=VIEWS[index]
                    if (v.get("yaw"),v.get("pitch"))!=(expected_yaw,expected_pitch):
                        issues.append(
                            f"{role}/{name}: camera angle mismatch at view {index}: "
                            f"expected yaw={expected_yaw} pitch={expected_pitch}, "
                            f"got yaw={v.get('yaw')} pitch={v.get('pitch')}")
                    expected_image=(f"{name}/{index:02d}_yaw{expected_yaw}_"
                                    f"pitch{expected_pitch}.png")
                    if v.get("image")!=expected_image:
                        issues.append(f"{role}/{name}: camera screenshot path mismatch at view {index}")
                        continue
                    img=path.parent/expected_image
                    if not img.is_file() or img.stat().st_size<1000 or (
                        hashlib.sha256(img.read_bytes()).hexdigest()!=v["sha256"]):
                        issues.append(f"{role}/{name}: screenshot missing/changed")
                    if v.get("modal_overlay_fraction",1)>=.70:
                        issues.append(f"{role}/{name}: system-UI dialog obscured actual 3D frame")
                    if (v.get("foreground_fraction",0)<.0015 or v.get("channel_stddev",0)<3):
                        issues.append(f"{role}/{name}: blank or near-empty actual render")
            if count!=len(VIEWS)*len(names) or r.get("screenshot_count")!=count:
                issues.append(f"{role}: view count mismatch")
            if not (path.parent/"device_logcat.txt").is_file():
                issues.append(f"{role}: GPU/error log missing")
            if not (path.parent/"android_meminfo.txt").is_file():
                issues.append(f"{role}: Android process memory report missing")
            findings.append({"worker":role,"assets":len(assets),"images":count,
                "android_api":r.get("device_android_api"),
                "apk_sha256":r.get("apk_sha256"),
                "real_material_textures":r.get("texture_counts")})
        except (OSError,ValueError,KeyError,TypeError) as e:
            issues.append(f"{role}: corrupt emulator evidence ({e})")
    if issues:
        for msg in issues[:40]:
            repair.append({"owner":"studio","priority":"blocker",
                           "subject":"android_render_qa","action":msg})
    report={"schema_version":1,"engine":"VEILFORGE","mode":"android_gles_emulator",
        "required_roles":list(ROLES),"devices_passed":len(findings),
        "expected_devices":len(ROLES),"screenshots_checked":sum(x["images"] for x in findings),
        "worker_results":findings,"all_emulator_gates_passed":not issues,
        "problems":issues,"repair_queue":repair,
        "source_commit":source_sha,"shared_apk_sha256":apk_sha,
        "automatically_promoted_to_games":False,
        "photorealism_verified":False,"hardware_phone_fps_verified":False,
        "next_priority":"Validate tangent-space normal/AO sampling, reference-graded materials, cinematic lighting and physical device performance"}
    (out/"android_gate_report.json").write_text(json.dumps(report,indent=2)+"\n")
    (out/"android_repair_backlog.json").write_text(json.dumps(repair,indent=2)+"\n")
    lines=["# VEILFORGE Android renderer worker review","",
           f"Actual Android 15 emulators audited: {len(findings)}/{len(ROLES)}",
           f"Actual screenshots with integrity/foreground gates: {report['screenshots_checked']}",
           f"Structural visual gate: {'PASS' if not issues else 'FAIL'}",
           "","**Not artist signoff, photorealistic rating, or physical phone performance.**",
           "","## Defects"] + (["- "+issue for issue in issues] if issues else
                              ["- No missing or blank emulator evidence detected."])
    (out/"android_gate_report.md").write_text("\n".join(lines)+"\n")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--source-sha",required=True)
    p.add_argument("--apk-sha",required=True)
    a=p.parse_args()
    r=review(a.root,a.out,a.source_sha,a.apk_sha)
    print("VEILFORGE_ANDROID_GATE",r["devices_passed"],"/",r["expected_devices"],
          "screenshots",r["screenshots_checked"],"success",r["all_emulator_gates_passed"])
    if not r["all_emulator_gates_passed"]:raise SystemExit(1)

if __name__=="__main__":
    main()
