#!/usr/bin/env python3
"""Hierarchical VEILBOUND director -> team managers -> parallel code workers.

Manager levels are real independent CI jobs, not self-replicating agents.
Role ownership and budgets are fixed by trusted source. A team manager may
approve/decline child assignments but cannot create unbounded jobs, choose
untrusted source paths, or spend outside the top-level fifty-worker budget.
"""
import argparse
import json
from pathlib import Path

TEAM_ROLES = {
    "gameplay": ("combat", "animation"),
    "art": ("models", "materials"),
    "world": ("world", "studio"),
}
ROLE_TEAM = {role: team for team, roles in TEAM_ROLES.items() for role in roles}
assert len(ROLE_TEAM) == sum(map(len, TEAM_ROLES.values()))
MAX_TEAM_MANAGERS = len(TEAM_ROLES)
MAX_CHILDREN_PER_MANAGER = 18
MAX_TOTAL_WORKERS = 50

def make_hierarchy(workers):
    if not isinstance(workers, list) or len(workers) > MAX_TOTAL_WORKERS:
        raise ValueError("Invalid number of child workers")
    task_keys, slots, jobs = set(), set(), []
    per_team = {team: 0 for team in TEAM_ROLES}
    for index, task in enumerate(workers, start=1):
        if not isinstance(task, dict):
            raise ValueError("Invalid task")
        role = task.get("role")
        if role not in ROLE_TEAM:
            raise ValueError("Unowned role: " + str(role))
        task_id, goal = task.get("task_id"), task.get("goal")
        if not isinstance(task_id, str) or not task_id or not isinstance(goal, str) or not goal:
            raise ValueError("Incomplete task assignment")
        key = (role, task_id)
        if key in task_keys:
            raise ValueError("Duplicated task assignment: " + str(key))
        task_keys.add(key)
        slot = task.get("slot_id", "w%03d" % index)
        if not isinstance(slot, str) or not __import__("re").fullmatch(r"w\d{3}", slot) or slot in slots:
            raise ValueError("Invalid or duplicate worker slot")
        slots.add(slot)
        team = ROLE_TEAM[role]
        per_team[team] += 1
        if per_team[team] > MAX_CHILDREN_PER_MANAGER:
            raise ValueError("Team child budget exceeded")
        jobs.append(dict(task, slot_id=slot, team=team))
    managers = [{"team": name, "child_count": per_team[name]}
                for name in TEAM_ROLES if per_team[name]]
    return {"team_matrix": {"include": managers},
            "worker_matrix": {"include": jobs},
            "team_count": len(managers), "worker_count": len(jobs),
            "max_depth": 2, "max_workers_total": MAX_TOTAL_WORKERS}



def review_team(master, name):
    if name not in TEAM_ROLES:
        raise ValueError("Unknown team manager: " + str(name))
    teams = master.get("team_matrix", {}).get("include", [])
    workers = master.get("worker_matrix", {}).get("include", [])
    if not isinstance(teams, list) or not isinstance(workers, list):
        raise ValueError("Invalid master plan")
    expected = next((x for x in teams if isinstance(x, dict) and x.get("team") == name), None)
    if expected is None:
        raise ValueError("This team is not authorized by the director")
    rebuilt = make_hierarchy(workers)
    if rebuilt["team_matrix"] != master["team_matrix"]:
        raise ValueError("Director team assignments failed consistency check")
    children = [x for x in rebuilt["worker_matrix"]["include"] if x["team"] == name]
    if expected.get("child_count") != len(children):
        raise ValueError("Director child count mismatch")
    # Team manager verifies the budget and entire branch-scoped assignment.
    return {"schema_version": 1, "team": name, "approved": True,
            "child_count": len(children),
            "children": children, "max_children": MAX_CHILDREN_PER_MANAGER,
            "requires_review_before_merge": True}

def verify_child(team_plan, name, role, task_id, goal, slot_id=None):
    if team_plan.get("team") != name or team_plan.get("approved") is not True:
        raise ValueError("No approval from this team manager")
    if ROLE_TEAM.get(role) != name:
        raise ValueError("Worker does not belong to supervising team")
    valid = [x for x in team_plan.get("children", [])
             if x.get("role") == role and x.get("task_id") == task_id and x.get("goal") == goal
             and (slot_id is None or x.get("slot_id") == slot_id)]
    if len(valid) != 1:
        raise ValueError("Worker assignment differs from the team manager's approved scope")
    return True

def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--director-plan", type=Path)
    parser.add_argument("--team", choices=tuple(TEAM_ROLES))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-child", action="store_true")
    parser.add_argument("--role")
    parser.add_argument("--task-id")
    parser.add_argument("--goal")
    parser.add_argument("--slot-id")
    args = parser.parse_args()
    if not args.team or not args.output:
        parser.error("--team and --output are required")
    if args.verify_child:
        plan = json.loads(args.output.read_text(encoding="utf-8"))
        verify_child(plan, args.team, args.role, args.task_id, args.goal, args.slot_id)
        print(json.dumps({"approved": True, "team": args.team, "role": args.role,
                          "task_id": args.task_id, "slot_id": args.slot_id,
                          "source": "team-manager-review"}))
        return 0
    if args.director_plan is None:
        parser.error("--director-plan is required for manager planning")
    master = json.loads(args.director_plan.read_text(encoding="utf-8"))
    approved = review_team(master, args.team)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(approved, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"team": args.team, "approved": True,
                      "children": [x["role"] for x in approved["children"]]}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(cli())
