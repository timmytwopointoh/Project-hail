"""Four-level CI allocation: director -> divisions -> specialists -> workers."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / "scripts"
SPEC = importlib.util.spec_from_file_location("team_manager", HERE / "team_manager.py")
team = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(team)

ROLES = ("combat", "animation", "models", "materials", "world", "studio")

def child(role, task=None, slot=1):
    return {"role": role, "task_id": task or role.upper() + "-1",
            "priority": "P2", "goal": "Improve " + role + " using trusted Java tests",
            "source": "roadmap", "slot_id": "w%03d" % slot}

def fifty_jobs():
    return [child(ROLES[i % 6], "TASK-%03d" % i, i + 1) for i in range(50)]

class TeamManagerTests(unittest.TestCase):
    def test_director_produces_three_divisions_six_teams_and_fifty_workers(self):
        p = team.make_hierarchy(fifty_jobs())
        self.assertEqual(3, p["division_count"])
        self.assertEqual(6, p["team_count"])
        self.assertEqual(50, p["worker_count"])
        self.assertEqual(3, p["max_depth"])
        self.assertEqual(["game-systems", "visual-art", "world-tools"],
                         [x["division"] for x in p["division_matrix"]["include"]])
        self.assertEqual(list(team.TEAM_ROLES),
                         [x["team"] for x in p["team_matrix"]["include"]])
        self.assertTrue(all(x["child_count"] <= 10
                            for x in p["team_matrix"]["include"]))

    def test_only_active_divisions_and_specialists_spawn(self):
        p = team.make_hierarchy([child("combat"), child("world", slot=2)])
        self.assertEqual(2, p["division_count"])
        self.assertEqual(2, p["team_count"])
        self.assertEqual({"combat", "environment"},
                         {t["team"] for t in p["team_matrix"]["include"]})

    def test_division_manager_signs_two_specialists_and_rejects_other_division(self):
        p = team.make_hierarchy([child("combat"), child("animation", slot=2),
                                 child("world", slot=3)])
        div = team.review_division(p, "game-systems")
        self.assertEqual(2, div["team_count"])
        self.assertTrue(team.verify_team(div, "game-systems", "combat", 1))
        with self.assertRaises(ValueError):
            team.verify_team(div, "game-systems", "environment", 1)
        with self.assertRaises(ValueError):
            team.review_division(p, "visual-art")

    def test_specialist_manager_requires_correct_division_authorization(self):
        p = team.make_hierarchy([child("combat"), child("animation", slot=2)])
        parent = team.review_division(p, "game-systems")
        approved = team.review_team(p, "combat", parent)
        self.assertEqual("game-systems", approved["division"])
        self.assertTrue(team.verify_child(
            approved, "combat", "combat", "COMBAT-1",
            "Improve combat using trusted Java tests", "w001"))
        for role, identifier, goal, slot in [
            ("world", "COMBAT-1", "Improve combat using trusted Java tests", "w001"),
            ("combat", "FAKE", "Improve combat using trusted Java tests", "w001"),
            ("combat", "COMBAT-1", "altered instructions", "w001"),
            ("combat", "COMBAT-1", "Improve combat using trusted Java tests", "w002"),
        ]:
            with self.assertRaises(ValueError):
                team.verify_child(approved, "combat", role, identifier, goal, slot)
        with self.assertRaises(ValueError):
            team.review_team(p, "combat", {"approved": True, "division": "visual-art", "teams": []})

    def test_fifty_workers_parented_by_six_independent_specialists(self):
        p = team.make_hierarchy(fifty_jobs())
        for item in p["division_matrix"]["include"]:
            division = team.review_division(p, item["division"])
            for t in division["teams"]:
                approved = team.review_team(p, t["team"], division)
                for child_job in approved["children"]:
                    self.assertTrue(team.verify_child(
                        approved, t["team"], child_job["role"], child_job["task_id"],
                        child_job["goal"], child_job["slot_id"]))

    def test_tampered_hierarchy_is_rejected(self):
        p = team.make_hierarchy([child("combat")])
        p["division_matrix"]["include"][0]["worker_count"] = 100
        with self.assertRaises(ValueError):
            team.review_division(p, "game-systems")
        p = team.make_hierarchy([child("combat")])
        p["team_matrix"]["include"][0]["child_count"] = 10
        with self.assertRaises(ValueError):
            team.review_division(p, "game-systems")

    def test_invalid_tasks_limits_duplicates_and_unknown_roles(self):
        with self.assertRaises(ValueError):
            team.make_hierarchy([child("combat"), child("combat", slot=2)])
        with self.assertRaises(ValueError):
            team.make_hierarchy([child("badrole")])
        with self.assertRaises(ValueError):
            team.make_hierarchy([child(ROLES[i % 6], "A-%03d" % i, i + 1)
                                 for i in range(51)])
        with self.assertRaises(ValueError):
            team.make_hierarchy([child("combat", "A-%d" % i, i + 1) for i in range(11)])
        with self.assertRaises(ValueError):
            team.make_hierarchy([child("combat", "A", 1), child("animation", "B", 1)])

    def test_handoff_remains_read_only_data(self):
        p = team.make_hierarchy([child("studio")])
        parent = team.review_division(p, "world-tools")
        approved = team.review_team(p, "studio", parent)
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "approval.json"
            file.write_text(json.dumps(approved))
            data = json.loads(file.read_text())
            self.assertTrue(team.verify_child(data, "studio", "studio", "STUDIO-1",
                                              "Improve studio using trusted Java tests", "w001"))
            data["children"][0]["goal"] = "replaced"
            with self.assertRaises(ValueError):
                team.verify_child(data, "studio", "studio", "STUDIO-1",
                                  "Improve studio using trusted Java tests", "w001")

if __name__ == "__main__":
    unittest.main()
