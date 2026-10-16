"""Regression gates for the optional ten-job VEILFORGE dispatch pipeline."""
from __future__ import annotations
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"veilforge"))
spec=importlib.util.spec_from_file_location("veilforge_job_queue",ROOT/"veilforge"/"queue.py")
queue=importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)
BACKLOG=ROOT/"veilforge"/"queue_backlog.json"
CATALOG=ROOT/"veilforge"/"catalog.json"


class QueueTests(unittest.TestCase):
    def test_one_shared_budget_ten_includes_real_emulator_roles(self):
        assigned=queue.allocate(queue.tickets(BACKLOG,CATALOG),10,4)
        self.assertEqual(assigned["selected_count"],10)
        self.assertEqual(assigned["emulator_count"],4)
        self.assertEqual(assigned["asset_worker_count"],6)
        self.assertEqual(len(assigned["deferred_ids"]),2)
        self.assertTrue(assigned["review_only"])
        self.assertFalse(assigned["auto_promote"])
        self.assertEqual(len({row["id"] for row in assigned["matrix"]["include"]}),10)

    def test_no_idle_jobs_when_demand_is_lower(self):
        ticket=queue.tickets(BACKLOG,CATALOG)[:1]
        assigned=queue.allocate(ticket,10,4)
        self.assertEqual(assigned["selected_count"],1)
        self.assertEqual(assigned["emulator_count"],1)

    def test_zero_emulator_budget_is_respected(self):
        assigned=queue.allocate(queue.tickets(BACKLOG,CATALOG),10,0)
        self.assertEqual(assigned["selected_count"],8)
        self.assertEqual(assigned["emulator_count"],0)

    def test_hard_ceiling_cannot_be_overridden(self):
        for num in (0,11,1000):
            with self.assertRaises(ValueError):
                queue.allocate(queue.tickets(BACKLOG,CATALOG),num,4)
        for num in (-1,5,50):
            with self.assertRaises(ValueError):
                queue.allocate(queue.tickets(BACKLOG,CATALOG),10,num)

    def test_reject_duplicate_and_untrusted_tasks(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"backlog.json"
            data=json.loads(BACKLOG.read_text())
            data["tickets"].append(dict(data["tickets"][0]))
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"Duplicate"):
                queue.tickets(path,CATALOG)
            data["tickets"][-1]["id"]="asset-evil-path"
            data["tickets"][-1]["kind"]="asset"
            data["tickets"][-1]["asset"]="../../github/workflows"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,"unsupported"):
                queue.tickets(path,CATALOG)

    def test_plan_outputs_are_frozen_and_machine_readable(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)
            r=queue.plan(BACKLOG,CATALOG,out,10,4,out/"GITHUB_OUTPUT")
            self.assertEqual(json.loads((out/"queue_plan.json").read_text()),r)
            env=(out/"GITHUB_OUTPUT").read_text()
            self.assertIn("count=10\n",env)
            self.assertIn("has_emulators=true\n",env)
            self.assertIn('"kind":"emulator"',env)

    def test_review_fails_closed_without_actual_emulator_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            queue.plan(BACKLOG,CATALOG,root/"plan",10,4)
            r=queue.review(root/"plan"/"queue_plan.json",root/"missing",
                           root/"review","a"*40,"b"*64)
            self.assertFalse(r["technical_qa_passed"])
            self.assertEqual(len(r["errors"]),10)
            self.assertFalse(r["production_approved"])
            self.assertTrue(r["manual_art_review_required"])
            self.assertEqual(len(r["next_queue"]),12)

    def test_reviewer_rejects_missing_identity_and_unchecked_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)
            queue.plan(BACKLOG,CATALOG,p/"plan",1,0)
            with self.assertRaises(ValueError):
                queue.review(p/"plan"/"queue_plan.json",p,p/"bad","untrusted","")
            asset=(p/"veilforge-queue-asset-ancient_gate_standard")
            asset.mkdir()
            self.assertTrue(queue.evidence_ok(
                {"kind":"asset","asset":"ancient_gate_standard"},
                asset,"a"*40,""))

    def test_blocked_items_never_execute(self):
        rows=queue.tickets(BACKLOG,CATALOG)
        for row in rows:
            row["status"]="blocked"
        assigned=queue.allocate(rows,10,4)
        self.assertEqual(assigned["selected_count"],0)
        self.assertEqual(len(assigned["blocked_ids"]),len(rows))


if __name__=="__main__":
    unittest.main()
