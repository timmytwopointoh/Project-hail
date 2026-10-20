import unittest
from worker.command_protocol import validate, PROTOCOL

class ContractTests(unittest.TestCase):
    def test_valid_probe(self):
        x=validate({"protocol":PROTOCOL,"job_id":"test-001","command":"protocol.validate"})
        self.assertEqual(x["command"],"protocol.validate")
    def test_valid_pinned_build(self):
        x=validate({"protocol":PROTOCOL,"job_id":"test-002","command":"android.build_test","project":"echoform","source_sha":"1"*40})
        self.assertEqual(x["repository"],"timmytwopointoh/New-game-")
    def test_reject_unknown_project(self):
        with self.assertRaises(ValueError):
            validate({"protocol":PROTOCOL,"job_id":"test-003","command":"android.build_test","project":"some-other-repo","source_sha":"1"*40})
    def test_reject_arbitrary_shell(self):
        with self.assertRaises(ValueError):
            validate({"protocol":PROTOCOL,"job_id":"test-004","command":"sh -c curl"})
    def test_reject_path_traversal(self):
        with self.assertRaises(ValueError):
            validate({"protocol":PROTOCOL,"job_id":"test-005","command":"android.install_test","apk_path":"worker/staging/../../etc/passwd.apk"})
    def test_valid_staged_apk(self):
        x=validate({"protocol":PROTOCOL,"job_id":"test-006","command":"android.install_test","apk_path":"worker/staging/game.apk","expected_package":"com.example.game"})
        self.assertEqual(x["expected_package"],"com.example.game")
    def test_reject_version_mismatch(self):
        with self.assertRaises(ValueError):
            validate({"protocol":"vq.worker.v2","job_id":"test-007","command":"protocol.validate"})
    def test_reject_unpinned_ref(self):
        with self.assertRaises(ValueError):
            validate({"protocol":PROTOCOL,"job_id":"test-008","command":"android.build_test","project":"echoform","source_sha":"main"})

if __name__=="__main__":
    unittest.main()
