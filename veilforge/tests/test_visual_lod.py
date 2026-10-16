"""LOD screenshot comparison validation tests, independent of Pillow and ADB."""
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from visual_lod import iou,report

class VisualLODTest(unittest.TestCase):
    def test_mask_intersection_over_union(self):
        self.assertAlmostEqual(iou([True,True,False,False],
                                   [True,False,True,False]),1/3)
        self.assertEqual(iou([True,True],[True,True]),1)
        self.assertEqual(iou([False,False],[False,False]),0)
    def test_mismatched_masks_rejected(self):
        with self.assertRaises(ValueError):
            iou([True,False],[True])
    def test_missing_real_device_screenshots_do_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                report(Path(tmp)/"nonexistent",Path(tmp)/"out")
if __name__=="__main__":
    unittest.main()
