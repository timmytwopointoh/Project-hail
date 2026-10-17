"""Pinned forest-tree camera regression: analytic geometry, not artistic QA."""
import itertools
import math
import unittest
from pathlib import Path

VIEWER = (Path(__file__).resolve().parents[1] / "android-probe/app/src/main/java/game/veilforge/probe/ViewerActivity.java")
# Source: real glTF POSITION extrema, scene artifact 12096891296.
BOUNDS = [
    ((-1.1079420485481999, 0., -0.8867876469651536),
     (1.2152131859403823, 3.136731550585762, 0.9324150310508768)),
    ((-1.469374111055436, 0.9692801907969715, -1.199460924430988),
     (1.6045008014866937, 3.8158961874720174, 1.238379288099268)),
]


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


class ForestTreeCameraFitTests(unittest.TestCase):
    def test_asset_specific_override_preserves_other_cameras(self):
        source = VIEWER.read_text(encoding="utf-8")
        self.assertEqual(source.count('if("forest_tree_mobile".equals(filter))'), 1)
        self.assertIn("eyeRadius=Math.max(3.0f,radius*1.95f+0.9f);", source)
        self.assertIn("float eyeRadius=Math.max(3.0f,radius*2.35f+1.2f);", source)
        self.assertIn('if("ancient_tree".equals(filter))', source)
        self.assertIn('if("ceremonial_sword".equals(filter))', source)

    def test_pinned_fourteen_view_near_plane_and_frame_margin(self):
        low = [min(b[0][i] for b in BOUNDS) for i in range(3)]
        high = [max(b[1][i] for b in BOUNDS) for i in range(3)]
        middle = [(low[i]+high[i])/2 for i in range(3)]
        half = [(high[i]-low[i])/2 for i in range(3)]
        radius = math.sqrt(dot(half, half))*.8
        co, si = math.cos(math.radians(114)), math.sin(math.radians(114))

        def rotate(p):
            return (co*p[0]+si*p[2], p[1], -si*p[0]+co*p[2])

        pos = (-2.6, 0., 3.5)
        center = tuple(pos[i]+.8*rotate(middle)[i] for i in range(3))
        points = [tuple(pos[i]+.8*rotate(p)[i] for i in range(3))
                  for a, b in BOUNDS for p in itertools.product(*zip(a, b))]
        generic = max(3., radius*2.35+1.2)
        fitted = max(3., radius*1.95+.9)
        self.assertAlmostEqual(generic, 6.34454, places=4)
        self.assertAlmostEqual(fitted, 5.16888, places=4)
        max_y, max_x, nearest = 0., 0., float("inf")
        for index, yaw in enumerate(range(0, 350, 25)):
            pitch = (15, 25, 42)[index%3]
            y, p = math.radians(yaw), math.radians(pitch)
            s, c, sp, cp = math.sin(y), math.cos(y), math.sin(p), math.cos(p)
            outward = (s*cp, sp, c*cp)
            forward = tuple(-v for v in outward)
            right, up = (c, 0., -s), (-s*sp, cp, -c*sp)
            eye = tuple(center[i]+fitted*outward[i] for i in range(3))
            for point in points:
                delta = tuple(point[i]-eye[i] for i in range(3))
                depth = dot(delta, forward)
                nearest = min(nearest, depth)
                self.assertGreater(depth, 2.)  # GLES near plane
                max_y = max(max_y, abs(2*dot(delta, up)/depth))
                max_x = max(max_x, abs(2*dot(delta, right)/depth/(2400/1080)))
        self.assertGreater(nearest, 3.)
        self.assertLess(max_y, .90)
        self.assertLess(max_x, .90)


if __name__ == "__main__":
    unittest.main()
