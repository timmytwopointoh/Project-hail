"""M34-06 regression tests exercise actual Git ancestry and workflow wiring."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "vq_ci_impact.py"
spec = importlib.util.spec_from_file_location("vq_ci_impact", SCRIPT)
impact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(impact)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL).decode().strip()


class ImpactRouterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "qa@example.invalid")
        git(self.root, "config", "user.name", "VQ QA")
        self.write("veilforge/VQ_EXAMPLE.md", "old docs\n")
        self.write("veilforge/factory.py", "print('original')\n")
        self.base = self.commit()

    def write(self, name, content):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return p

    def commit(self):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "test fixture")
        return git(self.root, "rev-parse", "HEAD")

    def check(self, base=None, event="push"):
        return impact.decide(self.root, self.base if base is None else base,
                             git(self.root, "rev-parse", "HEAD"), event)

    def test_docs_only_skips_android_but_never_source_tests(self):
        self.write("veilforge/VQ_EXAMPLE.md", "new docs\n")
        self.write("docs/vq-library/guide.md", "updated\n")
        self.commit()
        r = self.check()
        self.assertFalse(r["run_full_factory"])
        self.assertTrue(r["skip_android_approved"])
        self.assertTrue(r["source_tests_always_required"])
        self.assertEqual(len(r["changed_paths"]), 2)
        self.assertEqual(r, self.check())

    def test_mixed_docs_and_python_requires_full_factory(self):
        self.write("veilforge/VQ_EXAMPLE.md", "new docs\n")
        self.write("veilforge/factory.py", "print('changed')\n")
        self.commit()
        self.assertTrue(self.check()["run_full_factory"])

    def test_android_material_catalog_workflow_and_unknown_are_full(self):
        cases = ("veilforge/android-probe/app/src/main/java/Probe.java",
                 "veilforge/catalog.json", "veilforge/textures/skin.png",
                 ".github/workflows/veilforge-factory.yml", "veilforge/VQ_EXAMPLE.json",
                 "veilforge/docs/fixture.txt", "veilbound/app/src/main/java/Foo.java")
        for path in cases:
            with self.subTest(path=path):
                root = self.root
                old = git(root, "rev-parse", "HEAD")
                self.write(path, "new\n")
                self.commit()
                result = impact.decide(root, old, git(root, "rev-parse", "HEAD"))
                self.assertTrue(result["run_full_factory"])

    def test_rename_source_to_docs_cannot_hide_deleted_source(self):
        (self.root / "veilforge" / "factory.py").rename(self.root / "veilforge" / "VQ_RENAMED.md")
        self.commit()
        result = self.check()
        self.assertTrue(result["run_full_factory"])
        self.assertIn("veilforge/factory.py", result["changed_paths"])

    def test_invalid_sha_new_branch_manual_and_mismatched_head_fail_closed(self):
        self.write("veilforge/VQ_EXAMPLE.md", "new docs\n")
        head = self.commit()
        for base, end, event in (("0"*40, head, "push"), ("bad", head, "push"),
                                 (self.base, "f"*40, "push"), (self.base, head, "workflow_dispatch"),
                                 (head, head, "push")):
            with self.subTest(base=base, end=end, event=event):
                self.assertTrue(impact.decide(self.root, base, end, event)["run_full_factory"])

    def test_unrelated_git_history_or_missing_base_fails_closed(self):
        self.write("veilforge/VQ_EXAMPLE.md", "new docs\n")
        self.commit()
        self.assertTrue(self.check(base="a"*40)["run_full_factory"])

    def test_path_policy_does_not_trust_escape_or_docs_like_code(self):
        allowed = ("veilforge/VQ_ENGINE_QUALITY.md", "veilforge/docs/safety.md", "docs/vq-library/START_HERE.md")
        denied = ("../veilforge/VQ_DOC.md", "/veilforge/VQ_DOC.md", "veilforge/VQ_DOC.md/../x.md",
                  "veilforge/VQ_DOC.py", "veilforge/docs/a.py", "veilforge/VQ_.txt", "veilforge/notes.md",
                  "docs/vq-library/fake.json", "veilforge/VQ_DOC.md\nmalicious")
        self.assertTrue(all(impact.documentation_only(p) for p in allowed))
        self.assertTrue(all(not impact.documentation_only(p) for p in denied))

    def test_factory_workflow_keeps_source_qa_and_all_android_roles(self):
        workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/veilforge-factory.yml").read_text()
        self.assertIn("python3 -m unittest discover -s veilforge/tests -v", workflow)
        self.assertIn("needs: [library-manager, impact-gate]", workflow)
        self.assertIn("needs.impact-gate.result != 'success' || needs.impact-gate.outputs.run_full_factory != 'false'", workflow)
        self.assertIn("if: always() && (needs.impact-gate.result != 'success' || needs.impact-gate.outputs.run_full_factory != 'false')", workflow)
        self.assertIn("tools/vq_ci_impact.py", workflow)
        self.assertIn("tests/test_vq_ci_impact.py", workflow)
        self.assertIn("sha256sum -c -", workflow)
        self.assertIn("max-parallel: 4", workflow)
        for role in ("scene-world", "nature-mobile", "props-equipment", "characters"):
            self.assertIn("role: " + role, workflow)


if __name__ == "__main__":
    unittest.main()