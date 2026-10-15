"""Master worker planner tests: work isolation, dynamic caps and QA urgency."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MANAGER_PATH = Path(__file__).resolve().parents[1] / "scripts/worker_manager.py"
SPEC = importlib.util.spec_from_file_location("worker_manager", MANAGER_PATH)
manager = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manager)

class ManagerTests(unittest.TestCase):
    def fixture(self):
        return {"tasks": [
            {"id": "c", "role": "combat", "goal": "fix objective counters", "priority": "P1"},
            {"id": "a", "role": "animation", "goal": "smooth sword arc", "priority": "P1"},
            {"id": "m", "role": "models", "goal": "improve armor meshes", "priority": "P2"},
            {"id": "t", "role": "materials", "goal": "surface atlas maps", "priority": "P2"},
            {"id": "w", "role": "world", "goal": "improve ruins", "priority": "P2"},
            {"id": "s", "role": "studio", "goal": "orbit framing", "priority": "P2"},
        ]}

    def test_manager_spawns_four_of_six_independent_roles(self):
        p = manager.plan(self.fixture(), max_workers=4)
        self.assertEqual(4, p["allocated"])
        self.assertEqual(4, len(set(p["spawned_roles"])))
        self.assertEqual(4, len(p["matrix"]["include"]))
        self.assertEqual(["combat", "animation", "models", "materials"],
                         p["spawned_roles"])

    def test_manager_can_scale_six_and_down_to_two(self):
        self.assertEqual(6, manager.plan(self.fixture(), max_workers=6)["allocated"])
        self.assertEqual(2, manager.plan(self.fixture(), max_workers=2)["allocated"])

    def test_qa_regression_preempts_roadmap_with_same_owner(self):
        findings = {"tasks": [{"id": "GL-bug", "worker": "studio",
                               "priority": "P0", "repair_guidance": "camera test fails"}]}
        p = manager.plan(self.fixture(), findings, max_workers=3)
        row = next(x for x in p["matrix"]["include"] if x["role"] == "studio")
        self.assertEqual("measured-qa", row["source"])
        self.assertEqual("GL-bug", row["task_id"])
        self.assertEqual(3, p["allocated"])

    def test_failed_build_without_report_pauses_speculative_coders(self):
        p = manager.plan(self.fixture(), {}, max_workers=6,
                         workflow_conclusion="failure")
        self.assertEqual(0, p["allocated"])
        self.assertTrue(p["paused_for_missing_failure_evidence"])
        self.assertEqual("VB-CI-FAILURE-NO-ARTIFACT",
                         p["review_only"][0]["task_id"])

    def test_failed_emulator_with_specific_studio_issue_dispatches_studio(self):
        findings = {"tasks": [
            {"id": "VB-STUDIO-ORBIT", "worker": "studio", "priority": "P1",
             "repair_guidance": "Investigate real touch orbit mismatch"}]}
        p = manager.plan(self.fixture(), findings, max_workers=2,
                         workflow_conclusion="failure")
        self.assertFalse(p["paused_for_missing_failure_evidence"])
        self.assertIn("studio", p["spawned_roles"])
        self.assertEqual("measured-qa", next(x["source"] for x in
                         p["matrix"]["include"] if x["role"] == "studio"))

    def test_unsafe_roles_never_reach_code_job(self):
        findings = {"tasks": [
            {"id": "renderer", "worker": "renderer", "priority": "P0",
             "repair_guidance": "untrusted shader"},
            {"id": "performance", "worker": "performance", "priority": "P1",
             "repair_guidance": "optimize dynamic GL resources"}]}
        p = manager.plan(self.fixture(), findings, max_workers=6)
        self.assertTrue({"renderer", "performance"}.isdisjoint(p["spawned_roles"]))
        self.assertEqual(2, len(p["review_only"]))

    def test_multiple_distinct_same_role_tasks_are_isolated_not_deduplicated(self):
        findings = {"tasks": [{"id": "urgent-c", "worker": "combat", "priority": "P0",
                               "repair_guidance": "objective count regression"}]}
        p = manager.plan(self.fixture(), findings, max_workers=6)
        self.assertEqual(6, p["allocated"])
        self.assertEqual(2, p["spawned_roles"].count("combat"))
        self.assertEqual(6, len(set(x["slot_id"] for x in p["matrix"]["include"])))
        self.assertIn("urgent-c", [x["task_id"] for x in p["matrix"]["include"]])

    def test_rejects_invalid_budget_and_unsafe_inputs(self):
        for cap in (0, -1, 51, 100, True, "3"):
            with self.assertRaises(ValueError):
                manager.plan(self.fixture(), max_workers=cap)
        bad = {"tasks": [{"id": "bad", "role": "script-runner", "goal": "echo hi"},
                          {"id": "bad2", "role": "combat", "goal": 123}]}
        self.assertEqual(0, manager.plan(bad)["allocated"])

    def test_fifty_task_slots_are_unique_and_balanced_across_three_teams(self):
        roles = ("combat", "animation", "models", "materials", "world", "studio")
        backlog = {"tasks": [
            {"id": "TASK-%03d" % i, "role": roles[i % len(roles)],
             "goal": "Repair unique subsystem item %d" % i, "priority": "P2"}
            for i in range(60)]}
        p = manager.plan(backlog, max_workers=50)
        self.assertEqual(50, p["allocated"])
        self.assertEqual(3, p["team_count"])
        self.assertEqual(50, len(set(x["slot_id"] for x in p["matrix"]["include"])))
        self.assertEqual(50, len(set(x["task_id"] for x in p["matrix"]["include"])))
        self.assertEqual("w050", p["matrix"]["include"][-1]["slot_id"])
        counts = {x["team"]: x["child_count"] for x in p["team_matrix"]["include"]}
        self.assertEqual(50, sum(counts.values()))
        self.assertTrue(all(0 < value <= 18 for value in counts.values()))
        self.assertTrue(all(value >= 15 for value in counts.values()))

    def test_live_fifty_task_backlog_covers_every_slot(self):
        path = MANAGER_PATH.parents[1] / "worker_backlog.json"
        backlog = manager.load_object(path)
        self.assertEqual(50, len(backlog["tasks"]))
        actual = manager.plan(backlog, max_workers=50)
        self.assertEqual(50, actual["allocated"])
        self.assertEqual(3, actual["team_count"])
        self.assertEqual("w050", actual["matrix"]["include"][-1]["slot_id"])

    def test_duplicate_exact_task_id_is_not_double_billed(self):
        backlog = {"tasks": [
            {"id": "DUP", "role": "combat", "goal": "same task", "priority": "P2"},
            {"id": "DUP", "role": "combat", "goal": "same task", "priority": "P2"}]}
        self.assertEqual(1, manager.plan(backlog, max_workers=50)["allocated"])

    def test_json_matrix_and_ci_output(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "backlog.json"
            path.write_text(json.dumps(self.fixture()))
            self.assertEqual(6, len(manager.load_object(path)["tasks"]))
            p = manager.plan(manager.load_object(path), max_workers=4)
            self.assertEqual(4, len(json.loads(json.dumps(p["matrix"]))["include"]))

if __name__ == "__main__":
    unittest.main()
