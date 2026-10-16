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
    # M2 topology review is deliberately stricter than "job completed". Closed
    # bodies must have no open edges; deliberately open cloth/architecture may.
    # All models must still have zero nonmanifold edge multiplicity before being
    # declared topology-ready. None is auto-approved.
    topology_files=sorted(collected.rglob("*_topology_report.json"))
    topology=[]
    unresolved=[]
    for file in topology_files:
        try:
            row=json.loads(file.read_text())
            before,after=row["before"],row["after"]
            for key in ("boundary_edges","nonmanifold_edges","degenerate_triangles","triangles"):
                if not isinstance(before.get(key),int) or not isinstance(after.get(key),int):
                    raise ValueError("Missing numeric topology evidence")
            if not row.get("topology_improved",False):
                issues.append(f"{file}: topology counts regressed")
            if not row.get("candidate"):
                issues.append(f"{file}: missing repaired-candidate field")
            shape=file.stem.replace("_repaired_topology_report","")
            record={
                "asset":shape,"role":file.parent.name,
                "input_triangles":before["triangles"],
                "output_triangles":after["triangles"],
                "before_boundary":before["boundary_edges"],
                "after_boundary":after["boundary_edges"],
                "before_nonmanifold":before["nonmanifold_edges"],
                "after_nonmanifold":after["nonmanifold_edges"],
                "removed_duplicate_faces":row.get("coincident_faces_removed",0),
                "inserted_small_hole_faces":row.get("small_hole_triangles_inserted",0)
            }
            topology.append(record)
            defects=[]
            if after["nonmanifold_edges"]>0:
                defects.append("remaining nonmanifold edges")
            if after["degenerate_triangles"]>0:
                defects.append("remaining degenerate faces")
            if "human" in shape and after["boundary_edges"]>0:
                defects.append("remaining open body boundary edges")
            if defects:
                unresolved.append({"asset":shape,"role":file.parent.name,
                    "defects":defects,"after_boundary":after["boundary_edges"],
                    "after_nonmanifold":after["nonmanifold_edges"]})
        except (OSError,KeyError,ValueError,TypeError) as error:
            issues.append(f"{file}: invalid topology review: {error}")
    if len(topology_files)!=5:
        issues.append(f"Expected five independent M2 topology reports, got {len(topology_files)}")
    out.mkdir(parents=True,exist_ok=True)
    result={
        "schema_version":2,"engine":"VEILFORGE","sources":expected,
        "roles_with_reports":sorted(evidence),"mesh_reports":len(audits),
        "gates_passed":not issues, "issues":issues,
        "topology_quality_passed":not issues and not unresolved,
        "topology_reports":topology,
        "unresolved_topology":unresolved,
        "asset_automatically_promoted":False,
        "photorealism_verified":False,
        "human_visual_signoff":False,
        "recommendation":"Inspect source geometry, topology, all 14 previews, skin/steel/stone materials, and phone screenshots before approving."
    }
    (out/"forge_review.json").write_text(json.dumps(result,indent=2)+"\n")
    md=(["# VEILFORGE M2 — Asset production and topology review","",
        f"Production evidence: {len(evidence)}/6 roles, {len(audits)} canonical mesh audits, {len(topology)} topology comparisons.",
        "",
        f"CI structural evidence: {'PASS' if not issues else 'FAIL'}",
        f"Source topology quality: {'PASS' if not unresolved and not issues else 'PENDING / UNRESOLVED'}",
        "","**No automatic game integration, photorealism signoff, or visual approval.**",
        "","| Asset | Boundary before -> after | Nonmanifold before -> after |",
        "|---|---:|---:|"] + [
          f"| {m['asset']} | {m['before_boundary']} -> {m['after_boundary']} | {m['before_nonmanifold']} -> {m['after_nonmanifold']} |"
          for m in topology
        ] + ["","Remaining geometry defects:"] +
        ([f"- {x['asset']}: {', '.join(x['defects'])} (boundaries {x['after_boundary']}, nonmanifold {x['after_nonmanifold']})" for x in unresolved]
         if unresolved else ["- None detected by these discrete edge counters. Visual approval still pending."]) +
        ["","CI evidence failures:"] +
        (["- "+msg for msg in issues] if issues else ["- None"]))
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
