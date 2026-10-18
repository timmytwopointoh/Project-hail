"""H21: low color-mask coverage must not be mistaken for a missing mesh."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from visual_semantics import outline_analysis,visibility_evidence


def sample(coverage=.01,width=.12,height=.35):
    return {"coverage":coverage,"bbox_width":width,"bbox_height":height}


class VisibilityEvidenceTest(unittest.TestCase):
    def test_bbox_is_measured_from_actual_binary_pixels(self):
        mask=[False]*400
        for y in range(3,17):
            for x in range(8,11):
                mask[y*20+x]=True
        metric=outline_analysis(mask,20,20)
        self.assertAlmostEqual(metric["bbox_width"],.15)
        self.assertAlmostEqual(metric["bbox_height"],.70)
        self.assertEqual(outline_analysis([False]*400,20,20)["bbox_height"],0)

    def test_tall_broadside_plus_narrow_edge_on_is_review_not_missing_geometry(self):
        frames=[sample() for _ in range(14)]
        frames[0]=sample(.0015,.031,.12)
        frames[10]=sample(.0254,.125,.885)
        row=visibility_evidence(frames)
        self.assertEqual(row["interpretation"],"possible_edge_on_view")
        self.assertEqual((row["lowest_view_yaw"],row["lowest_view_pitch"]),(0,15))
        self.assertEqual((row["strongest_view_yaw"],row["strongest_view_pitch"]),(250,25))
        self.assertFalse(row["interpretation_is_artistic_approval"])

    def test_tall_but_low_mask_occupancy_flags_contrast_uncertainty(self):
        frames=[sample() for _ in range(14)]
        frames[9]=sample(.0033,.12,.604)
        frames[1]=sample(.0428,.146,.630)
        row=visibility_evidence(frames)
        self.assertEqual(row["interpretation"],"low_color_contrast_or_thin_geometry")
        self.assertEqual(row["lowest_view_index"],9)

    def test_small_views_stay_open_for_camera_review(self):
        frames=[sample(.012,.13,.25) for _ in range(14)]
        frames[0]=sample(.002,.04,.10)
        frames[10]=sample(.034,.20,.38)
        row=visibility_evidence(frames)
        self.assertEqual(row["interpretation"],"framing_or_visibility_review")

    def test_missing_measurements_fail_closed(self):
        with self.assertRaises(ValueError):visibility_evidence([])


if __name__=="__main__":
    unittest.main()
