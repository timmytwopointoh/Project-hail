"""M2 human/armor reusable glTF -> Android probe pack regression tests."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gltf_export import export
from probe_pack import pack,PackError

class ProbePackTest(unittest.TestCase):
    def init(self,root):
        scene=root/"scene";scene.mkdir()
        blank={"asset":{"version":"2.0"},
               "extras":{"production_approved":False},
               "buffers":[],"bufferViews":[],"accessors":[],
               "materials":[],"meshes":[],"nodes":[],
               "scenes":[{"nodes":[]}]}
        (scene/"ruin_courtyard_demo.gltf").write_text(json.dumps(blank))
        return scene
    def asset(self,root,name):
        obj=root/(name+".obj")
        obj.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
        gltf=root/(name+".gltf")
        export(obj,gltf,profile="skin")
        return gltf
    def test_injects_real_triangle_source_without_approving(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            scene=self.init(root)
            hero=self.asset(root,"human_repaired")
            out=pack(scene,{"human_repaired":hero})
            self.assertEqual(len(out["nodes"]),1)
            self.assertEqual(len(out["meshes"]),1)
            self.assertEqual(len(out["buffers"]),1)
            self.assertEqual(out["meshes"][0]["primitives"][0]["attributes"]["POSITION"],0)
            self.assertFalse(out["extras"]["production_approved"])
            self.assertTrue((scene/"buffers"/"human_repaired.bin").is_file())
    def test_integrity_and_missing_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            scene=self.init(root)
            with self.assertRaises(FileNotFoundError):
                pack(scene,{"human_repaired":root/"nonexistent.gltf"})
            valid=self.asset(root,"human_repaired")
            with self.assertRaises(PackError):
                pack(scene,{"unapproved_asset":valid})

if __name__=="__main__":
    unittest.main()
