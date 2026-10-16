from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import inspect_obj
from topology import repair_obj

class TopologyTest(unittest.TestCase):
    def test_small_closed_hole_can_be_capped_without_modifying_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=root/"missing_face.obj"
            src.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
                "f 1 3 2\nf 1 2 4\nf 2 3 4\n")
            original=src.read_bytes()
            before=inspect_obj(src)
            self.assertEqual(before["boundary_edges"],3)
            result=repair_obj(src,root/"repaired.obj",max_hole_diameter=2)
            self.assertEqual(src.read_bytes(),original)
            self.assertEqual(result["small_hole_triangles_inserted"],1)
            self.assertEqual(result["after"]["boundary_edges"],0)
            self.assertEqual(result["after"]["nonmanifold_edges"],0)
            self.assertEqual(result["after"]["triangles"],4)
            self.assertFalse(result["ready_for_game"])
    def test_large_opening_must_remain_for_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=root/"open.obj"
            src.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            result=repair_obj(src,root/"out.obj")
            self.assertEqual(result["after"]["boundary_edges"],3)
            self.assertEqual(result["small_hole_triangles_inserted"],0)
            self.assertEqual(len(result["skipped_boundary_loops"]),1)
    def test_duplicate_armor_cape_face_removed_only_in_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=root/"cloth.obj"
            src.write_text("v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\n"
                "f 1 2 3\nf 1 3 4\nf 3 2 1\nf 4 3 1\n")
            before=inspect_obj(src)
            self.assertEqual(before["nonmanifold_edges"],1)
            after=repair_obj(src,root/"clean.obj",mode="assembly")
            self.assertEqual(after["coincident_faces_removed"],2)
            self.assertEqual(after["after"]["triangles"],2)
            self.assertEqual(after["after"]["nonmanifold_edges"],0)
            self.assertEqual(before["triangles"],4)
            self.assertEqual(inspect_obj(src)["triangles"],4)
    def test_partial_nonplanar_boundary_is_not_faked_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=root/"nonplanar.obj"
            src.write_text("v 0 0 0\nv .5 0 0\nv .5 .5 .15\nv 0 .5 0\n"
                "f 1 2 3\nf 1 3 4\n")
            result=repair_obj(src,root/"clean.obj",max_hole_diameter=2)
            self.assertEqual(result["small_hole_triangles_inserted"],0)
            self.assertEqual(result["after"]["boundary_edges"],4)
    def test_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            src=Path(tmp)/"a.obj"
            src.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            with self.assertRaises(ValueError):
                repair_obj(src,src)

if __name__=="__main__":
    unittest.main()
