"""Proposals cannot escape role-owned Java files or bypass approval checks."""
import difflib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "scripts/promote_proposal.py"
SPEC = importlib.util.spec_from_file_location("promote_proposal", PATH)
import sys
sys.path.insert(0, str(PATH.parent))
promote = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(promote)

SHA = "a" * 40

class PromoteTests(unittest.TestCase):
    def make(self, folder, *, role="combat", name="WorldState.java",
             status="proposed_change_passed_java_tests"):
        root = Path(folder)
        relative = str(promote.JAVA / name)
        target = root / "proposed" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("class Test {}")
        (root / "worker_result.json").write_text(json.dumps({
            "role": role, "slot_id": "w001", "status": status, "source_commit": SHA,
            "edited_paths": [relative],
            "proposal_requires_human_review": True}))
        return relative

    def test_accepts_valid_model_tested_scope(self):
        with tempfile.TemporaryDirectory() as p:
            target = self.make(p)
            got = promote.load_proposal(p, "combat", SHA)
            self.assertEqual([target], list(got))
            self.assertEqual("class Test {}", got[target])

    def test_distinct_worker_slot_prevents_wrong_artifact_promotion(self):
        with tempfile.TemporaryDirectory() as folder:
            self.make(folder)
            self.assertTrue(promote.load_proposal(folder, "combat", SHA, "w001"))
            with self.assertRaises(ValueError):
                promote.load_proposal(folder, "combat", SHA, "w002")
            with self.assertRaises(ValueError):
                promote.load_proposal(folder, "combat", SHA, "../../unsafe")

    def test_rejects_cross_role_files(self):
        with tempfile.TemporaryDirectory() as p:
            self.make(p, name="ValeRenderer.java")
            with self.assertRaises(ValueError):
                promote.load_proposal(p, "combat", SHA)

    def test_rejects_wrong_sha_and_unverified_result(self):
        with tempfile.TemporaryDirectory() as p:
            self.make(p)
            with self.assertRaises(ValueError):
                promote.load_proposal(p, "combat", "b" * 40)
        with tempfile.TemporaryDirectory() as p:
            self.make(p, status="skipped_no_gemini_key")
            with self.assertRaises(ValueError):
                promote.load_proposal(p, "combat", SHA)

    def test_rejects_symlink_and_missing_artifacts(self):
        with tempfile.TemporaryDirectory() as p:
            name = self.make(p)
            path = Path(p) / "proposed" / name
            path.unlink()
            path.symlink_to(Path(p) / "worker_result.json")
            with self.assertRaises(ValueError):
                promote.load_proposal(p, "combat", SHA)

    def test_rejects_review_patch_that_disagrees_with_actual_source(self):
        with tempfile.TemporaryDirectory() as rootdir, tempfile.TemporaryDirectory() as artifact:
            relative = str(promote.JAVA / "WorldState.java")
            src = Path(rootdir) / relative
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_text("old\n")
            pending = {relative: "new\n"}
            patch = "".join(difflib.unified_diff(
                ["old\n"], ["new\n"],
                fromfile="a/" + relative, tofile="b/" + relative))
            (Path(artifact) / "changes.patch").write_text(patch)
            promote.verify_reviewed_patch(rootdir, artifact, pending)
            (Path(artifact) / "changes.patch").write_text("unrelated code")
            with self.assertRaises(ValueError):
                promote.verify_reviewed_patch(rootdir, artifact, pending)

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as p:
            self.make(p)
            report_path = Path(p) / "worker_result.json"
            report = json.loads(report_path.read_text())
            report["edited_paths"] = ["../../.github/workflows/steal.yml"]
            report_path.write_text(json.dumps(report))
            with self.assertRaises(ValueError):
                promote.load_proposal(p, "combat", SHA)

if __name__ == "__main__":
    unittest.main()
