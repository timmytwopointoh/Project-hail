"""M30 Android package and independent render-evidence safety tests."""
import hashlib,json
from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vq_m30_android_pack import pack
from vq_m30_android_review import review
from vq_sculpt_detail_patch import build
ROOT=Path(__file__).resolve().parents[1]

class AndroidM30Tests(unittest.TestCase):
    def test_actual_baked_geometry_textured_gltf_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build(root/"meshes")
            m=pack(root/"meshes/source_low.obj",root/"meshes/source_high.obj",root/"scene")
            doc=json.loads((root/"scene/ruin_courtyard_demo.gltf").read_text())
            self.assertEqual(doc["extras"]["production_approved"],False)
            self.assertEqual(doc["materials"][0]["normalTexture"]["index"],2)
            self.assertEqual(len(doc["meshes"]),1)
            self.assertEqual(len(doc["images"]),4)
            self.assertEqual(doc["nodes"][0]["extras"]["asset_id"],"vq_m30_patch")
            self.assertGreater(m["bake_normal_variation_texels"],1000)
            self.assertTrue(all((root/"scene"/i["uri"]).is_file() for i in doc["images"]))
            self.assertFalse((root/"scene/_build_review").exists())
            self.assertFalse(m["artistic_approval"])
    def test_missing_emulator_reports_never_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            r=review(root/"none",root/"report")
            self.assertFalse(r["android_material_gate_passed"])
            self.assertEqual(r["android_15_emulators_completed"],0)
            self.assertTrue(any("Missing emulator role" in p for p in r["problems"]))
    def test_forged_emulator_report_missing_actual_pngs_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=root/"pixel_4";folder.mkdir()
            (folder/"m30_emulator_report.json").write_text(json.dumps({
                "role":"pixel_4","android_api":35,"technical_gate_passed":True,
                "real_gles_normal_and_ao_uploaded":True,
                "shading_enabled_comparison_verified":True,
                "artistic_approval":False,"photorealism_verified":False,
                "source_commit":"sha","apk_sha256":"apk",
                "screenshots":[{"image":"angle_00.png","sha256":"fake"}]*14,
                "actual_emulator_frames":15,
                "normal_map_on_off_pixel_difference":.13,
                "flat_baseline_sha256":"fake"
            }))
            r=review(root,root/"review",source_sha="sha",apk_sha="apk")
            self.assertFalse(r["android_material_gate_passed"])
            self.assertTrue(any("missing source screenshot" in p for p in r["problems"]))
    def test_android_shader_contains_real_normal_toggle_and_ao_sampler(self):
        java=(ROOT/"android-probe/app/src/main/java/game/veilforge/probe/ViewerActivity.java").read_text()
        for marker in ("uNormalTexture","uAOTexture","aTangent","aBitangent",
                       'getBooleanExtra("flat",false)',
                       "M30_NORMAL_MAP_DRAW"):
            self.assertIn(marker,java)
if __name__=="__main__":unittest.main()
