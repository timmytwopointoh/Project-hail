"""VQ portable multi-material source and texture preservation tests."""
import json
from pathlib import Path
import struct
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory import build_asset
from vq_multimaterial_export import export
from vq_adaptive_remesh import refine
from vq_model_tools import check_gltf
ROOT=Path(__file__).resolve().parents[1]
class VQMultiMaterialTest(unittest.TestCase):
    def test_real_catalog_textures_survive_refined_glTF(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            manifest=build_asset(ROOT/"catalog.json","rolling_terrain",folder/"source")
            src=folder/"source"/"rolling_terrain.obj"
            recipe=json.loads((ROOT/"vq_adaptive_remesh_demo.json").read_text())
            result=refine(src,recipe,folder/"refined.obj")
            doc=export(folder/"refined.obj",folder/"pack"/"refined.gltf",
                       source_gltf=folder/"source"/"rolling_terrain.gltf",
                       source_manifest=folder/"source"/"asset_manifest.json")
            self.assertEqual(doc["extras"]["triangles"],result["candidate_triangles"])
            self.assertEqual(set(x["name"] for x in doc["materials"]),set(manifest["materials"]))
            self.assertEqual(len(doc["meshes"][0]["primitives"]),len(manifest["materials"]))
            self.assertEqual(len(doc["images"]),len(manifest["materials"])*4)
            self.assertEqual(doc["extras"]["original_material_library_verified"],True)
            self.assertFalse(doc["extras"]["production_approved"])
            self.assertTrue(check_gltf(folder/"pack"/"refined.gltf")["structural_smoke_passed"])
            for image in doc["images"]:
                self.assertTrue((folder/"pack"/image["uri"]).is_file())
            packed=(folder/"pack"/"refined.bin").read_bytes()
            for item in doc["meshes"][0]["primitives"]:
                indices=doc["accessors"][item["indices"]]
                positions=doc["accessors"][item["attributes"]["POSITION"]]
                view=doc["bufferViews"][indices["bufferView"]]
                values=struct.unpack_from("<"+"I"*indices["count"],packed,view["byteOffset"])
                self.assertLess(max(values),positions["count"])
                self.assertIn("TEXCOORD_0",item["attributes"])
    def test_reject_tampered_baked_texture_and_original_gltf(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);source=folder/"source"
            build_asset(ROOT/"catalog.json","treasure_chest",source)
            image=next(source.glob("textures/*/albedo.png"))
            image.write_bytes(image.read_bytes()+b"tampered")
            with self.assertRaisesRegex(ValueError,"Texture digest"):
                export(source/"treasure_chest.obj",folder/"out"/"out.gltf",
                       source_gltf=source/"treasure_chest.gltf",
                       source_manifest=source/"asset_manifest.json")
    def test_reject_external_texture_and_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);source=folder/"source"
            build_asset(ROOT/"catalog.json","treasure_chest",source)
            original=json.loads((source/"treasure_chest.gltf").read_text())
            for uri in ("../secret.png","https://malware.invalid/file.png","data:application/png;base64,AA"):
                original["images"][0]["uri"]=uri
                alt=source/"broken.gltf";alt.write_text(json.dumps(original))
                with self.assertRaisesRegex(ValueError,"Unsafe"):
                    export(source/"treasure_chest.obj",folder/"out"/"out.gltf",
                           source_gltf=alt)
            with self.assertRaisesRegex(ValueError,"requires source glTF"):
                export(source/"treasure_chest.obj",folder/"out"/"out.gltf",
                       source_manifest=source/"asset_manifest.json")
if __name__=="__main__":unittest.main()
