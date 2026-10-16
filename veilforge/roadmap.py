#!/usr/bin/env python3
"""Read-only verified-capability roadmap and safe next-iteration planner.

No automatic approval, code execution or GitHub writes. An empty/finished
roadmap is never inferred from a passing CI run. Only a reviewer can change
milestone status after concrete acceptance evidence has been inspected.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

STATUS=("verified","partial","planned")
ROLES={"models","materials","animation","studio","world","combat"}
def validate(plan):
    if not isinstance(plan,dict) or plan.get("schema_version")!=1:
        raise ValueError("Roadmap must be schema-versioned")
    rows=plan.get("milestones")
    if not isinstance(rows,list) or not rows or len(rows)>100:
        raise ValueError("Roadmap requires bounded milestones")
    ids={}
    for row in rows:
        if not isinstance(row,dict) or set(row)!={"id","domain","name","status","gate","depends_on","owner","automatic_approval"}:
            raise ValueError("Malformed milestone")
        ident=row["id"]
        if not isinstance(ident,str) or not ident.startswith("VF-") or not ident[3:].isdigit() or ident in ids:
            raise ValueError("Invalid milestone identifier")
        if row["status"] not in STATUS or row["owner"] not in ROLES:
            raise ValueError("Invalid milestone status or owner")
        if not isinstance(row["gate"],str) or len(row["gate"].strip())<16:
            raise ValueError("Missing measurable completion gate")
        if row["automatic_approval"] is not False:
            raise ValueError("Automatic milestones cannot bypass human review")
        if not isinstance(row["depends_on"],list) or len(set(row["depends_on"]))!=len(row["depends_on"]):
            raise ValueError("Duplicate dependencies")
        ids[ident]=row
    state={}
    def visit(k):
        if k not in ids:
            raise ValueError("Missing dependency "+k)
        if state.get(k)==1:
            raise ValueError("Dependency cycle")
        if state.get(k)==2:
            return
        state[k]=1
        for dep in ids[k]["depends_on"]:
            visit(dep)
            if ids[k]["status"]=="verified" and ids[dep]["status"]!="verified":
                raise ValueError("Verified milestone depends on unverified work")
        state[k]=2
    for k in ids:visit(k)
    return ids

def summarize(path):
    plan=json.loads(Path(path).read_text(encoding="utf-8"))
    ids=validate(plan)
    counts={k:sum(x["status"]==k for x in ids.values()) for k in STATUS}
    eligible=[r for r in ids.values() if r["status"]!="verified" and
              all(ids[d]["status"]=="verified" for d in r["depends_on"])]
    eligible.sort(key=lambda r:(0 if r["status"]=="partial" else 1,int(r["id"][3:])))
    blocked=[r["id"] for r in ids.values() if r["status"]!="verified" and r not in eligible]
    all_complete=(counts["verified"]==len(ids))
    return {"schema_version":1,"engine":"VEILFORGE","milestone_count":len(ids),
            "counts":counts,"acceptance_complete":False,
            "all_technical_milestones_verified":all_complete,
            "pending_human_release_signoff":True,
            "next_safe_candidate":(
                {"id":eligible[0]["id"],"name":eligible[0]["name"],
                 "gate":eligible[0]["gate"],"owner":eligible[0]["owner"]}
                if eligible else None),
            "eligible": [r["id"] for r in eligible],
            "blocked_by_dependencies":blocked,
            "message": "Human artistic/game-import approval remains required even after all technical milestone gates."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--plan",type=Path,default=Path("veilforge/ENGINE_MASTER_PLAN.json"))
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    summary=summarize(a.plan)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"roadmap_status.json").write_text(json.dumps(summary,indent=2)+"\n")
    lines=["# VEILFORGE Continuous Engine Roadmap","",
          f"Verified: {summary['counts']['verified']}/{summary['milestone_count']} technical capability groups.",
          f"Partial: {summary['counts']['partial']} | Planned: {summary['counts']['planned']}",
          "","A green production CI run does not mean photorealism or release approval.","",
          "## Next available engine improvement",""]
    nxt=summary["next_safe_candidate"]
    lines.append(f"{nxt['id']} — {nxt['name']}: {nxt['gate']}" if nxt else
                 "No unblocked technical milestone; human review or new dependencies required.")
    (a.out/"roadmap_status.md").write_text("\n".join(lines)+"\n")
    print("VEILFORGE_ROADMAP",json.dumps({"counts":summary["counts"],
          "next":summary["next_safe_candidate"]}))
if __name__=="__main__":
    main()
