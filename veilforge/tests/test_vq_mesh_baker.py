"""Mesh-derived sculpt detail baking is real, reproducible, bounded and honest."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vq_mesh_baker import bake,uv_rows,raster
from vq_sculpt_detail_patch import build
from engine import inspect_obj

class M30BakingTests(unittest.TestCase):
    def test_high_poly_sculpt_creates_measurable_tangent_normals_and_height(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=build(root/"meshes")
            self.assertGreater(src["high_triangles"],src["low_triangles"]*20)
            output=bake(root/"meshes/source_low.obj",root/"meshes/source_high.obj",root/"bake",size=64)
            self.assertGreater(output["texels_sampled"],64*64*.90)
            self.assertGreater(output["meaningful_normal_variation_texels"],output["texels_sampled"]*.10)
            self.assertGreater(output["max_high_poly_normal_angle_deg"],3)
            self.assertGreater(output["max_high_poly_height_world_units"],.001)
            self.assertFalse(output["ao_baked"])
            self.assertFalse(output["artistic_signoff"])
            self.assertTrue(output["geometric_surface_used"])
            for name,meta in output["textures"].items():
                data=(root/"bake"/meta["path"]).read_bytes()
                self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
                self.assertEqual(meta["sha256"],hashlib.sha256(data).hexdigest())
            output2=bake(root/"meshes/source_low.obj",root/"meshes/source_high.obj",root/"bake2",size=64)
            self.assertEqual(output["textures"],output2["textures"])
            self.assertEqual(output["low_source_sha256"],src["low_sha256"])
    def test_source_immutability_and_bounded_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build(root/"meshes")
            low=root/"meshes/source_low.obj";high=root/"meshes/source_high.obj"
            first=low.read_bytes();second=high.read_bytes()
            with self.assertRaisesRegex(ValueError,"Supported output size"):
                bake(low,high,root/"out",size=700)
            with self.assertRaisesRegex(ValueError,"A distinct high-detail"):
                bake(low,low,root/"out")
            with self.assertRaisesRegex(ValueError,"height limit"):
                bake(low,high,root/"out",height_limit=.00001,size=64)
            self.assertEqual(low.read_bytes(),first)
            self.assertEqual(high.read_bytes(),second)
    def test_tiled_uv_assets_are_not_silently_reinterpreted_as_unique_atlas(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build(root/"meshes")
            low=root/"meshes/source_low.obj"
            data=low.read_text()
            data=data.replace("vt 1.000000000 0.000000000","vt 1.400000000 0.000000000")
            low.write_text(data)
            with self.assertRaisesRegex(ValueError,"tiled/overflow"):
                bake(low,root/"meshes/source_high.obj",root/"out",size=64)
    def test_overlapping_different_geometry_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build(root/"meshes")
            low=root/"meshes/source_low.obj"
            text=low.read_text()
            # Repeat one UV triangle at different object-space location, with
            # indices pointing to a new triangle; all original UVs retained.
            text+="\nv 0 .5 0\nv 1 .5 0\nv 1 .5 1\nf 26/1/1 27/2/1 28/7/1\n"
            low.write_text(text)
            with self.assertRaisesRegex(ValueError,"Overlapping UV islands"):
                bake(low,root/"meshes/source_high.obj",root/"out",size=64)
    def test_reject_nonfinite_collapsed_uv(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build(root/"meshes")
            low=root/"meshes/source_low.obj"
            data=low.read_text().replace("vt 0.250000000 0.000000000","vt 0.000000000 0.000000000")
            low.write_text(data)
            with self.assertRaisesRegex(ValueError,"UV triangle collapsed|Overlapping"):
                bake(low,root/"meshes/source_high.obj",root/"out",size=64)
if __name__=="__main__":unittest.main()
