"""Deterministic multi-category asset generation and safety guarantees."""
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import inspect_obj
from factory import AssetError, CATEGORIES, generate, load_catalog, export_gltf, export_obj, build_asset
from library_manager import plan, review

CATALOG=Path(__file__).resolve().parents[1]/"catalog.json"

class FactoryTest(unittest.TestCase):
    def test_catalog_covers_all_six_families_and_multiple_tiers(self):
        specs=load_catalog(CATALOG)
        self.assertEqual({s["category"] for s in specs.values()},set(CATEGORIES))
        self.assertGreaterEqual(len(specs),8)
        self.assertIn("mobile",{s["detail"] for s in specs.values()})
    def test_all_recipes_produce_real_geometry_and_in_budget(self):
        for ident,spec in load_catalog(CATALOG).items():
            with self.subTest(id=ident):
                mesh=generate(spec)
                self.assertGreater(mesh.triangle_count,100)
                self.assertGreaterEqual(len(mesh.parts),2)
                bbox=mesh.bounds()
                self.assertTrue(all(bbox[1][i]>bbox[0][i] for i in range(3)))
    def test_gltf_multi_material_buffers_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)
            recipe=load_catalog(CATALOG)["ceremonial_sword"]
            m=generate(recipe)
            export_obj(m,dest/"sword.obj")
            gt=export_gltf(m,dest/"sword.gltf",recipe)
            self.assertGreaterEqual(len(gt["meshes"][0]["primitives"]),3)
            self.assertEqual(len(gt["materials"]),len(gt["meshes"][0]["primitives"]))
            self.assertEqual(gt["extras"]["production_approved"],False)
            self.assertEqual((dest/"sword.bin").stat().st_size,gt["buffers"][0]["byteLength"])
            qa=inspect_obj(dest/"sword.obj")
            self.assertEqual(qa["degenerate_triangles"],0)
            self.assertEqual(qa["triangles"],m.triangle_count)
            self.assertEqual(gt["extras"]["original_vertex_corners"],3*m.triangle_count)
            self.assertLess(gt["extras"]["indexed_vertices"],3*m.triangle_count)
            self.assertEqual(gt["extras"]["vertices_saved"],
                gt["extras"]["original_vertex_corners"]-gt["extras"]["indexed_vertices"])
            # Each primitive preserves its input triangle index count while
            # reusing exact matching attribute tuples. Indices never refer
            # outside that primitive's vertex accessor.
            binary=(dest/"sword.bin").read_bytes()
            import struct
            for primitive in gt["meshes"][0]["primitives"]:
                index_access=gt["accessors"][primitive["indices"]]
                positions=gt["accessors"][primitive["attributes"]["POSITION"]]
                self.assertEqual(index_access["count"]%3,0)
                view=gt["bufferViews"][index_access["bufferView"]]
                offset=view["byteOffset"]+index_access.get("byteOffset",0)
                values=struct.unpack_from("<"+"I"*index_access["count"],binary,offset)
                self.assertLess(max(values),positions["count"])
                self.assertGreaterEqual(positions["count"],3)
    def test_deterministic_artifact_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            left=Path(tmp)/"a";right=Path(tmp)/"b"
            a=build_asset(CATALOG,"ancient_tree",left)
            b=build_asset(CATALOG,"ancient_tree",right)
            self.assertEqual(a["obj_sha256"],b["obj_sha256"])
            self.assertEqual(a["gltf_sha256"],b["gltf_sha256"])
            self.assertFalse(a["production_approved"])
    def test_reject_injection_duplicate_invalid_scale(self):
        template={"schema_version":1,"assets":[
            {"id":"valid-asset","category":"terrain","detail":"mobile","seed":1}]}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"invalid.json"
            tests=[
                [dict(template["assets"][0],id="../danger")],
                [dict(template["assets"][0],seed=-1)],
                [dict(template["assets"][0],scale=0)],
                [dict(template["assets"][0],scale=float("nan"))],
                [dict(template["assets"][0],category="malicious")],
                [template["assets"][0],template["assets"][0]],
                [dict(template["assets"][0],tags=["../../evil"])]]
            for case in tests:
                p.write_text(json.dumps({"schema_version":1,"assets":case}))
                with self.assertRaises(AssetError):
                    load_catalog(p)
    def test_worker_plan_bounded_and_review_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)
            data=plan(CATALOG,directory/"plan")
            self.assertEqual(data["jobs"],len(load_catalog(CATALOG)))
            self.assertEqual(len(data["matrix"]["include"]),data["jobs"])
            result=review(CATALOG,directory/"none",directory/"review")
            self.assertFalse(result["evidence_passed"])
            self.assertEqual(result["complete"],0)
            self.assertFalse(result["production_approved"])
if __name__=="__main__":
    unittest.main()
