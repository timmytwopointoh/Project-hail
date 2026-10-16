"""VQ topology-safe sculpt, Taubin smoothing and transferable pattern strokes."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vq_brushes import apply_brushes,validate_recipe
from engine import read_obj,inspect_obj

def grid_obj(path, size=7, peak=False):
    lines=["# exact indexed grid; open rim must remain pinned","usemtl stone"]
    for z in range(size):
        for x in range(size):
            y=.25 if peak and x==size//2 and z==size//2 else 0
            lines.append(f"v {x} {y} {z} 0.2 0.3 0.4")
    for z in range(size):
        for x in range(size):
            lines.append(f"vt {x/6:.7f} {z/6:.7f}")
    lines.append("vn 0 -1 0")
    for z in range(size-1):
        for x in range(size-1):
            a=z*size+x+1;b=a+1;c=a+size;d=c+1
            for i,j,k in ((a,b,d),(a,d,c)):
                lines.append(f"f {i}/{i}/1 {j}/{j}/1 {k}/{k}/1")
    path.write_text("\n".join(lines)+"\n")
    return path

def tip(kind="raise",center=None,name="height-one"):
    return {"id":name,"op":"sculpt","center":center or [3,0,3],
            "radius":2.8,"strength":.03,"materials":["stone"],
            "kind":kind,"seed":8}

class VQBrushTest(unittest.TestCase):
    def test_sculpt_preserves_source_faces_uv_and_boundary_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=grid_obj(root/"base.obj");candidate=root/"brush.obj"
            original=source.read_bytes()
            report=apply_brushes(source,{"schema_version":1,"strokes":[tip()]},candidate)
            self.assertEqual(source.read_bytes(),original)
            self.assertTrue(report["technical_geometry_gate_passed"])
            self.assertGreater(report["strokes"][0]["groups_moved"],0)
            self.assertEqual(report["candidate_triangles"],72)
            a,uv,n,faces=read_obj(source)
            b,uv2,n2,faces2=read_obj(candidate)
            self.assertEqual(uv,uv2)
            self.assertEqual(faces,faces2)
            self.assertEqual(len(a),len(b))
            self.assertEqual(a[0],b[0])
            self.assertEqual(inspect_obj(source)["boundary_edges"],
                             inspect_obj(candidate)["boundary_edges"])
            self.assertEqual(tuple(a[len(a)//2][3:]),tuple(b[len(b)//2][3:]))
    def test_smoothing_reduces_a_peak_instead_of_inflating_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=grid_obj(root/"peak.obj",peak=True)
            stroke={"id":"relax-bump","op":"smooth","center":[3,.25,3],
                    "radius":3.2,"strength":.90,"materials":["stone"],"iterations":3}
            report=apply_brushes(source,{"schema_version":1,"strokes":[stroke]},root/"smoothed.obj")
            self.assertGreater(report["strokes"][0]["groups_moved"],0)
            a,_,_,_=read_obj(source)
            b,_,_,_=read_obj(root/"smoothed.obj")
            center_index=3*7+3
            self.assertLess(abs(b[center_index][1]),abs(a[center_index][1]))
            self.assertEqual(a[0],b[0])
            self.assertEqual(report["strokes"][0]["mesh_faces_inserted"],0)
    def test_stamp_reuses_prior_procedural_motif_not_raw_mesh(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=grid_obj(root/"mesh.obj")
            brush=tip("roughen",center=[2,0,2],name="grain-source")
            stamp={"id":"repeat-grain","op":"stamp","from":"grain-source",
                   "center":[4,0,4],"radius":2.8,"strength":.85,
                   "materials":["stone"]}
            recipe={"schema_version":1,"strokes":[brush,stamp]}
            a=apply_brushes(source,recipe,root/"a.obj")
            b=apply_brushes(source,recipe,root/"b.obj")
            self.assertEqual((root/"a.obj").read_bytes(),(root/"b.obj").read_bytes())
            self.assertGreater(a["strokes"][1]["groups_moved"],0)
            self.assertTrue(a["raw_geometry_copy_paste_performed"] is False)
            self.assertEqual(a["candidate_sha256"],b["candidate_sha256"])
    def test_fail_closed_for_invalid_recipes_and_unsafe_source_overwrite(self):
        base=tip()
        recipes=[
           {"schema_version":1,"strokes":[dict(base,strength=100)]},
           {"schema_version":1,"strokes":[dict(base,radius=float("nan"))]},
           {"schema_version":1,"strokes":[dict(base,center=[0,0,float("inf")])]},
           {"schema_version":1,"strokes":[dict(base,materials=["unknown"])]},
           {"schema_version":1,"strokes":[dict(base,seed=-2)]},
           {"schema_version":1,"strokes":[base,base]},
           {"schema_version":1,"strokes":[dict(base,op="stamp",**{"from":"not-here"})]},
           {"schema_version":1,"strokes":[dict(base,op="smooth",iterations=0)]},
        ]
        for row in recipes:
            with self.subTest(recipe=str(row)[:85]),self.assertRaises(ValueError):
                validate_recipe(row,{"stone"})
        with tempfile.TemporaryDirectory() as tmp:
            source=grid_obj(Path(tmp)/"source.obj")
            with self.assertRaises(ValueError):
                apply_brushes(source,{"schema_version":1,"strokes":[base]},source)
    def test_open_triangle_never_gets_smoothed_as_solid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=root/"triangle.obj"
            src.write_text("v 0 0 0\nv 1 0 0\nv 0 0 1\nf 1 2 3\n")
            brush=tip()
            brush["materials"]=["default"]
            brush["center"]=[0,0,0]
            with self.assertRaisesRegex(ValueError,"pinned|outside"):
                apply_brushes(src,{"schema_version":1,"strokes":[brush]},root/"out.obj")
    def test_actual_catalog_asset_compatibility(self):
        from factory import build_asset
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            catalog=Path(__file__).resolve().parents[1]/"catalog.json"
            model=build_asset(catalog,"rolling_terrain",root/"terrain")
            original=root/"terrain"/"rolling_terrain.obj"
            recipe=json.loads((Path(__file__).resolve().parents[1]/"vq_brush_demo.json").read_text())
            report=apply_brushes(original,recipe,root/"refined_terrain.obj")
            self.assertEqual(report["source_sha256"],model["obj_sha256"])
            self.assertGreater(sum(s["groups_moved"] for s in report["strokes"]),0)
            self.assertFalse(report["ready_for_game"])
            self.assertFalse(report["android_emulator_verified"])

if __name__=="__main__":
    unittest.main()
