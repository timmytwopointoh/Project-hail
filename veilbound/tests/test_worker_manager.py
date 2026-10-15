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

    def test_unsafe_roles_never_reach_code_job(self):
        findings = {"tasks": [
            {"id": "renderer", "worker": "renderer", "priority": "P0",
             "repair_guidance": "untrusted shader"},
            {"id": "performance", "worker": "performance", "priority": "P1",
             "repair_guidance": "optimize dynamic GL resources"}]}
        p = manager.plan(self.fixture(), findings, max_workers=6)
        self.assertTrue({"renderer", "performance"}.isdisjoint(p["spawned_roles"]))
        self.assertEqual(2, len(p["review_only"]))

    def test_cloned_tasks_do_not_spawn_same_role_twice(self):
        findings = {"tasks": [{"id": "urgent-c", "worker": "combat", "priority": "P0",
                               "repair_guidance": "objective count regression"}]}
        p = manager.plan(self.fixture(), findings, max_workers=6)
        self.assertEqual(6, p["allocated"])
        self.assertEqual(1, p["spawned_roles"].count("combat"))

    def test_rejects_invalid_budget_and_unsafe_inputs(self):
        for cap in (0, -1, 7, 11, True, "3"):
            with self.assertRaises(ValueError):
                manager.plan(self.fixture(), max_workers=cap)
        bad = {"tasks": [{"id": "bad", "role": "script-runner", "goal": "echo hi"},
                          {"id": "bad2", "role": "combat", "goal": 123}]}
        self.assertEqual(0, manager.plan(bad)["allocated"])

    def test_json_matrix_and_ci_output(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "backlog.json"
            path.write_text(json.dumps(self.fixture()))
            self.assertEqual(6, len(manager.load_object(path)["tasks"]))
            p = manager.plan(manager.load_object(path), max_workers=4)
            self.assertEqual(4, len(json.loads(json.dumps(p["matrix"]))["include"]))

if __name__ == "__main__":
    unittest.main()
