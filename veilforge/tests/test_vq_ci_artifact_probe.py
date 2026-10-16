"""Adversarial tests for real ZIP payload accounting and 14-view guards."""
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "veilforge"))
from vq_ci_artifact_probe import inspect_captures, inspect_apk, inspect_run

PNG = bytes.fromhex("89504e470d0a1a0a") + b"valid-fixture-data"


def write_zip(path, entries):
    with zipfile.ZipFile(path, "w") as z:
        for name, data in entries.items():
            z.writestr(name, data)


class ArtifactPayloadTests(unittest.TestCase):
    def test_fourteen_real_pngs_and_blocked_modal_kept_separate(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "captures.zip"
            entries = {f"asset/{i:02d}_yaw{i}_pitch15.png": PNG for i in range(14)}
            entries["asset/01_yaw1_pitch15_blocked_modal_1.png"] = PNG
            write_zip(path, entries)
            row = inspect_captures(path)
            self.assertEqual(row["accepted_png_count"], 14)
            self.assertEqual(row["blocked_png_count"], 1)
            self.assertEqual(row["accepted_png_bytes"], 14 * len(PNG))

    def test_missing_camera_angle_is_not_a_valid_asset(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "captures.zip"
            write_zip(path, {f"asset/{i:02d}_yaw{i}_pitch15.png": PNG
                             for i in range(13)})
            with self.assertRaisesRegex(ValueError, "14 unique"):
                inspect_captures(path)

    def test_non_png_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "captures.zip"
            write_zip(path, {f"asset/{i:02d}_yaw{i}_pitch15.png": b"fake"
                             for i in range(14)})
            with self.assertRaisesRegex(ValueError, "not PNG"):
                inspect_captures(path)

    def test_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "captures.zip"
            write_zip(path, {"../asset/00_yaw0_pitch15.png": PNG})
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                inspect_captures(path)

    def test_missing_or_multiple_apk_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "apk.zip"
            write_zip(path, {"a.apk": b"PKdata", "b.apk": b"PKdata"})
            with self.assertRaisesRegex(ValueError, "duplicated"):
                inspect_apk(path)

    def test_pinned_real_evidence_has_two_154_view_runs(self):
        evidence = json.loads((ROOT / "veilforge/evidence/m34-09-artifact-payloads.json").read_text())
        self.assertEqual([r["run_id"] for r in evidence["runs"]],
                         [38916145322, 38918040166])
        self.assertTrue(all(r["accepted_png_count"] == 154 for r in evidence["runs"]))
        self.assertEqual([r["blocked_png_count"] for r in evidence["runs"]], [7, 9])
        self.assertTrue(all(r["apk"]["bytes"] == 2304080 for r in evidence["runs"]))
        self.assertFalse(evidence["claims"]["controlled_speedup"])


if __name__ == "__main__":
    unittest.main()
