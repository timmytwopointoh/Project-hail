from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engine
import gltf_export

class GltfTest(unittest.TestCase):
    def test_indexed_gltf_with_pbr_maps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            mesh=root/"triangle.obj"
            mesh.write_text("v 0 0 0 1 0 0\nv 1 0 0 0 1 0\nv 0 1 0 0 0 1\n"
                "vn 0 0 1\nvt 0 0\nvt 1 0\nvt 0 1\n"
                "f 1/1/1 2/2/1 3/3/1\n")
            materials=root/"mat"
            engine.bake_pbr(materials,"steel",128,42)
            result=gltf_export.export(mesh,root/"mesh.gltf",material_dir=materials,profile="steel")
            self.assertEqual(result["asset"]["version"],"2.0")
            self.assertEqual(result["extras"]["triangles"],1)
            self.assertEqual(result["accessors"][0]["count"],3)
            self.assertEqual(result["accessors"][4]["count"],3)
            self.assertTrue((root/"mesh.bin").is_file())
            self.assertEqual((root/"mesh.bin").stat().st_size,result["buffers"][0]["byteLength"])
            self.assertEqual(len(result["images"]),4)
            w,h,pixels=gltf_export._unpack_gray_png(materials/"roughness.png")
            self.assertEqual((w,h,len(pixels)),(128,128,128*128))
            self.assertTrue((root/"mesh_metallic_roughness.png").read_bytes().startswith(b"\x89PNG"))
            self.assertFalse(result["extras"]["manually_approved"])
    def test_no_textures_still_standard_pbr(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            mesh=root/"shape.obj"
            mesh.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
            result=gltf_export.export(mesh,root/"asset.gltf",profile="stone")
            self.assertEqual(result["materials"][0]["pbrMetallicRoughness"]["metallicFactor"],0)
            self.assertEqual(result["accessors"][4]["count"],3)
if __name__=="__main__":
    unittest.main()
