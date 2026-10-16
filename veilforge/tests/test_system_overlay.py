"""Genuine Android frame QA must never confuse system ANR dialogs with assets."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import android_visual_qa as qa

class SyntheticFrame:
    width=160
    height=90
    def __init__(self,overlay):
        self.overlay=overlay
    def convert(self,mode):return self
    def resize(self,dims):return self
    def getpixel(self,xy):
        x,y=xy
        if self.overlay and 32<=x<128 and 36<=y<63:
            return (241,240,247)
        return (17,21,29)

class SystemOverlayTest(unittest.TestCase):
    def test_detects_large_bright_system_dialog_without_ocr(self):
        self.assertGreater(qa.dialog_overlay_fraction(SyntheticFrame(True)),.9)
        self.assertLess(qa.dialog_overlay_fraction(SyntheticFrame(False)),.01)
    def test_overlay_must_never_count_as_successful_3d_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"frame.png"
            def shot(p):
                p.write_bytes(b"unapproved modal bytes")
                return SyntheticFrame(True)
            with patch.object(qa,"screenshot",side_effect=shot), \
                 patch.object(qa,"metrics",return_value={
                   "modal_overlay_fraction":.92,"foreground_fraction":.32,
                   "channel_stddev":80}),\
                 patch.object(qa,"adb",return_value=""),\
                 patch.object(qa.time,"sleep",return_value=None):
                with self.assertRaisesRegex(RuntimeError,"system UI|obscured"):
                    qa.capture_visible_frame(path,attempts=2,interval=0)
            self.assertEqual(len(list(Path(tmp).glob("*blocked_modal*"))),2)
    def test_one_recovered_modal_then_real_frame_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"frame.png"
            calls=[0]
            def shot(p):
                calls[0]+=1
                p.write_bytes(b"new frame "+str(calls[0]).encode())
                return SyntheticFrame(calls[0]==1)
            def measure(image):
                return {"modal_overlay_fraction":.92 if image.overlay else 0,
                        "foreground_fraction":.30,"channel_stddev":65}
            with patch.object(qa,"screenshot",side_effect=shot), \
                 patch.object(qa,"metrics",side_effect=measure),\
                 patch.object(qa,"adb",return_value=""),\
                 patch.object(qa.time,"sleep",return_value=None):
                im,score,tries=qa.capture_visible_frame(path,attempts=2,interval=0)
            self.assertEqual(tries,2)
            self.assertFalse(im.overlay)
            self.assertEqual(score["modal_overlay_fraction"],0)
            self.assertTrue((Path(tmp)/"frame_blocked_modal_1.png").is_file())
if __name__=="__main__":unittest.main()
