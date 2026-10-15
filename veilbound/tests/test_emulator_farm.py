"""Test immutable cross-runner emulator matrix and strict result aggregation."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "scripts/emulator_farm.py"
SPEC = importlib.util.spec_from_file_location("emulator_farm", FILE)
farm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(farm)

class EmulatorFarmTests(unittest.TestCase):
    def test_select_one_two_four_and_eight_separate_emulators(self):
        for count in (1, 2, 4, 8):
            p = farm.make_matrix(count)
            self.assertEqual(count, p["count"])
            self.assertEqual(count, len(p["matrix"]["include"]))
            self.assertEqual(count, len({x["id"] for x in p["matrix"]["include"]}))
            self.assertTrue(all(x["api"] in (33, 34, 35)
                                for x in p["matrix"]["include"]))

    def test_invalid_budget_is_rejected(self):
        for count in (0, 9, -1, True, "4", 50):
            with self.assertRaises(ValueError):
                farm.make_matrix(count)

    def test_success_requires_every_emulator_report_and_quality_metrics(self):
        with tempfile.TemporaryDirectory() as root:
            for cfg in farm.CONFIGS[:2]:
                path = Path(root) / ("veilbound-emulator-" + cfg["id"] + "-inspection")
                path.mkdir()
                (path / "emulator_report.json").write_text(json.dumps({
                    "status": "passed",
                    "screenshots": [{} for i in range(17)]}))
                (path / "visual_quality_metrics.json").write_text("{}")
            result = farm.summarize(root, 2)
            self.assertTrue(result["success"])
            self.assertEqual(2, result["passed"])

    def test_missing_report_fails_even_when_other_device_passed(self):
        with tempfile.TemporaryDirectory() as root:
            cfg = farm.CONFIGS[0]
            folder = Path(root) / ("veilbound-emulator-" + cfg["id"] + "-inspection")
            folder.mkdir()
            (folder / "emulator_report.json").write_text(json.dumps({
                "status": "passed", "screenshots": [{} for i in range(17)]}))
            (folder / "visual_quality_metrics.json").write_text("{}")
            result = farm.summarize(root, 2)
            self.assertFalse(result["success"])
            self.assertEqual(1, result["passed"])
            self.assertEqual("missing", result["instances"][1]["result"])

    def test_cross_platform_studio_failure_clusters_without_hiding_failures(self):
        with tempfile.TemporaryDirectory() as root:
            for cfg in farm.CONFIGS[:2]:
                path = Path(root) / ("veilbound-emulator-" + cfg["id"] + "-inspection")
                path.mkdir()
                (path / "emulator_report.json").write_text(json.dumps({
                    "status": "failed", "screenshots": [{} for i in range(11)]}))
                (path / "visual_quality_metrics.json").write_text("{}")
                (path / "task_plan.json").write_text(json.dumps({
                    "tasks": [{"id": "VB-STUDIO-ORBIT", "priority": "P1",
                               "worker": "studio", "title": "Orbit gesture inactive"}]}))
            result = farm.summarize(root, 2)
            self.assertFalse(result["success"])
            self.assertEqual(1, len(result["findings"]))
            self.assertEqual("cross-emulator", result["findings"][0]["scope"])
            self.assertEqual(2, len(result["findings"][0]["affected_emulators"]))

    def test_missing_failure_plan_is_prioritized_for_review(self):
        with tempfile.TemporaryDirectory() as root:
            result = farm.summarize(root, 1)
            self.assertFalse(result["success"])
            self.assertEqual("VB-EMULATOR-EVIDENCE-MISSING", result["findings"][0]["id"])
            self.assertEqual("P0", result["findings"][0]["priority"])

    def test_qa_failure_or_too_few_screenshots_blocks_aggregate(self):
        with tempfile.TemporaryDirectory() as root:
            cfg = farm.CONFIGS[0]
            path = Path(root) / ("veilbound-emulator-" + cfg["id"] + "-inspection")
            path.mkdir()
            (path / "emulator_report.json").write_text(json.dumps({
                "status": "failed", "screenshots": [{} for i in range(17)]}))
            (path / "visual_quality_metrics.json").write_text("{}")
            self.assertFalse(farm.summarize(root, 1)["success"])
            (path / "emulator_report.json").write_text(json.dumps({
                "status": "passed", "screenshots": [{} for i in range(2)]}))
            self.assertFalse(farm.summarize(root, 1)["success"])

if __name__ == "__main__":
    unittest.main()
