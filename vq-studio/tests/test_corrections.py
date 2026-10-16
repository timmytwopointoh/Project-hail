"""Corrected generation is isolated, deterministic and never modifies source recipes."""
import json
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from corrections import write_adjusted

CATALOG=Path(__file__).resolve().parents[2]/"veilforge/catalog.json"

class VQCorrectionsTest(unittest.TestCase):
    def test_scale_adjustment_produces_distinct_safe_immutable_catalog(self):
        initial=CATALOG.read_bytes()
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            variants={}
            for adjustment in ("smaller","original","larger"):
                target=root/(adjustment+".json")
                result=write_adjusted(CATALOG,"ancient_tree",adjustment,target)
                generated=json.loads(target.read_text())
                obj=next(a for a in generated["assets"] if a["id"]=="ancient_tree")
                self.assertFalse(result["production_approved"])
                self.assertEqual(obj["scale"],result["source_scale"])
                variants[adjustment]=result["source_scale"]
            self.assertLess(variants["smaller"],variants["original"])
            self.assertLess(variants["original"],variants["larger"])
        self.assertEqual(CATALOG.read_bytes(),initial)
    def test_public_dispatch_cannot_inject_arbitrary_parameters(self):
        with tempfile.TemporaryDirectory() as td:
            for value in ("../../payload","execute","",None):
                with self.assertRaises(ValueError):
                    write_adjusted(CATALOG,"ancient_tree",value,Path(td)/"bad.json")
            with self.assertRaises(ValueError):
                write_adjusted(CATALOG,"../secret","original",Path(td)/"bad.json")
    def test_legacy_model_scale_is_applied_relatively(self):
        with tempfile.TemporaryDirectory() as td:
            r=write_adjusted(CATALOG,"forest_tree_mobile","smaller",Path(td)/"mobile.json")
            self.assertAlmostEqual(r["source_scale"],0.7225)
    def test_original_catalog_cannot_be_replaced_implicitly(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            catalog=root/"bad.json";catalog.write_text("{}")
            with self.assertRaises(ValueError):
                write_adjusted(catalog,"ancient_tree","larger",root/"out.json")

if __name__=="__main__":unittest.main()
