"""A3 actual distal geometry and semantic landmarks, not artistic sign-off."""
import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vq_distal_anatomy import RECIPE,hand_landmarks,foot_landmarks
from vq_anatomy_next import parse_description,sdf_body

class DistalAnatomyTests(unittest.TestCase):
    def test_anatomic_digit_count(self):
        self.assertEqual(RECIPE.fingers+RECIPE.thumbs,5)
        self.assertEqual(RECIPE.toes,5)
    def test_distinct_bilateral_hands(self):
        for sign in (-1,1):
            palm,fingers,thumb=hand_landmarks((sign*.65,1.3,0),sign,1.72)
            self.assertEqual(len(fingers),4)
            self.assertEqual(len({round(b[1][1],5) for b in fingers}),4)
            lengths=[abs(b[1][0]-b[0][0]) for b in fingers]
            self.assertGreater(lengths[1],lengths[0])
            self.assertGreater(lengths[2],lengths[3])
            self.assertLess(thumb[1][1],palm[1])
    def test_distinct_bilateral_toes(self):
        for sign in (-1,1):
            ball,toes=foot_landmarks((sign*.19,.16,0),sign,1.72)
            self.assertEqual(len(toes),5)
            self.assertEqual(len({round(b[1][0],5) for b in toes}),5)
            self.assertLess(toes[0][1][2],toes[-1][1][2])
    def test_watertight_character_and_actual_tip_positions(self):
        import trimesh
        from scipy.spatial import cKDTree
        spec=parse_description('human slender long legs teal')
        v,f,_,land=sdf_body(spec,voxel=.016)
        mesh=trimesh.Trimesh(vertices=v,faces=f,process=False)
        self.assertTrue(mesh.is_watertight)
        self.assertEqual(len(mesh.split(only_watertight=False)),1)
        tree=cKDTree(v)
        for item in land['distal_landmarks']['hands']:
            for tip in item['finger_tips']+[item['thumb_tip']]:
                self.assertLess(tree.query(tip)[0],.032*spec.height)
        for item in land['distal_landmarks']['feet']:
            for tip in item['toe_tips']:
                self.assertLess(tree.query(tip)[0],.026*spec.height)

if __name__=='__main__':unittest.main()