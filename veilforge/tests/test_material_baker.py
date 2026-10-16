"""M5 texture provenance and UV continuity for game asset export."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from factory import Mesh,build_asset
from assembly import compile_scene
from material_baker import bake

CATALOG=Path(__file__).resolve().parents[1]/"catalog.json"

class TextureTest(unittest.TestCase):
    def test_pbr_four_maps_deterministic_and_packed_rgb(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            a=bake("steel",root/"one",size=64,seed=29)
            b=bake("steel",root/"two",size=64,seed=29)
            self.assertEqual(set(a["maps"]),{"albedo","normal","metallic_roughness","ao"})
            self.assertEqual(a["maps"],b["maps"])
            for name,row in a["maps"].items():
                data=(root/"one"/row["file"]).read_bytes()
                self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
                self.assertEqual(struct.unpack(">II",data[16:24]),(64,64))
                self.assertEqual(hashlib.sha256(data).hexdigest(),row["sha256"])
            self.assertFalse(a["physically_based_reference_approved"])
    def test_quad_uv_orientation_and_physical_tile_repeat(self):
        m=Mesh()
        a=(0,0,0);b=(3.4,0,0);c=(3.4,0,1.7);d=(0,0,1.7)
        m.quad(a,b,c,d,"stone")
        first,second=m.parts["stone"]
        self.assertEqual(first[4][0],second[4][0])
        self.assertEqual(first[4][2],second[4][1])
        self.assertEqual(first[4][1],(4,0))
        self.assertEqual(first[4][2],(4,2))
    def test_real_material_images_export_and_scene_repack(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=root/"assets"/"treasure_chest"
            asset=build_asset(CATALOG,"treasure_chest",source)
            doc=json.loads((source/"treasure_chest.gltf").read_text())
            self.assertEqual(len(doc["images"]),len(asset["materials"])*4)
            self.assertEqual(len(doc["textures"]),len(doc["images"]))
            self.assertEqual(len(doc["samplers"]),1)
            for mat in doc["materials"]:
                pbr=mat["pbrMetallicRoughness"]
                self.assertIn("baseColorTexture",pbr)
                self.assertIn("metallicRoughnessTexture",pbr)
                self.assertIn("normalTexture",mat)
                self.assertIn("occlusionTexture",mat)
                self.assertEqual(pbr["baseColorFactor"],[1,1,1,1])
            scenes=root/"scenes.json"
            scenes.write_text(json.dumps({"schema_version":1,"scenes":[{
                "id":"testscene","instances":[{"id":"chest01","asset":"treasure_chest",
                    "position":[0,0,0],"yaw":0,"scale":1}]}]}))
            report=compile_scene(CATALOG,scenes,"testscene",root/"assets",root/"scene")
            packed=json.loads((root/"scene"/"testscene.gltf").read_text())
            self.assertEqual(report["texture_images"],len(doc["images"]))
            self.assertEqual(len(packed["textures"]),len(doc["textures"]))
            self.assertTrue(all((root/"scene"/i["uri"]).is_file() for i in packed["images"]))
            self.assertTrue(all(t["index"]<len(packed["textures"]) for m in packed["materials"]
               for t in [m["pbrMetallicRoughness"]["baseColorTexture"],
                         m["pbrMetallicRoughness"]["metallicRoughnessTexture"],
                         m["normalTexture"],m["occlusionTexture"]]))
            self.assertFalse(report["production_approved"])
    def test_modified_texture_rejected_by_scene_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=root/"assets"/"ancient_gate_mobile"
            build_asset(CATALOG,"ancient_gate_mobile",source)
            image=next(source.glob("textures/*/albedo.png"))
            image.write_bytes(image.read_bytes()+b"tampered")
            scenes=root/"scenes.json"
            scenes.write_text(json.dumps({"schema_version":1,"scenes":[{
                "id":"testscene","instances":[{"id":"gate01","asset":"ancient_gate_mobile",
                    "position":[0,0,0],"yaw":0,"scale":1}]}]}))
            with self.assertRaisesRegex(ValueError,"Texture bytes differ"):
                compile_scene(CATALOG,scenes,"testscene",root/"assets",root/"scene")
if __name__=="__main__":unittest.main()
