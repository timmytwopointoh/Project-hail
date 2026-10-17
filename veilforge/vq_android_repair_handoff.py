#!/usr/bin/env python3
"""Turn genuine Android semantic screenshot findings into durable review tasks.

This DOES NOT silently patch models or trigger unlimited emulators. Each entry
references an exact GitHub commit, workflow run, Android role, 14 source views
and measured coverage, for a specialist to verify before making a bounded
repair. Untrusted report text is retained as evidence, never executable input.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from android_visual_qa import ROLES,VIEWS

HEX_SHA=re.compile(r"^[a-f0-9]{40}$")
HEX_SHA256=re.compile(r"^[a-f0-9]{64}$")
FIELD=re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
MAX_NOTES=256

def handoff(report_path,out,*,source_sha,run_id):
    report_path=Path(report_path);out=Path(out)
    if not HEX_SHA.fullmatch(source_sha):
        raise ValueError("A pinned 40-hex Git source SHA is required")
    if type(run_id) is not int or run_id<=0:
        raise ValueError("The real GitHub Actions run id is required")
    doc=json.loads(report_path.read_text(encoding="utf-8"))
    assets=doc.get("assets")
    expected={asset:role for role,names in ROLES.items() for asset in names}
    if not isinstance(assets,dict) or set(assets)!=set(expected):
        raise ValueError("Semantic report must contain exactly all expected Android assets")
    if (doc.get("technical_gate_passed") is not True or
        doc.get("roles")!=len(ROLES) or doc.get("assets_scanned")!=len(expected) or
        doc.get("frames_scanned")!=sum(len(names)*len(VIEWS) for names in ROLES.values()) or
        doc.get("problems")!=[] or doc.get("photorealism_verified") is not False):
        raise ValueError("Cannot create trusted repair handoff from failed/incomplete QA")
    for asset,info in assets.items():
        if not isinstance(info,dict) or info.get("role")!=expected[asset] or (
            info.get("views")!=len(VIEWS)):
            raise ValueError("Asset role/view evidence is incomplete: "+asset)
        views=info.get("view_evidence")
        if not isinstance(views,list) or len(views)!=len(VIEWS):
            raise ValueError("Missing exact per-angle screenshot evidence: "+asset)
        coverages=[]
        for index,(item,(yaw,pitch)) in enumerate(zip(views,VIEWS)):
            expected_image=f"{asset}/{index:02d}_yaw{yaw}_pitch{pitch}.png"
            if not isinstance(item,dict) or item.get("index")!=index or (
                item.get("yaw"),item.get("pitch"))!=(yaw,pitch) or (
                item.get("image")!=expected_image):
                raise ValueError("Invalid per-angle camera/path provenance: "+asset)
            digest=item.get("sha256")
            if not isinstance(digest,str) or not HEX_SHA256.fullmatch(digest):
                raise ValueError("Invalid screenshot digest: "+asset)
            coverage=item.get("coverage")
            if type(coverage) not in (int,float) or not math.isfinite(coverage) or not 0<=coverage<=1:
                raise ValueError("Invalid per-angle coverage: "+asset)
            coverages.append(coverage)
        if (round(min(coverages),4)!=info.get("min_coverage") or
            round(max(coverages),4)!=info.get("max_coverage")):
            raise ValueError("Per-angle coverage contradicts semantic summary: "+asset)
    raw_warnings=doc.get("warnings")
    source_queue=doc.get("repair_queue")
    if not isinstance(raw_warnings,list) or not isinstance(source_queue,list) or (
        len(source_queue)!=len(raw_warnings)):
        raise ValueError("Missing/mismatched semantic warnings and repair queue")
    tasks=[]
    seen=set()
    for warning in raw_warnings:
        if not isinstance(warning,dict):
            raise ValueError("Invalid semantic warning entry")
        asset=warning.get("asset")
        subject=warning.get("subject")
        reason=warning.get("reason")
        if asset not in expected or not isinstance(subject,str) or not FIELD.fullmatch(subject):
            raise ValueError("Unknown asset or unsafe warning subject")
        if not isinstance(reason,str) or not 1<=len(reason)<=MAX_NOTES:
            raise ValueError("Invalid warning diagnostic")
        row=assets[asset]
        if not any(x.get("asset")==asset and x.get("action")==reason for x in source_queue):
            raise ValueError("Semantic warning absent from original repair queue")
        task_id=f"review-{asset}-{subject}"
        if task_id in seen:
            raise ValueError("Duplicate repair task for asset/diagnostic")
        seen.add(task_id)
        severity=("high" if subject=="view_visibility" and row.get("min_coverage",1)<.001
                  else "review")
        tasks.append({
            "id":task_id,"kind":"visual_review","status":"needs_specialist_review",
            "priority":severity,"asset":asset,"emulator_role":expected[asset],
            "diagnostic":subject,
            "source_reason":reason,
            "suggested_next_action":"Inspect the actual source screenshot angles and camera/framing/culling, then implement and retest only a measured defect.",
            "screenshots_in_evidence":len(VIEWS),
            "source_views":row["view_evidence"],
            "lowest_coverage_view":min(row["view_evidence"],key=lambda v:v["coverage"]),
            "minimum_foreground_coverage":row.get("min_coverage"),
            "maximum_foreground_coverage":row.get("max_coverage"),
            "source_commit":source_sha,"github_actions_run_id":run_id,
            "screenshot_artifact":"veilforge-android-"+expected[asset],
            "input_report_sha256":hashlib.sha256(report_path.read_bytes()).hexdigest(),
            "automatic_model_edit":False,"auto_promote":False
        })
    tasks.sort(key=lambda x:(0 if x["priority"]=="high" else 1,x["asset"],x["diagnostic"]))
    pack={
        "schema_version":1,"engine":"VEILFORGE","stage":"android-qa-to-next-model-iteration",
        "source_commit":source_sha,"github_actions_run_id":run_id,
        "source_semantic_report_sha256":hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "assets_reviewed":len(expected),"emulators_reviewed":len(ROLES),
        "frames_reviewed":doc["frames_scanned"],
        "warning_count":len(raw_warnings),"tasks":tasks,
        "all_semantic_warnings_accounted_for":len(tasks)==len(raw_warnings),
        "ready_for_automated_model_rewrite":False,
        "requires_actual_screenshot_inspection":bool(tasks),
        "artistic_signoff":False,
        "human_signoff_required":True,
        "note":"Task suggestions are not proof a geometry defect exists; never merge or overwrite original models without source review."
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"next_iteration_tasks.json").write_text(json.dumps(pack,indent=2)+"\n",encoding="utf-8")
    lines=["# VEILFORGE Android-to-model review handoff","",
        f"Run: {run_id} | Commit: {source_sha}",
        f"Android evidence: {len(ROLES)} devices, {pack['frames_reviewed']} captures",
        f"Open visual review tasks: {len(tasks)}","",
        "All tasks require examining real screenshots. No geometry edits/merges are authorized.",""]
    for task in tasks:
        worst=task["lowest_coverage_view"]
        lines.append(f"- {task['id']} ({task['priority']}, {task['emulator_role']}): {task['source_reason']}")
        lines.append(f"  - Lowest measured view: {worst['image']} "
                     f"(yaw {worst['yaw']}, pitch {worst['pitch']}, "
                     f"coverage {worst['coverage']:.5f}, SHA256 {worst['sha256']}). "
                     "All 14 screenshot hashes and angles are in the JSON task.")
    if not tasks:lines.append("- No unreviewed semantic warnings for this run.")
    (out/"next_iteration_tasks.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return pack

def main():
    p=argparse.ArgumentParser(description="Fail-closed emulator visual repair handoff")
    p.add_argument("--semantic",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--source-sha",required=True)
    p.add_argument("--run-id",required=True,type=int)
    a=p.parse_args()
    result=handoff(a.semantic,a.out,source_sha=a.source_sha,run_id=a.run_id)
    print("VEILFORGE_ANDROID_REPAIR_HANDOFF",result["warning_count"],
          "tasks from",result["frames_reviewed"],"genuine emulator frames")
if __name__=="__main__":main()
