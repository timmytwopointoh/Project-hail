#!/usr/bin/env python3
"""VQ Studio screenshot cache policy.

Keep visual evidence until the technical check is complete and the NEXT STEP
is recorded. Afterward retain a small contact sheet, latest close-up, verified
SHA256 model/report identities, and enough metadata for manual review.

Only delete the explicitly enumerated TEMPORARY orbit/mask PNG files from
a bounded sandbox directory. Never purge the source OBJ, glTF, materials,
provenance manifest, reviewed checkpoint or an Android emulator raw capture
prior to its independent quality audit.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

NEXT_ACTIONS={
  "needs_artist_review",
  "request_reference_alignment",
  "repair_mesh_defects",
  "approve_after_review",
}
MAX_FRAMES=14

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def bounded(root:Path,path:Path)->Path:
    path=path.resolve(strict=True)
    if path.parent!=root.resolve() or path.is_symlink():
        raise ValueError("Screenshots must be direct regular children of sandbox")
    if not path.is_file():
        raise ValueError("Nonregular screenshot cannot be pruned")
    return path

def prune(inspect_dir:Path,out_dir:Path,*,next_action:str)->dict:
    if next_action not in NEXT_ACTIONS:
        raise ValueError("No recognized next modeling step; keep screenshots")
    inspect_dir=inspect_dir.resolve(strict=True)
    out_dir=out_dir.resolve()
    if out_dir.is_relative_to(inspect_dir) or inspect_dir.is_relative_to(out_dir):
        raise ValueError("Output must be separate from temporary screenshot directory")
    report_path=inspect_dir/"vq_model_report.json"
    if not report_path.is_file():raise ValueError("Cannot release screenshots without VQ model QA report")
    report=json.loads(report_path.read_text(encoding="utf-8"))
    frames=report.get("visual",{}).get("views",[])
    if (report.get("engine")!="VEYLQUORIN" or len(frames)!=MAX_FRAMES
        or report.get("technical_geometry_smoke_passed") is not True
        or report.get("production_approved") is not False
        or report.get("human_review_required") is not True):
        raise ValueError("Quality/provenance gate not complete; preserve raw frames")
    views=inspect_dir/"views"
    if not views.is_dir() or views.is_symlink():
        raise ValueError("Untrusted screenshot directory")
    signed=[]
    expected={}
    for i,frame in enumerate(frames):
        if frame.get("view_index")!=i:
            raise ValueError("Wrong orbit index")
        for field,checksum in (("image","image_sha256"),("mask","mask_sha256")):
            name=frame.get(field)
            if not isinstance(name,str) or "/" in name or "\\" in name or name in (".",".."):
                raise ValueError("Unsafe screenshot basename")
            if name in expected:raise ValueError("Duplicate screenshot path")
            file=bounded(views,views/name)
            if sha256(file)!=frame.get(checksum):
                raise ValueError("Image evidence altered before cleanup")
            expected[name]=frame[checksum]
        signed.append({"yaw":frame["yaw"],"pitch":frame["pitch"],"sha256":frame["image_sha256"]})
    contact=bounded(views,views/"contact_sheet.png")
    if sha256(contact)!=report["visual"]["contact_sheet_sha256"]:
        raise ValueError("Contact sheet changed since review")
    out_dir.mkdir(parents=True,exist_ok=True)
    if any(out_dir.iterdir()):
        raise ValueError("Evidence output must start empty")
    # First publish durable reviewable evidence and a concrete next step.
    shutil.copyfile(contact,out_dir/"contact_sheet.png")
    last=bounded(views,views/frames[-1]["image"])
    shutil.copyfile(last,out_dir/"latest_orbit.png")
    shutil.copyfile(report_path,out_dir/"vq_model_report.json")
    checkpoint={
       "schema_version":1,"engine":"VEYLQUORIN","mode":"review_evidence_after_qa",
       "next_action":next_action,
       "source_obj_sha256":report["source_sha256"],
       "model_report_sha256":sha256(out_dir/"vq_model_report.json"),
       "saved_contact_sha256":sha256(out_dir/"contact_sheet.png"),
       "saved_orbit_sha256":sha256(out_dir/"latest_orbit.png"),
       "transient_frames_verified":len(expected),
       "transient_frame_hashes":expected,
       "deleted_only_after_next_action_recorded":True,
       "artistic_approval":False,
    }
    tmp=out_dir/"checkpoint.tmp"
    tmp.write_text(json.dumps(checkpoint,indent=2)+"\n",encoding="utf-8")
    tmp.replace(out_dir/"checkpoint.json")
    # Fail closed before releasing scratch data; do not remove the saved copies.
    saved=json.loads((out_dir/"checkpoint.json").read_text())
    if saved["next_action"]!=next_action or sha256(out_dir/"latest_orbit.png")!=saved["saved_orbit_sha256"]:
        raise ValueError("Durable checkpoint could not be verified")
    for name in expected:
        (views/name).unlink()
    return checkpoint

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--inspection",type=Path,required=True)
    parser.add_argument("--evidence",type=Path,required=True)
    parser.add_argument("--next-action",choices=sorted(NEXT_ACTIONS),required=True)
    args=parser.parse_args()
    proof=prune(args.inspection,args.evidence,next_action=args.next_action)
    print("VQ_GC_PASS",proof["next_action"],"screenshots_released",proof["transient_frames_verified"])

if __name__=="__main__":
    main()
