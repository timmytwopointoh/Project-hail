import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from assembly import load_scenes, compile_scene
from factory import AssetError, build_asset

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/"catalog.json"
SCENES=ROOT/"scenes.json"

class SceneTest(unittest.TestCase):
    def test_scene_catalog_supports_repeated_asset_instances(self):
        scene=load_scenes(SCENES)["ruin_courtyard_demo"]
        self.assertEqual(len(scene["instances"]),8)
        self.assertLess(len({a["asset"] for a in scene["instances"]}),8)
    def test_compiled_scene_has_multiple_independent_meshes_and_nodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            scene={"schema_version":1,"scenes":[
                {"id":"example","instances":[
                    {"id":"a1","asset":"treasure_chest","position":[1,0,1],"yaw":0,"scale":1},
                    {"id":"b1","asset":"treasure_chest","position":[2,0,1],"yaw":45,"scale":.5},
                    {"id":"c1","asset":"ceremonial_sword","position":[0,1,0],"yaw":-32,"scale":1}]}]}
            path=root/"scene.json"
            path.write_text(json.dumps(scene))
            assets=root/"assets"
            for name in ("treasure_chest","ceremonial_sword"):
                build_asset(CATALOG,name,assets/name)
            report=compile_scene(CATALOG,path,"example",assets,root/"out")
            self.assertEqual(report["instances"],3)
            self.assertEqual(report["unique_asset_sources"],2)
            gltf=json.loads((root/"out"/"example.gltf").read_text())
            self.assertEqual(len(gltf["nodes"]),3)
            self.assertEqual(len(gltf["meshes"]),2)
            self.assertEqual(len(gltf["buffers"]),2)
            self.assertEqual(gltf["nodes"][0]["mesh"],gltf["nodes"][1]["mesh"])
            self.assertNotEqual(gltf["nodes"][1]["mesh"],gltf["nodes"][2]["mesh"])
            self.assertEqual(gltf["extras"]["production_approved"],False)
            self.assertTrue((root/"out"/"buffers"/"treasure_chest.bin").is_file())
    def test_reject_bad_instance_and_path_style(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"scene.json"
            def try_scene(instances):
                path.write_text(json.dumps({"schema_version":1,"scenes":[
                    {"id":"test-scene","instances":instances}]}))
                with self.assertRaises(AssetError):load_scenes(path)
            good={"id":"item","asset":"treasure_chest","position":[0,0,0],"yaw":0,"scale":1}
            try_scene([dict(good,asset="../secrets")])
            try_scene([dict(good,position=[0,float("nan"),0])])
            try_scene([dict(good,scale=0)])
            try_scene([dict(good,id="my/item")])
            try_scene([good,good])
    def test_missing_dependencies_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(AssetError):
                compile_scene(CATALOG,SCENES,"ruin_courtyard_demo",
                    Path(tmp)/"empty",Path(tmp)/"out")
if __name__=="__main__":
    unittest.main()
