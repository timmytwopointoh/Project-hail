#!/usr/bin/env python3
"""Human-approved transport for a local AI's vq.worker.v1 JSON commands.

Dry-run unless --submit; token remains in the controller environment, never the model.
"""
import argparse
import base64
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from command_protocol import validate

REPOSITORY="timmytwopointoh/Project-hail"
API="https://api.github.com/repos/"+REPOSITORY

def call(endpoint, token, method="GET", payload=None):
    body=json.dumps(payload).encode("utf-8") if payload is not None else None
    request=Request(API+endpoint,data=body,method=method,headers={
        "Authorization":"Bearer "+token,
        "Accept":"application/vnd.github+json",
        "X-GitHub-Api-Version":"2022-11-28",
        "User-Agent":"vq-worker-controller-v1",
        "Content-Type":"application/json",
    })
    try:
        with urlopen(request,timeout=25) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError("GitHub refused "+method+" "+endpoint+" (HTTP "+str(exc.code)+")") from None
    except URLError as exc:
        raise RuntimeError("GitHub connection failed") from None

def submit(path, token):
    request=json.loads(Path(path).read_text(encoding="utf-8"))
    plan=validate(request)
    job_id=plan["job_id"]
    branch="ai-job/"+job_id
    main=call("/git/ref/heads/main",token)
    sha=main["object"]["sha"]
    call("/git/refs",token,"POST",{"ref":"refs/heads/"+branch,"sha":sha})
    canonical=json.dumps(request,sort_keys=True,indent=2)+"\n"
    call("/contents/worker/requests/"+job_id+".json",token,"PUT",{
        "message":"Submit reviewed worker job "+job_id,
        "content":base64.b64encode(canonical.encode("utf-8")).decode("ascii"),
        "branch":branch,
    })
    pr=call("/pulls",token,"POST",{
        "title":"Worker job: "+job_id+" ["+plan["command"]+"]",
        "head":branch,"base":"main",
        "body":"Review this allowlisted one-shot job before merging. After merge, the GitHub worker validates its protocol and runs the requested test once. No continuous workers or arbitrary commands.",
    })
    return pr["html_url"]

def main():
    parser=argparse.ArgumentParser(description="Validate or review-gate an AI worker command")
    parser.add_argument("request",help="JSON command produced by any AI")
    parser.add_argument("--submit",action="store_true",help="Actually open a job PR (default is dry-run)")
    args=parser.parse_args()
    try:
        request=json.loads(Path(args.request).read_text(encoding="utf-8"))
        plan=validate(request)
        if not args.submit:
            print(json.dumps({"valid":True,"dry_run":True,"plan":plan},indent=2))
            return 0
        token=os.environ.get("VQ_GITHUB_TOKEN","")
        if not token:
            raise ValueError("Set VQ_GITHUB_TOKEN only in the trusted controller")
        print(submit(args.request,token))
        return 0
    except (OSError,ValueError,RuntimeError) as exc:
        print("Rejected: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    sys.exit(main())
