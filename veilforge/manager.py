#!/usr/bin/env python3
"""Review-only manager of managers. Reuses existing Project-hail roles/safety."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

def plan(backlog: Path, out: Path, max_workers: int):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"veilbound"/"scripts"))
    from worker_manager import plan as existing_plan
    data=json.loads(backlog.read_text(encoding="utf-8"))
    assigned=existing_plan(data,{},max_workers=max_workers)
    out.mkdir(parents=True,exist_ok=True)
    (out/"worker_plan.json").write_text(json.dumps(assigned,indent=2)+"\n")
    return assigned

def review(collected: Path, out: Path):
    expected = ("human","models","materials","animation","world","studio")
    evidence = {}
    issues = []
    for role in expected:
        candidates = list(collected.rglob("engine_report.json")) if role!="human" else list(collected.rglob("forge_human.json"))
        matches = []
        for file in candidates:
            if role=="human" and file.parent.name=="human":
                matches.append(file)
            elif role!="human" and file.parent.name==role:
                matches.append(file)
        if len(matches)!=1:
            issues.append(f"{role}: expected exactly one isolated engine report, found {len(matches)}")
            continue
        try:
            evidence[role] = json.loads(matches[0].read_text())
        except (ValueError,OSError):
            issues.append(f"{role}: unreadable or invalid JSON")
            continue
        if role=="human":
            images=list(matches[0].parent.glob("turntable_*.png"))
            if len(images)!=14:
                issues.append("human: 14 actual mesh projections are required")
            if not (matches[0].parent/"human_source.obj").is_file():
                issues.append("human: missing source OBJ")
    audits = list(collected.rglob("mesh_quality.json"))
    if not audits:
        issues.append("No independent mesh-quality reports")
    for audit in audits:
        try:
            value=json.loads(audit.read_text())
            if value.get("triangles",0)<1:
                issues.append(f"{audit}: empty mesh")
            if value.get("degenerate_triangles",0)>value.get("triangles",0)*.02:
                issues.append(f"{audit}: >2% degenerates")
        except (ValueError,OSError):
            issues.append(f"{audit}: invalid QA data")
    out.mkdir(parents=True,exist_ok=True)
    result={
        "schema_version":1,"engine":"VEILFORGE","sources":expected,
        "roles_with_reports":sorted(evidence),"mesh_reports":len(audits),
        "gates_passed":not issues, "issues":issues,
        "asset_automatically_promoted":False,
        "photorealism_verified":False,
        "human_visual_signoff":False,
        "recommendation":"Inspect source geometry, topology, all 14 previews, skin/steel/stone materials, and phone screenshots before approving."
    }
    (out/"forge_review.json").write_text(json.dumps(result,indent=2)+"\n")
    md=["# VEILFORGE M1 — Asset production review","",
        f"Evidence received: {len(evidence)}/6 independent roles, {len(audits)} mesh audits.",
        "","**No automatic game integration or approval.**",
        "","Failures:"] + (["- "+msg for msg in issues] if issues else ["- No missing CI artifacts. Visual quality remains unapproved."])
    (out/"forge_review.md").write_text("\n".join(md)+"\n")
    return result

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="cmd",required=True)
    t=sub.add_parser("plan")
    t.add_argument("--backlog",type=Path,default=Path("veilforge/backlog.json"))
    t.add_argument("--out",type=Path,required=True)
    t.add_argument("--max-workers",type=int,default=12)
    a=sub.add_parser("review")
    a.add_argument("--collected",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=plan(args.backlog,args.out,args.max_workers) if args.cmd=="plan" else review(args.collected,args.out)
    print(json.dumps({"engine":"VEILFORGE","status": "review-only","details":result.get("gates_passed"),"allocated":result.get("allocated")}))
    if args.cmd=="review" and not result["gates_passed"]:
        raise SystemExit(1)
if __name__=="__main__":
    main()
