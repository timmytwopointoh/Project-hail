"""M34: efficiency improvements cannot silently remove real emulator QA gates."""
from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vq_emulator_efficiency import audit

ROOT=Path(__file__).resolve().parents[2]

class EmulatorEfficiencyTest(unittest.TestCase):
    def test_shared_emulator_apk_and_both_real_visual_algorithms(self):
        row=audit(ROOT)
        self.assertTrue(row["static_gate_passed"],row["problems"])
        self.assertEqual(row["emulator_roles_expected"],4)
        self.assertEqual(row["max_parallel_emulators_configured"],4)
        self.assertEqual(row["per_asset_angles_expected"],14)
        self.assertEqual(row["reviewer_job_count"],1)
        self.assertEqual(len(row["independent_algorithms_required"]),2)
        self.assertFalse(row["runtime_speedup_measured"])
        self.assertFalse(row["production_artistic_approval"])
    def test_missing_independent_semantic_review_must_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for p in (
                ".github/workflows/veilforge-factory.yml",
                "veilforge/android_visual_qa.py",
                "veilforge/vq_m30_android_qa.py"
            ):
                output=root/p;output.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/p,output)
            source=root/".github/workflows/veilforge-factory.yml"
            data=source.read_text().replace("python3 veilforge/visual_semantics.py",
                                           "python3 veilforge/bogus_visual.py")
            source.write_text(data)
            issues=audit(root)["problems"]
            self.assertTrue(any("Missing reviewer" in s for s in issues))
    def test_serial_three_emulator_wave_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for p in (
                ".github/workflows/veilforge-factory.yml",
                "veilforge/android_visual_qa.py",
                "veilforge/vq_m30_android_qa.py"
            ):
                output=root/p;output.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/p,output)
            path=root/".github/workflows/veilforge-factory.yml"
            path.write_text(path.read_text().replace("max-parallel: 4",
                                                     "max-parallel: 3"))
            self.assertFalse(audit(root)["static_gate_passed"])
    def test_multistage_milestone_map_requires_real_runtime_evidence(self):
        plan=json.loads((ROOT/"veilforge/VQ_M34_EFFICIENCY_MAP.json").read_text())
        ids=[m["id"] for m in plan["milestones"]]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertGreaterEqual(len(ids),12)
        self.assertIn("M34-09",ids)
        self.assertFalse(plan["success_requirements"]["artistic_approval"])
        self.assertFalse(plan["success_requirements"]["game_source_modification"])
        self.assertTrue(any(m["status"]=="planned" for m in plan["milestones"]))
if __name__=="__main__":unittest.main()
