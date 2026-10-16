"""QA artifact integrity: never spawn repairs from missing or forged evidence."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "scripts/evidence_guard.py"
SPEC = importlib.util.spec_from_file_location("evidence_guard", PATH)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def valid():
    tasks = [{"id": "VB-STUDIO-CONTROLS", "priority": "P1", "worker": "studio",
              "title": "Atelier control inputs not changing state",
              "repair_guidance": "Check Android touch coordinates"}]
    return {"project": "VEILBOUND", "schema_version": 1,
            "source_commit": "a" * 40, "emulator_status": "failed",
            "release_gate": "blocked", "task_count": 1, "tasks": tasks,
            "blocker_ids": ["VB-STUDIO-CONTROLS"]}


class EvidenceGateTests(unittest.TestCase):
    def checked(self, record):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "task_plan.json").write_text(json.dumps(record))
            return gate.verify_evidence(folder, run_id="38826236884")

    def test_actual_completed_emulator_bug_is_accepted(self):
        result = self.checked(valid())
        self.assertEqual("blocked", result["release_gate"])
        self.assertEqual("a" * 40, result["source_commit"])

    def test_missing_plan_does_not_degrade_to_roadmap(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "did not provide"):
                gate.verify_evidence(folder, run_id="38826236884")

    def test_bad_run_id_and_bad_commit_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "run ID"):
                gate.verify_evidence(folder, run_id="../otherrepo")
        data = valid()
        data["source_commit"] = "unknown"
        with self.assertRaisesRegex(ValueError, "source commit"):
            self.checked(data)

    def test_failures_cannot_be_reported_as_clear(self):
        data = valid()
        data["release_gate"] = "clear"
        with self.assertRaisesRegex(ValueError, "contradicts"):
            self.checked(data)
        data = valid()
        data["tasks"] = []
        data["blocker_ids"] = []
        data["task_count"] = 0
        data["release_gate"] = "clear"
        with self.assertRaisesRegex(ValueError, "blocking"):
            self.checked(data)

    def test_invalid_or_duplicate_tasks_rejected(self):
        data = valid()
        data["tasks"].append(dict(data["tasks"][0]))
        data["task_count"] = 2
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.checked(data)

    def test_clean_completed_run_is_allowed_without_fake_tasks(self):
        data = valid()
        data["emulator_status"] = "passed"
        data["release_gate"] = "clear"
        data["blocker_ids"] = []
        data["tasks"] = []
        data["task_count"] = 0
        self.assertEqual(0, self.checked(data)["tasks"])

    def test_invalid_json_is_failed_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "task_plan.json").write_text("{ broken")
            with self.assertRaises(ValueError):
                gate.verify_evidence(folder, run_id="38826236884")

if __name__ == "__main__":
    unittest.main()
