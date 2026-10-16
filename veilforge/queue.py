#!/usr/bin/env python3
"""Bounded, review-only VEILFORGE worker + Android emulator dispatch queue.

One GitHub Actions matrix owns the shared ten-job budget. Entries are static,
allowlisted recipes or existing Android QA roles, never executable backlog text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from android_visual_qa import ROLES, VIEWS
from factory import load_catalog

MAX_ACTIVE = 10
MAX_EMULATORS = 4
PROFILES = {
    "scene-world": "pixel_6",
    "nature-mobile": "pixel_7",
    "props-equipment": "pixel_5",
    "characters": "pixel_4",
}
STATUSES = {"pending", "blocked", "reviewed", "done"}
KINDS = {"asset", "emulator"}
SAFE_ID = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tickets(backlog: Path, catalog: Path) -> list[dict]:
    data = json.loads(backlog.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("tickets"), list):
        raise ValueError("Invalid queue schema")
    assets = set(load_catalog(catalog))
    seen = set()
    result = []
    for item in data["tickets"]:
        if not isinstance(item, dict) or item.get("kind") not in KINDS:
            raise ValueError("Unsupported task kind")
        kind = item["kind"]
        target = item.get("asset") if kind == "asset" else item.get("role")
        allowed = assets if kind == "asset" else set(ROLES)
        expected = f"{kind}-{target}"
        if not isinstance(target, str) or target not in allowed:
            raise ValueError("Task references unsupported asset or Android role")
        if item.get("id") != expected or not SAFE_ID.fullmatch(expected):
            raise ValueError("Task ID must match its fixed allowlisted target")
        if item["id"] in seen:
            raise ValueError("Duplicate queue task")
        seen.add(item["id"])
        if item.get("status") not in STATUSES:
            raise ValueError("Queue status must be explicit")
        priority = item.get("priority")
        if type(priority) is not int or not 0 <= priority <= 100:
            raise ValueError("Priority out of range")
        result.append(dict(item))
    return result


def allocate(all_tickets: list[dict], max_jobs: int, emulator_limit: int) -> dict:
    if type(max_jobs) is not int or not 1 <= max_jobs <= MAX_ACTIVE:
        raise ValueError("Active job budget must be between 1 and 10")
    if type(emulator_limit) is not int or not 0 <= emulator_limit <= MAX_EMULATORS:
        raise ValueError("Emulator limit must be between 0 and 4")
    pending = sorted((t for t in all_tickets if t["status"] == "pending"),
                     key=lambda t: (t["priority"], t["id"]))
    selected = []
    emus = 0
    for task in pending:
        if len(selected) == max_jobs:
            break
        if task["kind"] == "emulator":
            if emus >= emulator_limit:
                continue
            emus += 1
        selected.append(task)
    matrix = []
    for task in selected:
        row = {"id": task["id"], "kind": task["kind"],
               "asset": task.get("asset", ""), "role": task.get("role", ""),
               "profile": PROFILES.get(task.get("role", ""), "")}
        matrix.append(row)
    return {
        "schema_version": 1, "engine": "VEILFORGE",
        "global_active_job_cap": MAX_ACTIVE, "requested_job_cap": max_jobs,
        "selected_count": len(selected), "emulator_count": emus,
        "asset_worker_count": len(selected)-emus,
        "source_tasks": len(all_tickets),
        "selected_ids": [t["id"] for t in selected],
        "deferred_ids": [t["id"] for t in pending if t["id"] not in
                         {s["id"] for s in selected}],
        "blocked_ids": [t["id"] for t in all_tickets if t["status"] == "blocked"],
        "matrix": {"include": matrix},
        "review_only": True, "game_source_mutation": False,
        "auto_promote": False,
    }


def plan(backlog: Path, catalog: Path, out: Path, max_jobs: int,
         emulator_limit: int, github_output: Path | None = None) -> dict:
    output = allocate(tickets(backlog, catalog), max_jobs, emulator_limit)
    out.mkdir(parents=True, exist_ok=True)
    (out/"queue_plan.json").write_text(json.dumps(output, indent=2)+"\n",
                                       encoding="utf-8")
    if github_output is not None:
        with github_output.open("a", encoding="utf-8") as handle:
            for k,v in (
                ("matrix", json.dumps(output["matrix"],separators=(",",":"))),
                ("count", str(output["selected_count"])),
                ("has_emulators", str(output["emulator_count"]>0).lower()),
            ):
                handle.write(k+"="+v+"\n")
    return output


def evidence_ok(job: dict, folder: Path, source_sha: str, apk_sha: str) -> list[str]:
    errors = []
    if job["kind"] == "asset":
        name = job["asset"]
        manifest = folder/"asset_manifest.json"
        if not manifest.is_file():
            return ["Missing asset production manifest"]
        try:
            m = json.loads(manifest.read_text())
            if m["id"] != name or m["production_approved"] is not False or (
                m.get("manual_visual_review_required") is not True):
                errors.append("Asset identity or review policy mismatch")
            if m.get("triangles", 0) <= 0 or m.get("triangles", 0) > m.get("budget", 0):
                errors.append("Asset triangle budget violation")
            for kind, filename in (("obj",m["source_obj"]),("gltf",m["gltf"])):
                path = folder/filename
                if filename != name+"."+kind or not path.is_file() or (
                    sha(path) != m[kind+"_sha256"]):
                    errors.append("Missing or corrupted "+kind+" source")
            for view in ("front","side","three_quarter","elevated"):
                p=folder/"previews"/("view_"+view+".png")
                if not p.is_file() or p.stat().st_size < 1000:
                    errors.append("Missing actual preview "+view)
            gltf_path=folder/m["gltf"]
            if gltf_path.is_file():
                g=json.loads(gltf_path.read_text())
                if g.get("extras",{}).get("production_approved") is not False:
                    errors.append("Production approval unexpectedly set")
                for buffer in g.get("buffers",[]):
                    p=folder/buffer["uri"]
                    if not p.is_file() or p.stat().st_size!=buffer["byteLength"]:
                        errors.append("Invalid glTF binary")
                maps=m.get("texture_maps",{})
                if not maps or not isinstance(maps,dict):
                    errors.append("Missing authored PBR material maps")
                expected_images=set()
                for material,bake in maps.items():
                    if len(bake.get("maps",{}))!=4:
                        errors.append("Missing four PBR maps for "+material)
                    for metadata in bake.get("maps",{}).values():
                        uri="textures/"+material+"/"+metadata["file"]
                        expected_images.add(uri)
                        texture=folder/uri
                        if not texture.is_file() or sha(texture)!=metadata["sha256"]:
                            errors.append("Corrupt PBR texture: "+uri)
                if {i.get("uri") for i in g.get("images",[])}!=expected_images:
                    errors.append("glTF materials do not reference verified textures")
            # VQ's independent model tool supplies 14 source-mesh orbit frames.
            # The manager must verify both their presence and their SHA256 digests
            # before treating an asset worker as technically complete.
            vq_dir=folder/"vq_model_inspection"
            vq_path=vq_dir/"vq_model_report.json"
            if not vq_path.is_file():
                errors.append("Missing independent VQ 14-angle geometry inspection")
            else:
                vq=json.loads(vq_path.read_text(encoding="utf-8"))
                if (vq.get("engine")!="VEYLQUORIN" or
                    vq.get("source_sha256")!=m["obj_sha256"] or
                    vq.get("technical_geometry_smoke_passed") is not True or
                    vq.get("production_approved") is not False or
                    vq.get("gltf",{}).get("structural_smoke_passed") is not True or
                    len(vq.get("visual",{}).get("views",[]))!=14):
                    errors.append("VQ independent source/UV/glTF QA did not pass")
                for i,view in enumerate(vq.get("visual",{}).get("views",[])):
                    if (view.get("view_index")!=i or
                        view.get("yaw")!=i*25):
                        errors.append("VQ camera index/yaw mismatch")
                        continue
                    for name,digest in (("image","image_sha256"),("mask","mask_sha256")):
                        file= vq_dir/"views"/str(view.get(name,""))
                        if (not file.resolve().is_relative_to((vq_dir/"views").resolve())
                            or not file.is_file() or sha(file)!=view.get(digest)):
                            errors.append("VQ source orbit image missing or modified")
                            break
        except (KeyError,ValueError,TypeError,OSError) as error:
            errors.append(f"Invalid asset evidence: {error}")
    else:
        role=job["role"]
        report=folder/role/"emulator_visual_qa.json"
        if not report.is_file():
            return ["Missing real Android screenshot report"]
        try:
            r=json.loads(report.read_text())
            if (r.get("role")!=role or r.get("source_commit")!=source_sha or
                r.get("apk_sha256")!=apk_sha or
                r.get("technical_visual_smoke_pass") is not True or
                r.get("screenshots_clear_of_modal_ui") is not True or
                r.get("artistic_quality_approved") is not False or
                r.get("physical_device_qa_pass") is not False):
                errors.append("Invalid Android run identity or QA attestation")
            views=r.get("assets",[])
            if tuple(x.get("asset") for x in views)!=ROLES[role]:
                errors.append("Wrong Android test asset coverage")
            for a in views:
                if len(a.get("views",[]))!=len(VIEWS):
                    errors.append("Incomplete actual-angle screenshot set")
                for frame in a.get("views",[]):
                    p=report.parent/frame["image"]
                    if not p.is_file() or sha(p)!=frame["sha256"]:
                        errors.append("Missing or corrupt device screenshot")
            if not (report.parent/"device_logcat.txt").is_file():
                errors.append("Missing Android renderer log")
        except (KeyError,ValueError,TypeError,OSError) as error:
            errors.append(f"Invalid Android evidence: {error}")
    return errors


def review(plan_path: Path, root: Path, out: Path,
           source_sha: str, apk_sha: str,
           baseline_scene: Path | None = None) -> dict:
    plan_data=json.loads(plan_path.read_text(encoding="utf-8"))
    selected=plan_data["matrix"]["include"]
    if (plan_data.get("global_active_job_cap")!=MAX_ACTIVE or
        len(selected)!=plan_data.get("selected_count") or
        len(selected)>MAX_ACTIVE or
        sum(t["kind"]=="emulator" for t in selected)>MAX_EMULATORS):
        raise ValueError("Tampered queue budget or incomplete plan")
    if len(source_sha)!=40 or not re.fullmatch(r"[0-9a-f]{40}",source_sha):
        raise ValueError("Invalid immutable source revision")
    if plan_data["emulator_count"] and not re.fullmatch(r"[0-9a-f]{64}",apk_sha):
        raise ValueError("Invalid shared emulator APK digest")
    problems=[]
    successes=[]
    for task in selected:
        folder=root/("veilforge-queue-"+task["id"])
        if not folder.is_dir():
            problems.append(task["id"]+": missing immutable worker artifact")
            continue
        issues=evidence_ok(task,folder,source_sha,apk_sha)
        if issues:
            problems.extend(task["id"]+": "+msg for msg in issues)
        else:
            successes.append(task["id"])
    # The Android probe must contain the SAME deterministic mesh revisions
    # that the concurrently assigned asset workers just produced. A green
    # Android screenshot of unrelated old geometry is not sufficient.
    if baseline_scene is not None:
        if not baseline_scene.is_file():
            problems.append("Missing frozen scene-pack source provenance")
        else:
            scene=json.loads(baseline_scene.read_text(encoding="utf-8"))
            sources=scene.get("source_provenance",{})
            for task in selected:
                if task["kind"]!="asset":
                    continue
                name=task["asset"]
                manifest=root/("veilforge-queue-"+task["id"])/"asset_manifest.json"
                if not manifest.is_file():
                    continue
                worker=json.loads(manifest.read_text(encoding="utf-8"))
                entry=sources.get(name)
                if not entry or worker.get("obj_sha256")!=entry.get("geometry_sha256") or (
                    worker.get("gltf_sha256")!=entry.get("source_gltf_sha256")):
                    problems.append(task["id"]+": source geometry differs from Android APK baseline")
                    if task["id"] in successes:
                        successes.remove(task["id"])
    result={
        "engine":"VEILFORGE", "schema_version":1,
        "source_commit":source_sha, "apk_sha256":apk_sha or None,
        "requested":len(selected), "technically_verified":successes,
        "errors":problems, "technical_qa_passed":not problems,
        "manual_art_review_required":True, "production_approved":False,
        "game_source_mutation":False, "auto_merge":False,
        "next_queue": [
            {"id":task["id"],
             "status":"review_required" if task["id"] in successes else "pending",
             "next_action":"human visual approval / specialist review" if task["id"] in successes
             else "repair and rerun with original source evidence"}
            for task in selected
        ]+[{"id":i,"status":"pending","next_action":"run in next bounded batch"}
           for i in plan_data["deferred_ids"]],
    }
    out.mkdir(parents=True, exist_ok=True)
    (out/"queue_review.json").write_text(json.dumps(result,indent=2)+"\n")
    (out/"queue_review.md").write_text(
        "# VEILFORGE bounded queue review\n\n"+
        f"- Planned: {len(selected)} independent jobs; passed: {len(successes)}.\n"+
        f"- Verified shared APK: {apk_sha or 'no Android jobs'}.\n"+
        "- Assets remain review-only; no game files are modified or merged.\n"+
        ("\n".join("- ERROR: "+p for p in problems) if problems else
         "- All required technical evidence verified.")+"\n"
    )
    return result


def main() -> None:
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("plan")
    a.add_argument("--backlog",type=Path,default=Path("veilforge/queue_backlog.json"))
    a.add_argument("--catalog",type=Path,default=Path("veilforge/catalog.json"))
    a.add_argument("--max-jobs",type=int,default=10)
    a.add_argument("--emulator-limit",type=int,default=4)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--github-output",type=Path)
    b=sub.add_parser("review")
    b.add_argument("--plan",type=Path,required=True)
    b.add_argument("--root",type=Path,required=True)
    b.add_argument("--out",type=Path,required=True)
    b.add_argument("--source-sha",required=True)
    b.add_argument("--apk-sha",default="")
    b.add_argument("--baseline-scene",type=Path)
    x=p.parse_args()
    if x.cmd=="plan":
        r=plan(x.backlog,x.catalog,x.out,x.max_jobs,x.emulator_limit,x.github_output)
        print("VEILFORGE_QUEUE_PLANNED",r["selected_count"],
              "workers",r["asset_worker_count"],"emulators",r["emulator_count"])
    else:
        r=review(x.plan,x.root,x.out,x.source_sha,x.apk_sha,x.baseline_scene)
        print("VEILFORGE_QUEUE_REVIEW",r["technical_qa_passed"],
              "verified",len(r["technically_verified"]))
        if not r["technical_qa_passed"]:
            raise SystemExit(1)


if __name__=="__main__":
    main()
