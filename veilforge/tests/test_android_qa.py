"""Emulator QA planner and fail-closed evidence reviewer; no Android needed."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from android_visual_qa import ROLES,VIEWS,BACKGROUND
from android_review import review
from factory import load_catalog

CATALOG=Path(__file__).resolve().parents[1]/"catalog.json"

class AndroidVisualQATest(unittest.TestCase):
    def test_all_catalog_meshes_and_scene_covered_on_emulators(self):
        assigned=[id for assets in ROLES.values() for id in assets]
        self.assertEqual(len(VIEWS),14)
        self.assertEqual(len(ROLES),4)
        self.assertEqual(len(assigned),len(set(assigned)))
        self.assertEqual(set(assigned),set(load_catalog(CATALOG))|{"scene","human_repaired","bellwarden_full_anatomy_repaired"})
        self.assertEqual(BACKGROUND,(17,21,29))
    def test_reviewer_fails_closed_when_emulators_did_not_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            r=review(root/"empty",root/"report","a"*40,"b"*64)
            self.assertFalse(r["all_emulator_gates_passed"])
            self.assertEqual(r["devices_passed"],0)
            self.assertGreaterEqual(len(r["repair_queue"]),3)
            self.assertFalse(r["automatically_promoted_to_games"])
    def test_fake_attestations_and_missing_frames_do_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            d=root/"veilforge-android-scene-world"
            d.mkdir()
            (d/"emulator_visual_qa.json").write_text(json.dumps({
                "role":"scene-world","source_commit":"f"*40,"apk_sha256":"b"*64,
                "device_android_api":35,"technical_visual_smoke_pass":True,
                "artistic_quality_approved":False,"physical_device_qa_pass":False,
                "assets":[{"asset":k,"views":[],"max_orbit_change":.5} for k in ROLES["scene-world"]],
                "screenshot_count":0}))
            r=review(root,root/"report","a"*40,"b"*64)
            self.assertFalse(r["all_emulator_gates_passed"])
            self.assertTrue(any("attestations" in v for v in r["problems"]))
            self.assertTrue(any("frames" in v for v in r["problems"]))
    def test_reviewer_rejects_repeated_adjacent_camera_screenshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=root/"veilforge-android-scene-world";d.mkdir()
            payload=b"test-image-evidence"*100
            digest=hashlib.sha256(payload).hexdigest()
            assets=[]
            for name in ROLES["scene-world"]:
                views=[]
                for index,(yaw,pitch) in enumerate(VIEWS):
                    image=f"{name}/{index:02d}.png"
                    dest=d/image;dest.parent.mkdir(exist_ok=True)
                    dest.write_bytes(payload)
                    views.append({"image":image,"sha256":digest,"yaw":yaw,"pitch":pitch,
                                  "foreground_fraction":.12,"channel_stddev":15,
                                  "modal_overlay_fraction":0})
                assets.append({"asset":name,"views":views,"max_orbit_change":.2})
            report={"role":"scene-world","source_commit":"a"*40,"apk_sha256":"b"*64,
                    "device_android_api":35,"technical_visual_smoke_pass":True,
                    "material_textures_uploaded":True,"screenshots_clear_of_modal_ui":True,
                    "texture_counts":{"basecolor":8,"metallic_roughness":8},
                    "artistic_quality_approved":False,"physical_device_qa_pass":False,
                    "assets":assets,"screenshot_count":len(VIEWS)*len(assets)}
            (d/"emulator_visual_qa.json").write_text(json.dumps(report))
            (d/"device_logcat.txt").write_text("GLTF_LOADED actual_scene=true")
            (d/"android_meminfo.txt").write_text("test")
            result=review(root,root/"review","a"*40,"b"*64)
            self.assertFalse(result["all_emulator_gates_passed"])
            self.assertTrue(any("repeated adjacent screenshot" in msg
                                for msg in result["problems"]))

    def test_reviewer_rejects_wrong_expected_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                review(Path(tmp),Path(tmp)/"out","too-short","b"*64)

if __name__=="__main__":
    unittest.main()
