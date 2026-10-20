#!/usr/bin/env python3
"""Validated, versioned model -> Android worker contract. No shell-string execution."""
import argparse
import json
import re
import sys
from pathlib import Path

PROTOCOL = "vq.worker.v1"
ALLOWED_PROJECTS = {"echoform": "timmytwopointoh/New-game-"}
COMMANDS = ("protocol.validate", "android.build_test", "android.install_test")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,63}$")
SHA_RE = re.compile(r"^[a-fA-F0-9]{40}$")
PKG_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)+$")

def validate(request):
    if not isinstance(request, dict):
        raise ValueError("request must be a JSON object")
    if set(request) - {"protocol","job_id","command","project","source_sha","apk_path","expected_package"}:
        raise ValueError("unknown request field")
    if request.get("protocol") != PROTOCOL:
        raise ValueError("unsupported protocol version")
    job_id = request.get("job_id", "")
    if not isinstance(job_id,str) or not ID_RE.fullmatch(job_id):
        raise ValueError("invalid job_id")
    command = request.get("command")
    if command not in COMMANDS:
        raise ValueError("command not allowed")
    result = dict(protocol=PROTOCOL,job_id=job_id,command=command,project="",repository="",source_sha="",apk_path="",expected_package="")
    if command == "protocol.validate":
        if set(request) != {"protocol","job_id","command"}:
            raise ValueError("validate accepts no build inputs")
        return result
    pkg=request.get("expected_package","")
    if pkg and (not isinstance(pkg,str) or not PKG_RE.fullmatch(pkg)):
        raise ValueError("invalid expected_package")
    result["expected_package"]=pkg
    if command == "android.build_test":
        project=request.get("project")
        sha=request.get("source_sha")
        if project not in ALLOWED_PROJECTS:
            raise ValueError("project is not allowlisted")
        if not isinstance(sha,str) or not SHA_RE.fullmatch(sha):
            raise ValueError("source_sha must be pinned 40-character commit hash")
        if "apk_path" in request:
            raise ValueError("apk_path invalid for build_test")
        result.update(project=project,repository=ALLOWED_PROJECTS[project],source_sha=sha.lower())
    else:
        if "project" in request or "source_sha" in request:
            raise ValueError("source fields invalid for install_test")
        apk_path=request.get("apk_path","")
        if not isinstance(apk_path,str) or not re.fullmatch(r"worker/staging/[a-zA-Z0-9_.-]+\.apk",apk_path):
            raise ValueError("apk_path must be in worker/staging/ without traversal")
        result["apk_path"]=apk_path
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("request_file")
    parser.add_argument("--github-output",default="")
    parser.add_argument("--report",default="worker_result.json")
    args=parser.parse_args()
    try:
        request=json.loads(Path(args.request_file).read_text(encoding="utf-8"))
        plan=validate(request)
        if Path(args.request_file).stem != plan["job_id"]:
            raise ValueError("request filename must match job_id")
        result={"protocol":PROTOCOL,"job_id":plan["job_id"],"status":"validated","plan":plan}
        code=0
    except (OSError,ValueError) as exc:
        result={"protocol":PROTOCOL,"status":"rejected","error":str(exc)}
        code=2
    Path(args.report).parent.mkdir(parents=True,exist_ok=True)
    Path(args.report).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    if code==0 and args.github_output:
        with open(args.github_output,"a",encoding="utf-8") as stream:
            for key,val in result["plan"].items():
                print(f"{key}={val}",file=stream)
    print(json.dumps(result))
    return code

if __name__=="__main__":
    sys.exit(main())
