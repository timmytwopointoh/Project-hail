"""An auditor must not treat a green runner or fake report as a tested AI patch."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/worker_scorecard.py"
SPEC = importlib.util.spec_from_file_location("worker_scorecard", SCRIPT)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)

def plan():
    return {"worker_matrix": {"include": [
        {"role": "studio", "slot_id": "w001", "task_id": "studio-1"},
        {"role": "animation", "slot_id": "w002", "task_id": "rig-1"}]}}

def verified(role, slot, task, edited):
    return {"role": role, "slot_id": slot, "task_id": task,
            "status": "proposed_change_passed_java_tests",
            "edited_paths": edited,
            "local_ai": {"provider": "VEILBOUND local inference",
                         "model": "qwen2.5-coder:1.5b", "usage": {"eval_count": 55}},
            "proposal_requires_human_review": True, "ai_attempts": 2,
            "source_commit": "f" * 40}


class WorkerScorecardTests(unittest.TestCase):
    def test_missing_worker_report_blocks_full_acceptance(self):
        with tempfile.TemporaryDirectory() as d:
            score = audit.summarize(plan(), Path(d))
            self.assertEqual(0, score["accepted_patches"])
            self.assertFalse(score["all_accepted"])
            self.assertEqual("missing_report", score["rows"][0]["status"])

    def test_actual_local_models_must_pass_real_java_tests(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "w001"; p.mkdir()
            row = verified("studio", "w001", "studio-1",
                           [str(audit.JAVA / "ModelStudio.java")])
            (p / "worker_result.json").write_text(json.dumps(row))
            score = audit.summarize(plan(), d)
            self.assertEqual(1, score["accepted_patches"])
            self.assertFalse(score["all_accepted"])
            self.assertTrue(score["rows"][0]["accepted"])

    def test_scope_fraud_or_mocked_model_does_not_count(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "w001"; p.mkdir()
            row = verified("studio", "w001", "studio-1",
                           [str(audit.JAVA / "WorldState.java")])
            (p / "worker_result.json").write_text(json.dumps(row))
            self.assertEqual(0, audit.summarize(plan(), d)["accepted_patches"])
            row["edited_paths"] = [str(audit.JAVA / "ModelStudio.java")]
            row["local_ai"]["provider"] = "simulated fixture"
            (p / "worker_result.json").write_text(json.dumps(row))
            self.assertEqual(0, audit.summarize(plan(), d)["accepted_patches"])

    def test_failed_compile_never_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "w001"; p.mkdir()
            row = verified("studio", "w001", "studio-1",
                           [str(audit.JAVA / "ModelStudio.java")])
            row["status"] = "proposed_change_failed_compile"
            (p / "worker_result.json").write_text(json.dumps(row))
            self.assertFalse(audit.summarize(plan(), d)["rows"][0]["accepted"])

    def test_all_authorized_models_with_passing_java_are_still_review_only(self):
        with tempfile.TemporaryDirectory() as d:
            for role, slot, ident, java in (
                ("studio", "w001", "studio-1", "ModelStudio.java"),
                ("animation", "w002", "rig-1", "CharacterRig.java"),
            ):
                p = Path(d) / slot; p.mkdir()
                (p / "worker_result.json").write_text(
                    json.dumps(verified(role, slot, ident, [str(audit.JAVA / java)])))
            score = audit.summarize(plan(), d)
            self.assertEqual(2, score["accepted_patches"])
            self.assertTrue(score["all_accepted"])
            self.assertTrue(score["manual_review_required"])
            self.assertIn("review-only", audit.markdown(score))

    def test_duplicate_slot_reports_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            for folder in ("a", "b"):
                p = Path(d) / folder; p.mkdir()
                row = verified("studio", "w001", "studio-1",
                               [str(audit.JAVA / "ModelStudio.java")])
                (p / "worker_result.json").write_text(json.dumps(row))
            self.assertEqual("duplicate_report", audit.summarize(plan(), d)["rows"][0]["status"])

if __name__ == "__main__":
    unittest.main()
