#!/usr/bin/env python3
"""Fail-closed static audit of VEILFORGE Android worker efficiency configuration.

Configured policies are not real timing, GPU or artistic approval evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

def audit(root,out=None):
    root=Path(root)
    workflow=root/".github/workflows/veilforge-factory.yml"
    if not workflow.is_file():raise ValueError("Missing factory workflow")
    text=workflow.read_text(encoding="utf-8")
    issues=[]
    pieces=text.split("\n  android-visual-workers:\n")
    if len(pieces)!=2:raise ValueError("Missing or duplicated Android workers")
    worker=pieces[1].split("\n  android-visual-review:\n",1)[0]
    if "max-parallel: 4" not in worker:
        issues.append("A three-device emulator wave leaves a fourth idle")
    role_names=("scene-world","nature-mobile","props-equipment","characters")
    for role in role_names:
        if worker.count(f"role: {role},")!=1:
            issues.append("Missing/duplicated role: "+role)
    for marker in ("reactivecircus/android-emulator-runner@v2",
                   "sha256sum -c -","android_visual_qa.py --role",
                   "veilforge-android-","api: 35"):
        if marker not in worker:
            issues.append("Missing real emulator worker safeguard: "+marker)
    # Restrict both reviewers to the four actual screenshot evidence archives:
    # the old wildcard also downloaded the large immutable test APK artifact.
    exact="pattern: veilforge-android-{scene-world,nature-mobile,props-equipment,characters}"
    if text.count(exact)!=2:
        issues.append("Both reviews must download only real emulator screenshot evidence")
    if "pattern: veilforge-android-*" in text:
        issues.append("Overbroad pattern downloads unrelated APK/review artifacts")
    blocks=text.split("\n  extended-visual-review:\n")
    if len(blocks)!=2:
        issues.append("Expected exactly one combined reviewer job")
        reviews=""
    else:
        reviews=blocks[1]
        if reviews.count("actions/download-artifact@v4")!=1:
            issues.append("Duplicate reviewer screenshot downloads")
        if reviews.count("pip install --quiet pillow==11.3.0")!=1:
            issues.append("Duplicate reviewer image setup")
        for module in ("veilforge/visual_lod.py","veilforge/visual_semantics.py"):
            if reviews.count(module)!=1:issues.append("Missing reviewer: "+module)
        for marker in ("LOD_RESULT=$?","SEMANTIC_RESULT=$?",
                       'test "$LOD_RESULT" -eq 0',
                       'test "$SEMANTIC_RESULT" -eq 0',
                       "needs.android-visual-review.result == 'success'",
                       "veilforge-android-visual-lod-review",
                       "veilforge-android-semantic-review"):
            if marker not in reviews:
                issues.append("Reviewer integrity/identity safeguard missing: "+marker)
    if "\n  visual-lod-review:\n" in text or "\n  semantic-android-visual-review:\n" in text:
        issues.append("Old duplicate review jobs remain")
    capture=(root/"veilforge/android_visual_qa.py").read_text(encoding="utf-8")
    m30=(root/"veilforge/vq_m30_android_qa.py").read_text(encoding="utf-8")
    if ('last.get("renderer_background_confirmed") is True' not in capture or
        "def renderer_background_confirmed(" not in capture):
        issues.append("General screenshot gate does not reject splash screens")
    if 'background_ok=score["renderer_background_confirmed"]' not in m30:
        issues.append("M30 screenshot gate does not reuse strict common validation")
    if "VIEWS=[" not in capture or "ROLES={" not in capture:
        issues.append("Existing source camera and asset roles missing")
    result={
        "schema_version":1,"milestone":"M34",
        "scope":"static source/workflow configuration, not runtime evidence",
        "workflow_sha256":hashlib.sha256(workflow.read_bytes()).hexdigest(),
        "emulator_roles_expected":4,"per_asset_angles_expected":14,
        "max_parallel_emulators_configured":4,
        "reviewer_job_count":1 if reviews else 0,
        "independent_algorithms_required":["visual_lod","visual_semantics"],
        "single_download_required":True,"shared_apk_sha_required":True,
        "runtime_speedup_measured":False,"real_android_execution_proven":False,
        "production_artistic_approval":False,"game_code_modified":False,
        "problems":issues,"static_gate_passed":not issues
    }
    if out is not None:
        out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",default=".")
    parser.add_argument("--out",required=True)
    args=parser.parse_args()
    report=audit(args.root,args.out)
    print("VEILFORGE_M34_EMULATOR_EFFICIENCY_STATIC_GATE",
          "PASS" if report["static_gate_passed"] else "FAIL",
          json.dumps(report["problems"]))
    if not report["static_gate_passed"]:raise SystemExit(1)
if __name__=="__main__":main()
