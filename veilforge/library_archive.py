#!/usr/bin/env python3
"""VQ source-library: build and verify deterministic offline source archives.

The archive contains the entire tracked Git checkout (engine, workers,
Android-probe test app and required Java build dependencies) at one immutable
commit. It deliberately excludes untracked/generated files and Git history.
No APK, downloaded weights, credentials or external libraries are implied.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import zipfile

SCHEMA=1
MANIFEST="VQ_OFFLINE_SOURCE_MANIFEST.json"
MAX_SINGLE=12*1024*1024
MAX_TOTAL=160*1024*1024
BANNED_SUFFIX={".pem",".p12",".pfx",".jks",".keystore",".key"}
BANNED_BASENAMES={".env",".env.local","id_rsa","id_ed25519","credentials.json",
                  "service_account.json","google-services.json"}
NEEDED={"veilforge/vq_brushes.py","veilforge/vq_mesh_baker.py",
        "veilforge/vq_logcat_stream.py","veilforge/vq_uv_atlas.py",
        "veilforge/android_visual_qa.py",
        "veilforge/VQ_ENGINE_QUALITY_PLAN.json",
        ".github/workflows/veilforge-factory.yml",
        ".github/workflows/vq-model-tools.yml",
        "veilbound/app/src/main/AndroidManifest.xml"}

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def safe_name(name:str)->bool:
    p=PurePosixPath(name)
    return bool(name and not name.startswith("/") and "\\" not in name
                and not p.is_absolute() and ".." not in p.parts
                and len(p.parts)>0 and all(part not in ("",".") for part in p.parts)
                and not p.name.lower() in BANNED_BASENAMES
                and not p.suffix.lower() in BANNED_SUFFIX
                and not any(part==".git" for part in p.parts))

def git(root,*args):
    result=subprocess.run(["git","-C",str(root),*args],capture_output=True,
                          check=True)
    return result.stdout

def checkout_files(root):
    raw=git(root,"ls-files","-z")
    names=[os.fsdecode(x) for x in raw.split(b"\0") if x]
    if names!=sorted(names):
        names.sort()
    if not names or len(names)!=len(set(names)):
        raise ValueError("Missing or duplicated tracked Git paths")
    if not NEEDED.issubset(names):
        raise ValueError("Required QV/VQ source modules missing: "+str(sorted(NEEDED-set(names))))
    total=0
    for name in names:
        if not safe_name(name):raise ValueError("Unsafe/sensitive tracked path: "+name)
        p=root/name
        if not p.is_file() or p.is_symlink():raise ValueError("Source is missing/symlinked: "+name)
        total+=p.stat().st_size
        if p.stat().st_size>MAX_SINGLE or total>MAX_TOTAL:
            raise ValueError("Source exceeds bounded archive size")
    return names

def zip_member(name,data):
    info=zipfile.ZipInfo(name,date_time=(2020,1,1,0,0,0))
    info.compress_type=zipfile.ZIP_DEFLATED
    info.create_system=3
    info.external_attr=(0o100644<<16)
    return info,data

def build(root,output,source_commit=None):
    root=Path(root).resolve()
    output=Path(output).resolve()
    if output.is_relative_to(root):
        raise ValueError("Archive must be written outside the tracked source checkout")
    actual=git(root,"rev-parse","HEAD").decode().strip()
    if len(actual)!=40 or any(ch not in "0123456789abcdef" for ch in actual):
        raise ValueError("Invalid source commit")
    if source_commit is not None and actual!=source_commit:
        raise ValueError("Requested source commit does not match checkout HEAD")
    if git(root,"status","--porcelain","--untracked-files=no").strip():
        raise ValueError("Tracked source is dirty; refuse non-reproducible backup")
    names=checkout_files(root)
    entries=[]
    for name in names:
        data=(root/name).read_bytes()
        entries.append({"path":name,"sha256":sha(data),"bytes":len(data)})
    manifest={"schema_version":SCHEMA,
              "format":"VQ offline tracked-source snapshot (no Git history)",
              "repository":"timmytwopointoh/Project-hail",
              "source_commit":actual,
              "file_count":len(entries),
              "files":entries,
              "included_scope":"all tracked files: VEILFORGE/VQ, VEILBOUND build dependencies, GitHub workflow definitions and instructions",
              "not_included":[".git history","untracked assets","GitHub Actions artifacts",
                              "Android SDK","JDK","third-party Python packages",
                              "credentials","any separate unmerged feature branch"],
              "game_approved":False,"reference_artistry_approved":False}
    encoded=(json.dumps(manifest,indent=2,sort_keys=True)+"\n").encode()
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():raise FileExistsError("Refusing to overwrite an existing library backup")
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9,allowZip64=False) as z:
        for row in entries:
            name=row["path"]
            entry,data=zip_member(name,(root/name).read_bytes())
            z.writestr(entry,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
        entry,data=zip_member(MANIFEST,encoded)
        z.writestr(entry,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    verification=verify(output,expected_commit=actual)
    return {"source_commit":actual,"archive_path":str(output),
            "archive_sha256":sha(output.read_bytes()),
            "file_count":len(entries),"validation":verification}

def verify(archive,expected_commit=None):
    archive=Path(archive)
    if not archive.is_file():raise ValueError("Archive is missing")
    if archive.stat().st_size>MAX_TOTAL:raise ValueError("Archive too large")
    with zipfile.ZipFile(archive,"r") as z:
        members=z.infolist()
        names=[i.filename for i in members]
        if not members or len(names)!=len(set(names)) or MANIFEST not in names:
            raise ValueError("Archive missing manifest or has duplicate member names")
        for i in members:
            if not safe_name(i.filename) or i.is_dir():
                raise ValueError("Archive contains unsafe member: "+i.filename)
            if i.file_size>MAX_SINGLE:raise ValueError("Oversize zip entry")
        if sum(i.file_size for i in members)>MAX_TOTAL:
            raise ValueError("Uncompressed archive exceeds size cap")
        doc=json.loads(z.read(MANIFEST))
        if doc.get("schema_version")!=1 or doc.get("repository")!="timmytwopointoh/Project-hail":
            raise ValueError("Wrong source backup manifest schema")
        commit=doc.get("source_commit")
        if not isinstance(commit,str) or len(commit)!=40:
            raise ValueError("Invalid pinned Git commit")
        if expected_commit and commit!=expected_commit:
            raise ValueError("Archive commit does not match requested build")
        files=doc.get("files",[])
        paths=[x["path"] for x in files]
        if set(paths)!=set(names)-{MANIFEST} or len(paths)!=len(set(paths)):
            raise ValueError("Manifest omits or fabricates archived source files")
        if not NEEDED.issubset(paths):
            raise ValueError("Required VEILFORGE sources missing")
        for row in files:
            if not safe_name(row["path"]):
                raise ValueError("Unsafe file path in index")
            data=z.read(row["path"])
            if row["bytes"]!=len(data) or row["sha256"]!=sha(data):
                raise ValueError("Archive file SHA256 mismatch: "+row["path"])
        if len(files)!=doc.get("file_count"):
            raise ValueError("Manifest file count mismatch")
        return {"verified":True,"source_commit":commit,
                "file_count":len(files),"total_source_bytes":sum(x["bytes"] for x in files),
                "sha256":sha(archive.read_bytes())}

def main():
    parser=argparse.ArgumentParser()
    sub=parser.add_subparsers(dest="command",required=True)
    a=sub.add_parser("build")
    a.add_argument("--root",type=Path,default=Path("."))
    a.add_argument("--output",type=Path,required=True)
    a.add_argument("--commit")
    a=sub.add_parser("verify")
    a.add_argument("--archive",type=Path,required=True)
    a.add_argument("--commit")
    args=parser.parse_args()
    if args.command=="build":
        result=build(args.root,args.output,args.commit)
    else:result=verify(args.archive,args.commit)
    print("VQ_LIBRARY_SOURCE_ARCHIVE_VERIFIED",json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
