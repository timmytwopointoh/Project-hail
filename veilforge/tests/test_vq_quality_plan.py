"""VQ quality roadmap is fail-closed and never equates green CI with perfection."""
import copy,json
from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vq_quality_plan import PLAN,review
class VQQualityPlanTests(unittest.TestCase):
    def test_comprehensive_named_release_gates_and_unfinished_work(self):
        result=review(PLAN)
        self.assertGreaterEqual(result["milestones"],30)
        self.assertEqual(result["milestones"],result["p0"]+result["p1"]+result["p2"])
        self.assertFalse(result["all_milestones_verified"])
        self.assertFalse(result["game_auto_promotion_allowed"])
        self.assertGreater(result["planned"],0)
        self.assertEqual(result["verified"],0)
    def test_fails_closed_on_false_completion_or_removed_release_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"plan.json"
            doc=json.loads(PLAN.read_text())
            doc["milestones"][0]["status"]="verified"
            target.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError,"explicit provenance"):
                review(target)
            doc["milestones"][0]["status"]="partial"
            doc["release_gates"].remove("reference_appearance_human_signoff")
            target.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError,"Critical release"):
                review(target)
    def test_duplicate_ids_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc=json.loads(PLAN.read_text())
            doc["milestones"][1]["id"]=doc["milestones"][0]["id"]
            p=Path(tmp)/"bad.json";p.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError,"Duplicated"):
                review(p)
if __name__=="__main__":unittest.main()
