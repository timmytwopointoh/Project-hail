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

class SafeAutoRewriteTests(unittest.TestCase):
    def test_real_sword_source_rewritten_copy_while_material_uv_indices_and_original_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);src=root/"sword"
            build_asset(ROOT/"catalog.json","ceremonial_sword",src)
            original=src/"ceremonial_sword.obj";first=original.read_bytes()
            tasks=root/"tasks.json";tasks.write_text(json.dumps(plan([task()])))
            result=rewrite(tasks,src,root/"candidates",source_sha=SHA)
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
            p=root/"tasks.json";p.write_text(json.dumps(plan([task()])))
            with self.assertRaisesRegex(ValueError,"manifest hash"):
                rewrite(p,src,root/"out",source_sha=SHA)
            self.assertFalse((root/"out/ceremonial_sword_candidate.obj").exists())
if __name__=="__main__":unittest.main()
