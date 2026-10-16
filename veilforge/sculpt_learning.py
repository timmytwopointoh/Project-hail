#!/usr/bin/env python3
"""VEILFORGE M26: review-driven, reproducible sculpt lessons and mesh evidence.

This is a deterministic, bounded search curriculum, NOT autonomous vision or
training of a neural network. Every defect label comes from a human-reviewed
record with source evidence. The engine turns those labels into candidate
geometry controls, compares real OBJ meshes, and stops for visual approval.
"""
from __future__ import annotations
import argparse
from collections import Counter
from hashlib import sha256
from itertools import zip_longest
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRICULUM = ROOT / "veilforge/sculpt_curriculum.json"
LESSONS = ROOT / "veilforge/feedback/sculpt_lessons.json"

DIALS = ("eye_recession", "upper_lid_transition", "cheek_plane",
         "nose_bridge", "jaw_transition", "shoulder_flow", "chest_flow",
         "ankle_transition")
DEFECT_TO_DIAL = {
    "protruding_eyes": {"eye_recession": 1.0, "upper_lid_transition": .36},
    "flat_eyelids": {"upper_lid_transition": 1.0},
    "inflated_cheeks": {"cheek_plane": 1.0, "jaw_transition": .24},
    "weak_nose_bridge": {"nose_bridge": 1.0},
    "puppet_jaw": {"jaw_transition": 1.0, "cheek_plane": .22},
    "lumpy_shoulders": {"shoulder_flow": 1.0},
    "capsule_chest": {"chest_flow": 1.0},
    "stump_ankles": {"ankle_transition": 1.0},
}
GROUPS = {"face": ("S2",), "surface": ("S4",),
          "feet": ("S3",), "full": ("S2", "S3", "S4")}
STRENGTHS = {"baseline": 0.0, "cautious": .40,
             "balanced": .72, "assertive": 1.0}
PROTECTED = ("armor_hero", "historical_knight", "hair",
             "shorts", "m25_source", "combat_loop")

def load_records(curriculum: Path = CURRICULUM, lessons: Path = LESSONS):
    c = json.loads(curriculum.read_text(encoding="utf-8"))
    m = json.loads(lessons.read_text(encoding="utf-8"))
    if c.get("schema_version") != 1 or m.get("schema_version") != 1:
        raise ValueError("Unsupported sculpt-curriculum schema")
    if tuple(x["id"] for x in c["dials"]) != DIALS:
        raise ValueError("Sculpt dial order differs from compiled Java contract")
    allowed = set(c["feedback_schema"]["allowed_defects"])
    if allowed != set(DEFECT_TO_DIAL):
        raise ValueError("Learning labels differ from documented curriculum")
    stage = {s["id"] for s in c["stages"]}
    found_ids = set()
    for row in m["records"]:
        if row["id"] in found_ids:
            raise ValueError("Duplicate sculpt-lesson identity")
        found_ids.add(row["id"])
        if row["stage"] not in stage or row["defect"] not in allowed:
            raise ValueError("Lesson refers to an unknown stage/defect")
        if not (1 <= row["severity"] <= 5 and
                isinstance(row["confidence"], (int,float)) and
                0 <= row["confidence"] <= 1):
            raise ValueError("Invalid lesson severity/confidence")
        if row["decision"] not in c["feedback_schema"]["decision_values"]:
            raise ValueError("Invalid manual decision")
        e = row["evidence"]
        if not all(e.get(k) for k in ("source_run", "artifact", "views", "kind")):
            raise ValueError("Lesson without verifiable source metadata")
        if e["kind"] != "actual_offline_mesh_projection":
            raise ValueError("Unverified evidence kind")
        if not all(isinstance(x,str) and x.endswith(".png") for x in e["views"]):
            raise ValueError("Lesson source views must be PNG filenames")
    if m.get("automatic_image_interpretation") is not False or m["safety"]["auto_promote"]:
        raise ValueError("Sculpt learner may not pretend to infer reference pixels")
    return c, m

def candidates(focus: str, curriculum=CURRICULUM, lessons=LESSONS):
    if focus not in GROUPS:
        raise ValueError("Unknown specialist focus")
    _, memory = load_records(curriculum, lessons)
    weight = {d: 0.0 for d in DIALS}
    used = []
    for row in memory["records"]:
        if row["stage"] not in GROUPS[focus]:
            continue
        used.append(row["id"])
        signed = row["severity"] * row["confidence"] / 5.0
        for dial, factor in DEFECT_TO_DIAL[row["defect"]].items():
            weight[dial] += signed * factor
    target = {name: min(1.0, round(value, 6)) for name,value in weight.items()}
    trials = []
    for label, strength in STRENGTHS.items():
        controls = [round(min(1.0, target[dial]*strength), 6) for dial in DIALS]
        trials.append({
            "id": label,
            "dial_values": controls,
            "csv": ",".join(f"{v:.6f}" for v in controls),
            "priority_magnitude_not_visual_score": round(sum(controls), 6),
            "auto_promote": False,
            "human_visual_review_required": True,
        })
    return {
        "schema_version":1, "engine":"VEILFORGE", "iteration":"M26",
        "focus": focus, "source":"human_labeled_prior_visual_defects",
        "lesson_ids": sorted(used), "dial_names":list(DIALS),
        "candidates":trials,
        "silhouette_likeness_measured":False,
        "photorealism_verified":False,
        "accepted_for_game":False,
        "learning_method":"deterministic bounded review-conditioned exploration",
        "reference":"Bellwarden Base Body Test",
        "protected":list(PROTECTED),
    }

def write_map(out: Path, curriculum=CURRICULUM, lessons=LESSONS):
    c,m=load_records(curriculum, lessons)
    out.mkdir(parents=True, exist_ok=True)
    counts=Counter(row["stage"] for row in m["records"])
    lines=["# VEILFORGE — Sculpting Skill Map (M26)","",
           "**This is a sequence of executable modeling lessons, not a claim of neural-network training.**",
           "All candidate proposals are read-only to playable game source and require artist review.",
           "",
           "Reference: Bellwarden Base Body Test.  Original Bellwarden knight and basic hair stay unchanged.",
           "",
           "| Stage | Focus | Evidence lessons | Skill/acceptance gates |",
           "|---|---|---:|---|"]
    for s in c["stages"]:
        lines.append(f"| {s['id']} | {s['name']} | {counts[s['id']]} | "+
                     "; ".join(s["gates"])+" |")
    lines.extend(["","## Closed-loop operating procedure","",
       "1. Preserve user-verified baseline and archive failed real-render examples.",
       "2. Reviewer labels visible defect with evidence run, camera files, severity and confidence.",
       "3. Manager maps label to bounded anatomy-specific sculpt controls; never infer labels from pixels automatically.",
       "4. Isolated workers build M25 baseline and 3 distinct M26 candidate meshes (plus zero-dial test).",
       "5. Validate mesh invariants, normals, digit preservation, non-manifold/boundary changes and all source hashes.",
       "6. Inspect 14 real-mesh angles and 3 close-up face views for each shortlist candidate.",
       "7. Manually reject/approve lessons; append provenance-backed records, not runtime self-modifying code.",
       "8. Test approved geometry in VEILFORGE Testing Grounds (same APK, synchronized Android 15 emulators).",
       "9. Promote to gameplay only by a separate explicit review and regression process.",
       "",
       "## Mandatory blockers","",
       "- Open boundaries or topology regressions must remain visible and never silently auto-repaired in the game.",
       "- No visual/photorealism claim based only on a numeric proxy, CI green check or higher polygon count.",
       "- No source image likeness is measured by the current program; manual review remains essential.",
       "- Keep baseline Bellwarden armor and historical knight; zero hair refinement until requested.",
       ""])
    (out/"SCULPT_SKILL_MAP.md").write_text("\n".join(lines),encoding="utf-8")
    status={"stages":len(c["stages"]), "recorded_manual_defects":len(m["records"]),
            "source_reference":m["source_reference"],"learner_mode":"review_conditioned",
            "auto_promote":False,"visual_signoff":False}
    (out/"map_summary.json").write_text(json.dumps(status,indent=2)+"\n")
    return status

def _verts(path: Path):
    with path.open(encoding="utf-8",errors="replace") as file:
        for line in file:
            if line.startswith("v "):
                bits=line.split()
                if len(bits)<4:
                    raise ValueError("Malformed OBJ vertex")
                values=[float(x) for x in bits[1:7]]
                if not all(math.isfinite(x) for x in values):
                    raise ValueError("Non-finite OBJ coordinates/materials")
                yield values

def mesh_delta(before: Path, after: Path):
    changed=0
    count=0
    max_shift=0.0
    protected_changed=0
    regions=Counter()
    total=0.0
    for orig,new in zip_longest(_verts(before), _verts(after)):
        if orig is None or new is None:
            raise ValueError("Candidate changed mesh vertex count")
        count+=1
        if len(orig)!=len(new):
            raise ValueError("Vertex colors absent in baseline/candidate")
        distance=math.dist(orig[:3],new[:3])
        if orig[3:]!=new[3:]:
            raise ValueError("M26 must preserve source material vertex colors")
        total+=distance
        max_shift=max(max_shift,distance)
        if distance<.000008:
            continue
        changed+=1
        x,y,z=orig[:3]
        red,green,blue=orig[3:6]
        hair=(y>2.50 and red<.24 and green<.24 and blue<.24)
        shorts=(.87<y<1.22 and abs(x)<.41 and
                red<.27 and green<.27 and blue<.27)
        if hair or shorts:
            protected_changed+=1
        if y>2.27: region="head"
        elif y>1.55: region="torso_shoulders"
        elif y<.46: region="feet_ankles"
        else: region="other"
        regions[region]+=1
    if not count:raise ValueError("No OBJ geometry")
    return {"vertices_compared":count, "vertices_moved":changed,
            "maximum_displacement":round(max_shift,8),
            "average_displacement":round(total/count,8),
            "protected_regions_modified":protected_changed,
            "changed_regions":dict(regions)}

def compare(focus: str, before: Path, after: Path, out: Path,
            plan: Path | None = None, candidate_id: str = "balanced"):
    from engine import inspect_obj
    if not before.is_file() or not after.is_file():
        raise FileNotFoundError("Source and candidate OBJ required")
    result=mesh_delta(before,after)
    baseline=inspect_obj(before)
    sculpted=inspect_obj(after)
    max_extra_boundaries=max(20,int(baseline["boundary_edges"]*.04))
    gates={
        "source_and_candidate_have_matching_vertices":True,
        "real_vertex_deformation":result["vertices_moved"]>50,
        "bounded_deformation":result["maximum_displacement"]<=.029,
        "hair_and_clothing_protected":result["protected_regions_modified"]==0,
        "nonmanifold_not_regressed":
            sculpted["nonmanifold_edges"]<=baseline["nonmanifold_edges"],
        "degenerate_faces_not_regressed":
            sculpted["degenerate_triangles"]<=baseline["degenerate_triangles"],
        "boundary_edges_not_regressed_beyond_numeric_tolerance":
            sculpted["boundary_edges"]<=baseline["boundary_edges"]+max_extra_boundaries,
        "triangle_count_unchanged":baseline["triangles"]==sculpted["triangles"],
        "camera_evidence_still_requires_human_review":True
    }
    if plan:
        manifest=json.loads(plan.read_text())
        choices=[x for x in manifest["candidates"] if x["id"]==candidate_id]
        if manifest["focus"]!=focus or len(choices)!=1:
            raise ValueError("Candidate provenance mismatch")
        vector=choices[0]["dial_values"]
        if all(v==0 for v in vector):
            gates["real_vertex_deformation"]=result["vertices_moved"]==0
    else:
        vector=[]
    audit={
        "schema_version":1,"engine":"VEILFORGE","iteration":"M26",
        "focus":focus,"candidate_id":candidate_id,"dial_values":vector,
        "baseline_obj_sha256":sha256(before.read_bytes()).hexdigest(),
        "candidate_obj_sha256":sha256(after.read_bytes()).hexdigest(),
        "mesh_changes":result,
        "baseline":{"triangles":baseline["triangles"],
                    "boundary_edges":baseline["boundary_edges"],
                    "nonmanifold_edges":baseline["nonmanifold_edges"],
                    "degenerate_triangles":baseline["degenerate_triangles"]},
        "candidate":{"triangles":sculpted["triangles"],
                    "boundary_edges":sculpted["boundary_edges"],
                    "nonmanifold_edges":sculpted["nonmanifold_edges"],
                    "degenerate_triangles":sculpted["degenerate_triangles"]},
        "gates":gates,"numeric_geometry_gates_passed":all(gates.values()),
        "reference_likeness_evaluated":False,"human_visual_review_required":True,
        "accepted_for_game":False,"auto_promoted":False
    }
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(audit,indent=2)+"\n")
    return audit

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("map")
    p.add_argument("--out",type=Path,required=True)
    p=sub.add_parser("propose")
    p.add_argument("--focus",choices=GROUPS,required=True)
    p.add_argument("--out",type=Path,required=True)
    p=sub.add_parser("print-csv")
    p.add_argument("--plan",type=Path,required=True)
    p.add_argument("--candidate",choices=STRENGTHS,required=True)
    p=sub.add_parser("compare")
    p.add_argument("--focus",choices=GROUPS,required=True)
    p.add_argument("--before",type=Path,required=True)
    p.add_argument("--after",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--plan",type=Path,required=True)
    p.add_argument("--candidate",choices=STRENGTHS,default="balanced")
    a=ap.parse_args()
    if a.cmd=="map":
        print(json.dumps(write_map(a.out)))
    elif a.cmd=="propose":
        plan=candidates(a.focus)
        a.out.parent.mkdir(parents=True,exist_ok=True)
        a.out.write_text(json.dumps(plan,indent=2)+"\n")
        print(json.dumps({"focus":a.focus,"candidates":len(plan["candidates"]),
                          "labelled_source_lessons":len(plan["lesson_ids"])}))
    elif a.cmd=="print-csv":
        plan=json.loads(a.plan.read_text())
        row=[x for x in plan["candidates"] if x["id"]==a.candidate]
        if len(row)!=1:raise ValueError("Candidate missing")
        print(row[0]["csv"])
    else:
        r=compare(a.focus,a.before,a.after,a.out,a.plan,a.candidate)
        print("M26_SCULPT_EVIDENCE",json.dumps({
            "focus":a.focus,"passed":r["numeric_geometry_gates_passed"],
            "moved":r["mesh_changes"]["vertices_moved"],
            "approved":r["accepted_for_game"]}))
        if not r["numeric_geometry_gates_passed"]:
            raise SystemExit(1)

if __name__=="__main__":main()
