import sys,json,tempfile,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vq_open_anatomy_reference import original_reference,landmarks,target_mask,silhouette_score,generate_dataset
from vq_open_anatomy_learning import train

class A2References(unittest.TestCase):
 def test_multi_family_landmarks(self):
  for species in ('human','elf','orc','axolotl','feline','dwarf','automaton'):
   r=original_reference(species,seed=2)
   p=landmarks(r)
   self.assertGreaterEqual(len(p),24)
   self.assertGreater(p['left_ankle'][1],0)
   self.assertAlmostEqual(p['left_shoulder'][0],-p['right_shoulder'][0])
 def test_silhouette_camera_independence(self):
  r=original_reference('human')
  a=target_mask(r,'front',192);b=target_mask(r,'side',192)
  self.assertGreater(silhouette_score(a,a),.999)
  self.assertLess(silhouette_score(a,b),.85)
 def test_original_provenance_no_external_mesh(self):
  with tempfile.TemporaryDirectory() as td:
   m=generate_dataset(td,35)
   self.assertEqual(m['count'],35)
   self.assertFalse(m['external_data_ingested'])
   ref=json.loads((Path(td)/'synthetic_landmarks.json').read_text())
   self.assertTrue(all(not row['provenance']['external_photos_or_3d_meshes_imported'] for row in ref['entries']))
   self.assertEqual(len({row['reference_id'] for row in ref['entries']}),35)
 def test_no_species_leakage_from_index_partition(self):
  with tempfile.TemporaryDirectory() as td:
   generate_dataset(td,140)
   rows=json.loads((Path(td)/'synthetic_landmarks.json').read_text())['entries']
   expected={'human','elf','orc','axolotl','feline','dwarf','automaton'}
   for subset in ('training','validation','test'):
    self.assertEqual({r['species'] for r in rows if r['set']==subset},expected)
 def test_synthetic_net_holdout(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);generate_dataset(root/'ref',140)
   report=train(root/'ref'/'synthetic_landmarks.json',root/'learn')
   self.assertEqual(report['heldout_test'],21)
   self.assertLess(report['heldout_mae_ratios'],report['heldout_constant_baseline_mae_ratios'])
   self.assertFalse(report['real_anatomy_learning_verified'])

if __name__=='__main__':unittest.main()