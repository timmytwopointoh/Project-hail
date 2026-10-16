"""Semantic frame QA only trusts real screenshot provenance and a complete role set."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from visual_semantics import iou,outline_analysis,diagnose

class SemanticVisualTest(unittest.TestCase):
    def test_binary_silhouette_metrics(self):
        mask=[False]*100
        for y in range(2,8):
            for x in range(2,8):mask[y*10+x]=True
        result=outline_analysis(mask,10,10)
        self.assertAlmostEqual(result["coverage"],.36)
        self.assertGreater(result["edge_crossings"],0)
        self.assertEqual(iou(mask,mask),1)
        self.assertEqual(iou(mask,[False]*100),0)
    def test_reject_mismatched_sizes(self):
        with self.assertRaises(ValueError):iou([True],[True,False])
    def test_no_emulator_evidence_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=diagnose(Path(tmp)/"missing",Path(tmp)/"out")
            self.assertFalse(r["technical_gate_passed"])
            self.assertEqual(r["frames_scanned"],0)
            self.assertFalse(r["photorealism_verified"])
            self.assertGreater(len(r["repair_queue"]),4)
    def test_duplicate_and_fake_report_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/"veilforge-android-characters"
            p.mkdir()
            data={"role":"characters","assets":[{"asset":"human_repaired","views":[]}]}
            (p/"emulator_visual_qa.json").write_text(json.dumps(data))
            r=diagnose(root,root/"out")
            self.assertFalse(r["technical_gate_passed"])
            self.assertTrue(any("incomplete" in t for t in r["problems"]))
if __name__=="__main__":unittest.main()
