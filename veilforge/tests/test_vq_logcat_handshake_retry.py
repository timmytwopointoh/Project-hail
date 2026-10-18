"""H20: startup logcat subscription races must not forge visual QA."""
from collections import deque
from pathlib import Path
from threading import Condition
from types import SimpleNamespace
from unittest.mock import patch
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vq_logcat_stream import LogcatStream


class FakePipe:
    def __init__(self):
        self.lines = deque()
        self.cv = Condition()

    def put(self, line):
        with self.cv:
            self.lines.append(line)
            self.cv.notify_all()

    def readline(self):
        with self.cv:
            if not self.cv.wait_for(lambda: bool(self.lines), timeout=2):
                raise TimeoutError("test fake logcat stalled")
            return self.lines.popleft()

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


class StartupSubscriptionRaceTests(unittest.TestCase):
    def test_first_device_probe_lost_second_real_echo_unlocks(self):
        proc = FakeProc()
        sent = []

        def device_log(args, **kwargs):
            sent.append(args)
            if len(sent) == 2:
                proc.stdout.put(
                    ("I/VEILFORGE_PROBE: " + args[-1] + "\n").encode())
            return SimpleNamespace(returncode=0)

        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "device_logcat.txt"
            with patch("vq_logcat_stream.subprocess.Popen", return_value=proc), \
                 patch("vq_logcat_stream.subprocess.run", side_effect=device_log), \
                 patch("vq_logcat_stream.uuid.uuid4",
                       return_value=SimpleNamespace(hex="H20")):
                with LogcatStream(log, startup_timeout=1,
                                  startup_probe_interval=.02) as monitor:
                    monitor.assert_healthy()
            self.assertEqual(len(sent), 2)
            self.assertEqual(sent[0][-1], sent[1][-1])
            self.assertIn("VQ_LOGCAT_ATTACHED_H20", log.read_text())

    def test_all_lost_probes_timeout_without_approving_any_frame(self):
        proc = FakeProc()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("vq_logcat_stream.subprocess.Popen", return_value=proc), \
                 patch("vq_logcat_stream.subprocess.run",
                       return_value=SimpleNamespace(returncode=0)) as run:
                with self.assertRaisesRegex(TimeoutError,
                                            "did not echo nonce"):
                    with LogcatStream(Path(tmp) / "lost.log",
                                      startup_timeout=.09,
                                      startup_probe_interval=.01):
                        self.fail("Never enter capture without device echo")
            self.assertGreaterEqual(run.call_count, 2)
            self.assertFalse(proc.alive)

    def test_fatal_renderer_event_is_not_retried_as_startup_race(self):
        proc = FakeProc()
        def device_log(*args, **kwargs):
            proc.stdout.put(b"I/VEILFORGE_PROBE: GL_ERROR 1282\n")
            return SimpleNamespace(returncode=0)
        with tempfile.TemporaryDirectory() as tmp:
            with patch("vq_logcat_stream.subprocess.Popen", return_value=proc), \
                 patch("vq_logcat_stream.subprocess.run",
                       side_effect=device_log) as run:
                with self.assertRaisesRegex(RuntimeError, "GL_ERROR 1282"):
                    with LogcatStream(Path(tmp) / "fatal.log",
                                      startup_timeout=.5,
                                      startup_probe_interval=.01):
                        self.fail("Fatal GLES evidence cannot be accepted")
            self.assertEqual(run.call_count, 1)
            self.assertFalse(proc.alive)


if __name__ == "__main__":
    unittest.main()
