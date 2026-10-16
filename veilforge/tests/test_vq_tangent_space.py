"""Adversarial tangent VEC4 basis tests, independent of Android screenshots."""
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vq_tangent_space import generate_tangents, triangle_handedness

class TangentSpaceTest(unittest.TestCase):
    def test_flat_quad_tangent_and_gltf_handedness(self):
        pos=[0,0,0, 1,0,0, 1,1,0, 0,1,0]
        normals=[0,0,1]*4
        uv=[0,0, 1,0, 1,1, 0,1]
        tangents=generate_tangents(pos,normals,uv,[0,1,2, 0,2,3])
        self.assertEqual(len(tangents),16)
        for i in range(4):
            t=tangents[4*i:4*i+4]
            for a,b in zip(t,[1,0,0,1]):
                self.assertAlmostEqual(a,b,places=6)
    def test_mirrored_uv_reverses_bitangent(self):
        p=[0,0,0, 1,0,0, 0,1,0]
        a=generate_tangents(p,[0,0,1]*3,[0,0, 1,0, 0,1],[0,1,2])
        b=generate_tangents(p,[0,0,1]*3,[0,0, 0,1, 1,0],[0,1,2])
        self.assertEqual(a[3],1.)
        self.assertEqual(b[3],-1.)
        for tangents in (a,b):
            for i in range(3):
                t=tangents[i*4:i*4+3]
                self.assertAlmostEqual(sum(x*x for x in t),1,places=6)
                self.assertAlmostEqual(t[2],0,places=6)
    def test_reject_shared_mirrored_vertex(self):
        pos=[0,0,0, 1,0,0, 1,1,0, 0,1,0]
        with self.assertRaisesRegex(ValueError,"Mirrored UV seam"):
            generate_tangents(pos,[0,0,1]*4,[0,0, 1,0, 1,1, 1,0],
                              [0,1,2, 0,2,3])
    def test_fail_closed_malformed_inputs(self):
        p=[0,0,0,1,0,0,0,1,0];n=[0,0,1]*3;uv=[0,0,1,0,0,1]
        for invalid in ([0,0,0,0,0,0],[0,0,1,0,2,0]):
            with self.assertRaisesRegex(ValueError,"UV"):
                generate_tangents(p,n,invalid,[0,1,2])
        with self.assertRaisesRegex(ValueError,"Nonfinite"):
            generate_tangents([math.nan,*p[1:]],n,uv,[0,1,2])
        with self.assertRaisesRegex(ValueError,"bounds"):
            generate_tangents(p,n,uv,[0,1,3])
        with self.assertRaisesRegex(ValueError,"Degenerate"):
            generate_tangents(p,[0,0,0]*3,uv,[0,1,2])
        with self.assertRaisesRegex(ValueError,"Inconsistent"):
            generate_tangents(p,[0,0,-1]*3,uv,[0,1,2])
        with self.assertRaisesRegex(ValueError,"Collapsed geometry"):
            triangle_handedness([(0,0,0)]*3,[(0,0),(1,0),(0,1)])

if __name__ == "__main__":
    unittest.main()
