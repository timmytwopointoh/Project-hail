"""LOD frame provenance unit regressions."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_visual_qa import VIEWS, BACKGROUND
from visual_lod import report
from vq_lod_evidence import PAIR_ROLES, verified_lod_frames

class LODProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for asset, role in PAIR_ROLES.items():
            folder = self.root / ("veilforge-android-" + role)
            folder.mkdir()
            views = []
            for i, (yaw, pitch) in enumerate(VIEWS):
                rel = f"{asset}/{i:02d}_yaw{yaw}_pitch{pitch}.png"
                dest = folder / rel
                dest.parent.mkdir(exist_ok=True)
                im = Image.new("RGB", (240, 180), BACKGROUND)
                x = 60 + i * 3
                ImageDraw.Draw(im).rectangle((x, 50, x + 38, 120),
                                             fill=(150, 105, 75))
                im.save(dest)
                views.append({"image": rel, "yaw": yaw, "pitch": pitch,
                              "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()})
            data = {"role": role, "source_commit": "a" * 40,
                    "apk_sha256": "b" * 64,
                    "assets": [{"asset": asset, "views": views}],
                    "screenshot_count": len(VIEWS)}
            (folder / "emulator_visual_qa.json").write_text(json.dumps(data))

    def manifest(self, role):
        return self.root / ("veilforge-android-" + role) / "emulator_visual_qa.json"

    def modify(self, role, callback):
        path = self.manifest(role)
        data = json.loads(path.read_text())
        callback(data)
        path.write_text(json.dumps(data))

    def test_28_canonical_hashed_frames_pass(self):
        images, source, apk = verified_lod_frames(self.root)
        self.assertEqual(sum(map(len, images.values())), 28)
        self.assertEqual((source, apk), ("a" * 40, "b" * 64))
        result = report(self.root, self.root / "lod-output")
        self.assertEqual(result["samples"], 14)
        self.assertTrue(result["lod_evidence_sha_and_camera_verified"])

    def test_changed_frame_bytes_fail(self):
        path = self.root / "veilforge-android-nature-mobile" / (
            "ancient_gate_mobile/00_yaw0_pitch15.png")
        path.write_bytes(path.read_bytes() + b"changed")
        with self.assertRaisesRegex(ValueError, "SHA mismatch"):
            report(self.root, self.root / "lod-output")

    def test_mismatched_apk_fail(self):
        self.modify("nature-mobile", lambda data: data.update(apk_sha256="c" * 64))
        with self.assertRaisesRegex(ValueError, "different APK"):
            verified_lod_frames(self.root)

    def test_mismatched_source_fail(self):
        self.modify("nature-mobile", lambda data: data.update(source_commit="d" * 40))
        with self.assertRaisesRegex(ValueError, "different source"):
            verified_lod_frames(self.root)

    def test_wrong_camera_fails(self):
        self.modify("nature-mobile", lambda data:
                    data["assets"][0]["views"][0].update(yaw=25))
        with self.assertRaisesRegex(ValueError, "noncanonical"):
            verified_lod_frames(self.root)

if __name__ == "__main__":
    unittest.main()
