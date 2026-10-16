#!/usr/bin/env python3
"""Restartable VEILFORGE manager: produces safe, read-only handoff artifacts."""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path

CAP=10
EMULATORS=4


def produce(state_path:Path,roadmap_path:Path,backlog_path:Path,out:Path) -> dict:
    state=json.loads(state_path.read_text(encoding="utf-8"))
    roadmap=json.loads(roadmap_path.read_text(encoding="utf-8"))
    backlog=json.loads(backlog_path.read_text(encoding="utf-8"))
    if (state.get("schema_version")!=1 or state.get("engine")!="VEILFORGE"
        or state.get("claimant")!="Timothy Harris"
        or state.get("operating_mode")!="plan_only"
        or state.get("autonomous_execution_enabled") is not False
        or state.get("auto_merge") is not False
        or state.get("production_promote") is not False
        or state.get("allow_source_modification") is not False
        or state.get("max_active_worker_and_emulator_jobs")!=CAP
        or state.get("max_emulator_jobs")!=EMULATORS
        or state.get("max_expensive_inference_runs_per_day")!=0):
        raise ValueError("Steward may not bypass reviewed on-demand-only budget")
    if roadmap.get("engine")!="VEILFORGE" or roadmap.get("schema_version")!=1:
        raise ValueError("Unknown VEILFORGE milestone schema")
    if backlog.get("schema_version")!=1 or not isinstance(backlog.get("tickets"),list):
        raise ValueError("Invalid queue backlog")
    next_milestones=[
        {"id":entry["id"],"name":entry["name"],"status":entry["status"]}
        for entry in roadmap["milestones"]
        if entry.get("status")!="verified"
    ][:10]
    pending=sorted(
        (t for t in backlog["tickets"] if t.get("status")=="pending"),
        key=lambda t:(t["priority"],t["id"]))
    selected=pending[:CAP]
    report={
        "schema_version":1,"engine":"VEILFORGE",
        "claimant":state["claimant"],
        "observed_at_utc":datetime.now(timezone.utc).isoformat(),
        "operating_mode":"plan_only","executed_workers":0,
        "executed_emulators":0,"model_inference_calls":0,
        "git_mutations":0,"automatic_approvals":0,
        "queue_pending_total":len(pending),
        "next_queue_candidates":[x["id"] for x in selected],
        "milestone_candidates":next_milestones,
        "last_verified_provenance_run":state["handoff"]["last_verified_provenance_run"],
        "last_verified_mixed_queue_run":state["handoff"]["last_verified_mixed_queue_run"],
        "known_limitations":state["handoff"]["known_limitations"],
        "next_action":"Review the pending queue and manually dispatch approved bounded work; do not claim completed engine upgrades.",
    }
    out.mkdir(parents=True,exist_ok=True)
    (out/"handoff.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    (out/"handoff.md").write_text(
        "# VEILFORGE persistent planning checkpoint\n\n"+
        "Claimant: "+state["claimant"]+"\n\n"+
        "Observed UTC: "+report["observed_at_utc"]+"\n\n"+
        "Manual approval required; no model, worker, emulator or merge was started.\n\n"+
        "Next bounded work: "+", ".join(report["next_queue_candidates"])+"\n",
        encoding="utf-8")
    return report


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=["plan"])
    p.add_argument("--state",type=Path,default=Path("veilforge/steward_state.json"))
    p.add_argument("--roadmap",type=Path,default=Path("veilforge/ENGINE_MASTER_PLAN.json"))
    p.add_argument("--backlog",type=Path,default=Path("veilforge/queue_backlog.json"))
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=produce(a.state,a.roadmap,a.backlog,a.out)
    print("VEILFORGE_RESTART_CHECKPOINT",result["queue_pending_total"],
          "pending; zero agents and emulators executed")


if __name__=="__main__":
    main()
