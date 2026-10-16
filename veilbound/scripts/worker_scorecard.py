#!/usr/bin/env python3
"""Deterministic independent audit of all selected local-AI worker results.

A GitHub job being green does not prove its model authored code. This auditor
requires the exact director-approved slot/role, nonempty changed Java files,
a real local inference model, and a passing trusted Java test status.
Never approves merges automatically.
"""
import argparse
import json
import sys
from pathlib import Path

# Support direct script invocation AND importlib-based test loading.
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from ai_worker import JAVA, ROLES

PASS = "proposed_change_passed_java_tests"


def summarize(master, root):
    if not isinstance(master, dict):
        raise ValueError("Director plan must be JSON object")
    slots = master.get("worker_matrix", {}).get("include", [])
    if not isinstance(slots, list) or len(slots) > 50:
        raise ValueError("Invalid director worker slot list")
    found = {}
    for file in Path(root).rglob("worker_result.json"):
        try:
            obj = json.loads(file.read_text(encoding="utf-8"))
        except (UnicodeError, OSError, json.JSONDecodeError):
            continue
        if not isinstance(obj, dict):
            continue
        key = obj.get("slot_id")
        if isinstance(key, str) and key:
            found.setdefault(key, []).append(obj)
    rows = []
    for task in slots:
        role, slot, ident = task["role"], task["slot_id"], task["task_id"]
        candidates = found.get(slot, [])
        if len(candidates) == 0:
            rows.append({"slot_id": slot, "role": role, "task_id": ident,
                         "status": "missing_report", "accepted": False})
            continue
        if len(candidates) != 1:
            rows.append({"slot_id": slot, "role": role, "task_id": ident,
                         "status": "duplicate_report", "accepted": False})
            continue
        result = candidates[0]
        changes = result.get("edited_paths")
        exact_files = {str(JAVA / name) for name in ROLES[role]}
        scoped = (isinstance(changes, list) and len(changes) > 0
                  and len(changes) <= 3 and len(set(changes)) == len(changes)
                  and all(isinstance(f, str) and f in exact_files for f in changes))
        metadata = result.get("local_ai")
        live = (isinstance(metadata, dict) and
                metadata.get("provider") == "VEILBOUND local inference" and
                isinstance(metadata.get("model"), str) and
                metadata["model"].startswith("qwen2.5-coder:"))
        aligned = result.get("role") == role and result.get("task_id") == ident
        status = result.get("status", "unknown")
        accepted = all((aligned, scoped, live, status == PASS,
                        result.get("proposal_requires_human_review") is True))
        rows.append({"slot_id": slot, "role": role, "task_id": ident,
                     "status": status if aligned else "mismatched_assignment",
                     "accepted": accepted, "local_inference_verified": live,
                     "allowed_paths": scoped, "ai_attempts": result.get("ai_attempts"),
                     "source_commit": result.get("source_commit")})
    passed = sum(r["accepted"] for r in rows)
    return {"schema_version": 1, "total_slots": len(slots),
            "accepted_patches": passed, "rejected_or_missing": len(slots) - passed,
            "all_accepted": len(slots) > 0 and passed == len(slots),
            "manual_review_required": True,
            "rows": rows}


def markdown(score):
    lines = ["# VEILBOUND local AI worker acceptance scorecard", "",
             "Accepted model-generated, Java-tested patches: **" +
             str(score["accepted_patches"]) + " / " +
             str(score["total_slots"]) + "**", "",
             "| Slot | Specialist | Task | Verification |",
             "|---|---|---|---|"]
    for row in score["rows"]:
        lines.append("| " + row["slot_id"] + " | " + row["role"] + " | " +
                     row["task_id"].replace("|", "/") + " | " +
                     ("validated, review-only" if row["accepted"] else
                      "REJECTED: " + str(row["status"]).replace("|", "/")) + " |")
    lines.extend(["", "No patch is merged by this report; each accepted patch "
                  "still needs human review, Android emulator testing on the "
                  "Moto G (2025) profile, and eventually physical-phone QA.", ""])
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", type=Path, required=True)
    ap.add_argument("--results", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    try:
        master = json.loads(args.plan.read_text(encoding="utf-8"))
        score = summarize(master, args.results)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print("Worker audit FAILED:", str(exc)[:320], file=sys.stderr)
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "worker_scorecard.json").write_text(json.dumps(score, indent=2) + "\n")
    (args.out / "worker_scorecard.md").write_text(markdown(score))
    print(json.dumps({"total_slots": score["total_slots"],
                      "accepted_patches": score["accepted_patches"],
                      "rejected_or_missing": score["rejected_or_missing"]}, indent=2))
    return 0 if score["all_accepted"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
