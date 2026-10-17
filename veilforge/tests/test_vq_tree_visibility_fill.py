"""Source-level regression for ancient_tree-only Android inspection fill.

The unchanged four-emulator factory must verify real GLES output; this test
only guards the intended source scope and does not certify visual quality.
"""
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "android-probe/app/src/main/java/game/veilforge/probe/ViewerActivity.java"


class TreeVisibilityFillScopeTest(unittest.TestCase):
    def test_opt_in_only_for_selected_tree(self):
        s = SOURCE.read_text(encoding="utf-8")
        self.assertIn('uniform float uTreeVisibilityFill;', s)
        self.assertIn('uTreeVisibilityFill=GLES20.glGetUniformLocation(program,"uTreeVisibilityFill");', s)
        self.assertIn('("ancient_tree".equals(filter)&&"ancient_tree".equals(item.asset))?1f:0f', s)
        self.assertEqual(s.count('GLES20.glUniform1f(uTreeVisibilityFill,'), 1)

    def test_preserves_default_lighting_and_bounded_fill(self):
        s = SOURCE.read_text(encoding="utf-8")
        self.assertIn('"float diffuseLight=0.22+0.78*diffuse;"+', s)
        self.assertIn('"float treeFill=0.65+0.35*diffuse;"+', s)
        self.assertIn('mix(diffuseLight,treeFill,uTreeVisibilityFill)', s)
        self.assertAlmostEqual(0.22 + 0.78, 1.0)
        self.assertAlmostEqual(0.65 + 0.35, 1.0)


if __name__ == "__main__":
    unittest.main()
