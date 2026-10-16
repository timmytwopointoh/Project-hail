#!/usr/bin/env python3
"""Validate VQ/VEILFORGE completion gates and produce an honest progress report."""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).parent
PLAN=HERE/"VQ_ENGINE_QUALITY_PLAN.json"
VALID={"planned","partial","in_progress","verified"}
def review(path=PLAN,out=None):
    doc=json.loads(Path(path).read_text(encoding="utf-8"))
    milestones=doc.get("milestones",[])
    if doc.get("schema_version")!=1 or len(milestones)<30:
        raise ValueError("Missing comprehensive quality roadmap")
    used=set();counts=Counter()
    for row in milestones:
        ident=row["id"]
        if ident in used or not (isinstance(ident,str) and len(ident)>=5):
            raise ValueError("Duplicated/invalid milestone id")
        used.add(ident)
        if row["status"] not in VALID or row["priority"] not in ("P0","P1","P2"):
            raise ValueError("Unsupported roadmap milestone status/priority")
        if row.get("automatic_game_approval") is not False:
            raise ValueError("Milestone cannot authorize automatic game approval")
        if row["status"]=="verified" and not row.get("verified_evidence"):
            raise ValueError("Verified milestones require explicit provenance evidence")
        if not row["objective"] or not row["acceptance"]:
            raise ValueError("Missing measurable objective/acceptance")
        counts[row["status"]]+=1;counts[row["priority"]]+=1
    if set(doc.get("release_gates",[]))!={"source_hash_and_license",
        "topology_and_attributes","UV_tangent_material",
        "full_asset_import_and_export","14_real_view_source_inspection",
        "real_android_gles_texture_and_camera_qa",
        "reference_appearance_human_signoff",
        "performance_budget_on_target_devices_when_relevant",
        "no_unreviewed_auto_merge"}:
        raise ValueError("Critical release gates omitted/modified")
    result={"schema_version":1,"engine":"VEYLQUORIN / VEILFORGE",
            "milestones":len(milestones),"planned":counts["planned"],
            "partial":counts["partial"],"active":counts["in_progress"],
            "verified":counts["verified"],
            "p0":counts["P0"],"p1":counts["P1"],"p2":counts["P2"],
            "definition_of_done_requires_reference_and_device_review":True,
            "all_milestones_verified":counts["verified"]==len(milestones),
            "game_auto_promotion_allowed":False}
    if out:
        path=Path(out);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(result,indent=2)+"\n")
    return result
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--plan",type=Path,default=PLAN)
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    result=review(args.plan,args.out)
    print("VQ_MASTER_QUALITY_PLAN",json.dumps(result))
if __name__=="__main__":main()
