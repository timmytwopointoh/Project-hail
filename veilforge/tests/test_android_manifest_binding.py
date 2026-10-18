"""Synthetic Android screenshot manifest binding regressions."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw, PngImagePlugin
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from android_review import review
from android_visual_qa import ROLES, VIEWS, BACKGROUND

class CameraBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        serial=0
        for role,names in ROLES.items():
            folder=self.root/("veilforge-android-"+role)
            folder.mkdir()
            assets=[]
            for asset in names:
                views=[]
                for index,(yaw,pitch) in enumerate(VIEWS):
                    rel=f"{asset}/{index:02d}_yaw{yaw}_pitch{pitch}.png"
                    dest=folder/rel
                    dest.parent.mkdir(exist_ok=True)
                    img=Image.new("RGB",(480,270),BACKGROUND)
                    x=30+(serial%20)*9
                    y=35+(serial//20)*13
                    ImageDraw.Draw(img).rectangle((x,y,x+42,y+75),fill=(60+(serial*17)%170,50+(serial*29)%180,70+(serial*43)%150))
                    meta=PngImagePlugin.PngInfo()
                    meta.add_text("synthetic_fixture",f"{role}:{asset}:{index}:"+"x"*1100)
                    img.save(dest,pnginfo=meta)
                    views.append({"image":rel,"sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
                                  "yaw":yaw,"pitch":pitch,"foreground_fraction":.08,
                                  "channel_stddev":20,"modal_overlay_fraction":0})
                    serial+=1
                assets.append({"asset":asset,"views":views,"max_orbit_change":.2})
            report={"role":role,"source_commit":"a"*40,"apk_sha256":"b"*64,
                    "device_android_api":35,"technical_visual_smoke_pass":True,
                    "material_textures_uploaded":True,"screenshots_clear_of_modal_ui":True,
                    "texture_counts":{"basecolor":8,"metallic_roughness":8},
                    "artistic_quality_approved":False,"physical_device_qa_pass":False,
                    "assets":assets,"screenshot_count":len(VIEWS)*len(names)}
            (folder/"emulator_visual_qa.json").write_text(json.dumps(report))
            (folder/"device_logcat.txt").write_text("synthetic fixture")
            (folder/"android_meminfo.txt").write_text("synthetic fixture")

    def audit(self):
        return review(self.root,self.root/"audit","a"*40,"b"*64)

    def change(self,field,value):
        path=self.root/"veilforge-android-props-equipment"/"emulator_visual_qa.json"
        data=json.loads(path.read_text())
        data["assets"][0]["views"][0][field]=value
        path.write_text(json.dumps(data))

    def test_canonical_154_png_manifest_passes(self):
        result=self.audit()
        self.assertTrue(result["all_emulator_gates_passed"],result["problems"])
        self.assertEqual(result["screenshots_checked"],154)

    def test_wrong_yaw_is_rejected(self):
        self.change("yaw",999)
        result=self.audit()
        self.assertFalse(result["all_emulator_gates_passed"])
        self.assertTrue(any("camera angle mismatch" in s for s in result["problems"]))

    def test_wrong_image_is_rejected(self):
        asset=ROLES["props-equipment"][0]
        self.change("image",f"{asset}/01_yaw25_pitch25.png")
        result=self.audit()
        self.assertFalse(result["all_emulator_gates_passed"])
        self.assertTrue(any("camera screenshot path mismatch" in s for s in result["problems"]))

if __name__=="__main__":
    unittest.main()
