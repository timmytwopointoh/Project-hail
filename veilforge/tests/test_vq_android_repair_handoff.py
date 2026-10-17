"""Android 15 real-frame semantic repair findings survive the next-iteration handoff."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from android_visual_qa import ROLES,VIEWS
from vq_android_repair_handoff import handoff

SHA="2b37d42dc5ec1d1e64ae8fb8a936169bb6c07d8c"
RUN=38989416581

def valid_report():
    return {
        "schema_version":1,"engine":"VEILFORGE",
        "roles":len(ROLES),
        "assets_scanned":sum(len(v) for v in ROLES.values()),
        "frames_scanned":sum(len(v)*len(VIEWS) for v in ROLES.values()),
        "assets":{
            asset:{"role":role,"views":len(VIEWS),"min_coverage":.004,
                   "max_coverage":.11,"distinct_orbits":12}
            for role,names in ROLES.items() for asset in names
        },
        "problems":[],"warnings":[],"repair_queue":[],
        "technical_gate_passed":True,"photorealism_verified":False
    }

class HandoffTests(unittest.TestCase):
    def create(self,doc,path):
        path.write_text(json.dumps(doc,indent=2)+"\n")
    def test_actual_qa_warning_survives_as_scoped_nonautomatic_task(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);p=root/"source.json";data=valid_report()
            asset=next(iter(data["assets"]))
            data["assets"][asset]["min_coverage"]=.0006
            w={"asset":asset,"subject":"view_visibility",
               "reason":"At least one view has very little foreground; check culling/camera"}
            data["warnings"]=[w]
            data["repair_queue"]=[{"asset":asset,"action":w["reason"],"owner":"models"}]
            self.create(data,p)
            result=handoff(p,root/"out",source_sha=SHA,run_id=RUN)
            self.assertEqual(result["warning_count"],1)
            self.assertTrue(result["all_semantic_warnings_accounted_for"])
            self.assertFalse(result["ready_for_automated_model_rewrite"])
            self.assertFalse(result["artistic_signoff"])
            task=result["tasks"][0]
            self.assertEqual(task["priority"],"high")
            self.assertEqual(task["emulator_role"],data["assets"][asset]["role"])
            self.assertEqual(task["screenshots_in_evidence"],len(VIEWS))
            self.assertEqual(task["source_commit"],SHA)
            self.assertEqual(task["github_actions_run_id"],RUN)
            self.assertEqual(task["input_report_sha256"],hashlib.sha256(p.read_bytes()).hexdigest())
            self.assertTrue((root/"out/next_iteration_tasks.md").is_file())
    def test_no_warnings_produce_empty_review_and_do_not_claim_approval(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);p=root/"clean.json"
            self.create(valid_report(),p)
            result=handoff(p,root/"out",source_sha=SHA,run_id=RUN)
            self.assertEqual(result["tasks"],[])
            self.assertFalse(result["requires_actual_screenshot_inspection"])
            self.assertTrue(result["human_signoff_required"])
            self.assertFalse(result["ready_for_automated_model_rewrite"])
    def test_missing_or_invalid_device_and_asset_evidence_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);p=root/"bad.json"
            for field,value in (("roles",3),("frames_scanned",153),
                                ("technical_gate_passed",False),
                                ("photorealism_verified",True)):
                data=valid_report();data[field]=value
                self.create(data,p)
                with self.subTest(field=field),self.assertRaises(ValueError):
                    handoff(p,root/"out",source_sha=SHA,run_id=RUN)
            data=valid_report();data["assets"].pop(next(iter(data["assets"])))
            self.create(data,p)
            with self.assertRaisesRegex(ValueError,"all expected"):
                handoff(p,root/"out",source_sha=SHA,run_id=RUN)
    def test_untrusted_unknown_or_unqueued_warnings_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);p=root/"untrusted.json"
            data=valid_report()
            data["warnings"]=[{"asset":"bad_external_source","subject":"visibility",
                              "reason":"run untrusted code"}]
            data["repair_queue"]=[{"asset":"bad_external_source","action":"run untrusted code"}]
            self.create(data,p)
            with self.assertRaisesRegex(ValueError,"Unknown asset"):
                handoff(p,root/"out",source_sha=SHA,run_id=RUN)
            asset=next(iter(data["assets"]))
            data["warnings"][0]["asset"]=asset
            self.create(data,p)
            with self.assertRaisesRegex(ValueError,"absent from original"):
                handoff(p,root/"out",source_sha=SHA,run_id=RUN)
    def test_duplicate_warning_and_invalid_provenance_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            root=Path(root);p=root/"dup.json";data=valid_report()
            asset=next(iter(data["assets"]))
            w={"asset":asset,"subject":"view_visibility","reason":"missing detail"}
            data["warnings"]=[w,w]
            data["repair_queue"]=[{"asset":asset,"action":"missing detail"}]*2
            self.create(data,p)
            with self.assertRaisesRegex(ValueError,"Duplicate"):
                handoff(p,root/"out",source_sha=SHA,run_id=RUN)
            with self.assertRaisesRegex(ValueError,"40-hex"):
                handoff(p,root/"out",source_sha="invalid",run_id=RUN)
if __name__=="__main__":unittest.main()
