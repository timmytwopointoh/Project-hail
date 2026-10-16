#!/usr/bin/env python3
"""M34-09: inspect real downloaded GitHub Actions artifact ZIP payloads.

Do not confuse a ZIP archive's compressed transport size with the APK or
accepted screenshot payload bytes. Rejected modal captures are preserved but
excluded from the accepted 14-view evidence count.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

ROLES = ("nature", "characters", "scene", "props")
VIEWS = re.compile(r"^(\d{2})_yaw\d+_pitch\d+\.png$")
MAX_ZIP = 80 * 1024 * 1024
MAX_UNPACKED = 200 * 1024 * 1024
PNG_MAGIC = bytes.fromhex("89504e470d0a1a0a")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_members(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > MAX_ZIP:
        raise ValueError("Missing or oversized artifact ZIP")
    with zipfile.ZipFile(path) as z:
        members = [x for x in z.infolist() if not x.is_dir()]
        if not members or sum(x.file_size for x in members) > MAX_UNPACKED:
            raise ValueError("Empty or oversized artifact payload")
        names = [x.filename for x in members]
        if len(set(names)) != len(names):
            raise ValueError("Duplicate ZIP member")
        for name in names:
            p = PurePosixPath(name)
            if p.is_absolute() or ".." in p.parts or "\\" in name:
                raise ValueError("Unsafe ZIP member")
        return {x.filename: z.read(x) for x in members}


def inspect_apk(path):
    members = read_members(path)
    apks = [data for name, data in members.items() if name.endswith(".apk")]
    if len(apks) != 1 or not apks[0].startswith(b"PK"):
        raise ValueError("Missing, duplicated or malformed APK")
    return {"bytes": len(apks[0]), "sha256": sha(apks[0]),
            "artifact_zip_sha256": sha(Path(path).read_bytes())}


def inspect_captures(path):
    members = read_members(path)
    accepted, blocked = {}, {}
    for name, data in members.items():
        if not name.endswith(".png"):
            continue
        if not data.startswith(PNG_MAGIC):
            raise ValueError("Screenshot is not PNG: " + name)
        p = PurePosixPath(name)
        if len(p.parts) < 2:
            raise ValueError("Capture missing asset directory")
        base = p.name
        if "_blocked_" in base:
            blocked[name] = len(data)
        elif VIEWS.fullmatch(base):
            accepted[name] = len(data)
        else:
            raise ValueError("Unclassified screenshot: " + name)
    if not accepted:
        raise ValueError("No accepted real PNG screenshots")
    by_asset = {}
    for name in accepted:
        p = PurePosixPath(name)
        by_asset.setdefault(p.parent.as_posix(), set()).add(p.name[:2])
    if any(views != {f"{i:02d}" for i in range(14)} for views in by_asset.values()):
        raise ValueError("Every asset must have exactly 14 unique orbit angles")
    return {
        "accepted_png_count": len(accepted),
        "blocked_png_count": len(blocked),
        "accepted_png_bytes": sum(accepted.values()),
        "blocked_png_bytes": sum(blocked.values()),
        "artifact_zip_sha256": sha(Path(path).read_bytes()),
    }


def inspect_run(folder, run_id, apk_zip=None):
    folder = Path(folder)
    apk_zip = Path(apk_zip) if apk_zip else folder / f"vq-{run_id}-apk.zip"
    apk = inspect_apk(apk_zip)
    roles = {}
    for role in ROLES:
        roles[role] = inspect_captures(folder / f"vq-{run_id}-{role}.zip")
    return {
        "run_id": int(run_id), "apk": apk,
        "accepted_png_count": sum(r["accepted_png_count"] for r in roles.values()),
        "blocked_png_count": sum(r["blocked_png_count"] for r in roles.values()),
        "accepted_png_bytes": sum(r["accepted_png_bytes"] for r in roles.values()),
        "blocked_png_bytes": sum(r["blocked_png_bytes"] for r in roles.values()),
        "roles": roles,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--apk-zip", type=Path)
    parser.add_argument("--expected-manifest", type=Path)
    args = parser.parse_args()
    result = inspect_run(args.artifacts_dir, args.run_id, args.apk_zip)
    if args.expected_manifest:
        expected = json.loads(args.expected_manifest.read_text())
        found = [x for x in expected["runs"] if x["run_id"] == args.run_id]
        if len(found) != 1 or found[0] != result:
            raise ValueError("Inspected APK/PNG bytes disagree with pinned evidence")
    print("VQ_M34_09_REAL_APK_AND_CAPTURE_BYTES", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
