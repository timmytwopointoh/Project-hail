#!/usr/bin/env python3
"""One live, parent-approved VEILBOUND local AI coding task.

Exercises director -> division -> specialist -> actual self-hosted coder,
then runs the regular Java test/patch gate. Never writes to GitHub.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ai_worker import JAVA, ROLES, draft_code
from team_manager import TEAM_DIVISION, review_division, review_team, verify_child
from worker_manager import load_object, plan


ROOT = HERE.parents[1]


def verify_studio_finite_gestures(out):
    """Trusted *additional* behavioral gate for the narrow NaN-camera pilot."""
    candidate = (Path(out) / "proposed" / JAVA / "ModelStudio.java")
    trusted_test = (ROOT / "veilbound/tests/game/ashenveil/veilbound" /
                    "StudioFiniteGestureAcceptanceTest.java")
    if not candidate.is_file() or not trusted_test.is_file():
        return False, "Missing Studio replacement source or trusted postcondition test"
    environment = {key: value for key, value in os.environ.items()
                   if key in ("PATH", "JAVA_HOME", "HOME", "LANG", "LC_ALL", "TMPDIR")}
    with tempfile.TemporaryDirectory(prefix="veilbound-studio-postcondition-") as temp:
        classes = Path(temp) / "classes"
        classes.mkdir()
        compiled = subprocess.run(
            ["javac", "-d", str(classes), str(candidate), str(trusted_test)],
            cwd=ROOT, text=True, capture_output=True, timeout=90, env=environment)
        if compiled.returncode:
            return False, (compiled.stdout + compiled.stderr)[-5000:]
        executed = subprocess.run(
            ["java", "-cp", str(classes),
             "game.ashenveil.veilbound.StudioFiniteGestureAcceptanceTest"],
            cwd=ROOT, text=True, capture_output=True, timeout=30, env=environment)
        if executed.returncode:
            return False, (executed.stdout + executed.stderr)[-5000:]
        if "VEILBOUND_STUDIO_FINITE_GESTURE_PASS" not in executed.stdout:
            return False, "Required Studio finite-gesture marker was not emitted"
    return True, "trusted Studio NaN-gesture regression passed"



def check_studio_candidate(replacement):
    """Run the authoritative NaN-touch postcondition on an in-memory edit.

    This verifier runs inside the bounded AI correction loop. No generated
    source is installed into the real game checkout or trusted test directory.
    """
    path = str(JAVA / "ModelStudio.java")
    if path not in replacement:
        return False, "Studio specialist must actually update ModelStudio.java"
    with tempfile.TemporaryDirectory(prefix="veilbound-studio-candidate-") as folder:
        dest = Path(folder) / "proposed" / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(replacement[path], encoding="utf-8")
        passed, report = verify_studio_finite_gestures(folder)
    if not passed:
        report += ("\\nJava IEEE-754 fact: x == Float.NaN and x != Float.NaN "
                   "CANNOT test NaN; neither comparison behaves like a "
                   "finite-value check. Use Float.isNaN(x) to detect NaN, "
                   "return lo for NaN, preserve the exact finite clamp logic.")
    return passed, report


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
        verifier = (check_studio_candidate if
                    assigned["task_id"] == "VB-PILOT-STUDIO-FINITE" else None)
        result.update(draft_code(role, out, extra_verifier=verifier))
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
    parser.add_argument("--backlog", type=Path,
                        default=Path("veilbound/worker_backlog.json"))
    args = parser.parse_args()
    raise SystemExit(pilot(args.role, args.out, backlog=args.backlog))
