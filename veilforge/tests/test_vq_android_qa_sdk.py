"""M34-10: real PNG bytes, honest metrics and path safety across Android roles."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vq_android_qa_sdk import evidence_png, frame_is_trusted
from android_visual_qa import metrics


class SharedAndroidQASDKTest(unittest.TestCase):
    def make_capture(self, root, name="angle_00.png", *, background=(17, 21, 29)):
        from PIL import Image, ImageDraw
        image = Image.new("RGB", (800, 480), background)
        ImageDraw.Draw(image).rectangle((220, 130, 570, 390), fill=(120, 92, 73))
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(path)
        return path, metrics(image)

    def test_factory_and_m30_accept_same_real_png(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, score = self.make_capture(root, "human_repaired/00_yaw0_pitch15.png")
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertTrue(frame_is_trusted(score))
            self.assertEqual(
                evidence_png(root, "human_repaired/00_yaw0_pitch15.png", sha, score),
                score,
            )
            self.assertEqual(evidence_png(root / "human_repaired", path.name, sha, score), score)

    def test_spoofed_reported_pixel_metrics_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, score = self.make_capture(root)
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            altered = dict(score, foreground_fraction=0.8)
            with self.assertRaisesRegex(ValueError, "pixel metrics mismatch"):
                evidence_png(root, path.name, sha, altered)
            altered = dict(score, renderer_background_confirmed=False)
            with self.assertRaisesRegex(ValueError, "Reported screenshot"):
                evidence_png(root, path.name, sha, altered)

    def test_launcher_and_blank_cannot_pass_with_forged_metrics(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, score = self.make_capture(root, background=(48, 48, 48))
            fake = dict(score, renderer_background_confirmed=True)
            with self.assertRaisesRegex(ValueError, "Actual PNG pixels fail"):
                evidence_png(root, path.name, hashlib.sha256(path.read_bytes()).hexdigest(), fake)
            from PIL import Image
            Image.new("RGB", (800, 480), (17, 21, 29)).save(path)
            with self.assertRaisesRegex(ValueError, "Actual PNG pixels fail"):
                evidence_png(root, path.name, hashlib.sha256(path.read_bytes()).hexdigest(), fake)

    def test_corruption_traversal_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "evidence"
            root.mkdir()
            path, score = self.make_capture(root)
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            for unsafe in ("../angle_00.png", "/tmp/angle_00.png", "nested/../../angle_00.png", r"foo\bar.png"):
                with self.subTest(unsafe=unsafe), self.assertRaisesRegex(ValueError, "Unsafe screenshot path"):
                    evidence_png(root, unsafe, sha, score)
            (root / "alias.png").symlink_to(path)
            with self.assertRaisesRegex(ValueError, "escapes evidence directory"):
                evidence_png(root, "alias.png", sha, score)
            with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                evidence_png(root, path.name, "0" * 64, score)
            path.write_bytes(b"not-a-real-png")
            with self.assertRaisesRegex(ValueError, "byte length"):
                evidence_png(root, path.name, hashlib.sha256(path.read_bytes()).hexdigest(), score)

    def test_untrusted_fields_fail_closed(self):
        for score in (None, {}, {"renderer_background_confirmed": True},
                      {"renderer_background_confirmed": True, "foreground_fraction": .1,
                       "channel_stddev": 20, "modal_overlay_fraction": .71}):
            self.assertFalse(frame_is_trusted(score))


if __name__ == "__main__":
    unittest.main()
