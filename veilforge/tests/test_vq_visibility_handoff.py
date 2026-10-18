"""H21 handoff must bind visibility hypotheses to canonical Android angles."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from android_visual_qa import ROLES,VIEWS
from visual_semantics import visibility_evidence
from vq_android_repair_handoff import handoff


class VisibilityHandoffTest(unittest.TestCase):
    def test_propagates_verified_review_only_evidence_and_rejects_tampering(self):
        assets={asset:{"role":role,"views":14,"min_coverage":.004,"max_coverage":.03}
                for role,names in ROLES.items() for asset in names}
        frames=[{"coverage":.01,"bbox_width":.12,"bbox_height":.3} for _ in VIEWS]
        frames[0]={"coverage":.0015,"bbox_width":.031,"bbox_height":.12}
        frames[10]={"coverage":.0254,"bbox_width":.125,"bbox_height":.885}
        evidence=visibility_evidence(frames)
        assets["ceremonial_sword"]["visibility_evidence"]=evidence
        reason="At least one view has very little foreground; check culling/camera"
        warning={"asset":"ceremonial_sword","subject":"view_visibility","reason":reason,
                 "visibility_interpretation":"possible_edge_on_view"}
        doc={"schema_version":1,"engine":"VEILFORGE","roles":len(ROLES),
             "assets_scanned":len(assets),"frames_scanned":len(assets)*len(VIEWS),
             "assets":assets,"problems":[],"warnings":[warning],
             "repair_queue":[{"asset":"ceremonial_sword","action":reason}],
             "technical_gate_passed":True,"photorealism_verified":False}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"semantic.json";out=Path(tmp)/"out"
            def run():
                p.write_text(json.dumps(doc))
                return handoff(p,out,source_sha="a"*40,run_id=123)
            task=run()["tasks"][0]
            self.assertEqual(task["visibility_evidence"]["strongest_view_yaw"],250)
            self.assertFalse(task["auto_promote"])
            self.assertFalse(task["automatic_model_edit"])
            evidence["lowest_view_yaw"]=25
            with self.assertRaisesRegex(ValueError,"canonical camera"):run()
            evidence["lowest_view_yaw"]=0
            evidence["interpretation_is_artistic_approval"]=True
            with self.assertRaisesRegex(ValueError,"cannot approve art"):run()
            evidence["interpretation_is_artistic_approval"]=False
            warning["visibility_interpretation"]="framing_or_visibility_review"
            with self.assertRaisesRegex(ValueError,"differ"):run()


if __name__=="__main__":unittest.main()
