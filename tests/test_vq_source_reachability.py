"""Adversarial source-only checks: a candidate is never declared deletable."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "vq_source_reachability.py"
spec = importlib.util.spec_from_file_location("vq_source_reachability", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReachabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "veilforge" / "tests").mkdir(parents=True)
        (self.root / ".github" / "workflows").mkdir(parents=True)

    def write(self, path, content):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def test_workflow_import_chain_and_review_only_candidate(self):
        self.write("veilforge/alpha.py", "import beta\n")
        self.write("veilforge/beta.py", "def run(): pass\n")
        self.write("veilforge/unused_candidate.py", "def public_plugin_api(): pass\n")
        self.write(".github/workflows/qa.yml", "run: python3 veilforge/alpha.py\n")
        result = module.audit(self.root, "a" * 40)
        self.assertTrue(result["static_audit_passed"])
        self.assertEqual(result["referenced_production_modules"], ["alpha", "beta"])
        self.assertEqual(result["review_candidates_not_proven_unused"], ["unused_candidate"])
        self.assertFalse(result["safe_to_delete_candidates"])
        self.assertFalse(result["game_or_other_branch_coverage"])
        self.assertEqual(result["source_sha"], "a" * 40)

    def test_test_roots_relative_imports_and_literal_dynamic_import(self):
        self.write("veilforge/tests/test_tools.py", "from veilforge import helper\n")
        self.write("veilforge/helper.py", "import importlib\nimportlib.import_module('veilforge.inner')\n")
        self.write("veilforge/inner.py", "value = 2\n")
        self.write("veilforge/other.py", "value = 3\n")
        result = module.audit(self.root)
        self.assertEqual(result["referenced_production_modules"], ["helper", "inner"])
        self.assertEqual(result["review_candidates_not_proven_unused"], ["other"])

    def test_unknown_dynamic_import_is_visible_not_ignored(self):
        self.write("veilforge/alpha.py", "from importlib import import_module\nimport_module(get_name())\n")
        self.write("veilforge/hidden.py", "pass\n")
        self.write(".github/workflows/qa.yml", "run: python veilforge/alpha.py\n")
        result = module.audit(self.root)
        self.assertEqual(result["dynamic_load_uncertainty"][0]["module"], "alpha")
        self.assertIn("hidden", result["review_candidates_not_proven_unused"])
        self.assertFalse(result["safe_to_delete_candidates"])

    def test_invalid_source_and_sha_fail_closed(self):
        self.write("veilforge/broken.py", "def x(:\n")
        result = module.audit(self.root, "not-a-sha")
        self.assertFalse(result["static_audit_passed"])
        self.assertEqual(len(result["problems"]), 2)

    def test_unsafe_symlink_is_rejected_without_reading_target(self):
        target = self.write("outside.py", "print('do not execute')\n")
        (self.root / "veilforge" / "linked.py").symlink_to(target)
        result = module.audit(self.root)
        self.assertFalse(result["static_audit_passed"])
        self.assertTrue(any("symbolic" in p for p in result["problems"]))

    def test_report_is_stable_and_no_source_is_edited(self):
        path = self.write("veilforge/stable.py", "VALUE=1\n")
        original = path.read_bytes()
        a = module.audit(self.root)
        b = module.audit(self.root)
        self.assertEqual(a, b)
        self.assertEqual(path.read_bytes(), original)
        self.assertFalse(a["modules_deleted"])


if __name__ == "__main__":
    unittest.main()
