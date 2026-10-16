"""VQ model tool regression tests: real mesh QA, bounded previews and no fake reviews."""
from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vq_model_tools import ANGLES,check_gltf,uv_evidence,compare_mask,inspect

class VQModelToolsTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.obj=self.root/"tetra.obj"
        self.obj.write_text(
            "v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 0 1\n"
            "vt 0 0\nvt 1 0\nvt 0 1\n"
            "f 1/1 3/2 2/3\n"
            "f 1/1 2/2 4/3\n"
            "f 2/1 3/2 4/3\n"
            "f 1/1 4/2 3/3\n"
        )
    def tearDown(self):
        self.tmp.cleanup()

    def test_all_fourteen_frames_from_exported_obj(self):
        output=self.root/"qa"
        result=inspect(self.obj,output,render_faces=4)
        self.assertEqual(len(ANGLES),14)
        self.assertTrue(result["technical_geometry_smoke_passed"])
        self.assertFalse(result["artistic_quality_approved"])
        self.assertFalse(result["photorealism_verified"])
        self.assertEqual(result["uv"]["uv_coverage"],1)
        self.assertEqual(result["uv"]["collapsed_uv_faces"],0)
        self.assertFalse(result["visual"]["sampling_used"])
        self.assertTrue((output/"views/contact_sheet.png").exists())
        self.assertEqual(len(list((output/"views").glob("orbit_*.png"))),14)
        self.assertEqual(len(list((output/"views").glob("mask_*.png"))),14)
        saved=json.loads((output/"vq_model_report.json").read_text())
        self.assertEqual(saved["source_sha256"],result["source_sha256"])

    def test_missing_reference_never_assumes_likeness(self):
        report=inspect(self.obj,self.root/"check",render_faces=1)
        self.assertIsNone(report["reference_comparison"])
        self.assertFalse(report["reference_likeness_verified"])
        self.assertTrue(any("No human reference" in v for v in report["manual_review_warnings"]))

    def test_mask_comparison_rejects_unsegmented_reference(self):
        from PIL import Image
        reference=self.root/"invalid.png"
        Image.new("L",(32,32),127).save(reference)
        inspect(self.obj,self.root/"proof",render_faces=1)
        with self.assertRaises(ValueError):
            compare_mask(self.root/"proof/views/mask_00.png",reference)

    def test_missing_uv_is_reported_not_faked(self):
        coords=[(0,0,0),(1,0,0),(0,1,0)]
        faces=[((0,None,None),(1,None,None),(2,None,None))]
        result=uv_evidence(coords,[],faces)
        self.assertEqual(result["uv_coverage"],0)
        self.assertEqual(result["uv_faces"],0)
        self.assertIsNone(result["p90_relative_uv_area_scale_variation"])

    def test_collapsed_uv_fails_technical_smoke(self):
        self.obj.write_text(
            "v 0 0 0\nv 1 0 0\nv 0 1 0\n"
            "vt 0 0\nvt 0 0\nvt 0 0\n"
            "f 1/1 2/2 3/3\n"
        )
        result=inspect(self.obj,self.root/"bad",render_faces=1)
        self.assertFalse(result["technical_geometry_smoke_passed"])
        self.assertEqual(result["uv"]["collapsed_uv_faces"],1)

    def test_gltf_missing_binary_is_rejected(self):
        source=self.root/"missing.gltf"
        source.write_text(json.dumps({
            "asset":{"version":"2.0"},
            "buffers":[{"uri":"not-there.bin","byteLength":100}],
            "bufferViews":[{"buffer":0,"byteOffset":0,"byteLength":100}],
            "accessors":[],
        }))
        report=check_gltf(source)
        self.assertFalse(report["structural_smoke_passed"])
        self.assertTrue(report["errors"])

    def test_gltf_path_traversal_is_rejected(self):
        source=self.root/"bad.gltf"
        source.write_text(json.dumps({
            "asset":{"version":"2.0"},
            "buffers":[{"uri":"../secret.bin","byteLength":4}],
            "bufferViews":[],"accessors":[],
        }))
        result=check_gltf(source)
        self.assertTrue(any("escapes" in e for e in result["errors"]))

    def test_render_budget_is_hard_limited(self):
        with self.assertRaises(ValueError):
            inspect(self.obj,self.root/"budget",render_faces=10001)

    def test_integrated_queue_reviewer_checks_all_14_frame_hashes(self):
        from factory import build_asset
        from preview import build_views
        import importlib.util
        directory=self.root/"veylquorin-asset"
        catalog=Path(__file__).resolve().parents[1]/"catalog.json"
        manifest=build_asset(catalog,"ancient_tree",directory)
        build_views(catalog,"ancient_tree",directory/"previews")
        result=inspect(directory/"ancient_tree.obj",
                       directory/"vq_model_inspection",
                       gltf=directory/"ancient_tree.gltf")
        self.assertTrue(result["technical_geometry_smoke_passed"])
        modpath=Path(__file__).resolve().parents[1]/"queue.py"
        spec=importlib.util.spec_from_file_location("vq_legacy_queue",modpath)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        job={"kind":"asset","asset":"ancient_tree"}
        self.assertEqual(module.evidence_ok(job,directory,"a"*40,""),[])
        artifact=directory/"vq_model_inspection/views/orbit_00_yaw_000.png"
        artifact.write_bytes(b"modified")
        self.assertTrue(any("source orbit image missing or modified" in s
                            for s in module.evidence_ok(job,directory,"a"*40,"")))


if __name__=="__main__":
    unittest.main()
