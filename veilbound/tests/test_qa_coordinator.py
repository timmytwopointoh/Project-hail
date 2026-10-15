"""Regression tests for the zero-dependency QA triage worker."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "scripts/qa_coordinator.py"
SPEC = importlib.util.spec_from_file_location("qa_coordinator", MODULE)
qa = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qa)

class CoordinatorTests(unittest.TestCase):
    def fresh(self):
        return {"status": "passed", "lock_button_exercised": True,
                "lock_target_diagnostic": 7}, {
            "screenshots": [{"file": str(i)} for i in range(17)],
            "performance_samples": [{"fps": 24.0, "gl_error": 0}],
            "world_asset_stage_comparisons": [
                {"asset": "cenotaph", "stage_mean_absolute_change": 15.4}],
            "warnings": []}

    def test_clean_evidence_has_clear_gate(self):
        emulator, visual = self.fresh()
        plan = qa.create_plan(emulator, visual, commit="a1b2")
        self.assertEqual("clear", plan["release_gate"])
        self.assertEqual([], plan["tasks"])
        self.assertEqual("a1b2", plan["source_commit"])

    def test_emulator_failure_blocks_even_without_visual_metrics(self):
        plan = qa.create_plan({"status": "failed", "error": "startup crashed"}, None)
        self.assertEqual("blocked", plan["release_gate"])
        self.assertIn("VB-EMULATOR-SMOKE", plan["blocker_ids"])
        self.assertIn("VB-MISSING-QA", plan["blocker_ids"])

    def test_gl_failure_and_duplicate_warning_only_one_task(self):
        emulator, visual = self.fresh()
        visual["performance_samples"] = [
            {"fps": 31, "gl_error": 1282}, {"fps": 29, "gl_error": 1282}]
        visual["warnings"] = ["Non-zero OpenGL error codes: [1282]"]
        plan = qa.create_plan(emulator, visual)
        tasks = [t for t in plan["tasks"] if t["id"] == "VB-GL-ERROR"]
        self.assertEqual(1, len(tasks))
        self.assertEqual("P0", tasks[0]["priority"])

    def test_software_fps_is_not_a_hardware_blocker(self):
        emulator, visual = self.fresh()
        visual["performance_samples"][0]["fps"] = 4.2
        visual["warnings"] = ["Slow software-emulator frame rate; measure on physical Android"]
        plan = qa.create_plan(emulator, visual)
        self.assertEqual("needs-review", plan["release_gate"])
        self.assertEqual(["VB-SLOW-EMULATOR"], [x["id"] for x in plan["tasks"]])
        self.assertEqual("performance", plan["tasks"][0]["worker"])

    def test_lock_and_very_similar_assets_queue_separately(self):
        emulator, visual = self.fresh()
        emulator["lock_target_diagnostic"] = -1
        visual["world_asset_stage_comparisons"][0]["stage_mean_absolute_change"] = .45
        plan = qa.create_plan(emulator, visual)
        self.assertEqual(["VB-ASSET-COMPARISON", "VB-LOCK-UNTESTED"],
                         [x["id"] for x in plan["tasks"]])
        self.assertEqual("blocked", plan["release_gate"])

    def test_failed_studio_orbit_is_assigned_to_studio(self):
        plan = qa.create_plan({"status": "failed",
                               "error": "AssertionError('Model studio orbit gesture did not change image')"},
                              {"screenshots": [{"file": str(i)} for i in range(17)],
                               "performance_samples": [{"fps": 24, "gl_error": 0}],
                               "warnings": []})
        self.assertEqual("blocked", plan["release_gate"])
        self.assertEqual("studio", plan["tasks"][0]["worker"])
        self.assertEqual("VB-STUDIO-ORBIT", plan["tasks"][0]["id"])

    def test_invalid_json_returns_none_and_report_is_renderable(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text("{bad")
            self.assertIsNone(qa.load_json(path))
        plan = qa.create_plan({"status": "passed"}, {"screenshots": [], "warnings": []})
        self.assertIn("QA repair queue", qa.markdown(plan))
        self.assertEqual("P1", plan["tasks"][0]["priority"])

    def test_odd_warning_is_in_review_queue(self):
        em, vi = self.fresh()
        vi["warnings"] = ["Unknown renderer issue to investigate"]
        plan = qa.create_plan(em, vi)
        self.assertEqual(["VB-UNKNOWN-WARNING"], [x["id"] for x in plan["tasks"]])

if __name__ == "__main__":
    unittest.main()
