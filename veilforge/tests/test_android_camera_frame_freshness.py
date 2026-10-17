"""Check Android camera screenshot freshness with synthetic byte sequences."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import android_visual_qa as qa

class CameraFreshnessTests(unittest.TestCase):
    def run_capture(self, folder, frames, previous=None, attempts=3):
        path=Path(folder)/"01_yaw25_pitch25.png"
        iterator=iter(frames)
        def take(dest):
            dest.write_bytes(next(iterator))
            return object()
        stats={"foreground_fraction":.12,"channel_stddev":9.0,
               "modal_overlay_fraction":0.0,"renderer_background_confirmed":True}
        with patch.object(qa,"screenshot",side_effect=take), \
             patch.object(qa,"metrics",return_value=stats), \
             patch.object(qa.time,"sleep"):
            result=qa.capture_visible_frame(path,attempts=attempts,
                previous_frame_sha=previous,interval=0)
        return path,result

    def test_retries_previous_presented_buffer(self):
        old=b"angle-zero";fresh=b"angle-twenty-five"
        with tempfile.TemporaryDirectory() as folder:
            path,(_,_,count)=self.run_capture(folder,[old,fresh],
                hashlib.sha256(old).hexdigest())
            self.assertEqual(count,2)
            self.assertEqual(path.read_bytes(),fresh)
            self.assertEqual((path.parent/
                "01_yaw25_pitch25_stale_presented_1.png").read_bytes(),old)

    def test_permanently_stale_fails_closed(self):
        old=b"angle-zero"
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError,"after 3"):
                self.run_capture(folder,[old]*3,
                    hashlib.sha256(old).hexdigest())
            self.assertEqual(len(list(Path(folder).glob("*stale_presented*"))),3)

    def test_first_view_has_no_previous_frame(self):
        with tempfile.TemporaryDirectory() as folder:
            path,(_,_,count)=self.run_capture(folder,[b"first"])
            self.assertEqual(count,1)
            self.assertEqual(path.read_bytes(),b"first")

if __name__=="__main__":
    unittest.main()
