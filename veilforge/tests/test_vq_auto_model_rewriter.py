"""VQ autonomous candidate rewrites are real, bounded and never auto-approved."""
import hashlib,json,sys,tempfile
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory import build_asset
from engine import read_obj
from vq_auto_model_rewriter import rewrite

ROOT=Path(__file__).resolve().parents[1]
SHA="85f634f58d0a5863186b22a90c1fd74292cc8c2b"

def task(asset="ceremonial_sword"):
    return {"id":"review-"+asset+"-view_visibility","kind":"visual_review",
            "asset":asset,"diagnostic":"view_visibility",
            "emulator_role":"props-equipment",
            "source_commit":SHA,"screenshots_in_evidence":14,
            "minimum_foreground_coverage":.0006,
            "automatic_model_edit":False,"auto_promote":False}

def plan(tasks):
    return {"schema_version":1,"source_commit":SHA,"tasks":tasks,
            "all_semantic_warnings_accounted_for":True,
            "ready_for_automated_model_rewrite":False}

RUN=38993296206

def approved_task():
    row=task()
    row["screenshot_provenance_verified"]=True
    row["camera_view_evidence"]=[
        {"index":i,"yaw":i*25,"pitch":15,"sha256":f"{i+1:064x}"}
        for i in range(14)]
    return row

def write_review(root,task_file,row):
    review={"decision":"confirmed_geometry_defect",
            "asset":row["asset"],"task_id":row["id"],
            "source_commit":SHA,"run_id":RUN,
            "handoff_sha256":hashlib.sha256(task_file.read_bytes()).hexdigest(),
            "frame_sha256":[frame["sha256"] for frame in row["camera_view_evidence"]],
            "non_edge_on_view_indices":[2,9],
            "reason":"Synthetic unit test only; does not claim a real sword geometry defect."}
    dest=root/"manual_review.json"
    dest.write_text(json.dumps(review))
    return dest

class SafeAutoRewriteTests(unittest.TestCase):
    def test_real_sword_source_rewritten_copy_while_material_uv_indices_and_original_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);src=root/"sword"
            build_asset(ROOT/"catalog.json","ceremonial_sword",src)
            original=src/"ceremonial_sword.obj";first=original.read_bytes()
            row=approved_task()
            tasks=root/"tasks.json";tasks.write_text(json.dumps(plan([row])))
            plan_data=json.loads(tasks.read_text());plan_data["github_actions_run_id"]=RUN
            tasks.write_text(json.dumps(plan_data))
            review=write_review(root,tasks,row)
            result=rewrite(tasks,src,root/"candidates",source_sha=SHA,
                           review_approval=review)
            self.assertEqual(len(result["candidates"]),1)
            candidate=result["candidates"][0]
            self.assertGreater(candidate["gain"],1.0)
            self.assertLessEqual(candidate["gain"],1.08)
            self.assertLessEqual(candidate["relative_displacement_limit"],.008)
            self.assertEqual(candidate["original_14_views"],14)
            self.assertEqual(candidate["candidate_14_views"],14)
            self.assertEqual(candidate["approval"],"pending_android_and_artist_review")
            self.assertFalse(result["auto_promotion"])
            self.assertFalse(result["android_candidate_visual_qa_passed"])
            self.assertEqual(original.read_bytes(),first)
            other=root/"candidates/ceremonial_sword_candidate.obj"
            self.assertNotEqual(hashlib.sha256(first).hexdigest(),
                                hashlib.sha256(other.read_bytes()).hexdigest())
            a=read_obj(original);b=read_obj(other)
            self.assertEqual(a[3],b[3])
            self.assertEqual(a[1],b[1])
    def test_tickets_without_an_allowlisted_real_geometry_rewrite_are_not_automatically_modified(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/"tasks.json"
            row=task("human_repaired");row["emulator_role"]="characters"
            p.write_text(json.dumps(plan([row])))
            result=rewrite(p,root/"none",root/"out",source_sha=SHA)
            self.assertEqual(result["candidates"],[])
            self.assertFalse(result["artistic_acceptance"])
    def test_forged_or_automatically_approved_tickets_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);p=root/"tasks.json"
            for field,val in (("auto_promote",True),("automatic_model_edit",True),
                              ("screenshots_in_evidence",5)):
                row=task();row[field]=val
                p.write_text(json.dumps(plan([row])))
                result=rewrite(p,root/"none",root/"out",source_sha=SHA)
                self.assertFalse(result["candidates"])
            wrong=plan([task()])
            wrong["source_commit"]="f"*40
            p.write_text(json.dumps(wrong))
            with self.assertRaisesRegex(ValueError,"stale"):
                rewrite(p,root/"none",root/"out",source_sha=SHA)
    def test_verified_source_manifest_cannot_be_forged(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);src=root/"sword"
            build_asset(ROOT/"catalog.json","ceremonial_sword",src)
            obj=src/"ceremonial_sword.obj"
            obj.write_bytes(obj.read_bytes()+b"#tampered\n")
            row=approved_task()
            p=root/"tasks.json";data=plan([row]);data["github_actions_run_id"]=RUN
            p.write_text(json.dumps(data))
            review=write_review(root,p,row)
            with self.assertRaisesRegex(ValueError,"manifest hash"):
                rewrite(p,src,root/"out",source_sha=SHA,review_approval=review)
            self.assertFalse((root/"out/ceremonial_sword_candidate.obj").exists())
    def test_unreviewed_real_sword_warning_does_not_create_candidate(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);src=root/"sword"
            build_asset(ROOT/"catalog.json","ceremonial_sword",src)
            original=src/"ceremonial_sword.obj";before=original.read_bytes()
            p=root/"tasks.json";p.write_text(json.dumps(plan([task()])))
            result=rewrite(p,src,root/"out",source_sha=SHA)
            self.assertEqual(result["heuristic_tickets"],1)
            self.assertEqual(result["eligible_tickets"],0)
            self.assertEqual(result["candidates"],[])
            self.assertTrue(result["specialist_review_required"])
            self.assertIsNone(result["review_approval_sha256"])
            self.assertEqual(original.read_bytes(),before)
            self.assertFalse((root/"out/ceremonial_sword_candidate.obj").exists())

    def test_review_hash_or_camera_evidence_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);row=approved_task()
            p=root/"tasks.json";data=plan([row]);data["github_actions_run_id"]=RUN
            p.write_text(json.dumps(data))
            review=write_review(root,p,row)
            original=json.loads(review.read_text())
            for bad in ({"handoff_sha256":"0"*64},
                        {"frame_sha256":["0"*64]*14},
                        {"decision":"unreviewed"}):
                payload=dict(original);payload.update(bad)
                review.write_text(json.dumps(payload))
                with self.assertRaisesRegex(ValueError,"Specialist review"):
                    rewrite(p,root/"none",root/"out",source_sha=SHA,
                            review_approval=review)
            row["screenshot_provenance_verified"]=False
            p.write_text(json.dumps(plan([row])))
            with self.assertRaisesRegex(ValueError,"SHA-verified"):
                rewrite(p,root/"none",root/"out",source_sha=SHA,
                        review_approval=review)

if __name__=="__main__":unittest.main()
