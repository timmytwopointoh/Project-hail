#!/usr/bin/env python3
"""Independently replay immutable Android review tasks against archived real PNGs.

This is a provenance gate, not a geometry editor or an artistic quality score.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile
from PIL import Image
from android_visual_qa import ROLES, VIEWS
from visual_semantics import silhouette, outline_analysis


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify(tasks_file, archives):
    """Require four role archives, 154 PNG hashes and all REVIEW-task angles."""
    tasks_file = Path(tasks_file)
    tasks = json.loads(tasks_file.read_text(encoding="utf-8"))
    expected_assets = {asset: role for role, names in ROLES.items() for asset in names}
    source = tasks.get("source_commit")
    if not isinstance(source, str) or len(source) != 40 or any(c not in "0123456789abcdef" for c in source):
        raise ValueError("Missing immutable source SHA")
    if type(tasks.get("github_actions_run_id")) is not int or tasks["github_actions_run_id"] <= 0:
        raise ValueError("Missing immutable Actions run ID")
    if set(archives) != set(ROLES):
        raise ValueError("All four Android emulator role archives are required")
    if tasks.get("frames_reviewed") != 154 or tasks.get("emulators_reviewed") != 4:
        raise ValueError("Incomplete handoff frame/device evidence")
    if tasks.get("ready_for_automated_model_rewrite") is not False or tasks.get("human_signoff_required") is not True:
        raise ValueError("Review handoff may not authorize promotion or automatic edits")
    seen = set()
    records = {}
    archive_hashes = {}
    apk_hashes = set()
    for role, archive in sorted(archives.items()):
        archive = Path(archive)
        archive_hashes[role] = digest(archive.read_bytes())
        with ZipFile(archive) as z:
            names = z.namelist()
            if len(names) != len(set(names)) or any(x.startswith("/") or ".." in Path(x).parts for x in names):
                raise ValueError("Unsafe or duplicate ZIP entry")
            manifest = json.loads(z.read("emulator_visual_qa.json"))
            if (manifest.get("role") != role or manifest.get("source_commit") != source or
                manifest.get("device_android_api") != 35 or
                manifest.get("technical_visual_smoke_pass") is not True or
                manifest.get("artistic_quality_approved") is not False or
                manifest.get("screenshot_count") != len(ROLES[role]) * len(VIEWS)):
                raise ValueError("Wrong role/source/device or incomplete emulator manifest: " + role)
            apk_hashes.add(manifest.get("apk_sha256"))
            assets = manifest.get("assets")
            if not isinstance(assets, list) or {a.get("asset") for a in assets} != set(ROLES[role]):
                raise ValueError("Incomplete emulator assets: " + role)
            for asset in assets:
                name = asset["asset"]
                views = asset.get("views")
                if not isinstance(views, list) or len(views) != len(VIEWS):
                    raise ValueError("Missing 14 camera views: " + name)
                for index, (meta, (yaw, pitch)) in enumerate(zip(views, VIEWS)):
                    path = f"{name}/{index:02d}_yaw{yaw}_pitch{pitch}.png"
                    if (meta.get("image") != path or meta.get("index") != index or
                        (meta.get("yaw"), meta.get("pitch")) != (yaw, pitch)):
                        raise ValueError("Camera path/angle mismatch: " + path)
                    raw = z.read(path)
                    sha = digest(raw)
                    if sha != meta.get("sha256") or sha in seen or not raw.startswith(b"\x89PNG\r\n\x1a\n"):
                        raise ValueError("Altered, duplicate or non-PNG accepted frame: " + path)
                    seen.add(sha)
                    with Image.open(io.BytesIO(raw)) as im:
                        im.verify()
                    records[(name, index)] = (role, path, sha, raw)
    if len(seen) != 154 or len(apk_hashes) != 1 or not all(isinstance(x, str) and len(x) == 64 for x in apk_hashes):
        raise ValueError("Not 154 unique accepted PNGs from one APK")
    reviews = tasks.get("tasks")
    if not isinstance(reviews, list) or len(reviews) != tasks.get("warning_count"):
        raise ValueError("Missing REVIEW tasks")
    checked = 0
    for task in reviews:
        name = task.get("asset")
        if (name not in expected_assets or task.get("emulator_role") != expected_assets[name] or
            task.get("source_commit") != source or task.get("github_actions_run_id") != tasks["github_actions_run_id"] or
            task.get("automatic_model_edit") is not False or task.get("auto_promote") is not False):
            raise ValueError("Unsafe task identity/provenance")
        views = task.get("source_views")
        if not isinstance(views, list) or len(views) != 14:
            raise ValueError("Missing REVIEW source angles: " + name)
        fractions = []
        for i, view in enumerate(views):
            role, path, sha, raw = records[(name, i)]
            if (view.get("index") != i or view.get("image") != path or
                view.get("sha256") != sha or
                (view.get("yaw"), view.get("pitch")) != VIEWS[i]):
                raise ValueError("REVIEW task references wrong screenshot: " + path)
            with Image.open(io.BytesIO(raw)) as frame:
                mask, width, height = silhouette(frame)
            fraction = outline_analysis(mask, width, height)["coverage"]
            if fraction != view.get("coverage"):
                raise ValueError("REVIEW coverage not reproducible: " + path)
            fractions.append(fraction)
            checked += 1
        if (round(min(fractions), 4) != task.get("minimum_foreground_coverage") or
            round(max(fractions), 4) != task.get("maximum_foreground_coverage") or
            task.get("lowest_coverage_view") != min(views, key=lambda v: v["coverage"])):
            raise ValueError("REVIEW minimum/maximum contradict real frames: " + name)
    return {"status": "PASS", "source_commit": source,
            "github_actions_run_id": tasks["github_actions_run_id"],
            "tasks_sha256": digest(tasks_file.read_bytes()),
            "role_archive_sha256": archive_hashes,
            "apk_sha256": next(iter(apk_hashes)),
            "accepted_unique_pngs_verified": len(seen),
            "review_angles_recomputed": checked,
            "artistic_quality_approved": False,
            "physical_device_qa_pass": False,
            "automatic_model_edit": False}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tasks", required=True, type=Path)
    p.add_argument("--role-zip", action="append", required=True,
                   help="role=/path/to/actual-Android-artifact.zip (four required)")
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    archives = {}
    for item in args.role_zip:
        role, sep, path = item.partition("=")
        if not sep or role in archives:
            raise ValueError("Use one role=zip argument per emulator role")
        archives[role] = path
    result = verify(args.tasks, archives)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("VEILFORGE_IMMUTABLE_ANDROID_EVIDENCE", result["status"],
          result["accepted_unique_pngs_verified"], "PNGs",
          result["review_angles_recomputed"], "REVIEW angles")


if __name__ == "__main__":
    main()
