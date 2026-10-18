"""Fail closed on a repeated Android screenshot hash across different assets."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from android_review import review
from android_visual_qa import ROLES,VIEWS

def evidence(root,replay=False,nonadjacent=False):
    previous=None
    for role,names in ROLES.items():
        d=root/("veilforge-android-"+role)
        d.mkdir()
        assets=[]
        for name in names:
            views=[]
            for index,(yaw,pitch) in enumerate(VIEWS):
                data=(f"synthetic-{role}-{name}-{index}|".encode()*100)
                if role=="props-equipment" and name=="treasure_chest" and index==13:
                    previous=data
                if replay and role=="props-equipment" and name=="ceremonial_sword" and index==0:
                    data=previous
                if nonadjacent and role=="props-equipment" and name=="ceremonial_sword" and index==3:
                    data=(f"synthetic-{role}-{name}-0|".encode()*100)
                rel=f"{name}/{index:02d}_yaw{yaw}_pitch{pitch}.png"
                target=d/rel
                target.parent.mkdir(exist_ok=True)
                target.write_bytes(data)
                views.append({"image":rel,"sha256":hashlib.sha256(data).hexdigest(),
                              "yaw":yaw,"pitch":pitch,"foreground_fraction":.12,
                              "channel_stddev":15,"modal_overlay_fraction":0})
            assets.append({"asset":name,"views":views,"max_orbit_change":.2})
        report={"role":role,"source_commit":"a"*40,"apk_sha256":"b"*64,
                "device_android_api":35,"technical_visual_smoke_pass":True,
                "material_textures_uploaded":True,"screenshots_clear_of_modal_ui":True,
                "texture_counts":{"basecolor":8,"metallic_roughness":8},
                "artistic_quality_approved":False,"physical_device_qa_pass":False,
                "assets":assets,"screenshot_count":len(VIEWS)*len(names)}
        (d/"emulator_visual_qa.json").write_text(json.dumps(report))
        (d/"device_logcat.txt").write_text("synthetic fixture")
        (d/"android_meminfo.txt").write_text("synthetic fixture")

class CrossAssetEvidenceTests(unittest.TestCase):
    def test_unique_154_views_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            evidence(root)
            result=review(root,root/"out","a"*40,"b"*64)
            self.assertTrue(result["all_emulator_gates_passed"],result["problems"])
            self.assertEqual(result["screenshots_checked"],154)
    def test_delayed_same_asset_replay_fails_independent_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            evidence(root,nonadjacent=True)
            result=review(root,root/"out","a"*40,"b"*64)
            self.assertFalse(result["all_emulator_gates_passed"])
            self.assertEqual(len(result["problems"]),1,result["problems"])
            issue=result["problems"][0]
            self.assertIn("repeated nonadjacent screenshot",issue)
            self.assertIn("first yaw=0 pitch=15",issue)
            self.assertIn("replayed yaw=75 pitch=15",issue)

    def test_stale_chest_as_sword_fails_independent_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            evidence(root,replay=True)
            result=review(root,root/"out","a"*40,"b"*64)
            self.assertFalse(result["all_emulator_gates_passed"])
            self.assertEqual(len(result["problems"]),1,result["problems"])
            issue=result["problems"][0]
            self.assertIn("cross-asset identical screenshot",issue)
            self.assertIn("treasure_chest yaw=325 pitch=25",issue)
            self.assertIn("ceremonial_sword yaw=0 pitch=15",issue)
            self.assertFalse(result["automatically_promoted_to_games"])

if __name__=="__main__":
    unittest.main()
