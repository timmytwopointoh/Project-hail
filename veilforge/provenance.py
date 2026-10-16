#!/usr/bin/env python3
"""Source fingerprint, recorded CI time, and human rights-claim evidence.

A GitHub attestation can sign the output file as a provenance witness.
A content digest is not itself a signature or copyright assignment.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo

SCHEMA=1
CLAIMANT="Timothy Harris"
ACCOUNT="timmytwopointoh"


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git","-C",str(root),*args],stderr=subprocess.PIPE).decode("utf-8").strip()


def digest(file: Path) -> str:
    h=hashlib.sha256()
    with file.open("rb") as source:
        for chunk in iter(lambda:source.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def tracked(root: Path) -> list[dict]:
    files=subprocess.check_output(
        ["git","-C",str(root),"ls-files","--cached","-z"])
    seen=set()
    result=[]
    for entry in files.split(b"\x00"):
        if not entry:
            continue
        relative=os.fsdecode(entry)
        if relative in seen:
            raise ValueError("Duplicate tracked pathname")
        seen.add(relative)
        file=(root/relative)
        # Symlinks and submodules are skipped explicitly, never followed.
        if not file.is_file() or file.is_symlink():
            raise ValueError(f"Tracked path is not a regular file: {relative}")
        result.append({
            "path":relative.replace(os.sep,"/"),
            "bytes":file.stat().st_size,
            "sha256":digest(file),
        })
    return sorted(result,key=lambda row:row["path"])


def make_snapshot(root: Path, *, when:datetime|None=None,
                  actor:str|None=None, run_id:str|None=None,
                  run_attempt:str|None=None) -> dict:
    root=root.resolve()
    when=when or datetime.now(timezone.utc)
    if when.tzinfo is None:
        raise ValueError("A timezone-aware clock is mandatory")
    instant=when.astimezone(timezone.utc)
    commit=git(root,"rev-parse","HEAD")
    if len(commit)!=40 or not all(c in "0123456789abcdef" for c in commit):
        raise ValueError("Invalid Git source revision")
    changes=git(root,"status","--porcelain","--untracked-files=no")
    if changes:
        raise ValueError("Tracked files differ from the committed revision")
    files=tracked(root)
    state=json.loads((root/"veilforge/steward_state.json").read_text())
    if (state["claimant"]!=CLAIMANT or state["github_account"]!=ACCOUNT
        or state["repository"]!="timmytwopointoh/Project-hail"):
        raise ValueError("Project owner and account identifiers differ")
    serial=json.dumps(files,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return {
        "schema_version":SCHEMA, "engine":"VEILFORGE",
        "engine_display_name":state.get("display_name","VEILFORGE"),
        "short_name":state.get("short_name"),
        "record_type":"repository_source_manifest",
        "claimed_owner":CLAIMANT,
        "github_account":ACCOUNT,
        "repository":state["repository"],
        "source_commit_sha":commit,
        "observed_at_utc":instant.isoformat().replace("+00:00","Z"),
        "observed_at_america_new_york":instant.astimezone(
            ZoneInfo("America/New_York")).isoformat(),
        "triggering_actor":actor or os.getenv("GITHUB_ACTOR","local"),
        "github_run_id":run_id or os.getenv("GITHUB_RUN_ID") or None,
        "github_run_attempt":run_attempt or os.getenv("GITHUB_RUN_ATTEMPT") or None,
        "github_run_url":(
            "https://github.com/"+state["repository"]+"/actions/runs/"+
            str(run_id or os.getenv("GITHUB_RUN_ID"))
        ) if (run_id or os.getenv("GITHUB_RUN_ID")) else None,
        "file_count":len(files),
        "file_digest_list_sha256":hashlib.sha256(serial.encode("utf-8")).hexdigest(),
        "files":files,
        "rights_notice":"Claim applies only to rights lawfully owned or assigned.",
        "third_party_status":"not_yet_cleared",
        "human_signature_present":False,
        "copyright_registration_attested":False,
        "independent_person_identity_verified":False,
        "not_proof_of_original_creation_date":True,
        "not_claiming_model_weights":True,
    }


def write_snapshot(root:Path,out:Path) -> dict:
    payload=make_snapshot(root)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",
                   encoding="utf-8")
    return payload


def verify_snapshot(root:Path,snapshot:Path) -> bool:
    document=json.loads(snapshot.read_text(encoding="utf-8"))
    if (document.get("schema_version")!=SCHEMA or
        document.get("engine")!="VEILFORGE" or
        document.get("source_commit_sha")!=git(root,"rev-parse","HEAD")):
        raise ValueError("Provenance record source identity mismatch")
    if document.get("claimed_owner")!=CLAIMANT or document.get("github_account")!=ACCOUNT:
        raise ValueError("Provenance record claimant differs")
    actual=tracked(root.resolve())
    if document.get("files")!=actual or document.get("file_count")!=len(actual):
        raise ValueError("Source fingerprint mismatch")
    serial=json.dumps(actual,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    if document.get("file_digest_list_sha256")!=hashlib.sha256(
        serial.encode("utf-8")).hexdigest():
        raise ValueError("Aggregate source fingerprint mismatch")
    return True


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("snapshot","verify"))
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--out",type=Path)
    p.add_argument("--snapshot",type=Path)
    args=p.parse_args()
    if args.command=="snapshot":
        if not args.out:
            p.error("--out is required for snapshot")
        result=write_snapshot(args.root,args.out)
        print("VEILFORGE_PROVENANCE_SNAPSHOT",result["source_commit_sha"],
              result["observed_at_utc"],"files",result["file_count"])
    else:
        if not args.snapshot:
            p.error("--snapshot is required for verify")
        verify_snapshot(args.root,args.snapshot)
        print("VEILFORGE_PROVENANCE_VERIFIED",args.snapshot)


if __name__=="__main__":
    main()
