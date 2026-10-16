"""M34-09: real Actions timestamps must be audited without inventing speedups."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "veilforge"))
from vq_ci_benchmarks import summarize, report, duration

EVIDENCE = ROOT / "veilforge/evidence/m34-09-observed-runs.json"


class RuntimeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_two_real_green_runs_have_complete_jobs_and_artifacts(self):
        rows = [summarize(x["run"], x["jobs"], x["artifacts"]) for x in self.data]
        self.assertEqual([r["run_id"] for r in rows], [38916145322, 38918040166])
        self.assertTrue(all(r["job_wall_span_seconds"] > 0 for r in rows))
        self.assertTrue(all(len(r["android_seconds"]) == 4 for r in rows))
        self.assertTrue(all(r["capture_archive_bytes"] > 0 for r in rows))
        self.assertTrue(all(r["apk_archive_bytes"] > 0 for r in rows))
        self.assertTrue(all(r["apk_payload_bytes"] is None for r in rows))
        output = report(rows)
        self.assertEqual(output["observations"], 2)
        self.assertFalse(output["minimum_observations_met"])
        self.assertFalse(output["speedup_claim_supported"])
        self.assertFalse(output["artistic_approval"])
        self.assertFalse(output["hardware_approval"])

    def test_failure_cannot_be_counted_as_a_benchmark(self):
        case = copy.deepcopy(self.data[0])
        case["run"]["conclusion"] = "failure"
        with self.assertRaisesRegex(ValueError, "not a successful"):
            summarize(**case)

    def test_missing_android_role_fails_closed(self):
        case = copy.deepcopy(self.data[0])
        case["jobs"]["jobs"] = [j for j in case["jobs"]["jobs"]
                                if " / characters / " not in j["name"]]
        case["jobs"]["total_count"] -= 1
        with self.assertRaisesRegex(ValueError, "4 real Android"):
            summarize(**case)

    def test_missing_semantic_review_fails_closed(self):
        case = copy.deepcopy(self.data[0])
        case["artifacts"]["artifacts"] = [a for a in case["artifacts"]["artifacts"]
                                         if a["name"] != "veilforge-android-semantic-review"]
        case["artifacts"]["total_count"] -= 1
        with self.assertRaisesRegex(ValueError, "Missing actual Android"):
            summarize(**case)

    def test_incomplete_paginated_evidence_fails_closed(self):
        case = copy.deepcopy(self.data[0])
        case["jobs"]["total_count"] += 1
        with self.assertRaisesRegex(ValueError, "pagination"):
            summarize(**case)

    def test_unfinished_job_fails_closed(self):
        case = copy.deepcopy(self.data[0])
        case["jobs"]["jobs"][0]["conclusion"] = "cancelled"
        with self.assertRaisesRegex(ValueError, "Unsuccessful"):
            summarize(**case)

    def test_invalid_job_clock_rejected(self):
        with self.assertRaises(ValueError):
            duration("2026-10-16T14:34:00Z", "2026-10-16T14:30:00Z")

    def test_duplicate_run_ids_rejected(self):
        row = summarize(**self.data[0])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            report([row, row])

    def test_three_samples_still_do_not_prove_speedup(self):
        rows = [summarize(**x) for x in self.data]
        synthetic = copy.deepcopy(rows[0])
        synthetic["run_id"] = -1
        result = report(rows + [synthetic])
        self.assertTrue(result["minimum_observations_met"])
        self.assertFalse(result["speedup_claim_supported"])


if __name__ == "__main__":
    unittest.main()
