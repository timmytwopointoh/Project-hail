"""Read-only structural tests for independent AI worker source scopes."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/ai_worker.py"
SPEC = importlib.util.spec_from_file_location("ai_worker", SCRIPT)
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)

class WorkerScopeTests(unittest.TestCase):
    def test_all_six_domains_are_isolated(self):
        self.assertEqual({"combat", "animation", "models", "materials", "world", "studio"},
                         set(worker.ROLES))
        owned = [name for group in worker.ROLES.values() for name in group]
        self.assertEqual(len(owned), len(set(owned)))

    def test_nobody_can_write_renderer_hud_or_workflows(self):
        owned = set(sum((names for names in worker.ROLES.values()), []))
        self.assertFalse({"ValeRenderer.java", "WardenHud.java", "MainActivity.java"} & owned)
        for file in owned:
            self.assertTrue(file.endswith(".java"))
            self.assertFalse("/" in file or "\\" in file)
            self.assertTrue((worker.ROOT / worker.JAVA / file).is_file())

    def test_manager_roles_equal_available_code_worker_roles(self):
        other = Path(__file__).resolve().parents[1] / "scripts/worker_manager.py"
        spec = importlib.util.spec_from_file_location("worker_manager_scope", other)
        manager = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(manager)
        self.assertEqual(set(manager.ALLOWED), set(worker.ROLES))

if __name__ == "__main__":
    unittest.main()
