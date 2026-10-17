"""M30/M31 positive-area UV audit regressions (not pixel-sampled)."""
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vq_mesh_baker import bake,uv_rows
from vq_uv_overlap_audit import validate_unique_uv_atlas,_uv_triangles_overlap


class UVOverlapAuditTests(unittest.TestCase):
    def test_shared_edge_is_legal(self):
        a=((.1,.1),(.9,.1),(.1,.9))
        b=((.9,.9),(.1,.9),(.9,.1))
        self.assertFalse(_uv_triangles_overlap(a,b))
        self.assertEqual(validate_unique_uv_atlas([
            (None,a,None,None),(None,b,None,None)])["triangles_checked"],2)

    def test_positive_area_wedge_below_texel_is_rejected(self):
        a=((.1,.1),(.9,.1),(.1,.9))
        b=((.8989,.101),(.99,.101),(.8989,.19))
        self.assertTrue(_uv_triangles_overlap(a,b))
        with self.assertRaisesRegex(ValueError,"Overlapping UV islands"):
            validate_unique_uv_atlas([(None,a,None,None),(None,b,None,None)])

    def test_identical_geometry_uv_stacking_fails_before_bake_outputs(self):
        # Old raster tolerated identical 3D positions at the same UV texel.
        obj=("v 0 0 0\nv 1 0 0\nv 0 1 0\n"
             "vt .2 .2\nvt .8 .2\nvt .2 .8\n"
             "f 1/1 2/2 3/3\nf 1/1 2/2 3/3\n")
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);low=root/"low.obj";high=root/"high.obj"
            low.write_text(obj);high.write_text(obj)
            with self.assertRaisesRegex(ValueError,"Overlapping UV islands"):
                bake(low,high,root/"out",size=64)
            self.assertFalse((root/"out").exists())
            self.assertEqual(low.read_text(),obj)

    def test_shared_edge_obj_passes_audit(self):
        obj=("v 0 0 0\nv 1 0 0\nv 0 1 0\nv 1 1 0\n"
             "vt 0 0\nvt 1 0\nvt 0 1\nvt 1 1\n"
             "f 1/1 2/2 3/3\nf 2/2 4/4 3/3\n")
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"mesh.obj";path.write_text(obj)
            rows,_=uv_rows(path)
            self.assertEqual(validate_unique_uv_atlas(rows)["triangles_checked"],2)


if __name__=="__main__":
    unittest.main()
