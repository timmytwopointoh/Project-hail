#!/usr/bin/env python3
"""Fail closed if manually selected Android QA evidence is missing or malformed.

Protects director planning from silently replacing a failed artifact download
with speculative roadmap work. This is an evidence integrity and shape check,
not cryptographic authentication of the upstream CI run.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SHA40 = re.compile(r"^[a-fA-F0-9]{40}$")
RUN_ID = re.compile(r"^[0-9]{5,20}$")
ALLOWED_STATES = {"blocked", "needs-review", "clear"}
ALLOWED_EMULATOR = {"passed", "failed"}


def verify_evidence(folder, *, run_id=None):
    if run_id is not None and not RUN_ID.fullmatch(str(run_id)):
        raise ValueError("Invalid selected Android workflow run ID")
    root = Path(folder)
    file = root / "task_plan.json"
    if not file.is_file():
        raise ValueError("Selected emulator run did not provide task_plan.json")
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise ValueError("Selected emulator QA task plan is invalid JSON") from None
    if not isinstance(data, dict):
        raise ValueError("Selected emulator task plan is not an object")
    if data.get("project") != "VEILBOUND" or data.get("schema_version") != 1:
        raise ValueError("Selected QA evidence is not a supported VEILBOUND report")
    sha = data.get("source_commit")
    if not isinstance(sha, str) or not SHA40.fullmatch(sha):
        raise ValueError("Selected QA evidence is missing its original source commit")
    if data.get("emulator_status") not in ALLOWED_EMULATOR:
        raise ValueError("Selected QA report lacks a completed emulator outcome")
    if data.get("release_gate") not in ALLOWED_STATES:
        raise ValueError("Selected QA report lacks a known release gate")
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or len(tasks) > 60:
        raise ValueError("Selected QA report contains an invalid task list")
    if data.get("task_count") != len(tasks):
        raise ValueError("Selected QA report task count does not match")
    ids = set()
    for task in tasks:
        if (not isinstance(task, dict) or
                not isinstance(task.get("id"), str) or
                not re.fullmatch(r"VB-[A-Z0-9-]{3,90}", task["id"]) or
                task["id"] in ids or
                task.get("priority") not in {"P0", "P1", "P2", "P3"} or
                not isinstance(task.get("worker"), str)):
            raise ValueError("Selected QA report contains a malformed or duplicate task")
        ids.add(task["id"])
    blockers = data.get("blocker_ids")
    if (not isinstance(blockers, list) or
            set(blockers) != {t["id"] for t in tasks
                              if t["priority"] in ("P0", "P1")}):
        raise ValueError("Selected QA blockers disagree with tasks")
    expected_gate = ("blocked" if blockers else
                     ("needs-review" if tasks else "clear"))
    if data.get("release_gate") != expected_gate:
        raise ValueError("Selected QA release gate contradicts the findings")
    if data["emulator_status"] == "failed" and not blockers:
        raise ValueError("Failed Android acceptance has no blocking QA task")
    return {"validated": True, "source_commit": sha,
            "run_id": str(run_id) if run_id is not None else "workflow-trigger",
            "emulator_status": data["emulator_status"],
            "release_gate": expected_gate, "tasks": len(tasks)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--run-id")
    args = parser.parse_args()
    try:
        result = verify_evidence(args.input, run_id=args.run_id)
    except ValueError as exc:
        print("Android QA evidence gate FAILED:", str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
