#!/usr/bin/env python3
"""Exercise proposal -> pure Java validation -> approval gate with NO AI/API key.

Each role gets a deterministic harmless package-line comment on a temporary
replacement copy. The live repo is never modified. This tests the actual
worker implementation and approval validator, not simulated pass statuses.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import ai_worker
import promote_proposal

def run(role, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rel = ai_worker.JAVA / ai_worker.ROLES[role][0]
    original = (ROOT / rel).read_text(encoding="utf-8")
    package = "package game.ashenveil.veilbound;"
    if original.count(package) != 1:
        raise AssertionError("Expected a unique Java package statement in " + str(rel))
    fixture = {
        "summary": "Deterministic CI-only harmless unused import; not an AI improvement",
        "edits": [{"path": str(rel), "find": package,
                   "replace": package + "\nimport java.util.concurrent.TimeUnit; // QA FIXTURE ONLY"}],
        "risks": ["Fixture change is never promoted or committed"],
    }
    # Real draft_code executes javac and every existing pure-Java test suite.
    # Only the external model response is simulated in this test.
    with patch.object(ai_worker, "ask_local", return_value=json.dumps(fixture)):
        result = ai_worker.draft_code(role, out)
    if result["status"] != "proposed_change_passed_java_tests":
        raise AssertionError("Worker did not compile/test actual proposed Java: " +
                             json.dumps(result))
    (out / "worker_result.json").write_text(json.dumps(result, indent=2) + "\n")
    expected_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    files = promote_proposal.stage_proposal(ROOT, out, role, expected_sha, dry_run=True)
    if files != [str(rel)]:
        raise AssertionError("Promotion scoped wrong files: " + repr(files))
    if (ROOT / rel).read_text(encoding="utf-8") != original:
        raise AssertionError("CI dry-run modified the real game source")
    bad = dict(result)
    bad["source_commit"] = "f" * 40
    (out / "worker_result.json").write_text(json.dumps(bad) + "\n")
    try:
        promote_proposal.load_proposal(out, role, expected_sha)
    except ValueError:
        pass
    else:
        raise AssertionError("Forged source commit accepted by promotion gate")
    (out / "worker_result.json").write_text(json.dumps(result, indent=2) + "\n")
    evidence = {
        "role": role, "test_mode": "provider-free deterministic fixture",
        "actual_java_tests": result["status"],
        "promotion_dry_run": "passed",
        "wrong_sha_rejected": True,
        "live_repo_unchanged": True,
        "source_commit": expected_sha,
    }
    (out / "pipeline_verification.json").write_text(
        json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=sorted(ai_worker.ROLES), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    sys.exit(run(args.role, args.out))
