"""VQ M30 cleanup is additive, parse-checked and does not delete working tools."""
import json
from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vq_engine_health import audit,REQUIRED
ROOT=Path(__file__).resolve().parents[2]
class SourceAuditTests(unittest.TestCase):
    def test_explicit_engine_entrypoints_parse_and_remain_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=audit(ROOT,Path(tmp)/"health.json")
            self.assertTrue(result["technical_cleanup_gate_passed"])
            self.assertEqual(result["modules_checked"],len(REQUIRED))
            self.assertFalse(result["unverified_orphan_code_deleted"])
            self.assertFalse(result["existing_game_modules_deleted"])
    def test_duplicate_entrypoint_symbol_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            folder=root/"veilforge";folder.mkdir()
            workflow=root/".github/workflows";workflow.mkdir(parents=True)
            (workflow/"vq-model-tools.yml").write_text("name: safe\n")
            for n in REQUIRED:
                (folder/n).write_text("def once(): pass\n")
            target=folder/"vq_engine_health.py"
            target.write_text("def repeated(): pass\ndef repeated(): pass\n")
            result=audit(root,root/"out.json")
            self.assertFalse(result["technical_cleanup_gate_passed"])
            self.assertTrue(any("duplicate" in x for x in result["problems"]))
if __name__=="__main__":unittest.main()
