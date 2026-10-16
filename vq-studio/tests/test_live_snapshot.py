"""Snapshot stages are identifiable, bounded and fail closed on invalid QA."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from live_snapshot import stage,digest

class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.obj=self.root/"test.obj"
        self.obj.write_text(
            "v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
            "f 1 3 2\nf 1 2 4\nf 1 4 3\nf 2 3 4\n")
    def tearDown(self):self.temp.cleanup()
    def start(self,sequence,**kw):
        return stage(self.obj,self.root/f"rev{sequence}",
              "a"*16,"123456789",sequence,"b"*40,**kw)
    def test_first_revision_authentic_and_not_artistic_approved(self):
        r=self.start(1)
        self.assertEqual(r["quality_stage"],"geometry_integrity")
        self.assertEqual(r["source_commit"],"b"*40)
        self.assertFalse(r["artist_approved"])
        self.assertEqual(digest(self.root/"rev1/model.obj"),r["obj_sha256"])
    def test_second_revision_requires_real_matching_report(self):
        with self.assertRaises(ValueError):
            self.start(2)
        report=self.root/"qa.json"
        report.write_text(json.dumps({
            "engine":"VEYLQUORIN","source_sha256":digest(self.obj),
            "technical_geometry_smoke_passed":True,"production_approved":False,
            "gltf":{"structural_smoke_passed":True},
            "visual":{"views":[{"view_index":i} for i in range(14)]},
        }))
        result=self.start(2,report=report)
        self.assertEqual(result["quality_stage"],"technical_review")
    def test_mismatch_model_sha_cannot_be_staged(self):
        file=self.root/"wrong.json"
        file.write_text(json.dumps({
            "engine":"VEYLQUORIN","source_sha256":"a"*64,
            "technical_geometry_smoke_passed":True,"production_approved":False,
            "gltf":{"structural_smoke_passed":True},
            "visual":{"views":[{}]*14}
        }))
        with self.assertRaises(ValueError):
            self.start(2,report=file)
    def test_invalid_request_prevents_staging(self):
        with self.assertRaises(ValueError):
            stage(self.obj,self.root/"out","../../bad","123456789",1,"b"*40)
    def test_geometry_rejects_degenerate_triangle(self):
        self.obj.write_text("v 0 0 0\nv 0 0 0\nv 0 1 0\nf 1 2 3\n")
        with self.assertRaises(ValueError):
            self.start(1)
if __name__=="__main__":unittest.main()
