"""Compositor settling must never turn missing real frames into false success."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_visual_qa import capture_visible_frame

class PresentedFrameTest(unittest.TestCase):
    def test_waits_for_real_visible_frame(self):
        blank={"foreground_fraction":1.0,"channel_stddev":0.0}
        visible={"foreground_fraction":.14,"channel_stddev":19.5,
                 "renderer_background_confirmed":True}
        with patch("android_visual_qa.screenshot", side_effect=["blank","visible"]) as shot, \
             patch("android_visual_qa.metrics", side_effect=[blank,visible]), \
             patch("android_visual_qa.adb", return_value="FRAME_OK"), \
             patch("android_visual_qa.time.sleep") as delay:
            pic,measured,attempt=capture_visible_frame("actual.png",attempts=3,interval=.1)
        self.assertEqual((pic,measured,attempt),("visible",visible,2))
        self.assertEqual(shot.call_count,2)
        delay.assert_called_once_with(.1)

    def test_launcher_foreground_is_not_genuine_gles_geometry(self):
        # Contrast and foreground alone cannot distinguish a splash screen.
        launcher={"foreground_fraction":.65,"channel_stddev":45,
                  "renderer_background_confirmed":False}
        with patch("android_visual_qa.screenshot",return_value="launcher") as shot, \
             patch("android_visual_qa.metrics",return_value=launcher), \
             patch("android_visual_qa.adb",return_value="FRAME_OK"), \
             patch("android_visual_qa.time.sleep"):
            with self.assertRaisesRegex(RuntimeError,"launcher/splash"):
                capture_visible_frame("actual.png",attempts=2,interval=0)
        self.assertEqual(shot.call_count,2)

    def test_renderer_background_pixels_are_checked_on_real_images(self):
        from PIL import Image,ImageDraw
        from android_visual_qa import metrics
        valid=Image.new("RGB",(640,360),(17,21,29))
        ImageDraw.Draw(valid).rectangle((180,110,490,300),fill=(96,83,60))
        splash=Image.new("RGB",(640,360),(48,48,48))
        ImageDraw.Draw(splash).rectangle((180,110,490,300),fill=(96,83,60))
        self.assertTrue(metrics(valid)["renderer_background_confirmed"])
        self.assertFalse(metrics(splash)["renderer_background_confirmed"])

    def test_persistent_blank_fails_closed(self):
        blank={"foreground_fraction":.999,"channel_stddev":1.0}
        with patch("android_visual_qa.screenshot", return_value="blank") as shot, \
             patch("android_visual_qa.metrics", return_value=blank), \
             patch("android_visual_qa.adb", return_value="FRAME_OK"), \
             patch("android_visual_qa.time.sleep") as delay:
            with self.assertRaisesRegex(RuntimeError,"after 3 real screenshot attempts"):
                capture_visible_frame("actual.png",attempts=3,interval=.1)
        self.assertEqual(shot.call_count,3)
        self.assertEqual(delay.call_count,2)

    def test_renderer_errors_do_not_get_hidden_by_retries(self):
        blank={"foreground_fraction":0,"channel_stddev":0}
        with patch("android_visual_qa.screenshot", return_value="blank") as shot, \
             patch("android_visual_qa.metrics", return_value=blank), \
             patch("android_visual_qa.adb", return_value="GL_ERROR 1282"), \
             patch("android_visual_qa.time.sleep") as delay:
            with self.assertRaisesRegex(RuntimeError,"renderer failed"):
                capture_visible_frame("actual.png",attempts=8)
        self.assertEqual(shot.call_count,1)
        delay.assert_not_called()

    def test_previous_frame_digest_is_carried_across_assets(self):
        # A new FRAME_OK event does not prove the Android compositor
        # has presented the new asset. Guard the first frame as well.
        import inspect
        from android_visual_qa import capture
        source=inspect.getsource(capture)
        self.assertEqual(source.count("previous_frame_sha=None"),1)
        self.assertLess(source.index("previous_frame_sha=None"),
                        source.index("for asset in ROLES[role]:"))

    def test_cross_asset_stale_frame_is_archived_then_recaptured(self):
        import hashlib
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"00_yaw0_pitch15.png"
            values=[b"previous-asset-frame",b"correct-new-asset-frame"]
            def take(path):
                Path(path).write_bytes(values.pop(0))
                return "presented-image"
            visible={"foreground_fraction":.14,"channel_stddev":20.,
                     "renderer_background_confirmed":True}
            with patch("android_visual_qa.screenshot",side_effect=take), \
                 patch("android_visual_qa.metrics",return_value=visible), \
                 patch("android_visual_qa.time.sleep"):
                _,measured,attempt=capture_visible_frame(
                    target,attempts=2,interval=0,
                    previous_frame_sha=hashlib.sha256(b"previous-asset-frame").hexdigest())
            self.assertEqual(attempt,2)
            self.assertEqual(measured,visible)
            self.assertEqual(target.read_bytes(),b"correct-new-asset-frame")
            self.assertEqual(
                (target.parent/"00_yaw0_pitch15_stale_presented_1.png").read_bytes(),
                b"previous-asset-frame")

    def test_zero_attempts_rejected(self):
        with self.assertRaises(ValueError):
            capture_visible_frame("actual.png",attempts=0)

if __name__=="__main__":
    unittest.main()
