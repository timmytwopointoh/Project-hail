"""Regression: real task-specific behavior failure gets a bounded AI repair attempt."""
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/ai_worker.py"
SPEC = importlib.util.spec_from_file_location("studio_behavior_worker", SCRIPT)
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)

SOURCE = str(worker.JAVA / "ModelStudio.java")
CLAMP = "private static float clamp(float x,float lo,float hi){return Math.max(lo,Math.min(hi,x));}"

def response(replace):
    return json.dumps({
        "summary": "Prevent nonfinite touch input from invalidating the Studio camera",
        "edits": [{"path": SOURCE, "find": CLAMP, "replace": replace}],
        "risks": ["Requires device-emulator acceptance before merge"],
    })


class BehavioralRetryTests(unittest.TestCase):
    def run_trial(self, answers, checker):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            with patch.object(worker, "ask_local", side_effect=answers) as called, \
                 patch.object(worker, "run_java_checks",
                              return_value=("proposed_change_passed_java_tests", "")), \
                 patch.dict(os.environ, {"VEILBOUND_TASK_GOAL": "Fix NaN clamp for camera"},
                            clear=False):
                result = worker.draft_code("studio", out, extra_verifier=checker)
            patch_text = (out / "changes.patch").read_text()
            return result, called.call_count, patch_text

    def test_real_nan_logic_failure_is_returned_to_second_model_attempt(self):
        naive = CLAMP.replace(
            "return Math.max(lo,Math.min(hi,x));",
            "return x != Float.NaN ? Math.max(lo,Math.min(hi,x)) : lo;")
        safe = CLAMP.replace(
            "return Math.max(lo,Math.min(hi,x));",
            "return Float.isNaN(x) ? lo : Math.max(lo,Math.min(hi,x));")
        inspected = []
        def verifier(changes):
            candidate = changes[SOURCE]
            inspected.append(candidate)
            if "Float.isNaN(x)" in candidate:
                return True, "trusted Studio finite gesture behavior test passed"
            return False, "Java NaN comparator invalid; use Float.isNaN(x)"
        result, calls, patch_text = self.run_trial(
            [response(naive), response(safe)], verifier)
        self.assertEqual("proposed_change_passed_java_tests", result["status"])
        self.assertEqual(2, calls)
        self.assertEqual(2, len(inspected))
        self.assertEqual(
            ["proposed_change_failed_postcondition", "proposed_change_passed_java_tests"],
            [r["status"] for r in result["attempt_history"]])
        self.assertTrue(result["behavioral_postcondition"]["passed"])
        self.assertIn("Float.isNaN(x)", patch_text)
        self.assertNotIn("x != Float.NaN", patch_text)

    def test_postcondition_failure_never_counts_as_verified(self):
        naive = CLAMP.replace(
            "return Math.max(lo,Math.min(hi,x));",
            "return x != Float.NaN ? Math.max(lo,Math.min(hi,x)) : lo;")
        result, calls, _ = self.run_trial(
            [response(naive), response(naive)],
            lambda changes: (False, "trusted NaN-camera test failed"))
        self.assertEqual("proposed_change_failed_postcondition", result["status"])
        self.assertEqual(2, calls)
        self.assertFalse(result["behavioral_postcondition"]["passed"])

if __name__ == "__main__":
    unittest.main()
