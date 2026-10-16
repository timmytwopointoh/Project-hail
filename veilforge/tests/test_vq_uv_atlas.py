"""M31: real catalog UV chart atlas, attribute preservation, and baking handoff."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import inspect_obj,read_obj
from vq_uv_atlas import unwrap,plan
from vq_mesh_baker import uv_rows,raster,bake
from vq_uv_transfer import transfer
from vq_sculpt_detail_patch import build
from factory import build_asset

ROOT=Path(__file__).resolve().parents[1]

class UVAtlasTests(unittest.TestCase):
    def test_uneven_original_uvs_become_bounded_nonoverlapping_unique_charts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            build(root/"source")
            low=root/"source"/"source_low.obj"
            original=low.read_bytes()
            # Source has a continuous square UV map; new independent atlas
            # makes it safe even if original UVs are outside the unit domain.
            source=low.read_text().replace("vt 1.000000000 0.000000000",
                                           "vt 3.000000000 0.000000000")
            low.write_text(source)
            old=low.read_bytes()
            result=unwrap(low,root/"atlas.obj",texture_size=256,padding=3)
            self.assertEqual(low.read_bytes(),old)
            self.assertNotEqual(result["candidate_sha256"],hashlib.sha256(old).hexdigest())
            self.assertTrue(result["geometry_invariants_preserved"])
            self.assertEqual(result["charts"],32)
            before=inspect_obj(low);after=inspect_obj(root/"atlas.obj")
            for key in ("triangles","vertices_welded","boundary_edges",
                        "nonmanifold_edges","degenerate_triangles"):
                self.assertEqual(before[key],after[key])
            self.assertEqual(after["uvs_outside_zero_one"],0)
            rows,ns=uv_rows(root/"atlas.obj")
            pixels=raster(rows,ns,256)
            self.assertGreater(sum(x is not None for x in pixels),256*256*.55)
            self.assertLess(sum(x is not None for x in pixels),256*256)
    def test_real_treasure_chest_materials_preserved_and_budget_enforced(self):
        from vq_brushes import _face_materials
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            build_asset(ROOT/"catalog.json","treasure_chest",root/"chest")
            obj=root/"chest"/"treasure_chest.obj"
            source_bytes=obj.read_bytes()
            candidate=root/"refined.obj"
            r=unwrap(obj,candidate,texture_size=512,padding=2)
            self.assertEqual(source_bytes,obj.read_bytes())
            self.assertEqual(r["source_triangles"],372)
            self.assertEqual(_face_materials(obj,372),
                             _face_materials(candidate,372))
            self.assertEqual(len(read_obj(candidate)[1]),372*3)
            self.assertEqual(r["texture_stretch_optimized"],False)
            with self.assertRaisesRegex(ValueError,"Insufficient texel density"):
                unwrap(obj,root/"too_small.obj",texture_size=128,padding=2)
            self.assertFalse((root/"too_small.obj").exists())
    def test_atlas_to_refine_sculpt_to_real_normal_baker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build(root/"meshes")
            low=root/"meshes"/"source_low.obj"
            atlas=root/"atlas.obj"
            atlas_report=unwrap(low,atlas,texture_size=256,padding=2)
            high=root/"meshes"/"source_high.obj"
            # A real 3200-face sculpt wave is mapped to low parent UV charts;
            # no fabricated surface curvature or lowered bake thresholds.
            correspondence=transfer(atlas,high,root/"projected_high.obj",
                                    cage_distance=.06)
            self.assertEqual(correspondence["high_faces"],3200)
            self.assertGreaterEqual(correspondence["parent_charts_used"],25)
            baked=bake(atlas,root/"projected_high.obj",root/"baked",size=256)
            self.assertGreater(baked["meaningful_normal_variation_texels"],100)
            self.assertGreater(baked["textured_coverage_fraction"],.60)
            self.assertEqual(baked["low_source_sha256"],atlas_report["candidate_sha256"])
            self.assertFalse(baked["android_emulator_verified"])
            self.assertFalse(baked["production_approved"])
    def test_uv_projection_rejects_unrelated_geometry_outside_cage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build(root/"meshes")
            low=root/"atlas.obj"
            unwrap(root/"meshes/source_low.obj",low,texture_size=256,padding=2)
            high=root/"meshes/source_high.obj"
            altered=root/"invalid_high.obj"
            data=high.read_text()
            # Shift the very first real vertex outside the limited projection
            # cage while leaving its UV and index topology unchanged.
            for line in data.splitlines():
                if line.startswith("v "):
                    parts=line.split()
                    parts[2]="0.500000000"
                    data=data.replace(line," ".join(parts),1)
                    break
            altered.write_text(data)
            with self.assertRaisesRegex(ValueError,"projection cage|UV charts"):
                transfer(low,altered,root/"must_fail.obj",cage_distance=.06)
            self.assertFalse((root/"must_fail.obj").exists())
    def test_reject_invalid_budget_padding_and_source_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build(root/"source")
            src=root/"source"/"source_low.obj"
            for kw in ({"texture_size":512,"padding":0},
                       {"texture_size":1024,"padding":9},
                       {"texture_size":300,"padding":2},
                       {"texture_size":128,"padding":True}):
                with self.subTest(kw=kw),self.assertRaises(ValueError):
                    unwrap(src,root/"candidate.obj",**kw)
            with self.assertRaisesRegex(ValueError,"Never overwrite"):
                unwrap(src,src,texture_size=256,padding=2)

if __name__=="__main__":unittest.main()
