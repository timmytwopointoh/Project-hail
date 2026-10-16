#!/usr/bin/env python3
"""Stage an immutable, SHA-256 verified VQ Studio geometry snapshot for Android.

Run metadata and checks are written before upload; no game source is changed.
'geometry_integrity' means geometry parsed, NOT visually approved.
'technical_review' means independent VQ 14-angle+glTF QA passed, NOT artistic approval.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"veilforge"))
from engine import inspect_obj

MAX_OBJ=8*1024*1024

def digest(f:Path)->str:
    h=hashlib.sha256()
    with f.open("rb") as src:
        for b in iter(lambda:src.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()

def stage(obj:Path,out:Path,request_id:str,run_id:str,sequence:int,
          source_commit:str,report:Path|None=None)->dict:
    if not re.fullmatch(r"[a-f0-9]{16}",request_id):
        raise ValueError("Invalid VQ request ID")
    if not re.fullmatch(r"[1-9][0-9]{0,17}",run_id):
        raise ValueError("Invalid GitHub run identifier")
    if sequence not in (1,2):
        raise ValueError("Unrecognized VQ revision number")
    if not re.fullmatch(r"[0-9a-f]{40}",source_commit):
        raise ValueError("Not a Git source commit")
    if (not obj.is_file() or obj.is_symlink() or obj.suffix.lower()!=".obj"
        or obj.stat().st_size>MAX_OBJ or obj.stat().st_size<25):
        raise ValueError("Invalid, missing or oversized OBJ source")
    metrics=inspect_obj(obj)
    if metrics["degenerate_triangles"] or metrics["duplicate_triangles"]:
        raise ValueError("Source fails basic mesh integrity")
    if not metrics["triangles"] or metrics["triangles"]>120000:
        raise ValueError("Unsupported source mesh budget")
    quality="geometry_integrity"
    if sequence==2:
        if report is None or not report.is_file():
            raise ValueError("Revision 2 requires independent VQ 14-view QA")
        qa=json.loads(report.read_text(encoding="utf-8"))
        if (qa.get("engine")!="VEYLQUORIN" or
            qa.get("source_sha256")!=digest(obj) or
            qa.get("technical_geometry_smoke_passed") is not True or
            qa.get("production_approved") is not False or
            qa.get("gltf",{}).get("structural_smoke_passed") is not True or
            len(qa.get("visual",{}).get("views",[]))!=14):
            raise ValueError("No valid matching technical QA")
        quality="technical_review"
    elif report is not None:
        raise ValueError("Revision 1 must not masquerade as fully QA reviewed")
    if out.exists() and any(out.iterdir()):
        raise ValueError("Snapshot stage must begin empty")
    out.mkdir(parents=True,exist_ok=True)
    model=out/"model.obj"
    shutil.copyfile(obj,model)
    payload={
        "schema_version":1,
        "engine":"VEYLQUORIN",
        "request_id":request_id,"github_run_id":run_id,
        "source_commit":source_commit,
        "sequence":sequence,"file":"model.obj",
        "source_asset":obj.stem,
        "bytes":model.stat().st_size,
        "obj_sha256":digest(model),
        "triangles":metrics["triangles"],
        "quality_stage":quality,
        "observed_at_utc":datetime.now(timezone.utc).isoformat(),
        "artist_approved":False,"production_approved":False,
        "verification":"source-hash-plus-geometry-and-optional-independent-review"
    }
    (out/"vq_snapshot.json").write_text(json.dumps(payload,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return payload

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--obj",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--request-id",required=True)
    parser.add_argument("--run-id",required=True)
    parser.add_argument("--sequence",type=int,required=True)
    parser.add_argument("--source-commit",required=True)
    parser.add_argument("--report",type=Path)
    a=parser.parse_args()
    result=stage(a.obj,a.out,a.request_id,a.run_id,a.sequence,a.source_commit,a.report)
    print("VQ_LIVE_SNAPSHOT_VERIFIED",result["sequence"],result["quality_stage"],
          result["obj_sha256"],"triangles",result["triangles"])

if __name__=="__main__":main()
