"""Adversarial GEO-02 material-aware regional topology regression tests."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import MeshError
from vq_topology_regions import inspect_regions

def fixture(root, name, faces, uv=""):
    src=root/name
    src.write_text(
        "v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\n"
        "v 0 0 1\nv 1 0 1\nv 1 1 1\n"
        +uv+faces,encoding="utf-8")
    return src

class RegionalTopologyAuditTests(unittest.TestCase):
    def test_welded_uv_seam_not_a_false_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=fixture(root,"seam.obj",
                "usemtl stone\nf 1/1 2/2 3/3\n"
                "usemtl wood\nf 1/4 3/5 4/6\n",
                "vt 0 0\nvt 1 0\nvt 1 1\n"
                "vt .1 .1\nvt .9 .9\nvt 0 1\n")
            before=src.read_bytes()
            a=inspect_regions(src)
            self.assertEqual(src.read_bytes(),before)
            self.assertEqual(a["source_sha256"],hashlib.sha256(before).hexdigest())
            self.assertEqual(a["region_count"],1)
            self.assertEqual(a["totals"]["boundary_edges"],4)
            self.assertEqual(a["totals"]["nonmanifold_edges"],0)
            self.assertEqual(a["totals"]["orientation_conflict_edges"],0)
            self.assertEqual(a["regions"][0]["materials"],{"stone":1,"wood":1})
            self.assertFalse(a["game_approved"])

    def test_semantic_overlay_is_not_disposable_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=fixture(Path(tmp),"layers.obj",
                "f 1 2 3\nf 3 2 1\nusemtl metal\nf 1 2 3\n")
            a=inspect_regions(src)
            self.assertEqual(a["totals"]["exact_duplicate_triangles"],1)
            self.assertEqual(a["totals"]["semantic_overlay_triangles"],1)
            self.assertEqual(a["totals"]["nonmanifold_edges"],3)
            self.assertEqual(a["totals"]["triangles"],3)

    def test_shared_edge_same_winding_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=fixture(Path(tmp),"bad_winding.obj","f 1 2 3\nf 1 4 3\n")
            a=inspect_regions(src)
            self.assertEqual(a["totals"]["orientation_conflict_edges"],1)
            self.assertEqual(a["totals"]["boundary_edges"],4)
            self.assertFalse(a["closed_manifold_candidate"])

    def test_disconnected_components_and_degenerate_face(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=fixture(Path(tmp),"islands.obj",
                "f 1 2 3\nf 5 6 7\nf 1 1 2\n")
            a=inspect_regions(src)
            self.assertEqual(a["region_count"],2)
            self.assertEqual(a["totals"]["degenerate_triangles"],1)
            self.assertEqual(a["totals"]["triangles"],3)
            self.assertFalse(a["artistic_signoff"])

    def test_deterministic_report_and_malformed_input_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=fixture(root,"good.obj","f 1 2 3\nf 1 3 4\n")
            a=inspect_regions(src)
            b=inspect_regions(src)
            self.assertEqual(json.dumps(a,sort_keys=True),json.dumps(b,sort_keys=True))
            self.assertEqual(a["region_count"],1)
            self.assertEqual(a["totals"]["boundary_edges"],4)
            bad=fixture(root,"bad.obj","f 1 2 999\n")
            with self.assertRaises(MeshError):
                inspect_regions(bad)

if __name__=="__main__":
    unittest.main()
