"""Fail-closed screenshot provenance regression for Android REVIEW handoff."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import vq_handoff_angle_provenance as h
from visual_semantics import silhouette,outline_analysis
SHA="a"*40
class AngleEvidenceTests(unittest.TestCase):
    def fixture(self,root):
        base=root/"shots"/"veilforge-android-nature-mobile"
        frames=[];cov=[]
        for i,(yaw,pitch) in enumerate([(0,15),(25,25)]):
            name=f"ancient_tree/{i:02d}_yaw{yaw}_pitch{pitch}.png"
            path=base/name;path.parent.mkdir(parents=True,exist_ok=True)
            im=Image.new("RGB",(256,256),(17,21,29))
            ImageDraw.Draw(im).rectangle((90+i*10,80,120+i*10,160),fill=(25,220,35))
            im.save(path)
            mask,w,ht=silhouette(im)
            cov.append(outline_analysis(mask,w,ht)["coverage"])
            frames.append({"index":i,"yaw":yaw,"pitch":pitch,"image":name,
                           "sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
        report={"role":"nature-mobile","source_commit":SHA,"device_android_api":35,
                "technical_visual_smoke_pass":True,"screenshot_count":2,
                "apk_sha256":"b"*64,"assets":[{"asset":"ancient_tree","views":frames}]}
        (base/"emulator_visual_qa.json").write_text(json.dumps(report))
        sem=root/"semantic.json"
        sem.write_text(json.dumps({"technical_gate_passed":True,
            "assets":{"ancient_tree":{"min_coverage":round(min(cov),4),
                                      "max_coverage":round(max(cov),4)}}}))
        digest=hashlib.sha256(sem.read_bytes()).hexdigest()
        tasks=root/"tasks.json"
        tasks.write_text(json.dumps({"source_commit":SHA,"github_actions_run_id":1,
            "source_semantic_report_sha256":digest,"frames_reviewed":2,"warning_count":1,
            "ready_for_automated_model_rewrite":False,"artistic_signoff":False,
            "tasks":[{"asset":"ancient_tree","emulator_role":"nature-mobile",
                "source_commit":SHA,"github_actions_run_id":1,
                "input_report_sha256":digest}]}))
        return tasks,sem,root/"shots",base/frames[0]["image"]
    def test_hashes_and_review_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=self.fixture(Path(tmp))
            with patch.object(h,"ROLES",{"nature-mobile":("ancient_tree",)}),patch.object(h,"VIEWS",[(0,15),(25,25)]):
                result=h.bind(*args[:3],SHA,1)
            self.assertEqual(result["verified_android_frame_count"],2)
            self.assertEqual(len(result["tasks"][0]["camera_view_evidence"]),2)
            self.assertFalse(result["tasks"][0]["auto_promote"])
    def test_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=self.fixture(Path(tmp))
            args[3].write_bytes(args[3].read_bytes()+b"tamper")
            with patch.object(h,"ROLES",{"nature-mobile":("ancient_tree",)}),patch.object(h,"VIEWS",[(0,15),(25,25)]):
                with self.assertRaisesRegex(ValueError,"Altered"):
                    h.bind(*args[:3],SHA,1)
    def test_source_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=self.fixture(Path(tmp))
            with self.assertRaisesRegex(ValueError,"source"):
                h.bind(*args[:3],"c"*40,1)
if __name__=="__main__":unittest.main()
