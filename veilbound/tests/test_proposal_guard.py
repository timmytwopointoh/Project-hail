"""Offline adversarial tests for model patch boundaries and quality."""
import importlib.util
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "scripts/proposal_guard.py"
SPEC = importlib.util.spec_from_file_location("proposal_guard", PATH)
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)

PATH_OK = "veilbound/app/src/main/java/game/ashenveil/veilbound/CharacterRig.java"
ORIGINAL = "package game.ashenveil.veilbound;\npublic final class CharacterRig {}\n"


def proposal(old="public final class CharacterRig {}",
             new="public final class CharacterRig { /* detail */ }",
             path=PATH_OK, edits=None):
    return {"summary": "Introduce a small audited rig refinement",
            "edits": edits if edits is not None else [
                {"path": path, "find": old, "replace": new}],
            "risks": []}


class ProposalGuardTests(unittest.TestCase):
    def validate(self, obj, source=ORIGINAL):
        return guard.validate_proposal(obj, [PATH_OK], lambda p: source)

    def test_one_real_scoped_replacement(self):
        result = self.validate(proposal())
        self.assertIn("/* detail */", result[PATH_OK])
        self.assertIn("package game", result[PATH_OK])

    def test_noop_empty_and_unmatched_rejected(self):
        for obj in (
            proposal(edits=[]),
            proposal(old="package", new="package"),
            proposal(old="nonexistent", new="fixed"),
        ):
            with self.assertRaises(ValueError):
                self.validate(obj)

    def test_path_traversal_and_different_role_are_rejected(self):
        for path in ("../../.github/workflows/build.yml", "WorldState.java",
                     PATH_OK + "/../../MainActivity.java"):
            with self.assertRaisesRegex(ValueError, "outside"):
                self.validate(proposal(path=path))

    def test_duplicate_replace_intermediate_sequence_is_checked(self):
        obj = proposal(edits=[
            {"path": PATH_OK, "find": "class CharacterRig",
             "replace": "class CharacterRigDetail"},
            {"path": PATH_OK, "find": "class CharacterRig",
             "replace": "class CharacterRigDetail"}])
        with self.assertRaisesRegex(ValueError, "repeated an exact match"):
            self.validate(obj)

    def test_dangerous_generated_java_is_rejected(self):
        banned = (
            "Runtime.getRuntime().exec(\"x\");",
            "new ProcessBuilder(\"curl\");",
            "System.getenv(\"TOKEN\");",
            "new java.net.Socket(\"host\", 4);",
            "Class.forName(\"java.lang.Runtime\");",
            "Files.write(output, bytes);",
            "static { System.out.println(1); }",
        )
        for line in banned:
            with self.subTest(line=line):
                obj = proposal(new="public final class CharacterRig { " + line + " }")
                with self.assertRaisesRegex(ValueError, "prohibited"):
                    self.validate(obj)

    def test_malformed_shape_and_budget(self):
        for obj in (
            {**proposal(), "commands": ["curl x"]},
            {**proposal(), "summary": ""},
            {**proposal(), "risks": ["x" * 400]},
            proposal(edits=[proposal()["edits"][0]] * 4),
            proposal(new="x" * 6000),
        ):
            with self.assertRaises(ValueError):
                self.validate(obj)

    def test_source_read_is_never_written_by_guard(self):
        calls = []
        def read(path):
            calls.append(path)
            return ORIGINAL
        result = guard.validate_proposal(proposal(), [PATH_OK], read)
        self.assertEqual([PATH_OK], list(result))
        self.assertTrue(calls)
        self.assertEqual("package game.ashenveil.veilbound;\npublic final class CharacterRig {}\n",
                         ORIGINAL)

if __name__ == "__main__":
    unittest.main()
