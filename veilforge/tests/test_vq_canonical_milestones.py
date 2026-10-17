"""Fail closed on roadmap conflation, status invention and automatic approval."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from vq_canonical_milestones import summarize, write_report

FILES = ("VQ_ENGINE_QUALITY_PLAN.json", "VQ_M34_EFFICIENCY_MAP.json", "ENGINE_MASTER_PLAN.json")


class CanonicalMilestoneTests(unittest.TestCase):
    def test_tracks_are_distinct_and_no_acceptance_is_inferred(self):
        result = summarize(ROOT)
        self.assertEqual([result[k]["milestone_count"] for k in
                          ("canonical_quality", "m34_efficiency", "legacy_vf_capability_groups")], [34, 13, 24])
        self.assertFalse(result["human_artistic_acceptance"])
        self.assertFalse(result["real_phone_performance_acceptance"])
        self.assertFalse(result["auto_merge_or_model_promotion"])
        self.assertFalse(result["legacy_vf_capability_groups"]["is_canonical_34_map"])

    def test_machine_readable_report_keeps_all_acceptance_gates(self):
        with tempfile.TemporaryDirectory() as folder:
            result = write_report(ROOT, Path(folder))
            written = json.loads((Path(folder) / "vq_canonical_milestone_tracks.json").read_text())
            self.assertEqual(written, result)
            self.assertEqual(len(written["canonical_quality"]["items"]), 34)
            self.assertEqual(len(written["m34_efficiency"]["items"]), 13)

    def _mutated(self, file, change):
        temp = tempfile.TemporaryDirectory()
        path = Path(temp.name)
        for name in FILES:
            shutil.copyfile(ROOT / name, path / name)
        target = path / file
        data = json.loads(target.read_text())
        change(data)
        target.write_text(json.dumps(data))
        return temp, path

    def test_rejects_missing_canonical_milestone(self):
        temp, path = self._mutated(FILES[0], lambda d: d["milestones"].pop())
        with temp, self.assertRaises(ValueError):
            summarize(path)

    def test_rejects_automatic_approval_and_duplicate_ids(self):
        for change in (lambda d: d["milestones"][0].__setitem__("automatic_game_approval", True),
                       lambda d: d["milestones"][1].__setitem__("id", d["milestones"][0]["id"])):
            temp, path = self._mutated(FILES[0], change)
            with temp, self.assertRaises(ValueError):
                summarize(path)

    def test_rejects_efficiency_qa_downgrade(self):
        temp, path = self._mutated(FILES[1], lambda d: d["success_requirements"].__setitem__("android_devices", 2))
        with temp, self.assertRaises(ValueError):
            summarize(path)


if __name__ == "__main__":
    unittest.main()
