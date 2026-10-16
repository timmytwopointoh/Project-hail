#!/usr/bin/env python3
"""M34-06: conservative, provenance-pinned VEILFORGE factory impact router.

Only explicitly whitelisted human-readable documentation may skip the expensive
asset/Android stage. Every unknown, malformed, missing or untrustworthy diff
runs the full factory. Source unit tests remain unconditional in library-manager.
No files are deleted, moved or rewritten by this module.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

SHA = re.compile(r"[0-9a-f]{40}\Z")


def documentation_only(path: str) -> bool:
    """Explicit safe subset; all unknown extensions and directories are costly."""
    if not path or "\\" in path or "\x00" in path or "\n" in path:
        return False
    p = PurePosixPath(path)
    if p.is_absolute() or ".." in p.parts or any(x in ("", ".") for x in p.parts):
        return False
    if len(p.parts) == 2 and p.parts[0] == "veilforge":
        return bool(re.fullmatch(r"VQ_[A-Za-z0-9_-]+\.md", p.name))
    if len(p.parts) >= 3 and p.parts[:2] == ("veilforge", "docs"):
        return p.suffix.lower() == ".md"
    if len(p.parts) >= 3 and p.parts[:2] == ("docs", "vq-library"):
        return p.suffix.lower() == ".md"
    return False


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=30).stdout


def decide(root: Path, base: str | None, head: str | None, event: str = "push") -> dict:
    """Read-only decision. Fail CLOSED to full Android work on any uncertainty."""
    root = Path(root).resolve()
    result = {
        "schema_version": 1, "milestone": "M34-06",
        "source_sha": head, "base_sha": base, "event": event,
        "changed_paths": [], "change_statuses": [], "changed_paths_sha256": None,
        "run_full_factory": True, "source_tests_always_required": True,
        "skip_android_approved": False, "artistic_approval": False,
        "hardware_approval": False, "reason": "fail_closed_unclassified",
    }
    if event != "push":
        result["reason"] = "manual_or_other_event_requires_full_factory"
        return result
    if not isinstance(base, str) or not isinstance(head, str) or not SHA.fullmatch(base) or not SHA.fullmatch(head):
        result["reason"] = "missing_or_invalid_commit_range"
        return result
    if base == "0" * 40 or head == "0" * 40 or base == head:
        result["reason"] = "new_branch_or_empty_commit_range"
        return result
    try:
        checked_out = _git(root, "rev-parse", "HEAD").decode().strip()
        if checked_out != head:
            result["reason"] = "checkout_head_mismatch"
            return result
        _git(root, "merge-base", "--is-ancestor", base, head)
        # --no-renames makes a source->docs rename show BOTH old and new paths.
        # NUL status/path pairs prevent newline, tab and whitespace confusion.
        raw = _git(root, "diff", "--name-status", "--no-renames", "-z", base, head, "--")
        fields = [p.decode("utf-8", errors="strict") for p in raw.split(b"\0") if p]
        if len(fields) % 2:
            result["reason"] = "malformed_diff_statuses"
            return result
        changes = list(zip(fields[::2], fields[1::2]))
        paths = [path for _, path in changes]
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, UnicodeError):
        result["reason"] = "unverifiable_git_diff"
        return result
    if not paths or len(paths) != len(set(paths)):
        result["reason"] = "empty_or_duplicate_diff"
        return result
    changes.sort(key=lambda row: row[1])
    result["changed_paths"] = [path for _, path in changes]
    result["change_statuses"] = [status for status, _ in changes]
    result["changed_paths_sha256"] = hashlib.sha256(
        "\0".join(status + "\0" + path for status, path in changes).encode()
    ).hexdigest()
    # Only modifications of existing regular, non-executable markdown blobs
    # may skip Android. Adds/deletes, chmod, symlinks and type changes run full.
    safe_docs = all(status == "M" and documentation_only(path)
                    for status, path in changes)
    if safe_docs:
        try:
            for _, path in changes:
                for commit in (base, head):
                    row = _git(root, "ls-tree", "-z", commit, "--", path)
                    match = re.fullmatch(rb"100644 blob [0-9a-f]{40}\t" +
                                         re.escape(path.encode()) + rb"\x00", row)
                    if match is None:
                        safe_docs = False
                        break
                if not safe_docs:
                    break
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            safe_docs = False
    if safe_docs:
        result["run_full_factory"] = False
        result["skip_android_approved"] = True
        result["reason"] = "strict_documentation_only_with_source_tests"
    else:
        result["reason"] = "source_or_unknown_path_requires_full_factory"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--event", default="push")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    result = decide(args.root, args.base, args.head, args.event)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.github_output is not None:
        with args.github_output.open("a", encoding="utf-8") as f:
            f.write("run_full_factory=" + str(result["run_full_factory"]).lower() + "\n")
            f.write("impact_reason=" + result["reason"] + "\n")
    print("VQ_M34_06_IMPACT", "FULL" if result["run_full_factory"] else "SOURCE_ONLY", result["reason"])


if __name__ == "__main__":
    main()