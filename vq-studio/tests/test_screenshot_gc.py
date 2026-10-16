"""Screenshots are released only after validated 14-view source evidence exists."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from screenshot_gc import prune,sha256


class CheckpointCleanupTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.scan=self.root/"scan"
        self.views=self.scan/"views"
        self.views.mkdir(parents=True)
        self.keep=self.root/"kept"
        # Not fake Android evidence: these are synthetic unit-test fixtures,
        # only for validating pruning and hash guards.
        report={"engine":"VEYLQUORIN","technical_geometry_smoke_passed":True,
                "production_approved":False,"human_review_required":True,
                "source_sha256":"f"*64,"visual":{"views":[]}}
        for i in range(14):
            img=self.views/f"orbit_{i:02d}.png"
            mask=self.views/f"mask_{i:02d}.png"
            img.write_bytes(("synthetic_image_"+str(i)).encode()*100)
            mask.write_bytes(("synthetic_mask_"+str(i)).encode()*100)
            report["visual"]["views"].append({
                "view_index":i,"yaw":i*25,"pitch":15,
                "image":img.name,"image_sha256":sha256(img),
                "mask":mask.name,"mask_sha256":sha256(mask)})
        sheet=self.views/"contact_sheet.png"
        sheet.write_bytes(b"synthetic-contact"*150)
        report["visual"]["contact_sheet_sha256"]=sha256(sheet)
        (self.scan/"vq_model_report.json").write_text(json.dumps(report))
    def tearDown(self):self.temp.cleanup()
    def test_deliberate_step_and_hashes_before_cleanup(self):
        with self.assertRaises(ValueError):
            prune(self.scan,self.keep,next_action="unknown")
        self.assertEqual(len(list(self.views.glob("orbit_*.png"))),14)
        result=prune(self.scan,self.keep,next_action="needs_artist_review")
        self.assertEqual(result["transient_frames_verified"],28)
        self.assertEqual(result["next_action"],"needs_artist_review")
        self.assertEqual(len(list(self.views.glob("orbit_*.png"))),0)
        self.assertTrue((self.keep/"contact_sheet.png").exists())
        self.assertTrue((self.keep/"latest_orbit.png").exists())
        self.assertEqual(len(result["transient_frame_hashes"]),28)
    def test_modified_frame_blocks_deletion(self):
        (self.views/"orbit_05.png").write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            prune(self.scan,self.keep,next_action="needs_artist_review")
        self.assertEqual(len(list(self.views.glob("orbit_*.png"))),14)
    def test_missing_quality_gate_blocks_deletion(self):
        p=self.scan/"vq_model_report.json"
        report=json.loads(p.read_text())
        report["technical_geometry_smoke_passed"]=False
        p.write_text(json.dumps(report))
        with self.assertRaises(ValueError):
            prune(self.scan,self.keep,next_action="repair_mesh_defects")
        self.assertEqual(len(list(self.views.glob("mask_*.png"))),14)
    def test_checkpoint_folder_must_be_separate(self):
        with self.assertRaises(ValueError):
            prune(self.scan,self.views/"archive",next_action="needs_artist_review")
        self.assertEqual(len(list(self.views.glob("orbit_*.png"))),14)

if __name__=="__main__":
    unittest.main()
