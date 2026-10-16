"""Offline deterministic unit tests; no external renderer or emulator required."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engine
import manager

class EngineTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.dir=Path(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def simple_obj(self, invalid=False):
        path=self.dir/"shape.obj"
        path.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\n"
            "vt 0 0\nvt 1 0\nvt 0 1\nvn 0 0 1\n"
            + ("f 1/1/1 2/2/1 8/3/1\n" if invalid else
               "f 1/1/1 2/2/1 3/3/1\n"))
        return path
    def test_valid_topology_and_dimensions(self):
        r=engine.inspect_obj(self.simple_obj())
        self.assertEqual(r["triangles"],1)
        self.assertEqual(r["boundary_edges"],3)
        self.assertEqual(r["nonmanifold_edges"],0)
        self.assertEqual(r["degenerate_triangles"],0)
        self.assertEqual(r["dimensions"],[1,1,0])
        self.assertFalse(r["ready_for_game"])
    def test_bad_index_rejected(self):
        with self.assertRaises(engine.MeshError):
            engine.inspect_obj(self.simple_obj(True))
    def test_nonfinite_rejected(self):
        path=self.dir/"nan.obj"
        path.write_text("v NaN 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
        with self.assertRaises(engine.MeshError):
            engine.inspect_obj(path)
    def test_degenerate_detected(self):
        path=self.dir/"flat.obj"
        path.write_text("v 0 0 0\nv 1 0 0\nv 2 0 0\nf 1 2 3\n")
        self.assertEqual(engine.inspect_obj(path)["degenerate_triangles"],1)
    def test_materials_are_deterministic_and_png_valid(self):
        one=self.dir/"one";two=self.dir/"two"
        m=engine.bake_pbr(one,"skin",128,23)
        engine.bake_pbr(two,"skin",128,23)
        self.assertEqual(set(m["maps"]),{"albedo","normal","roughness","metallic","ao","height"})
        for name in m["maps"]:
            a=(one/(name+".png")).read_bytes()
            b=(two/(name+".png")).read_bytes()
            self.assertEqual(a,b)
            self.assertTrue(a.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(m["maps"]["normal"]["color_space"],"linear")
    def test_disallows_unsupported_texture_dimension(self):
        with self.assertRaises(ValueError):
            engine.bake_pbr(self.dir/"tex","stone",333)
    def test_plan_reuses_hierarchical_worker_manager(self):
        backlog=Path(__file__).resolve().parents[1]/"backlog.json"
        result=manager.plan(backlog,self.dir/"plan",12)
        self.assertGreaterEqual(result["allocated"],5)
        self.assertLessEqual(result["allocated"],12)
        self.assertEqual(result["max_workers"],12)
        self.assertFalse(any("renderer"==x["role"] for x in result["worker_matrix"]["include"]))
        self.assertTrue((self.dir/"plan"/"worker_plan.json").is_file())
    def test_review_rejects_missing_sources(self):
        result=manager.review(self.dir,self.dir/"summary")
        self.assertFalse(result["gates_passed"])
        self.assertFalse(result["asset_automatically_promoted"])
        self.assertGreater(len(result["issues"]),0)

if __name__=="__main__":
    unittest.main()
