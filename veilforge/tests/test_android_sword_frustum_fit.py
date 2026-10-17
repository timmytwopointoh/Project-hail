"""Pinned conservative sword QA frustum regression; geometry math is NOT Android QA."""
import itertools
import math
import unittest
from pathlib import Path

VIEWER = Path(__file__).resolve().parents[1] / "android-probe/app/src/main/java/game/veilforge/probe/ViewerActivity.java"
LOW = (-0.562, -0.9, -0.11412678)
HIGH = (0.562, 2.78, 0.11412678)
POSITION = (0.2, 1.0, -0.2)
SCALE = 0.5
QY, QW = 0.6626200482157375, 0.7489557207890022
ASPECT = 2340.0 / 1080.0


class SwordFrustumRegression(unittest.TestCase):
    def test_asset_scoped_camera_does_not_change_generic_or_tree(self):
        src = VIEWER.read_text(encoding="utf-8")
        self.assertIn('if ("ancient_tree".equals(filter)) {\n                frustumScale=0.75f;', src)
        self.assertIn('} else if ("ceremonial_sword".equals(filter)) {\n                frustumScale=0.65f;', src)
        self.assertIn('} else {\n                frustumScale=1.0f;', src)
        self.assertIn('float eyeRadius=Math.max(3.0f,radius*2.35f+1.2f);', src)
        self.assertIn('Matrix.frustumM(projection,0,-ratio*frustumScale,ratio*frustumScale,', src)

    def test_all_fourteen_camera_angles_keep_bounding_corners_inside_frustum(self):
        theta = 2 * math.atan2(QY, QW)
        co, si = math.cos(theta), math.sin(theta)
        def rot(p):
            return (co*p[0] + si*p[2], p[1], -si*p[0] + co*p[2])
        local_center = tuple((a+b)/2 for a,b in zip(LOW,HIGH))
        half = tuple((b-a)/2 for a,b in zip(LOW,HIGH))
        radius = math.sqrt(sum(x*x for x in half))*SCALE
        center = tuple(POSITION[k]+SCALE*rot(local_center)[k] for k in range(3))
        distance = max(3.0, radius*2.35+1.2)
        corners = [tuple(POSITION[k]+SCALE*rot(p)[k] for k in range(3))
                   for p in itertools.product(*zip(LOW,HIGH))]
        max_x=max_y=0.0
        min_depth=float("inf")
        for i,yaw_deg in enumerate(range(0,350,25)):
            yaw=math.radians(yaw_deg)
            pitch=math.radians((15,25,42)[i%3])
            outward=(math.sin(yaw)*math.cos(pitch),math.sin(pitch),
                     math.cos(yaw)*math.cos(pitch))
            right=(math.cos(yaw),0,-math.sin(yaw))
            up=(-math.sin(yaw)*math.sin(pitch),math.cos(pitch),
                -math.cos(yaw)*math.sin(pitch))
            eye=tuple(center[k]+distance*outward[k] for k in range(3))
            for p in corners:
                v=tuple(p[k]-eye[k] for k in range(3))
                depth=-sum(v[k]*outward[k] for k in range(3))
                min_depth=min(min_depth,depth)
                x=2*sum(v[k]*right[k] for k in range(3))/depth/ASPECT/.65
                y=2*sum(v[k]*up[k] for k in range(3))/depth/.65
                max_x=max(max_x,abs(x));max_y=max(max_y,abs(y))
        self.assertLess(max_x,0.15)
        self.assertLess(max_y,0.89)
        self.assertGreater(min_depth,2.6)  # near plane is 2.0


if __name__ == "__main__":
    unittest.main()
