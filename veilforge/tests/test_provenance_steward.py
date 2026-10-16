"""Evidence and budget tests for the VEILFORGE named-steward continuity system."""
import copy
from datetime import datetime,timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"veilforge"))
import provenance
import steward


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.root=Path(self.t.name)/"repo"
        self.root.mkdir()
        (self.root/"veilforge").mkdir()
        (self.root/"veilforge/steward_state.json").write_text(json.dumps({
            "claimant":"Timothy Harris", "github_account":"timmytwopointoh",
            "repository":"timmytwopointoh/Project-hail"
        }))
        (self.root/"hello.txt").write_text("VEILFORGE original work\n")
        subprocess.run(["git","init","-q",str(self.root)],check=True)
        subprocess.run(["git","-C",str(self.root),"add","."],check=True)
        subprocess.run(["git","-C",str(self.root),"-c","user.email=ci@example.invalid",
                        "-c","user.name=Test","commit","-qm","Fixture checkpoint"],check=True)

    def tearDown(self):
        self.t.cleanup()

    def test_timestamp_owner_and_commit_are_unambiguous(self):
        when=datetime(2026,10,16,13,20,tzinfo=timezone.utc)
        doc=provenance.make_snapshot(self.root,when=when,actor="ci",run_id="123")
        self.assertEqual(doc["claimed_owner"],"Timothy Harris")
        self.assertEqual(doc["github_account"],"timmytwopointoh")
        self.assertEqual(doc["observed_at_utc"],"2026-10-16T13:20:00Z")
        self.assertEqual(doc["observed_at_america_new_york"][:10],"2026-10-16")
        self.assertEqual(doc["file_count"],2)
        self.assertTrue(doc["not_proof_of_original_creation_date"])
        self.assertFalse(doc["human_signature_present"])

    def test_verify_detects_modified_source_or_manifest(self):
        output=Path(self.t.name)/"proof.json"
        provenance.write_snapshot(self.root,output)
        self.assertTrue(provenance.verify_snapshot(self.root,output))
        (self.root/"hello.txt").write_text("tampered\n")
        with self.assertRaisesRegex(ValueError,"fingerprint"):
            provenance.verify_snapshot(self.root,output)

    def test_uncommitted_tracked_files_are_rejected(self):
        (self.root/"hello.txt").write_text("uncommitted edit\n")
        with self.assertRaisesRegex(ValueError,"differ"):
            provenance.make_snapshot(self.root)

    def test_unverified_owner_identity_cannot_be_assumed(self):
        path=self.root/"veilforge/steward_state.json"
        data=json.loads(path.read_text())
        data["claimant"]="Other person"
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,"differ"):
            provenance.make_snapshot(self.root)


class StewardTests(unittest.TestCase):
    def test_plan_only_preserves_review_gate(self):
        with tempfile.TemporaryDirectory() as td:
            report=steward.produce(
                ROOT/"veilforge/steward_state.json",
                ROOT/"veilforge/ENGINE_MASTER_PLAN.json",
                ROOT/"veilforge/queue_backlog.json",
                Path(td)/"review")
            self.assertEqual(report["claimant"],"Timothy Harris")
            self.assertEqual(report["executed_workers"],0)
            self.assertEqual(report["executed_emulators"],0)
            self.assertEqual(report["git_mutations"],0)
            self.assertEqual(report["automatic_approvals"],0)
            self.assertLessEqual(len(report["next_queue_candidates"]),10)
            self.assertTrue((Path(td)/"review/handoff.json").is_file())

    def test_no_expensive_inference_can_be_enabled_by_accident(self):
        with tempfile.TemporaryDirectory() as td:
            state=json.loads((ROOT/"veilforge/steward_state.json").read_text())
            state["max_expensive_inference_runs_per_day"]=1
            path=Path(td)/"altered.json"
            path.write_text(json.dumps(state))
            with self.assertRaisesRegex(ValueError,"budget"):
                steward.produce(path,ROOT/"veilforge/ENGINE_MASTER_PLAN.json",
                                ROOT/"veilforge/queue_backlog.json",Path(td)/"out")


if __name__=="__main__":
    unittest.main()
