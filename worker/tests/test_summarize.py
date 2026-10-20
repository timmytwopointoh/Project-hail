import tempfile
import unittest
from pathlib import Path
from worker.summarize import summarize

class ResultTests(unittest.TestCase):
    def test_success(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"install.txt").write_text("Success\n")
            (root/"launch.txt").write_text("Events injected: 1\n")
            (root/"game.png").write_bytes(b"png")
            (root/"package.txt").write_text("com.example.game")
            self.assertEqual(summarize(root,"test-a","android.install_test","success","skipped","success")["status"],"passed")
    def test_fail_install(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(summarize(d,"test-b","android.install_test","success","skipped","failure")["failure_stage"],"android_install")
    def test_fail_build(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(summarize(d,"test-c","android.build_test","skipped","failure","skipped")["failure_stage"],"apk_build")
