"""Roadmap is a measurable coordination contract, not AI-approved work."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from roadmap import summarize,validate
PATH=Path(__file__).resolve().parents[1]/"ENGINE_MASTER_PLAN.json"

class RoadmapTest(unittest.TestCase):
    def test_complete_engine_roadmap_but_not_falsely_declared_finished(self):
        r=summarize(PATH)
        self.assertGreaterEqual(r["milestone_count"],20)
        self.assertGreater(r["counts"]["planned"],0)
        self.assertGreater(r["counts"]["partial"],0)
        self.assertFalse(r["acceptance_complete"])
        self.assertTrue(r["pending_human_release_signoff"])
        self.assertIsNotNone(r["next_safe_candidate"])
        self.assertEqual(r["next_safe_candidate"]["id"],"VF-004")
    def test_rejects_cycles_and_auto_accept(self):
        original=json.loads(PATH.read_text())
        changed=json.loads(json.dumps(original))
        changed["milestones"][0]["depends_on"]=["VF-002"]
        with self.assertRaises(ValueError):validate(changed)
        changed=json.loads(json.dumps(original))
        changed["milestones"][0]["automatic_approval"]=True
        with self.assertRaises(ValueError):validate(changed)
    def test_rejects_verified_on_unverified_dependency(self):
        data=json.loads(PATH.read_text())
        target=next(row for row in data["milestones"] if row["id"]=="VF-010")
        target["status"]="verified"
        with self.assertRaises(ValueError):validate(data)

if __name__=="__main__":
    unittest.main()
