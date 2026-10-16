"""UV-01 analytic Jacobian, source safety, and real VQ mesh regression."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vq_uv_distortion import audit_obj
from vq_sculpt_detail_patch import build
from vq_uv_atlas import unwrap

SQUARE = """v 0 0 0
v 1 0 0
v 1 1 0
v 0 1 0
vt 0 0
vt 1 0
vt 1 1
vt 0 1
f 1/1 2/2 3/3
f 1/1 3/3 4/4
"""

class UVDistortionTests(unittest.TestCase):
    def _source(self, root, content=SQUARE):
        path=Path(root)/"source.obj"
        path.write_text(content, encoding="utf-8")
        return path

    def test_isotropic_and_source_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=self._source(tmp)
            original=path.read_bytes()
            r=audit_obj(path, strict=True)
            self.assertEqual(path.read_bytes(),original)
            self.assertEqual(r["source_sha256"],hashlib.sha256(original).hexdigest())
            self.assertEqual(r["max_anisotropy"],1)
            self.assertEqual(r["max_density_deviation_factor"],1)
            self.assertEqual(r["uv_seams"],{"seam_edges":0,"continuous_edges":1})
            self.assertTrue(r["strict_threshold_pass"])
            self.assertFalse(r["black_seam_pixels_checked"])

    def test_directional_stretch_and_strict_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=self._source(tmp,SQUARE.replace("vt 1 0","vt .1 0").replace("vt 1 1","vt .1 1"))
            r=audit_obj(path)
            self.assertAlmostEqual(r["max_anisotropy"],10,places=4)
            self.assertEqual(r["anisotropy_outlier_triangles"],2)
            with self.assertRaisesRegex(ValueError,"thresholds exceeded"):
                audit_obj(path,strict=True)

    def test_collapsed_missing_and_nonfinite_uv_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=self._source(tmp,SQUARE.replace("vt 1 0","vt 0 0"))
            with self.assertRaisesRegex(ValueError,"Collapsed UV"):
                audit_obj(path)
            path=self._source(tmp,"v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            with self.assertRaisesRegex(ValueError,"Missing source UV"):
                audit_obj(path)
            path=self._source(tmp,SQUARE.replace("vt 1 1","vt nan 1"))
            with self.assertRaises(ValueError):
                audit_obj(path)

    def test_uv_winding_signs_are_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=self._source(tmp,SQUARE.replace("f 1/1 3/3 4/4","f 1/1 3/4 4/3"))
            r=audit_obj(path)
            self.assertTrue(r["mixed_uv_winding"])
            self.assertEqual(r["positive_uv_winding_triangles"],1)
            self.assertEqual(r["negative_uv_winding_triangles"],1)

    def test_density_outlier_and_texel_equivalent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=self._source(tmp,"""v 0 0 0
v 1 0 0
v 0 1 0
v 5 0 0
v 9 0 0
v 5 4 0
vt 0 0
vt 1 0
vt 0 1
f 1/1 2/2 3/3
f 4/1 5/2 6/3
""")
            r=audit_obj(path,texture_size=512)
            self.assertEqual(r["density_outlier_triangles"],1)
            self.assertEqual(r["max_density_deviation_factor"],4)
            self.assertEqual(r["median_area_equivalent_texels_per_world_unit"],128)

    def test_nonmanifold_thresholds_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=self._source(tmp,SQUARE+"f 1/1 2/2 4/4\n")
            with self.assertRaisesRegex(ValueError,"Nonmanifold"):
                audit_obj(path)
            path=self._source(tmp)
            for kwargs in ({"max_anisotropy":float("nan")},
                           {"max_density_ratio":0.5},
                           {"texture_size":True},{"strict":1}):
                with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                    audit_obj(path,**kwargs)
            link=Path(tmp)/"linked.obj"
            link.symlink_to(path)
            with self.assertRaisesRegex(ValueError,"unsafe"):
                audit_obj(link)

    def test_real_sculpt_and_triangle_local_atlas(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            build(root/"sculpt")
            source=root/"sculpt"/"source_low.obj"
            original=source.read_bytes()
            a=audit_obj(source,strict=True)
            self.assertEqual(a["triangle_count"],32)
            self.assertEqual(a["uv_seams"]["continuous_edges"],40)
            atlas=root/"atlas.obj"
            unwrap(source,atlas,texture_size=256,padding=2)
            b=audit_obj(atlas)
            self.assertEqual(b["uv_seams"]["seam_edges"],40)
            self.assertFalse(b["production_approved"])
            self.assertEqual(source.read_bytes(),original)

if __name__=="__main__":
    unittest.main()
