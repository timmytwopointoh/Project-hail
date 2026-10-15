#!/usr/bin/env python3
"""Bounded VEILBOUND development manager / dynamic GitHub Actions job planner.

Turns reviewed roadmap work plus machine QA findings into independently scoped
coding assignments. Manager creates *jobs*, not new privileged AI identities.
No generated commands, no code execution, no API calls, no repository writes.
"""
import argparse
import json
import os
from pathlib import Path

# Team managers are separate bounded CI jobs and approve each worker's scope.
import sys
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from team_manager import make_hierarchy

MAX_WORKERS = 6
ROLE_ORDER = ("combat", "animation", "models", "materials", "world", "studio")
ALLOWED = set(ROLE_ORDER)
P_SCORE = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
# These roles have no safe isolated Java ownership yet; create review items
# in the normal QA report instead of handing critical render code to AI.
OBSERVATION_ONLY = {"qa", "renderer", "performance"}

def load_object(path):
    if not path or not Path(path).is_file():
        return {}
    try:
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except (OSError, UnicodeError, ValueError):
        return {}

def normalize_task(obj, source):
    if not isinstance(obj, dict):
        return None
    role = obj.get("role", obj.get("worker"))
    if role not in ALLOWED:
        return None
    priority = obj.get("priority", "P2")
    if priority not in P_SCORE:
        return None
    goal = obj.get("goal", obj.get("repair_guidance", ""))
    if not isinstance(goal, str) or not goal.strip():
        return None
    ident = obj.get("id", "improvement-" + str(role))
    if not isinstance(ident, str) or not ident or len(ident) > 96:
        return None
    # Keep injected instructions from JSON as *data*; no shell interpolation.
    goal = " ".join(goal.split())[:750]
    return {"role": role, "task_id": ident, "priority": priority,
            "goal": goal, "source": source}

def plan(roadmap=None, findings=None, *, max_workers=4, workflow_conclusion=None):
    if isinstance(max_workers, bool) or not isinstance(max_workers, int):
        raise ValueError("Worker cap must be an integer")
    if not 1 <= max_workers <= MAX_WORKERS:
        raise ValueError("Worker cap must be between 1 and 6")
    findings = findings if isinstance(findings, dict) else {}
    roadmap = roadmap if isinstance(roadmap, dict) else {}
    # A failed native build with no machine-readable report is a high-priority
    # human/CI investigation. Do not let the manager dispatch speculative
    # changes to unrelated game code in that case.
    missing_failure_evidence = (workflow_conclusion == "failure"
                                and not isinstance(findings.get("tasks"), list))
    candidate = []
    for row in findings.get("tasks", []) if isinstance(findings.get("tasks", []), list) else []:
        task = normalize_task(row, "measured-qa")
        if task is not None:
            candidate.append(task)
    for row in roadmap.get("tasks", []) if isinstance(roadmap.get("tasks", []), list) else []:
        task = normalize_task(row, "roadmap")
        if task is not None:
            candidate.append(task)
    # Prioritize validated failures, then lower-priority roadmap work.
    candidate.sort(key=lambda x: (P_SCORE[x["priority"]],
                   0 if x["source"] == "measured-qa" else 1,
                   ROLE_ORDER.index(x["role"]), x["task_id"]))
    selected = []
    claimed = set()
    for item in candidate:
        if missing_failure_evidence:
            break
        if item["role"] in claimed:
            continue
        claimed.add(item["role"])
        selected.append(item)
        if len(selected) >= max_workers:
            break
    selected.sort(key=lambda x: ROLE_ORDER.index(x["role"]))
    ignored = []
    for row in findings.get("tasks", []) if isinstance(findings.get("tasks", []), list) else []:
        if isinstance(row, dict) and row.get("worker") in OBSERVATION_ONLY:
            ignored.append({"task_id": str(row.get("id", "unidentified")),
                            "owner": row["worker"],
                            "action": "manual-review-required"})
    if missing_failure_evidence:
        ignored.insert(0, {"task_id": "VB-CI-FAILURE-NO-ARTIFACT", "owner": "qa",
                           "priority": "P0", "action": "inspect-native-build-logs",
                           "reason": "Native workflow failed without a usable task_plan.json; "
                                     "automatic code proposals are paused for this cycle"})
    hierarchy = make_hierarchy(selected)
    return {"schema_version": 2,
            "max_workers": max_workers,
            "workflow_conclusion": workflow_conclusion or "unspecified",
            "paused_for_missing_failure_evidence": missing_failure_evidence,
            "allocated": len(selected),
            "spawned_roles": [x["role"] for x in selected],
            "matrix": hierarchy["worker_matrix"],
            "team_matrix": hierarchy["team_matrix"],
            "worker_matrix": hierarchy["worker_matrix"],
            "team_count": hierarchy["team_count"],
            "max_manager_depth": hierarchy["max_depth"],
            "review_only": ignored,
            "note": "Every worker edits separate allowlisted files in an isolated job. "
                    "No source files, branches or PRs are changed automatically."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backlog", type=Path,
                        default=Path("veilbound/worker_backlog.json"))
    parser.add_argument("--findings", type=Path,
                        default=Path("inspection_output/veilbound/task_plan.json"))
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--workflow-conclusion", default="")
    parser.add_argument("--out", type=Path,
                        default=Path("inspection_output/manager"))
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    result = plan(load_object(args.backlog), load_object(args.findings),
                  max_workers=args.max_workers,
                  workflow_conclusion=args.workflow_conclusion)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "assignment_plan.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = ["# VEILBOUND hierarchical development manager", "",
             "Team managers spawned: **" + str(result["team_count"]) + "** / 3  ",
             "Concurrent workers: **" + str(result["allocated"]) + "** / "
             + str(result["max_workers"]) + " requested", "",
             "| Team | Worker | Priority | Work assignment |", "|---|---|---|---|"]
    for entry in result["matrix"]["include"]:
        lines.append("| " + entry["team"] + " | " + entry["role"] + " | " + entry["priority"] + " | "
                     + entry["goal"].replace("|", "/") + " |")
    if result["paused_for_missing_failure_evidence"]:
        lines += ["", "**Automatic work paused:** failed native build with no usable "
                  "repair report. Inspect the Android build logs first.", ""]
    lines += ["", "High-risk renderer and performance failures are human-review "
              "tasks until those systems have dedicated isolated test gates.", ""]
    (args.out / "assignment_plan.md").write_text("\n".join(lines))
    matrix = json.dumps(result["matrix"], separators=(",", ":"))
    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as file:
            file.write("matrix=" + matrix + "\n")
            file.write("worker_count=" + str(result["allocated"]) + "\n")
            file.write("team_count=" + str(result["team_count"]) + "\n")
            file.write("team_matrix=" + json.dumps(result["team_matrix"], separators=(",", ":")) + "\n")
    print(json.dumps({"allocated": result["allocated"],
                      "roles": result["spawned_roles"],
                      "review_only": result["review_only"]}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
