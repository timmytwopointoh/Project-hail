#!/usr/bin/env python3
"""Verify all real Android frames before binding exact angles to REVIEW tasks."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from android_visual_qa import ROLES, VIEWS
from visual_semantics import silhouette, outline_analysis

def bind(tasks_path, semantic_path, root, source_sha, run_id):
    tasks_path, semantic_path, root = map(Path, (tasks_path, semantic_path, root))
    pack=json.loads(tasks_path.read_text())
    semantic=json.loads(semantic_path.read_text())
    semantic_hash=hashlib.sha256(semantic_path.read_bytes()).hexdigest()
    if (pack.get("source_commit")!=source_sha or
        pack.get("github_actions_run_id")!=run_id or
        pack.get("source_semantic_report_sha256")!=semantic_hash or
        semantic.get("technical_gate_passed") is not True or
        pack.get("ready_for_automated_model_rewrite") is not False or
        pack.get("artistic_signoff") is not False):
        raise ValueError("Handoff source or acceptance mismatch")
    reports=list(root.rglob("emulator_visual_qa.json"))
    if len(reports)!=len(ROLES):
        raise ValueError("Incomplete Android role report set")
    evidence={}
    apk_hashes=set()
    total=0
    for report in reports:
        data=json.loads(report.read_text())
        role=data.get("role")
        if (role not in ROLES or role in evidence or
            data.get("source_commit")!=source_sha or
            data.get("device_android_api")!=35 or
            data.get("technical_visual_smoke_pass") is not True or
            data.get("screenshot_count")!=len(ROLES[role])*len(VIEWS)):
            raise ValueError("Invalid Android role/source evidence")
        apk=data.get("apk_sha256")
        if not isinstance(apk,str) or len(apk)!=64 or any(c not in "0123456789abcdef" for c in apk):
            raise ValueError("Invalid APK digest")
        apk_hashes.add(apk)
        assets={}
        for item in data.get("assets",[]):
            asset=item.get("asset")
            if asset not in ROLES[role] or asset in assets:
                raise ValueError("Unknown/duplicate role asset")
            if len(item.get("views",[]))!=len(VIEWS):
                raise ValueError("Incomplete camera angles")
            seen=set()
            frames=[]
            for index,(v,(yaw,pitch)) in enumerate(zip(item["views"],VIEWS)):
                name=f"{asset}/{index:02d}_yaw{yaw}_pitch{pitch}.png"
                if (v.get("index")!=index or v.get("yaw")!=yaw or
                    v.get("pitch")!=pitch or v.get("image")!=name):
                    raise ValueError("Mismatched camera image path/angle")
                image=report.parent/name
                sha=hashlib.sha256(image.read_bytes()).hexdigest()
                if sha!=v.get("sha256") or sha in seen:
                    raise ValueError("Altered or stale Android PNG: "+name)
                seen.add(sha)
                with Image.open(image) as im:
                    mask,w,h=silhouette(im)
                    coverage=outline_analysis(mask,w,h)["coverage"]
                frames.append({"index":index,"yaw":yaw,"pitch":pitch,
                               "image":name,"sha256":sha,
                               "silhouette_coverage":coverage})
                total+=1
            assets[asset]=frames
        if set(assets)!=set(ROLES[role]):
            raise ValueError("Missing role asset")
        evidence[role]=assets
    if len(apk_hashes)!=1 or total!=pack.get("frames_reviewed"):
        raise ValueError("APK or frame-count provenance mismatch")
    if len(pack.get("tasks",[]))!=pack.get("warning_count"):
        raise ValueError("Missing REVIEW tasks")
    for task in pack["tasks"]:
        role,asset=task.get("emulator_role"),task.get("asset")
        if (role not in evidence or asset not in evidence[role] or
            task.get("source_commit")!=source_sha or
            task.get("github_actions_run_id")!=run_id or
            task.get("input_report_sha256")!=semantic_hash):
            raise ValueError("Unlinked REVIEW task")
        frames=evidence[role][asset]
        values=[f["silhouette_coverage"] for f in frames]
        expected=semantic["assets"][asset]
        if (abs(min(values)-expected["min_coverage"])>.00011 or
            abs(max(values)-expected["max_coverage"])>.00011):
            raise ValueError("Semantic coverage does not match original PNGs")
        task["camera_view_evidence"]=frames
        task["screenshot_provenance_verified"]=True
        task["automatic_model_edit"]=False
        task["auto_promote"]=False
    pack["all_android_frame_hashes_verified"]=True
    pack["verified_android_frame_count"]=total
    pack["verified_apk_sha256"]=next(iter(apk_hashes))
    tasks_path.write_text(json.dumps(pack,indent=2)+"\n")
    return pack

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for arg in ("tasks","semantic","screenshots-root","source-sha","run-id"):
        p.add_argument("--"+arg,required=True)
    a=p.parse_args()
    result=bind(a.tasks,a.semantic,a.screenshots_root,a.source_sha,int(a.run_id))
    print("VEILFORGE_REVIEW_ANGLE_PROVENANCE_VERIFIED",result["verified_android_frame_count"])
