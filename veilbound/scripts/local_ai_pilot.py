#!/usr/bin/env python3
"""One live, parent-approved VEILBOUND local AI coding task.

Exercises director -> division -> specialist -> actual self-hosted coder,
then runs the regular Java test/patch gate. Never writes to GitHub.
"""
import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ai_worker import ROLES, draft_code
from team_manager import TEAM_DIVISION, review_division, review_team, verify_child
from worker_manager import load_object, plan


def pilot(role, out, *, backlog=Path("veilbound/worker_backlog.json")):
    if role not in ROLES:
        raise ValueError("Unknown allowed coding role")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    result = {"role": role, "status": "failed", "source": "hierarchical-local-model-pilot",
              "actual_ai_inference_attempted": False}
    try:
        director = plan(load_object(backlog), max_workers=50)
        assigned = next((x for x in director["worker_matrix"]["include"]
                         if x["role"] == role), None)
        if assigned is None:
            raise ValueError("No director-reviewed task is allocated to this role")
        division = TEAM_DIVISION[assigned["team"]]
        division_approval = review_division(director, division)
        team_approval = review_team(director, assigned["team"], division_approval)
        verify_child(team_approval, assigned["team"], assigned["role"],
                     assigned["task_id"], assigned["goal"], assigned["slot_id"])
        os.environ["VEILBOUND_TASK_GOAL"] = assigned["goal"]
        os.environ["VEILBOUND_TASK_ID"] = assigned["task_id"]
        os.environ["VEILBOUND_WORKER_SLOT"] = assigned["slot_id"]
        result["actual_ai_inference_attempted"] = True
        result["attempt_history"] = []
        for attempt in range(3):
            try:
                proposal = draft_code(role, out)
                result.update(proposal)
                result["attempt_history"].append({
                    "attempt": attempt+1,"status": proposal.get("status")})
                if proposal.get("status") == "proposed_change_passed_java_tests":
                    break
                details = (out/"validation.txt").read_text(errors="replace") if (
                    out/"validation.txt").is_file() else proposal.get("status","")
                os.environ["VEILBOUND_REPAIR_FEEDBACK"] = (
                    "Last attempt failed compilation/tests. Keep all public method signatures "
                    "unchanged and preserve existing callers. Trusted javac/test output: "+
                    details[-1200:])
            except (ValueError, KeyError, TypeError) as edit_error:
                result["attempt_history"].append({
                    "attempt": attempt+1,"status":"invalid_proposal",
                    "reason":str(edit_error)[:180]})
                os.environ["VEILBOUND_REPAIR_FEEDBACK"] = (
                    "Rejected proposal: "+str(edit_error)+
                    ". Copy an EXISTING exact snippet from the supplied source; "
                    "never change public signatures or add parameters.")
                if attempt==2:
                    raise
        result["approved_by_division"] = division
        result["approved_by_specialist"] = assigned["team"]
        result["source"] = "hierarchical-local-model-pilot"
    except Exception as exc:
        # Worker failures remain visible as QA evidence, never silently green.
        result["status"] = "failed"
        result["error"] = str(exc)[:500]
    (out / "worker_result.json").write_text(json.dumps(result, indent=2) + "\n",
                                            encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "proposed_change_passed_java_tests" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=list(ROLES), default="animation")
    parser.add_argument("--out", type=Path, default=Path("inspection_output/local-coding-pilot"))
    parser.add_argument("--backlog", type=Path, default=Path("veilbound/worker_backlog.json"))
    args = parser.parse_args()
    raise SystemExit(pilot(args.role, args.out, backlog=args.backlog))
