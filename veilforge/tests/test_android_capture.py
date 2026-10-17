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

    def test_zoomed_real_sword_tip_does_not_invalidate_three_clear_sky_probes(self):
        # Regression from real H13 Pixel 5 yaw75 screenshot: old center-top
        # sample was (28,31,33), 11 off GLES background; off-axis sample
        # was (17,21,29). Keep all three new samples mandatory.
        from PIL import Image, ImageDraw
        from android_visual_qa import renderer_background_confirmed
        frame=Image.new("RGB",(640,360),(17,21,29))
        ImageDraw.Draw(frame).rectangle((318,5,324,180),fill=(28,31,33))
        self.assertTrue(renderer_background_confirmed(frame))
        frame.putpixel((int(640*.20),int(360*.08)),(48,48,48))
        self.assertFalse(renderer_background_confirmed(frame))

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

    def test_rejects_stale_presented_frame_and_preserves_evidence(self):
        from PIL import Image, ImageDraw
        from tempfile import TemporaryDirectory
        old=Image.new("RGB",(640,360),(17,21,29))
        ImageDraw.Draw(old).rectangle((180,110,350,300),fill=(100,90,70))
        fresh=Image.new("RGB",(640,360),(17,21,29))
        ImageDraw.Draw(fresh).rectangle((250,110,450,300),fill=(100,90,70))
        visible={"foreground_fraction":.12,"channel_stddev":19.5,
                 "renderer_background_confirmed":True}
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"01_yaw25_pitch25.png"
            shots=iter([old,fresh])
            def take(dest):
                pic=next(shots)
                pic.save(dest)
                return pic
            with patch("android_visual_qa.screenshot",side_effect=take) as shot, \
                 patch("android_visual_qa.metrics",return_value=visible.copy()), \
                 patch("android_visual_qa.time.sleep") as delay:
                pic,measured,attempt=capture_visible_frame(
                    path,attempts=3,interval=.1,previous_frame=old)
            self.assertEqual(attempt,2)
            self.assertEqual(shot.call_count,2)
            self.assertEqual(measured["rejected_duplicate_count"],1)
            self.assertGreater(measured["previous_view_change_fraction"],.0006)
            self.assertTrue((Path(tmp)/"01_yaw25_pitch25_rejected_duplicate_1.png").is_file())
            delay.assert_called_once_with(.1)

    def test_persistent_stale_frame_fails_closed(self):
        from PIL import Image
        from tempfile import TemporaryDirectory
        old=Image.new("RGB",(640,360),(17,21,29))
        visible={"foreground_fraction":.12,"channel_stddev":19.5,
                 "renderer_background_confirmed":True}
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"01.png"
            def take(dest):
                old.save(dest)
                return old
            with patch("android_visual_qa.screenshot",side_effect=take) as shot, \
                 patch("android_visual_qa.metrics",return_value=visible), \
                 patch("android_visual_qa.time.sleep"):
                with self.assertRaisesRegex(RuntimeError,"repeated stale GLES frame"):
                    capture_visible_frame(path,attempts=2,interval=0,previous_frame=old)
            self.assertEqual(shot.call_count,2)
            self.assertTrue((Path(tmp)/"01_rejected_duplicate_1.png").is_file())
            self.assertTrue((Path(tmp)/"01_rejected_duplicate_2.png").is_file())

    def test_cross_asset_stale_frame_handoff_is_required(self):
        # A fresh GLES FRAME_OK can precede the compositor presenting the
        # new asset. Source wiring must carry the last accepted frame even
        # when the asset loop changes from chest to sword.
        import inspect
        from android_visual_qa import capture
        source=inspect.getsource(capture)
        self.assertLess(source.index("previous_presented_frame=None"),
                        source.index("for asset in ROLES[role]:"))
        self.assertIn("previous_frame=previous_presented_frame",source)
        self.assertIn("previous_presented_frame=pic",source)
        self.assertNotIn("previous_frame=shots[-1] if shots else None",source)

    def test_cross_asset_duplicate_is_rejected_and_archived(self):
        from PIL import Image,ImageDraw
        from tempfile import TemporaryDirectory
        chest=Image.new("RGB",(640,360),(17,21,29))
        ImageDraw.Draw(chest).rectangle((250,120,390,270),fill=(105,70,39))
        sword=Image.new("RGB",(640,360),(17,21,29))
        ImageDraw.Draw(sword).rectangle((315,50,325,290),fill=(115,117,120))
        visible={"foreground_fraction":.03,"channel_stddev":18,
                 "renderer_background_confirmed":True}
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"ceremonial_sword"/"00_yaw0_pitch15.png"
            path.parent.mkdir()
            frames=iter((chest,sword))
            def take(dest):
                pic=next(frames)
                pic.save(dest)
                return pic
            with patch("android_visual_qa.screenshot",side_effect=take), \
                 patch("android_visual_qa.metrics",return_value=visible.copy()), \
                 patch("android_visual_qa.time.sleep"):
                pic,measured,attempt=capture_visible_frame(
                    path,attempts=2,interval=0,previous_frame=chest)
            self.assertEqual(attempt,2)
            self.assertEqual(measured["rejected_duplicate_count"],1)
            self.assertTrue((path.parent/"00_yaw0_pitch15_rejected_duplicate_1.png").is_file())
            self.assertNotEqual(path.read_bytes(),
                                (path.parent/"00_yaw0_pitch15_rejected_duplicate_1.png").read_bytes())

    def test_delayed_replay_retried_before_acceptance_and_archived(self):
        from PIL import Image, ImageDraw
        from tempfile import TemporaryDirectory
        from android_visual_qa import presented_pixel_sha256
        def frame(x):
            im=Image.new("RGB",(640,360),(17,21,29))
            ImageDraw.Draw(im).rectangle((x,110,x+35,280),fill=(110,100,85))
            return im
        yaw0, yaw50, yaw75 = frame(150),frame(250),frame(350)
        seen={presented_pixel_sha256(yaw0):"sword yaw=0 pitch=15",
              presented_pixel_sha256(yaw50):"sword yaw=50 pitch=42"}
        visible={"foreground_fraction":.03,"channel_stddev":18,
                 "renderer_background_confirmed":True}
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"03_yaw75_pitch15.png"
            images=iter((yaw0,yaw75))
            def take(dest):
                im=next(images)
                im.save(dest)
                return im
            with patch("android_visual_qa.screenshot",side_effect=take) as shot, \
                 patch("android_visual_qa.metrics",return_value=visible.copy()), \
                 patch("android_visual_qa.time.sleep") as delay:
                pic,measured,attempt=capture_visible_frame(
                    path,attempts=3,interval=.1,previous_frame=yaw50,
                    seen_pixel_shas=seen)
            self.assertEqual(attempt,2)
            self.assertEqual(shot.call_count,2)
            self.assertEqual(measured["rejected_replay_count"],1)
            self.assertGreater(measured["previous_view_change_fraction"],.0006)
            self.assertEqual(presented_pixel_sha256(pic),
                             presented_pixel_sha256(yaw75))
            rejected=path.parent/"03_yaw75_pitch15_rejected_replay_1.png"
            self.assertTrue(rejected.is_file())
            self.assertNotEqual(path.read_bytes(),rejected.read_bytes())
            delay.assert_called_once_with(.1)

    def test_live_replay_guard_is_carried_across_all_assets(self):
        import inspect
        from android_visual_qa import capture
        source=inspect.getsource(capture)
        self.assertLess(source.index("accepted_pixel_shas={}"),
                        source.index("for asset in ROLES[role]:"))
        self.assertIn("seen_pixel_shas=accepted_pixel_shas",source)
        self.assertIn("accepted_pixel_shas[presented_pixel_sha256(pic)]",source)

    def test_zero_attempts_rejected(self):
        with self.assertRaises(ValueError):
            capture_visible_frame("actual.png",attempts=0)

if __name__=="__main__":
    unittest.main()
