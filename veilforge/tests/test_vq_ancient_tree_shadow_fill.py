"""Bounded source contract for the QA-only ancient_tree shadow-fill experiment.

Static tests are not Android screenshot evidence. Full factory validation remains mandatory.
"""
from pathlib import Path
import unittest

RENDERER=(Path(__file__).resolve().parents[1]/"android-probe/app/src/main/java/game/veilforge/probe/ViewerActivity.java")

class AncientTreeShadowFillContract(unittest.TestCase):
    def test_tree_only_lighting_override(self):
        src=RENDERER.read_text(encoding="utf-8")
        self.assertIn('GLES20.glUniform1f(uAmbientFloor,"ancient_tree".equals(filter)?0.38f:0.22f);',src)
        self.assertIn('uAmbientFloor=GLES20.glGetUniformLocation(program,"uAmbientFloor");',src)
        self.assertIn('uniform float uAmbientFloor;',src)
        self.assertIn('uAmbientFloor+(1.0-uAmbientFloor)*diffuse',src)
        self.assertNotIn('0.22+0.78*diffuse',src)

    def test_diffuse_endpoint_and_shadow_change(self):
        # The exact algebra embedded in the shader: no direct-light peak change.
        def response(floor,diffuse):
            return floor+(1.0-floor)*diffuse
        for diffuse in (0.0,0.25,0.5,0.75,1.0):
            self.assertGreaterEqual(response(.38,diffuse),response(.22,diffuse))
        self.assertAlmostEqual(response(.38,1),response(.22,1))
        self.assertAlmostEqual(response(.38,0)-response(.22,0),.16)

if __name__=="__main__": unittest.main()
