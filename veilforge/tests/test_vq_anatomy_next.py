"""On-demand regression checks for VQ A1. No aesthetics/Android pass implied."""
import sys,json,unittest,tempfile
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vq_anatomy_next import ShapeSpec,parse_description,sdf_body
from vq_shape_gate_next import gate,proxy_proportion_error,bounded_shape_repair
from vq_shape_learning_next import accept_reference_dataset,encode
from vq_reference_gate_next import evaluate_masks,evaluate_landmarks

class VQAnatomyTests(unittest.TestCase):
 def test_semantic_variants(self):
  s=parse_description('chibi AXOLOTL large eyes teal robe')
  self.assertEqual(s.species,'axolotl')
  self.assertGreater(s.head_ratio,.20)
  self.assertEqual(s.palette,'teal')
  self.assertEqual(s.garment,'robes')
 def test_numeric_repair(self):
  from dataclasses import replace
  bad=replace(parse_description('human'),head_ratio=.22,shoulder_ratio=.32,leg_ratio=.38)
  fixed,log=bounded_shape_repair(bad)
  self.assertLess(proxy_proportion_error(fixed),.1*proxy_proportion_error(bad))
  self.assertGreater(len(log),0)
 def test_invalid_spec_fails(self):
  from dataclasses import replace
  with self.assertRaises(ValueError):replace(parse_description('elf'),leg_ratio=.98).validate()
 def test_connected_raw_sdf(self):
  import trimesh
  for prompt in ('human long legs','axolotl chibi large eyes','orc muscular'):
   sp=parse_description(prompt)
   v,f,_,meta=sdf_body(sp,voxel=.028)
   mesh=trimesh.Trimesh(vertices=v,faces=f,process=False)
   self.assertTrue(mesh.is_watertight,prompt)
   self.assertEqual(len(mesh.split()),1,prompt)
   self.assertTrue(np.isfinite(v).all())
 def test_visual_gate_requires_real_evidence(self):
  res=gate({'technical_pass':True})
  self.assertFalse(res['game_ready']);self.assertEqual(res['status'],'REVIEW_REQUIRED')
  self.assertIn('visual_reference',res['failures'])
 def test_reference_rights_required(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'rights.json';p.write_text('{"examples":[]}')
   with self.assertRaises(ValueError):accept_reference_dataset(p)
 def test_mask_iou(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);a=np.zeros((100,100),np.uint8);b=np.zeros_like(a)
   a[10:60,10:60]=255;b[10:60,10:60]=255
   Image.fromarray(a).save(p/'a.png');Image.fromarray(b).save(p/'b.png')
   self.assertAlmostEqual(evaluate_masks(p/'a.png',p/'b.png')['silhouette_iou'],1)
 def test_landmarks(self):
  src={str(i):[i*.1,0,0] for i in range(9)}
  r=evaluate_landmarks(src,src,scale_m=1)
  self.assertEqual(r['landmark_mean_error_norm'],0)
 def test_synthetic_input_dimensions(self):
  self.assertEqual(len(encode('feline large eyes chibi')),15)

if __name__=='__main__':unittest.main()