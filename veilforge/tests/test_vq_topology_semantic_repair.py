"""GEO-02: attribute-safe cleanup and fail-closed evidence tests."""
from pathlib import Path
import hashlib
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import read_obj
from topology import repair_obj
from vq_multimaterial_export import export

class SemanticTopologyTests(unittest.TestCase):
    def test_material_overlays_survive_real_multimaterial_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=root/"source.obj"
            src.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\n"
                           "usemtl stone\nf 1 2 3\n"
                           "usemtl wood\nf 3 2 1\n")
            original=src.read_bytes()
            dst=root/"candidate.obj"
            report=repair_obj(src,dst,mode="assembly")
            self.assertEqual(src.read_bytes(),original)
            self.assertEqual(report["coincident_faces_removed"],0)
            self.assertEqual(report["semantic_overlays_preserved"],1)
            self.assertEqual(len(read_obj(dst)[3]),2)
            doc=export(dst,root/"result.gltf")
            self.assertEqual({m["name"] for m in doc["materials"]},{"stone","wood"})
            self.assertEqual(len(doc["meshes"][0]["primitives"]),2)
            self.assertFalse(doc["extras"]["production_approved"])
            self.assertEqual(report["candidate_sha256"],hashlib.sha256(dst.read_bytes()).hexdigest())

    def test_uv_normal_and_group_layers_not_flattened(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=root/"source.obj"
            src.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\n"
                           "vt 0 0\nvt 1 0\nvt 0 1\n"
                           "vt .1 .1\nvt .9 .1\nvt .1 .9\n"
                           "vn 0 0 1\nvn 0 0 -1\n"
                           "usemtl skin\ng face\n"
                           "f 1/1/1 2/2/1 3/3/1\n"
                           "f 3/3/1 2/2/1 1/1/1\n"
                           "f 1/4/2 2/5/2 3/6/2\n"
                           "g eyes\nf 1/1/1 2/2/1 3/3/1\n")
            dst=root/"candidate.obj"
            report=repair_obj(src,dst,mode="assembly")
            self.assertEqual(report["coincident_faces_removed"],1)
            self.assertEqual(report["semantic_overlays_preserved"],2)
            self.assertEqual(len(read_obj(dst)[3]),3)
            self.assertIn("g eyes",dst.read_text())

    def test_mixed_material_rim_cannot_be_capped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=root/"source.obj"
            src.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
                           "usemtl skin\nf 1 3 2\n"
                           "usemtl cloth\nf 1 2 4\nf 2 3 4\n")
            report=repair_obj(src,root/"candidate.obj",max_hole_diameter=2)
            self.assertEqual(report["small_hole_triangles_inserted"],0)
            self.assertTrue(any(x["reason"]=="mixed-material-rim"
                                for x in report["skipped_boundary_loops"]))

    def test_single_material_cap_keeps_material(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=root/"source.obj"
            src.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
                           "usemtl skin\nf 1 3 2\nf 1 2 4\nf 2 3 4\n")
            dst=root/"candidate.obj"
            report=repair_obj(src,dst,max_hole_diameter=2)
            self.assertEqual(report["small_hole_triangles_inserted"],1)
            self.assertIn("g VQ_REPAIR_CAP",dst.read_text())
            self.assertIn("usemtl skin",dst.read_text())

    def test_never_overwrite_candidate_or_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=root/"source.obj"
            src.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            dst=root/"candidate.obj"
            dst.write_text("keep")
            with self.assertRaisesRegex(ValueError,"overwrite"):
                repair_obj(src,dst,mode="assembly")
            self.assertEqual(dst.read_text(),"keep")
            dst.unlink()
            evidence=root/"candidate_topology_report.json"
            evidence.write_text("keep")
            with self.assertRaisesRegex(ValueError,"overwrite"):
                repair_obj(src,dst,mode="assembly")
            self.assertEqual(evidence.read_text(),"keep")
            self.assertFalse(dst.exists())

if __name__=="__main__":
    unittest.main()
