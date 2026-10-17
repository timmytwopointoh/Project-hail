"""Real PNG pixel-provenance regression for independent camera evidence."""
import hashlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw, PngImagePlugin

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_visual_qa import ROLES, VIEWS, BACKGROUND
from vq_android_camera_evidence import audit_archive, compare


def fixture(path, *, commit, scale=0, replay=False, tamper=False):
    role = "props-equipment"
    names = ROLES[role]
    saved = {}
    assets = []
    for ai, asset in enumerate(names):
        views = []
        for i, (yaw, pitch) in enumerate(VIEWS):
            img = Image.new("RGB", (80, 48), BACKGROUND)
            draw = ImageDraw.Draw(img)
            width = 6 + (i % 3) + scale
            draw.rectangle((15, 8, 15+width, 24+scale),
                           fill=(80+ai*30, 110+i*5, 130+ai*10))
            png = io.BytesIO()
            img.save(png, format="PNG")
            data = png.getvalue()
            if ai == 0 and i == 13:
                saved["chest"] = img.copy()
            if replay and ai == 1 and i == 0:
                # Same decoded pixels as the chest, but a different PNG SHA.
                info = PngImagePlugin.PngInfo()
                info.add_text("different_png_metadata", "not_a_different_camera")
                png = io.BytesIO()
                saved["chest"].save(png, format="PNG", pnginfo=info)
                data = png.getvalue()
            name = f"{asset}/{i:02d}_yaw{yaw}_pitch{pitch}.png"
            saved[name] = data
            views.append({"yaw": yaw, "pitch": pitch, "image": name,
                          "sha256": "0"*64 if tamper and ai == 1 and i == 0
                          else hashlib.sha256(data).hexdigest()})
        assets.append({"asset": asset, "views": views})
    report = {"role": role, "source_commit": commit,
              "apk_sha256": "f"*64, "assets": assets,
              "screenshot_count": len(VIEWS)*len(names)}
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("emulator_visual_qa.json", json.dumps(report))
        for name, data in saved.items():
            if isinstance(data, bytes):
                z.writestr(name, data)
        z.writestr(names[0]+"/00_yaw0_pitch15_rejected_duplicate_1.png", b"rejected")


class CameraEvidenceTests(unittest.TestCase):
    def test_all_real_png_views_and_coverage_gain(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp)/"before.zip"
            new = Path(tmp)/"after.zip"
            fixture(old, commit="a"*40, scale=0)
            fixture(new, commit="b"*40, scale=4)
            result = compare(old, new, "ceremonial_sword")
            self.assertTrue(result["all_14_views_verified"])
            self.assertEqual(len(result["angles"]), 14)
            self.assertTrue(result["mean_coverage_improved"])
            self.assertTrue(result["minimum_coverage_improved"])
            self.assertGreater(result["mean_coverage_ratio"], 1.1)
            self.assertEqual(result["before_rejected_candidates_retained"], 1)
            self.assertFalse(result["artistic_quality_approved"])
            self.assertFalse(result["phone_hardware_performance_verified"])

    def test_reencoded_cross_asset_stale_pixels_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/"stale.zip"
            fixture(source, commit="a"*40, replay=True)
            with zipfile.ZipFile(source) as z:
                report = json.loads(z.read("emulator_visual_qa.json"))
                chest = z.read(report["assets"][0]["views"][13]["image"])
                sword = z.read(report["assets"][1]["views"][0]["image"])
            self.assertNotEqual(hashlib.sha256(chest).hexdigest(),
                                hashlib.sha256(sword).hexdigest())
            with self.assertRaisesRegex(ValueError, "cross-asset pixel-identical"):
                audit_archive(source)

    def test_manifest_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/"tampered.zip"
            fixture(source, commit="a"*40, tamper=True)
            with self.assertRaisesRegex(ValueError, "screenshot SHA mismatch"):
                audit_archive(source)

    def test_identical_source_sha_is_not_a_before_after_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = Path(tmp)/"before.zip"
            new = Path(tmp)/"after.zip"
            fixture(old, commit="a"*40)
            fixture(new, commit="a"*40, scale=3)
            with self.assertRaisesRegex(ValueError, "commits must differ"):
                compare(old, new, "ceremonial_sword")


if __name__ == "__main__":
    unittest.main()
