"""Pinned human camera regression; geometric predictions, not artistic QA.
POSITION extrema from Android APK artifact 12098503295, run 39026251267.
"""
import itertools
import math
import unittest
from pathlib import Path

VIEWER = Path(__file__).resolve().parents[1]/"android-probe/app/src/main/java/game/veilforge/probe/ViewerActivity.java"
LO = (-0.740716, 0.006797, -0.253948)
HI = (0.743298, 2.636725, 0.442893)
POS = (-1.05, 0.35, -0.2)
ASPECT = 2280/1080


def dot(a,b):
    return sum(x*y for x,y in zip(a,b))


def envelope(distance):
    mid = tuple((a+b)/2+p for a,b,p in zip(LO,HI,POS))
    corners = [tuple(v[i]+POS[i] for i in range(3))
               for v in itertools.product(*zip(LO,HI))]
    nearest, top, side = float("inf"), 0., 0.
    for k,yaw in enumerate(range(0,350,25)):
        pitch=(15,25,42)[k%3]
        y,p=math.radians(yaw),math.radians(pitch)
        s,c,sp,cp=math.sin(y),math.cos(y),math.sin(p),math.cos(p)
        outward=(s*cp,sp,c*cp)
        up=(-s*sp,cp,-c*sp)
        right=(c,0.,-s)
        eye=tuple(mid[i]+distance*outward[i] for i in range(3))
        for point in corners:
            delta=tuple(point[i]-eye[i] for i in range(3))
            depth=-dot(delta,outward)
            nearest=min(nearest,depth)
            top=max(top,abs(2*dot(delta,up)/depth))
            side=max(side,abs(2*dot(delta,right)/depth/ASPECT))
    return nearest,top,side


class HumanCameraFitTests(unittest.TestCase):
    def test_one_asset_only_and_prior_camera_paths_intact(self):
        src=VIEWER.read_text()
        self.assertEqual(src.count('if("human_repaired".equals(filter))'),1)
        self.assertIn('eyeRadius=Math.max(3.0f,radius*1.85f+0.9f);',src)
        self.assertIn('float eyeRadius=Math.max(3.0f,radius*2.35f+1.2f);',src)
        for name in ('ancient_tree','ceremonial_sword','forest_tree_mobile'):
            self.assertEqual(src.count('if("'+name+'".equals(filter))'),1)

    def test_fourteen_view_near_plane_and_conservative_frame_margin(self):
        half=tuple((b-a)/2 for a,b in zip(LO,HI))
        radius=math.sqrt(dot(half,half))
        generic=max(3.,radius*2.35+1.2)
        fitted=max(3.,radius*1.85+.9)
        rejected=max(3.,radius*1.65+.9)
        self.assertAlmostEqual(generic,4.84144,places=4)
        self.assertAlmostEqual(fitted,3.76667,places=4)
        baseline=envelope(generic)
        near,y,x=envelope(fitted)
        self.assertGreater(near,2.25)
        self.assertLess(y,.90)
        self.assertLess(x,.30)
        self.assertGreater(y,baseline[1]*1.30)
        self.assertLess(envelope(rejected)[0],2.0)


if __name__=="__main__":
    unittest.main()
