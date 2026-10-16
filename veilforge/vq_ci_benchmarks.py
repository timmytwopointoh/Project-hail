#!/usr/bin/env python3
"""M34-09: fail-closed timing and artifact evidence for VEILFORGE Actions."""
from __future__ import annotations
import argparse
import json
from datetime import datetime
from pathlib import Path

ROLES = ("scene-world", "nature-mobile", "props-equipment", "characters")
WORKFLOW = "VEILFORGE - Universal Game Asset Factory"

def duration(a, b):
    start = datetime.fromisoformat(a.replace("Z", "+00:00"))
    end = datetime.fromisoformat(b.replace("Z", "+00:00"))
    if start.tzinfo is None or end.tzinfo is None or end < start:
        raise ValueError("Invalid UTC job timestamp")
    return (end - start).total_seconds()

def summarize(run, jobs, artifacts):
    if run.get("name") != WORKFLOW or run.get("status") != "completed" or run.get("conclusion") != "success":
        raise ValueError("Run is not a successful completed universal factory")
    if len(run.get("head_sha", "")) != 40:
        raise ValueError("Missing pinned source SHA")
    if jobs.get("total_count", len(jobs["jobs"])) != len(jobs["jobs"]):
        raise ValueError("Incomplete jobs pagination")
    if artifacts.get("total_count", len(artifacts["artifacts"])) != len(artifacts["artifacts"]):
        raise ValueError("Incomplete artifacts pagination")
    names = {j["name"]: j for j in jobs["jobs"]}
    producer = [name for name in names if name.startswith("Factory asset / ")]
    android = [name for name in names if name.startswith("Android 15 / ")]
    if len(producer) != 8 or len(android) != 4:
        raise ValueError("Expected 8 producers and 4 real Android jobs")
    for role in ROLES:
        if sum("/ " + role + " /" in name for name in android) != 1:
            raise ValueError("Missing Android role: " + role)
    required = (
        "Build independent Android glTF renderer APK",
        "Fail closed on incomplete emulator visual QA evidence",
        "Independently verify mobile LOD and per-asset Android silhouettes",
    )
    if any(name not in names for name in required):
        raise ValueError("Missing build or independent review job")
    if any(j["conclusion"] != "success" for j in jobs["jobs"]):
        raise ValueError("Unsuccessful job")
    artifact_map = {a["name"]: a for a in artifacts["artifacts"]}
    needed = {"veilforge-android-shared-probe-apk",
              "veilforge-android-final-review",
              "veilforge-android-visual-lod-review",
              "veilforge-android-semantic-review"} | {
                  "veilforge-android-" + role for role in ROLES}
    if not needed.issubset(artifact_map):
        raise ValueError("Missing actual Android/reviewer artifact")
    if any(a.get("expired") or not isinstance(a.get("size_in_bytes"), int)
           or a["size_in_bytes"] <= 0 for a in artifacts["artifacts"]):
        raise ValueError("Expired or invalid artifact")
    times = {name: duration(j["started_at"], j["completed_at"]) for name, j in names.items()}
    starts = [datetime.fromisoformat(j["started_at"].replace("Z", "+00:00")) for j in jobs["jobs"]]
    ends = [datetime.fromisoformat(j["completed_at"].replace("Z", "+00:00")) for j in jobs["jobs"]]
    return {
        "run_id": run["id"], "source_sha": run["head_sha"],
        "run_url": run.get("html_url"),
        "job_wall_span_seconds": (max(ends) - min(starts)).total_seconds(),
        "job_seconds": times,
        "android_seconds": {role: next(times[name] for name in android
                                         if "/ " + role + " /" in name) for role in ROLES},
        "apk_build_seconds": times[required[0]],
        "artifact_archive_bytes": sum(a["size_in_bytes"] for a in artifacts["artifacts"]),
        "capture_archive_bytes": sum(artifact_map["veilforge-android-" + role]["size_in_bytes"] for role in ROLES),
        "apk_archive_bytes": artifact_map["veilforge-android-shared-probe-apk"]["size_in_bytes"],
        "apk_payload_bytes": None,
        "capture_png_payload_bytes": None,
        "artifact_count": len(artifacts["artifacts"]),
    }

def report(rows):
    if not rows or len({r["run_id"] for r in rows}) != len(rows):
        raise ValueError("Missing or duplicate run evidence")
    topology_equal = all(set(r["job_seconds"]) == set(rows[0]["job_seconds"]) for r in rows)
    return {
        "schema_version": 1, "milestone": "M34-09", "runs": rows,
        "observations": len(rows), "minimum_comparable_runs": 3,
        "job_topology_equal": topology_equal,
        "minimum_observations_met": len(rows) >= 3 and topology_equal,
        "speedup_claim_supported": False,
        "reason": "Different source commits and runner conditions do not establish a controlled speedup; archive sizes are compressed transport sizes, not APK/PNG payload bytes.",
        "artistic_approval": False, "hardware_approval": False,
        "game_source_modified": False,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True,
                        help="JSON list of exact GitHub API run/jobs/artifacts payloads")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    records = json.loads(args.input.read_text())
    rows = [summarize(x["run"], x["jobs"], x["artifacts"]) for x in records]
    result = report(rows)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("VQ_M34_09_EVIDENCE", result["observations"],
          "controlled_speedup_supported=false")

if __name__ == "__main__":
    main()
