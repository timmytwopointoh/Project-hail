#!/usr/bin/env python3
"""Versioned, machine-readable Android worker result from captured evidence."""
import argparse
import json
from pathlib import Path

def summarize(root, job_id, command, verification, build, emulator):
    root=Path(root)
    install=(root/"install.txt").read_text(errors="replace") if (root/"install.txt").exists() else ""
    launch=(root/"launch.txt").read_text(errors="replace") if (root/"launch.txt").exists() else ""
    package=(root/"package.txt").read_text().strip() if (root/"package.txt").exists() else ""
    installed="Success" in install
    launched="Events injected: 1" in launch and (root/"game.png").is_file()
    passed=verification=="success" and emulator=="success" and installed and launched
    if command=="android.build_test":
        passed=passed and build=="success"
    stage=None if passed else (
        "apk_build" if command=="android.build_test" and build!="success" else
        "apk_verify" if verification!="success" else
        "android_install" if not installed else
        "android_launch" if not launched else "emulator_runner"
    )
    return {
        "protocol":"vq.worker.result.v1", "job_id":job_id, "command":command,
        "status":"passed" if passed else "failed", "failure_stage":stage,
        "apk_verify_step":verification, "build_step":build, "emulator_step":emulator,
        "android_install":installed, "android_launch":launched, "package":package,
        "evidence":[p.name for p in root.iterdir() if p.is_file() and p.name!="result.json"] if root.exists() else []
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default="worker-results")
    p.add_argument("--job-id",required=True)
    p.add_argument("--command",required=True)
    p.add_argument("--verify",default="skipped")
    p.add_argument("--build",default="skipped")
    p.add_argument("--emulator",default="skipped")
    a=p.parse_args()
    result=summarize(a.root,a.job_id,a.command,a.verify,a.build,a.emulator)
    root=Path(a.root)
    root.mkdir(parents=True,exist_ok=True)
    (root/"result.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))

if __name__=="__main__":
    main()
