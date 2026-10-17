"""Conservative 14-angle sword camera projection regression (not Android evidence)."""
import itertools
import math
import unittest
from pathlib import Path

VIEWER = Path(__file__).resolve().parents[1] / "android-probe/app/src/main/java/game/veilforge/probe/ViewerActivity.java"
# Pinned glTF POSITION bounds and sword_drop instance, run 38993296206.
LO = (-.5619999766, -.8999999762, -.1141267791)
HI = (.5619999766, 2.7799999714, .1141267791)
POS = (.2, 1., -.2)
QY, QW = .6626200482, .7489557208
SCALE = .5


def projection(distance, center, points):
    max_x = max_y = 0.
    min_depth = float("inf")
    min_span = float("inf")
    for i, yaw in enumerate(range(0, 350, 25)):
        yr, pr = math.radians(yaw), math.radians((15, 25, 42)[i % 3])
        s, c = math.sin(yr), math.cos(yr)
        sp, cp = math.sin(pr), math.cos(pr)
        outward = (s * cp, sp, c * cp)
        right = (c, 0, -s)
        up = (-s * sp, cp, -c * sp)
        eye = [center[k] + distance * outward[k] for k in range(3)]
        ys = []
        for p in points:
            v = [p[k] - eye[k] for k in range(3)]
            depth = -sum(v[k] * outward[k] for k in range(3))
            min_depth = min(min_depth, depth)
            x = 2 * sum(v[k] * right[k] for k in range(3)) / depth / (2340 / 1080)
            y = 2 * sum(v[k] * up[k] for k in range(3)) / depth
            max_x, max_y = max(max_x, abs(x)), max(max_y, abs(y))
            ys.append(y)
        min_span = min(min_span, max(ys) - min(ys))
    return max_x, max_y, min_depth, min_span


class SwordCameraFitTests(unittest.TestCase):
    def test_scoped_camera_only(self):
        source = VIEWER.read_text(encoding="utf-8")
        self.assertIn('float eyeRadius=Math.max(3.0f,radius*2.35f+1.2f);', source)
        self.assertIn('if("ancient_tree".equals(filter))', source)
        self.assertEqual(source.count('if("ceremonial_sword".equals(filter))'), 1)
        self.assertIn('eyeRadius=Math.max(3.0f,radius*1.75f+0.9f);', source)

    def test_pinned_bounds_all_fourteen_views(self):
        theta = 2 * math.atan2(QY, QW)
        cs, sn = math.cos(theta), math.sin(theta)
        def rot(p):
            return (cs * p[0] + sn * p[2], p[1], -sn * p[0] + cs * p[2])
        local = [(a + b) / 2 for a, b in zip(LO, HI)]
        half = [(b - a) / 2 for a, b in zip(LO, HI)]
        center = [POS[k] + SCALE * rot(local)[k] for k in range(3)]
        radius = math.sqrt(sum(x * x for x in half)) * SCALE
        points = [tuple(POS[k] + SCALE * rot(p)[k] for k in range(3))
                  for p in itertools.product(*zip(LO, HI))]
        before = projection(max(3., radius * 2.35 + 1.2), center, points)
        after = projection(max(3., radius * 1.75 + .9), center, points)
        self.assertGreater(after[2], 2.15)  # GLES near=2.0
        self.assertLess(max(after[:2]), .85)
        self.assertGreater(after[3], before[3] * 1.10)
        self.assertLess(projection(2.7, center, points)[2], 2.0)  # rejected


if __name__ == "__main__":
    unittest.main()
