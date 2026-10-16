"""M34-08: a bounded log cursor must not lose renderer failures or views."""
from pathlib import Path
from collections import deque
from threading import Condition
from types import SimpleNamespace
from unittest.mock import patch
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vq_logcat_stream import LogcatEvents, LogcatStream
from android_visual_qa import capture_visible_frame, wait_frame


class EventCursorTests(unittest.TestCase):
    def test_only_new_frame_matches_camera(self):
        events = LogcatEvents()
        events.record("FRAME_OK asset=scene yaw=0 pitch=15")
        cursor = events.mark()
        events.record("FRAME_OK asset=scene yaw=25 pitch=25")
        result = wait_frame("scene", 25, 25, monitor=events, since=cursor, timeout=.2)
        self.assertIn("yaw=25", result)
        with self.assertRaisesRegex(RuntimeError, "Timed out"):
            wait_frame("scene", 0, 15, monitor=events, since=cursor, timeout=.01)

    def test_sticky_gpu_error_survives_window_eviction(self):
        events = LogcatEvents(capacity=2)
        events.record("GL_ERROR 1282")
        for index in range(30):
            events.record(f"FRAME_OK asset=scene yaw={index} pitch=15")
        with self.assertRaisesRegex(RuntimeError, "GL_ERROR 1282"):
            events.mark()

    def test_cursor_overrun_fails_closed(self):
        events = LogcatEvents(capacity=2)
        events.record("FRAME_OK asset=scene yaw=0 pitch=15")
        for index in range(3):
            events.record(f"other event {index}")
        with self.assertRaisesRegex(RuntimeError, "cursor expired"):
            events.wait_for(lambda line: "FRAME_OK" in line, since=0, timeout=.01)

    def test_wrong_gltf_pack_is_rejected(self):
        events = LogcatEvents(reject_wrong_pack=True)
        events.record("GLTF_LOADED actual_scene=true models=11 nodes=12")
        with self.assertRaisesRegex(RuntimeError, "unexpected mesh pack"):
            events.assert_healthy()

    def test_end_of_stream_is_not_silent_timeout(self):
        events = LogcatEvents()
        events.finish()
        with self.assertRaisesRegex(RuntimeError, "ended unexpectedly"):
            events.wait_for(lambda line: True, since=0, timeout=.1)

    def test_frame_retries_use_monitor_not_full_buffer_polling(self):
        blank = {"foreground_fraction": 0, "channel_stddev": 0}
        valid = {"foreground_fraction": .15, "channel_stddev": 18,
                 "renderer_background_confirmed": True, "modal_overlay_fraction": 0.0}
        monitor = SimpleNamespace(assert_healthy=lambda: None)
        with patch("android_visual_qa.screenshot", side_effect=["blank", "real"]), \
             patch("android_visual_qa.metrics", side_effect=[blank, valid]), \
             patch("android_visual_qa.adb") as adb, \
             patch("android_visual_qa.time.sleep"):
            pic, score, attempts = capture_visible_frame(
                "frame.png", attempts=2, interval=0, monitor=monitor)
        self.assertEqual((pic, score, attempts), ("real", valid, 2))
        adb.assert_not_called()

    def test_stream_handshake_and_durable_file_without_android(self):
        class FakePipe:
            def __init__(self):
                self.events = deque()
                self.cv = Condition()
            def put(self, line):
                with self.cv:
                    self.events.append(line)
                    self.cv.notify()
            def readline(self):
                with self.cv:
                    if not self.cv.wait_for(lambda: bool(self.events), timeout=2):
                        raise TimeoutError("fake log stream timed out")
                    return self.events.popleft()
            def close(self):
                pass

        class FakeProc:
            def __init__(self):
                self.stdout = FakePipe()
                self.alive = True
            def poll(self):
                return None if self.alive else 0
            def terminate(self):
                self.alive = False
                self.stdout.put(b"")
            def wait(self, timeout=None):
                return 0
            def kill(self):
                self.terminate()

        proc = FakeProc()
        def handshake(*args, **kwargs):
            proc.stdout.put(b"I/VEILFORGE_PROBE: VQ_LOGCAT_ATTACHED_FIXED\n")
            return SimpleNamespace(returncode=0)
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "device_logcat.txt"
            with patch("vq_logcat_stream.subprocess.Popen", return_value=proc) as popen, \
                 patch("vq_logcat_stream.subprocess.run", side_effect=handshake), \
                 patch("vq_logcat_stream.uuid.uuid4",
                       return_value=SimpleNamespace(hex="FIXED")):
                with LogcatStream(output) as stream:
                    cursor = stream.mark()
                    proc.stdout.put(
                        b"I/VEILFORGE_PROBE: FRAME_OK asset=scene yaw=0 pitch=15\n")
                    line = stream.wait_for(
                        lambda s: "FRAME_OK asset=scene yaw=0 pitch=15" in s,
                        since=cursor, timeout=1)
                    self.assertIn("FRAME_OK", line)
                self.assertEqual(popen.call_count, 1)
            self.assertIn("FRAME_OK", output.read_text())


if __name__ == "__main__":
    unittest.main()
