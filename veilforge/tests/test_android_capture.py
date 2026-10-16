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
        visible={"foreground_fraction":.14,"channel_stddev":19.5}
        with patch("android_visual_qa.screenshot", side_effect=["blank","visible"]) as shot, \
             patch("android_visual_qa.metrics", side_effect=[blank,visible]), \
             patch("android_visual_qa.adb", return_value="FRAME_OK"), \
             patch("android_visual_qa.time.sleep") as delay:
            pic,measured,attempt=capture_visible_frame("actual.png",attempts=3,interval=.1)
        self.assertEqual((pic,measured,attempt),("visible",visible,2))
        self.assertEqual(shot.call_count,2)
        delay.assert_called_once_with(.1)

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

    def test_zero_attempts_rejected(self):
        with self.assertRaises(ValueError):
            capture_visible_frame("actual.png",attempts=0)

if __name__=="__main__":
    unittest.main()
