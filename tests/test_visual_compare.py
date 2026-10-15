import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from inspector.visual_compare import compare

class VisualCompareTests(unittest.TestCase):
    def test_identical_screens(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            Image.new("RGB", (200, 200), "black").save(root / "a.png")
            Image.new("RGB", (200, 200), "black").save(root / "b.png")
            result = compare(root / "a.png", root / "b.png", root)
            self.assertEqual(result["changed_fraction"], 0.0)
            self.assertFalse(result["meaningful_change"])
            self.assertTrue((root / "visual_difference.png").exists())
            self.assertEqual(json.loads((root / "visual_comparison.json").read_text()), result)

    def test_significant_change(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            Image.new("RGB", (200, 200), "black").save(root / "a.png")
            Image.new("RGB", (200, 200), "white").save(root / "b.png")
            result = compare(root / "a.png", root / "b.png", root)
            self.assertEqual(result["changed_fraction"], 1.0)
            self.assertTrue(result["meaningful_change"])
            self.assertEqual(result["change_bounds"], [0, 0, 200, 200])

    def test_orientation_change(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            Image.new("RGB", (200, 300), "black").save(root / "a.png")
            Image.new("RGB", (300, 200), "black").save(root / "b.png")
            result = compare(root / "a.png", root / "b.png", root)
            self.assertEqual(result["status"], "different_dimensions")
            self.assertIsNone(result["meaningful_change"])

if __name__ == "__main__":
    unittest.main()
