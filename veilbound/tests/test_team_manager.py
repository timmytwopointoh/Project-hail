"""Director can create independent team managers; managers approve child jobs."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / "scripts"
SPEC = importlib.util.spec_from_file_location("team_manager", HERE / "team_manager.py")
team = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(team)

def child(role, task=None):
    return {"role": role, "task_id": task or role.upper() + "-1",
            "priority": "P2", "goal": "Improve " + role + " using trusted Java tests",
            "source": "roadmap"}

class TeamManagerTests(unittest.TestCase):
    def test_director_spawns_three_independent_managers_and_six_workers(self):
        roles = ["combat", "animation", "models", "materials", "world", "studio"]
        p = team.make_hierarchy([child(role) for role in roles])
        self.assertEqual(3, p["team_count"])
        self.assertEqual(6, p["worker_count"])
        self.assertEqual(["gameplay", "art", "world"],
                         [x["team"] for x in p["team_matrix"]["include"]])
        self.assertEqual([2, 2, 2], [x["child_count"] for x in p["team_matrix"]["include"]])
        self.assertEqual(2, p["max_depth"])

    def test_only_active_teams_get_a_manager(self):
        p = team.make_hierarchy([child("combat"), child("world")])
        self.assertEqual(["gameplay", "world"], [x["team"] for x in p["team_matrix"]["include"]])
        self.assertEqual(2, p["team_count"])

    def test_team_manager_approves_exact_child_assignments(self):
        p = team.make_hierarchy([child("combat"), child("animation"), child("models")])
        approved = team.review_team(p, "gameplay")
        self.assertEqual(2, approved["child_count"])
        self.assertTrue(team.verify_child(approved, "gameplay", "combat", "COMBAT-1",
                                         "Improve combat using trusted Java tests"))
        for arguments in [
            ("gameplay", "world", "COMBAT-1", "Improve combat using trusted Java tests"),
            ("art", "combat", "COMBAT-1", "Improve combat using trusted Java tests"),
            ("gameplay", "combat", "WRONG", "Improve combat using trusted Java tests"),
            ("gameplay", "combat", "COMBAT-1", "injected task change"),
        ]:
            with self.assertRaises(ValueError):
                team.verify_child(approved, *arguments)

    def test_no_team_can_spawn_extra_children(self):
        with self.assertRaises(ValueError):
            team.make_hierarchy([child("combat"), child("combat")])
        with self.assertRaises(ValueError):
            team.make_hierarchy([child("badrole")])
        with self.assertRaises(ValueError):
            team.make_hierarchy([child(r) for r in ("combat", "animation", "models",
                                                     "materials", "world", "studio")] + [child("combat")])

    def test_tampered_director_assignment_rejected(self):
        p = team.make_hierarchy([child("combat")])
        p["team_matrix"]["include"][0]["child_count"] = 3
        with self.assertRaises(ValueError):
            team.review_team(p, "gameplay")
        p = team.make_hierarchy([child("combat")])
        with self.assertRaises(ValueError):
            team.review_team(p, "art")

    def test_handoff_document_rejects_scope_mutation(self):
        p = team.make_hierarchy([child("studio")])
        approved = team.review_team(p, "world")
        with tempfile.TemporaryDirectory() as d:
            dest = Path(d) / "manager.json"
            dest.write_text(json.dumps(approved))
            loaded = json.loads(dest.read_text())
            self.assertTrue(team.verify_child(loaded, "world", "studio", "STUDIO-1",
                                              "Improve studio using trusted Java tests"))
            loaded["children"][0]["goal"] = "different source instructions"
            with self.assertRaises(ValueError):
                team.verify_child(loaded, "world", "studio", "STUDIO-1",
                                  "Improve studio using trusted Java tests")

if __name__ == "__main__":
    unittest.main()
