"""Pinned scene-envelope regression for one Android-probe camera change.

This is an analytical check against the two-tree scene geometry captured in
run 38993296206, NOT a substitute for 14 real-angle Android screenshots.
"""
import itertools
import math
import re
import unittest
from pathlib import Path


SOURCE = (Path(__file__).resolve().parents[1] / "android-probe/app/src/main/java/game/veilforge/probe/ViewerActivity.java")
# Primitive POSITION bounds and scene instances from the pinned assembled glTF.
BOUNDS = [
    ((-0.9575807065, 0.0, -0.9462904603), (1.4219551315, 3.8570304185, 1.1839416727)),
    ((-1.4313024812, 1.2368805805, -1.3299661389), (1.9009533326, 4.6620138902, 1.5668485184)),
]
INSTANCES = [
    ((-3.7, 0.0, -1.6), 0.1478094111, 0.9890158634, 1.0),
    ((3.8, 0.0, -1.2), -0.2672383761, 0.9636304532, 0.85),
]


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


class AncientTreeCameraFitTests(unittest.TestCase):
    def test_scoped_camera_override_and_generic_fallback(self):
        src = SOURCE.read_text(encoding="utf-8")
        self.assertIn("float eyeRadius=Math.max(3.0f,radius*2.35f+1.2f);", src)
        self.assertIn('if("ancient_tree".equals(filter))', src)
        self.assertEqual(src.count('if("ancient_tree".equals(filter))'), 1)
        self.assertIn("eyeRadius=Math.max(3.0f,radius*1.95f+0.9f);", src)

    def test_all_fourteen_pinned_tree_views_keep_projection_margin(self):
        # Replicate the renderer's conservative per-instance radius and
        # projection using glTF bounds, not subjective pixel heuristics.
        points, low, high = [], [float("inf")]*3, [float("-inf")]*3
        local_min = [min(b[0][i] for b in BOUNDS) for i in range(3)]
        local_max = [max(b[1][i] for b in BOUNDS) for i in range(3)]
        local_mid = [(a+b)/2 for a,b in zip(local_min,local_max)]
        half = [(b-a)/2 for a,b in zip(local_min,local_max)]
        for pos, qy, qw, scale in INSTANCES:
            theta = 2*math.atan2(qy, qw)
            co, si = math.cos(theta), math.sin(theta)
            def rotate(p):
                return (co*p[0]+si*p[2], p[1], -si*p[0]+co*p[2])
            center = [pos[i]+scale*rotate(local_mid)[i] for i in range(3)]
            r = math.sqrt(dot(half,half))*scale
            for i in range(3):
                low[i] = min(low[i], center[i]-r)
                high[i] = max(high[i], center[i]+r)
            for a,b in BOUNDS:
                for p in itertools.product(*zip(a,b)):
                    rp = rotate(p)
                    points.append(tuple(pos[i]+scale*rp[i] for i in range(3)))
        mid = [(a+b)/2 for a,b in zip(low,high)]
        radius = max(0.1,*[(b-a)/2 for a,b in zip(low,high)])
        distance = max(3.0, radius*1.95+0.9)
        self.assertLess(distance, max(3.0,radius*2.35+1.2))
        max_vertical = max_horizontal = 0.0
        for i,yaw in enumerate(range(0,350,25)):
            pitch = (15,25,42)[i%3]
            yr,pr = math.radians(yaw),math.radians(pitch)
            s,c = math.sin(yr),math.cos(yr)
            sp,cp = math.sin(pr),math.cos(pr)
            outward = (s*cp,sp,c*cp)
            forward = tuple(-x for x in outward)
            right = (c,0.0,-s)
            up = (-s*sp,cp,-c*sp)
            eye = [mid[k]+distance*outward[k] for k in range(3)]
            for point in points:
                v = [point[k]-eye[k] for k in range(3)]
                depth = dot(v,forward)
                self.assertGreater(depth,2.0)  # near plane
                max_horizontal = max(max_horizontal,abs(dot(v,right)*2/(depth*(2400/1080))))
                max_vertical = max(max_vertical,abs(dot(v,up)*2/depth))
        self.assertLess(max_horizontal,0.90)
        self.assertLess(max_vertical,0.90)


if __name__ == "__main__":
    unittest.main()
