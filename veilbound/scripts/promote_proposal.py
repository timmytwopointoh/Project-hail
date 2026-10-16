#!/usr/bin/env python3
"""Fail-closed artifact promoter for a HUMAN-APPROVED AI patch.

This tool never runs generated source. It only validates full replacement
files against role allowlists, the immutable source commit and artifact
metadata, then stages the contents for a reviewable draft pull request.
"""
import argparse
import difflib
import json
import os
import re
import subprocess
from pathlib import Path

from ai_worker import JAVA, ROLES
from proposal_guard import semantic_fingerprint

def allowed_paths(role):
    if role not in ROLES:
        raise ValueError("Unknown or unauthorized worker role")
    return {str(JAVA / name) for name in ROLES[role]}

def load_proposal(root, role, expected_sha, expected_slot=None):
    root = Path(root)
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise ValueError("Expected SHA must be a full git commit SHA")
    meta = root / "worker_result.json"
    if not meta.is_file() or meta.is_symlink():
        raise ValueError("Missing regular worker report")
    report = json.loads(meta.read_text())
    if not isinstance(report, dict):
        raise ValueError("Invalid worker report")
    if report.get("role") != role:
        raise ValueError("Worker role does not match selected artifact")
    if expected_slot is not None:
        if not re.fullmatch(r"w\d{3}", expected_slot):
            raise ValueError("Invalid worker slot")
        if report.get("slot_id") != expected_slot:
            raise ValueError("Proposal slot does not match selected artifact")
    if report.get("source_commit") != expected_sha:
        raise ValueError("Artifact generated from a different commit")
    if report.get("status") != "proposed_change_passed_java_tests":
        raise ValueError("Proposal has not passed trusted Java unit tests")
    if report.get("proposal_requires_human_review") is not True:
        raise ValueError("Missing mandatory review marker")
    paths = report.get("edited_paths")
    if not isinstance(paths, list) or not 1 <= len(paths) <= 3:
        raise ValueError("Expected between one and three edited files")
    allowlist = allowed_paths(role)
    if len(set(map(str, paths))) != len(paths) or any(not isinstance(x, str) for x in paths):
        raise ValueError("Duplicate or malformed path")
    if not set(paths) <= allowlist:
        raise ValueError("Artifact tries to edit out-of-scope source")
    proposal_root = root / "proposed"
    pending = {}
    for path in paths:
        p = proposal_root / path
        if not p.is_file() or p.is_symlink():
            raise ValueError("Missing replacement file or unsafe symlink")
        if p.stat().st_size > 250000:
            raise ValueError("Source replacement exceeds conservative size cap")
        contents = p.read_text(encoding="utf-8")
        if "\x00" in contents:
            raise ValueError("Source contains NUL bytes")
        pending[path] = contents
    return pending

def verify_reviewed_patch(root, artifact, pending):
    """The human-reviewed diff must describe exactly the files to be committed.

    A valid source replacement with an unrelated or forged changes.patch must
    be rejected rather than silently promoting different code.
    """
    manifest = Path(artifact) / "changes.patch"
    if not manifest.is_file() or manifest.is_symlink():
        raise ValueError("Missing regular reviewed changes.patch")
    expected = []
    for path, proposed in pending.items():
        original = (Path(root) / path).read_text(encoding="utf-8")
        if semantic_fingerprint(original) == semantic_fingerprint(proposed):
            raise ValueError("Reviewed AI patch changes only comments or formatting: " + path)
        expected.extend(difflib.unified_diff(
            original.splitlines(keepends=True),
            proposed.splitlines(keepends=True),
            fromfile="a/" + path, tofile="b/" + path))
    actual = manifest.read_text(encoding="utf-8")
    if not actual or actual != "".join(expected):
        raise ValueError("Reviewed patch does not match promoted Java source replacements")


def stage_proposal(root, artifact, role, expected_sha, dry_run=False, expected_slot=None):
    root = Path(root)
    actual = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                            capture_output=True, text=True, check=True).stdout.strip()
    if actual != expected_sha:
        raise ValueError("Checkout is not the worker's original source commit")
    pending = load_proposal(artifact, role, expected_sha, expected_slot)
    # Complete every validation before changing any file.
    for name, content in pending.items():
        target = root / name
        if not target.is_file() or target.is_symlink():
            raise ValueError("Original path absent or symlinked: " + name)
        if target.read_text(encoding="utf-8") == content:
            raise ValueError("No change supplied in source: " + name)
    verify_reviewed_patch(root, artifact, pending)
    if not dry_run:
        for name, content in pending.items():
            (root / name).write_text(content, encoding="utf-8")
    return sorted(pending)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--role", choices=sorted(ROLES), required=True)
    p.add_argument("--expected-sha", required=True)
    p.add_argument("--slot-id")
    p.add_argument("--repo-root", type=Path, default=Path("."))
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    touched = stage_proposal(args.repo_root, args.artifact,
                             args.role, args.expected_sha, args.dry_run,
                             expected_slot=args.slot_id)
    print(json.dumps({"result": "verified" if args.dry_run else "staged",
                      "role": args.role, "source_commit": args.expected_sha,
                      "files": touched, "requires_draft_PR_review": True}, indent=2))

if __name__ == "__main__":
    main()
