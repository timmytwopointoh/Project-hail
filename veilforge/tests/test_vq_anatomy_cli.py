"""End-to-end VQ A3 smoke test: OBJ, GLB, textures and QA. No emulator."""
import sys,tempfile,unittest,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vq_anatomy_cli import run

class Integration(unittest.TestCase):
 def test_prompt_to_glb_qa_review_only(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   r=run('human long legs teal tunic',root,voxel=.029,seed=31)
   self.assertTrue(Path(r['asset_glb']).is_file())
   self.assertTrue(r['qa']['technical_pass'])
   self.assertEqual(r['promotion_gate']['status'],'REVIEW_REQUIRED')
   self.assertTrue((root/'vq_a3_qa.json').is_file())
   self.assertEqual(json.loads((root/'vq_a3_qa.json').read_text())['asset_sha256'],r['asset_sha256'])
   self.assertTrue(list((root/'textures').rglob('normal.png')))
if __name__=='__main__':unittest.main()