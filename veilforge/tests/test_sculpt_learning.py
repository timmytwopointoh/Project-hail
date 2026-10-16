"""Real unit tests for VEILFORGE's review-conditioned sculpt curriculum."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sculpt_learning import (CURRICULUM,LESSONS,DIALS,candidates,load_records,
                             mesh_delta,write_map)

class SculptLearningTests(unittest.TestCase):
    def test_lessons_require_provenance(self):
        c,m=load_records()
        self.assertEqual(len(c["stages"]),9)
        self.assertEqual(len(c["dials"]),8)
        self.assertGreaterEqual(len(m["records"]),8)
        self.assertFalse(m["safety"]["auto_promote"])
        self.assertEqual(set(DIALS),{row["id"] for row in c["dials"]})

    def test_candidate_dials_are_bounded_and_review_only(self):
        for focus in ("face","surface","feet","full"):
            out=candidates(focus)
            self.assertFalse(out["accepted_for_game"])
            self.assertFalse(out["silhouette_likeness_measured"])
            self.assertEqual(len(out["candidates"]),4)
            baseline=out["candidates"][0]["dial_values"]
            selected=out["candidates"][2]["dial_values"]
            self.assertEqual(baseline,[0.0]*8)
            self.assertTrue(all(0.0<=x<=1.0 for x in selected))
            self.assertTrue(any(x>0 for x in selected))
            self.assertTrue(all(not row["auto_promote"] for row in out["candidates"]))
            if focus=="face":
                self.assertEqual(selected[5:],[0.0,0.0,0.0])
            if focus=="surface":
                self.assertEqual(selected[:5],[0.0]*5)
                self.assertEqual(selected[7],0.0)
            if focus=="feet":
                self.assertEqual(selected[:7],[0.0]*7)

    def test_reject_duplicate_and_unsubstantiated_feedback(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/"records.json"
            data=json.loads(LESSONS.read_text())
            data["records"].append(dict(data["records"][0]))
            target.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                load_records(lessons=target)
            data["records"].pop()
            data["records"][0]["evidence"]["source_run"]=""
            target.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                load_records(lessons=target)

    def test_emit_full_skill_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            result=write_map(out)
            self.assertEqual(result["stages"],9)
            self.assertTrue((out/"SCULPT_SKILL_MAP.md").is_file())
            self.assertIn("facial", (out/"SCULPT_SKILL_MAP.md").read_text().lower())
            self.assertFalse(result["visual_signoff"])

    def test_obj_delta_checks_color_and_vertex_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            a=root/"before.obj"; b=root/"after.obj"
            a.write_text(
                "v 0 2.54 .18 .69 .43 .32\n"
                "v 0 2.61 -.12 .15 .118 .108\n"
                "v .2 1.1 0 .205 .200 .195\n")
            b.write_text(
                "v 0 2.54 .175 .69 .43 .32\n"
                "v 0 2.61 -.12 .15 .118 .108\n"
                "v .2 1.1 0 .205 .200 .195\n")
            diff=mesh_delta(a,b)
            self.assertEqual(diff["vertices_compared"],3)
            self.assertEqual(diff["vertices_moved"],1)
            self.assertEqual(diff["protected_regions_modified"],0)
            self.assertAlmostEqual(diff["maximum_displacement"],.005,places=5)
            b.write_text(b.read_text().replace(".205 .200 .195",".5 .2 .4"))
            with self.assertRaises(ValueError):
                mesh_delta(a,b)
            b.write_text(a.read_text().splitlines()[0]+"\n")
            with self.assertRaises(ValueError):
                mesh_delta(a,b)

if __name__=="__main__":
    unittest.main()
