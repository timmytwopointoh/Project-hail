"""VEILFORGE M27 reusable source-sculpt layers and strict geometry limits."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory import AssetError, Mesh,generate,load_catalog,export_obj
from engine import inspect_obj
from sculpt_layers import validate_layers,apply_layers

CATALOG=Path(__file__).resolve().parents[1]/"catalog.json"
STONE={"id":"stone-wear","mode":"micro_relief","amplitude":.012,
       "frequency":4.0,"materials":["stone"]}

class SculptLayersTest(unittest.TestCase):
    def test_preserves_source_and_original_triangle_edges_uvs(self):
        m=Mesh()
        m.quad((0,0,0),(2,0,0),(2,0,2),(0,0,2),"stone")
        before=list(m.parts["stone"])
        after,report=apply_layers(m,[STONE],33,triangle_budget=50)
        self.assertEqual(m.parts["stone"],before)
        self.assertEqual(m.triangle_count,2)
        self.assertEqual(after.triangle_count,6)
        self.assertEqual(report["layers"][0]["original_edges_displaced"],0)
        self.assertTrue(report["non_destructive_source_preserved"])
        source_verts={tuple(v) for t in before for v in t[:3]}
        result_verts={tuple(v) for t in after.parts["stone"] for v in t[:3]}
        self.assertTrue(source_verts<=result_verts)
        # All original UV corners remain exactly in the sculpt layer.
        source_uvs={tuple(uv) for face in before for uv in face[4]}
        result_uvs={tuple(uv) for face in after.parts["stone"] for uv in face[4]}
        self.assertTrue(source_uvs<=result_uvs)
    def test_layer_may_be_disabled_without_geometry_changes(self):
        m=Mesh();m.box((0,0,0),(2,2,2),"wood")
        off={"id":"disabled-grain","mode":"micro_relief",
             "amplitude":.012,"frequency":2,"materials":["wood"],"enabled":False}
        out,report=apply_layers(m,[off],123,triangle_budget=100)
        self.assertEqual(out.triangle_count,m.triangle_count)
        self.assertEqual(report["layers"][0]["centroids_displaced"],0)
    def test_strict_input_and_triangle_budget(self):
        m=Mesh();m.box((0,0,0),(2,2,2),"stone")
        wrongs=[
            [dict(STONE,amplitude=float("nan"))],
            [dict(STONE,frequency=-3)],
            [dict(STONE,materials=["steel","unavailable"])],
            [dict(STONE,center=[0,0,float("inf")],radius=2)],
            [dict(STONE,radius=1)],
            [STONE,STONE],
            [STONE]*4,
            [dict(STONE,id="../unsafe")],
            [dict(STONE,enabled="yes")],
        ]
        for rows in wrongs:
            with self.subTest(rows=repr(rows)):
                with self.assertRaises(ValueError):validate_layers(rows,{"stone","wood","steel"})
        with self.assertRaises(AssetError):apply_layers(m,[STONE],42,triangle_budget=15)
    def test_reproducible_procedural_sculpt_in_three_families(self):
        catalog=load_catalog(CATALOG)
        target=["ancient_gate_standard","treasure_chest","rolling_terrain"]
        for name in target:
            spec=catalog[name]
            with self.subTest(asset=name):
                self.assertEqual(len(spec["sculpt_layers"]),1)
                base=generate({k:v for k,v in spec.items() if k!="sculpt_layers"})
                a=generate(spec);b=generate(spec)
                self.assertGreater(a.triangle_count,base.triangle_count)
                self.assertEqual(a.triangle_count,b.triangle_count)
                self.assertEqual(a.sculpt_report["source_triangles"],base.triangle_count)
                self.assertLessEqual(a.triangle_count,18000)
                self.assertTrue(a.sculpt_report["layers"][0]["centroids_displaced"]>0)
                with tempfile.TemporaryDirectory() as tmp:
                    root=Path(tmp)
                    export_obj(base,root/"base.obj")
                    export_obj(a,root/"sculpt.obj")
                    export_obj(b,root/"repeat.obj")
                    self.assertEqual((root/"sculpt.obj").read_bytes(),(root/"repeat.obj").read_bytes())
                    pre=inspect_obj(root/"base.obj")
                    post=inspect_obj(root/"sculpt.obj")
                    for key in ("nonmanifold_edges","boundary_edges","degenerate_triangles"):
                        self.assertEqual(pre[key],post[key],f"{name}:{key} must not regress")
if __name__=="__main__":unittest.main()
