"""VQ M29 conforming adaptive source subdivision and protection regression suite."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from engine import read_obj,inspect_obj
from vq_adaptive_remesh import refine,validate_recipe
from vq_model_tools import uv_evidence,check_gltf
from gltf_export import export

ROOT=Path(__file__).resolve().parents[1]
def grid(path,size=7,split_uv=False,two_materials=False):
    lines=["# shared geometric vertices, independent normal and UV streams"]
    for z in range(size):
        for x in range(size):
            lines.append(f"v {x*.6:.8f} 0 {z*.6:.8f} .3 .7 .2")
    lines.append("vn 0 -1 0")
    uv_start=[]
    for z in range(size-1):
        for x in range(size-1):
            group="stone" if not two_materials or x<size//2 else "wood"
            lines.append("usemtl "+group)
            triangles=((z*size+x,z*size+x+1,(z+1)*size+x+1),
                       (z*size+x,(z+1)*size+x+1,(z+1)*size+x))
            for ids in triangles:
                coords=[((i%size)/(size-1),(i//size)/(size-1)) for i in ids]
                if split_uv:
                    coords=[(uv[0]+.1*(x%2),uv[1]+.1*(z%2)) for uv in coords]
                index=[]
                for u,v in coords:
                    lines.append(f"vt {u:.8f} {v:.8f}")
                    index.append(sum(line.startswith("vt ") for line in lines))
                items=[f"{i+1}/{ui}/1" for i,ui in zip(ids,index)]
                lines.append("f "+" ".join(items))
    path.write_text("\n".join(lines)+"\n")
    return path

def recipe(**changes):
    r={"schema_version":1,"center":[1.8,0,1.8],"radius":3.5,
       "target_edge_length":.35,"max_edges":40,"triangle_budget":200,
       "materials":["stone"],"crease_angle_deg":60}
    r.update(changes)
    return r

class AdaptiveRefineTests(unittest.TestCase):
    def test_welded_uv_seams_split_on_both_sides_with_no_new_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=grid(root/"source.obj",split_uv=True)
            baseline=source.read_bytes()
            out=root/"refined.obj"
            a=refine(source,recipe(),out)
            self.assertEqual(source.read_bytes(),baseline)
            self.assertTrue(a["numeric_geometry_gate_passed"])
            self.assertGreater(a["edges_selected"],0)
            self.assertGreater(a["candidate_triangles"],a["source_triangles"])
            self.assertEqual(a["topology_before"],a["topology_after"])
            self.assertEqual(a["source_faces_by_split_count"]["0"]+
                             a["source_faces_by_split_count"]["1"]+
                             a["source_faces_by_split_count"]["2"]+
                             a["source_faces_by_split_count"]["3"],
                             a["source_triangles"])
            a_vertices,a_uv,_,a_faces=read_obj(source)
            b_vertices,b_uv,_,b_faces=read_obj(out)
            self.assertEqual(b_vertices[:len(a_vertices)],a_vertices)
            self.assertEqual(b_uv[:len(a_uv)],a_uv)
            self.assertEqual(len(b_faces),a["candidate_triangles"])
            self.assertEqual(uv_evidence(b_vertices,b_uv,b_faces)["collapsed_uv_faces"],0)
            self.assertEqual(a["candidate_sha256"],hashlib.sha256(out.read_bytes()).hexdigest())
            self.assertTrue(all(len(v)>=6 for v in b_vertices)) # preserved vertex colors
    def test_deterministic_bytes_and_glTF_binary_validity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=grid(root/"input.obj")
            a=refine(source,recipe(max_edges=8),root/"a.obj")
            b=refine(source,recipe(max_edges=8),root/"b.obj")
            self.assertEqual(a["candidate_sha256"],b["candidate_sha256"])
            model=export(root/"a.obj",root/"a.gltf",profile="stone")
            self.assertEqual(model["extras"]["triangles"],a["candidate_triangles"])
            self.assertTrue(check_gltf(root/"a.gltf")["structural_smoke_passed"])
    def test_no_splitting_across_material_islands(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);src=grid(root/"mat.obj",two_materials=True)
            out=root/"out.obj"
            r=refine(src,recipe(max_edges=20),out)
            self.assertGreater(r["edges_selected"],0)
            self.assertEqual(r["topology_before"],r["topology_after"])
            text=out.read_text()
            self.assertIn("usemtl stone",text)
            self.assertIn("usemtl wood",text)
    def test_hard_edges_and_mesh_boundaries_are_protected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=root/"single.obj";src.write_text(
              "v 0 0 0\nv 1 0 0\nv 0 0 1\n"
              "vt 0 0\nvt 1 0\nvt 0 1\n"
              "f 1/1 2/2 3/3\n")
            with self.assertRaisesRegex(ValueError,"No safe interior edges"):
                refine(src,recipe(materials=["default"]),root/"out.obj")
            self.assertFalse((root/"out.obj").exists())
    def test_fail_closed_for_bad_recipe_and_extreme_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=grid(root/"g.obj")
            for item in (recipe(radius=0),recipe(radius=float("nan")),
                         recipe(target_edge_length=0),recipe(center=[1,2,float("inf")]),
                         recipe(max_edges=0),recipe(triangle_budget=2),
                         recipe(materials=["unknown"]),
                         recipe(crease_angle_deg=95),
                         recipe(max_edges=True)):
                with self.subTest(recipe=str(item)[:90]),self.assertRaises(ValueError):
                    validate_recipe(item,{"stone"})
            with self.assertRaisesRegex(ValueError,"already exceeds"):
                refine(source,recipe(triangle_budget=4),root/"fail.obj")
            with self.assertRaisesRegex(ValueError,"Never overwrite"):
                refine(source,recipe(),source)
    def test_real_veilforge_terrain_and_material_maps(self):
        from factory import build_asset
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            manifest=build_asset(ROOT/"catalog.json","rolling_terrain",root/"source")
            src=root/"source"/"rolling_terrain.obj"
            params=json.loads((ROOT/"vq_adaptive_remesh_demo.json").read_text())
            row=refine(src,params,root/"terrain_refined.obj")
            self.assertGreater(row["edges_selected"],150)
            self.assertGreater(row["candidate_triangles"],manifest["triangles"])
            self.assertEqual(row["source_sha256"],manifest["obj_sha256"])
            self.assertFalse(row["artistic_signoff"])
            self.assertFalse(row["android_emulator_tested"])
            self.assertTrue(row["geometry_welded_topology_preserved"])
            before=inspect_obj(src);after=inspect_obj(root/"terrain_refined.obj")
            self.assertEqual(before["nonmanifold_edges"],after["nonmanifold_edges"])
            self.assertEqual(before["boundary_edges"],after["boundary_edges"])

if __name__=="__main__":unittest.main()
