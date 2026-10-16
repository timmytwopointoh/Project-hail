"""Check that VQ's full-source offline ZIP is deterministic and rejects tampering."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from library_archive import build,verify,NEEDED,MANIFEST

def git(root,*args):
    return subprocess.run(["git","-C",str(root),*args],check=True,capture_output=True).stdout.decode().strip()
def fixture(root):
    git(root,"init","-q")
    for name in NEEDED:
        f=root/name;f.parent.mkdir(parents=True,exist_ok=True)
        f.write_text("source "+name+"\n")
    git(root,"add",".")
    git(root,"-c","user.email=ci@example.invalid","-c","user.name=QA","commit","-qm","test fixture")
    return git(root,"rev-parse","HEAD")

class OfflineBackupTests(unittest.TestCase):
    def test_deterministic_roundtrip_all_source_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"repo";root.mkdir();commit=fixture(root)
            a=Path(temp)/"a.zip";b=Path(temp)/"b.zip"
            result=build(root,a,commit);other=build(root,b,commit)
            self.assertEqual(result["archive_sha256"],other["archive_sha256"])
            self.assertEqual(result["file_count"],len(NEEDED))
            self.assertTrue(verify(a,commit)["verified"])
            with zipfile.ZipFile(a) as z:self.assertIn(MANIFEST,z.namelist())
    def test_dirty_source_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"repo";root.mkdir();commit=fixture(root)
            (root/sorted(NEEDED)[0]).write_text("unsaved edit")
            with self.assertRaisesRegex(ValueError,"dirty"):
                build(root,Path(temp)/"bad.zip",commit)
    def test_invalid_commit_and_missing_modules_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"repo";root.mkdir();fixture(root)
            with self.assertRaisesRegex(ValueError,"does not match"):
                build(root,Path(temp)/"bad.zip","0"*40)
            git(root,"rm",sorted(NEEDED)[0])
            git(root,"-c","user.email=ci@example.invalid","-c","user.name=QA","commit","-qm","missing file")
            with self.assertRaisesRegex(ValueError,"Required QV/VQ"):
                build(root,Path(temp)/"bad.zip")
    def test_secret_path_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"repo";root.mkdir();fixture(root)
            (root/".env").write_text("secret=dummy\n")
            git(root,"add",".env")
            git(root,"-c","user.email=ci@example.invalid","-c","user.name=QA","commit","-qm","unsafe test")
            with self.assertRaisesRegex(ValueError,"Unsafe/sensitive"):
                build(root,Path(temp)/"bad.zip")
    def test_repacked_tampered_source_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/"repo";root.mkdir();commit=fixture(root)
            original=Path(temp)/"original.zip";build(root,original,commit)
            broken=Path(temp)/"broken.zip"
            with zipfile.ZipFile(original) as a,zipfile.ZipFile(broken,"w") as b:
                for name in a.namelist():
                    content=a.read(name)
                    if name==sorted(NEEDED)[0]:content+=b"tamper"
                    b.writestr(name,content)
            with self.assertRaisesRegex(ValueError,"SHA256"):
                verify(broken,commit)
if __name__=="__main__":unittest.main()
