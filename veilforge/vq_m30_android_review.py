#!/usr/bin/env python3
"""Independent four-emulator M30 review of real GLES normal-map difference."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from vq_android_qa_sdk import evidence_png
ROLES={"pixel_4","pixel_5","pixel_6","pixel_7"}
def review(root,out,*,source_sha=None,apk_sha=None):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    files=list(root.rglob("m30_emulator_report.json"))
    issues=[];roles={};deltas={}
    for path in files:
        try:
            r=json.loads(path.read_text())
            role=r["role"]
            if role not in ROLES or role in roles:
                issues.append("Unknown or duplicate emulator role: "+str(role));continue
            roles[role]=path
            if r.get("android_api")!=35 or r.get("technical_gate_passed") is not True:
                issues.append(role+": android technical gate incomplete")
            if not r.get("real_gles_normal_and_ao_uploaded") or not r.get("shading_enabled_comparison_verified"):
                issues.append(role+": missing hardware shader/sample evidence")
            if r.get("artistic_approval") is not False or r.get("photorealism_verified") is not False:
                issues.append(role+": false artistic/photoreal promotion")
            if source_sha and r.get("source_commit")!=source_sha:
                issues.append(role+": source commit mismatch")
            if apk_sha and r.get("apk_sha256")!=apk_sha:
                issues.append(role+": test APK mismatch")
            views=r.get("screenshots",[])
            if len(views)!=14 or r.get("actual_emulator_frames")!=17:
                issues.append(role+": missing 14 genuine orbit views and 3 same-angle material controls")
            for v in views:
                name=v.get("image","")
                frame=path.parent/name
                if not name.startswith("angle_") or not frame.is_file():
                    issues.append(role+": missing source screenshot "+name);continue
                try:
                    evidence_png(path.parent, name, v.get("sha256"), v.get("metrics"))
                except ValueError as error:
                    issues.append(role+": untrusted actual screenshot ("+str(error)+")")
            on_reference=path.parent/"normal_on_reference.png"
            if not on_reference.is_file() or hashlib.sha256(on_reference.read_bytes()).hexdigest()!=r.get("normal_on_reference_sha256"):
                issues.append(role+": missing/altered matched normal-on reference")
            on_repeat=path.parent/"normal_on_repeat.png"
            if not on_repeat.is_file() or hashlib.sha256(on_repeat.read_bytes()).hexdigest()!=r.get("normal_on_repeat_sha256"):
                issues.append(role+": missing same-angle noise-control frame")
            baseline=path.parent/"flat_baseline.png"
            if not baseline.is_file() or hashlib.sha256(baseline.read_bytes()).hexdigest()!=r.get("flat_baseline_sha256"):
                issues.append(role+": missing/altered no-normal baseline")
            difference=r.get("normal_map_on_off_pixel_difference",0)
            if not isinstance(difference,(int,float)) or not .003<=difference<=.15 or (
                difference<=r.get("same_angle_repeat_render_difference",1)+.001):
                issues.append(role+": no verified localized shading beyond same-angle GPU noise")
            deltas[role]=difference
        except (KeyError,ValueError,TypeError,OSError) as exc:
            issues.append(f"{path}: malformed QA evidence: {exc}")
    for role in sorted(ROLES-set(roles)):
        issues.append("Missing emulator role: "+role)
    result={"schema_version":1,"milestone":"M30","android_15_emulators_completed":len(roles),
            "expected_emulators":len(ROLES),
            "verified_real_screenshots":len(roles)*17 if not issues else 0,
            "normal_map_pixel_differences":deltas,
            "problems":issues,"android_material_gate_passed":not issues,
            "artist_approved":False,"game_promoted":False,"physical_devices_tested":False,
            "note":"True emulator screenshot normal map lighting comparison, not cinema-quality BRDF or final artist approval."}
    (out/"m30_android_review.json").write_text(json.dumps(result,indent=2)+"\n")
    (out/"m30_android_review.md").write_text(
        "# VQ M30 real Android normal-map validation\n\n"+
        f"Emulators: {len(roles)}/{len(ROLES)}. Technical gate: {'PASS' if not issues else 'FAIL'}.\n\n"+
        "Model is actual low-poly OBJ with high-poly-derived normal texture and flat baseline.\n"+
        "Manual artistic approval is still required.\n\n"+
        "Detected problems:\n"+("\n".join("- "+x for x in issues) if issues else "- None in technical checks.")+"\n")
    return result
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--source-sha")
    p.add_argument("--apk-sha")
    a=p.parse_args()
    r=review(a.root,a.out,source_sha=a.source_sha,apk_sha=a.apk_sha)
    print("VQ_M30_ANDROID_REVIEW",r["android_15_emulators_completed"],
          "devices, passed=",r["android_material_gate_passed"])
    if not r["android_material_gate_passed"]:raise SystemExit(1)
if __name__=="__main__":main()
