"""Bellwarden QA camera AABB envelope; not a subjective image-quality test.
POSITION extrema and node translation from Android APK artifact 12100688273,
run 39032474382, source 790b813bf8984eed3cc45f7fa140f2b861cab37a.
"""
import itertools
import math
import unittest
from pathlib import Path

VIEWER=Path(__file__).resolve().parents[1]/"android-probe/app/src/main/java/game/veilforge/probe/ViewerActivity.java"
LO=(-0.8535,0.04,-0.815)
HI=(0.8535,2.85,0.602)
POS=(1.18,0.25,-0.25)
ASPECT=2280/1080

def dot(a,b):
    return sum(x*y for x,y in zip(a,b))

def envelope(distance):
    mid=tuple((a+b)/2+p for a,b,p in zip(LO,HI,POS))
    corners=[tuple(v[i]+POS[i] for i in range(3))
             for v in itertools.product(*zip(LO,HI))]
    nearest,top,side=float("inf"),0.,0.
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

class BellwardenCameraFitTests(unittest.TestCase):
    def test_one_asset_only_and_older_camera_rules_intact(self):
        src=VIEWER.read_text()
        self.assertEqual(src.count('if("bellwarden_full_anatomy_repaired".equals(filter))'),1)
        self.assertIn('eyeRadius=Math.max(3.0f,radius*2.22f+1.13f);',src)
        self.assertIn('float eyeRadius=Math.max(3.0f,radius*2.35f+1.2f);',src)
        for name in ('ancient_tree','ceremonial_sword','forest_tree_mobile','human_repaired'):
            self.assertEqual(src.count('if("'+name+'".equals(filter))'),1)

    def test_fourteen_view_conservative_near_and_crop_margin(self):
        radius=max((b-a)/2 for a,b in zip(LO,HI))
        generic=max(3.,radius*2.35+1.2)
        fitted=max(3.,radius*2.22+1.13)
        rejected=max(3.,radius*2.10+1.0)
        self.assertAlmostEqual(generic,4.50175,places=5)
        self.assertAlmostEqual(fitted,4.24910,places=5)
        base=envelope(generic)
        near,vertical,horizontal=envelope(fitted)
        self.assertGreater(near,2.48)
        self.assertLess(vertical,.94)
        self.assertLess(horizontal,.35)
        self.assertGreater(vertical,base[1]*1.06)
        self.assertGreater(envelope(rejected)[1],1.0)

if __name__=="__main__":
    unittest.main()
