#!/usr/bin/env python3
"""Independent LOD screenshot manifest integrity; no artistic-quality verdict.

The structural Android reviewer runs earlier, but the LOD comparison must not
silently trust stale, relabeled or replaced frames from its own artifact inputs.
Only the two canonical gate LODs are inspected here; the other roles remain
the responsibility of the full Android and semantic reviewers.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from android_visual_qa import VIEWS

PAIR_ROLES = {
    "ancient_gate_standard": "scene-world",
    "ancient_gate_mobile": "nature-mobile",
}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


def verified_lod_frames(root):
    """Return {asset: [(PNG path, yaw, pitch), ...]}, source SHA, APK SHA.

    Fail closed on missing or duplicate roles, wrong source/APK provenance,
    noncanonical camera metadata, and bytes that disagree with the manifest.
    This is screenshot integrity, not a check of mesh fidelity or phone FPS.
    """
    root = Path(root)
    seen_roles = set()
    images = {}
    source_sha = apk_sha = None
    for manifest in root.rglob("emulator_visual_qa.json"):
        record = json.loads(manifest.read_text(encoding="utf-8"))
        role = record.get("role")
        if role not in PAIR_ROLES.values():
            continue
        if role in seen_roles:
            raise ValueError("Duplicate LOD emulator role: " + role)
        seen_roles.add(role)
        if manifest.parent.name not in (role, "veilforge-android-" + role):
            raise ValueError(role + ": LOD evidence stored in wrong role directory")
        current_sha = record.get("source_commit")
        current_apk = record.get("apk_sha256")
        if (not isinstance(current_sha, str) or
                not SHA40.fullmatch(current_sha) or
                not isinstance(current_apk, str) or
                not SHA64.fullmatch(current_apk)):
            raise ValueError(role + ": invalid source/APK provenance")
        if source_sha is not None and current_sha != source_sha:
            raise ValueError("LOD roles have different source commits")
        if apk_sha is not None and current_apk != apk_sha:
            raise ValueError("LOD roles used different APK binaries")
        source_sha, apk_sha = current_sha, current_apk
        asset_name = next(name for name, expected_role in PAIR_ROLES.items()
                          if expected_role == role)
        matches = [entry for entry in record.get("assets", [])
                   if entry.get("asset") == asset_name]
        if len(matches) != 1:
            raise ValueError(role + ": missing or duplicate expected LOD asset")
        views = matches[0].get("views", [])
        if len(views) != len(VIEWS):
            raise ValueError(asset_name + ": expected exactly 14 camera views")
        frames = []
        for index, (view, (yaw, pitch)) in enumerate(zip(views, VIEWS)):
            canonical = f"{asset_name}/{index:02d}_yaw{yaw}_pitch{pitch}.png"
            if ((view.get("yaw"), view.get("pitch")) != (yaw, pitch) or
                    view.get("image") != canonical):
                raise ValueError(asset_name + ": noncanonical LOD camera/path at " + str(index))
            image = manifest.parent / canonical
            if not image.is_file():
                raise ValueError(asset_name + ": missing LOD screenshot " + str(index))
            digest = view.get("sha256")
            if (not isinstance(digest, str) or
                    not SHA64.fullmatch(digest) or
                    hashlib.sha256(image.read_bytes()).hexdigest() != digest):
                raise ValueError(asset_name + ": LOD screenshot SHA mismatch at " + str(index))
            frames.append((image, yaw, pitch))
        images[asset_name] = frames
    if set(images) != set(PAIR_ROLES):
        raise ValueError("LOD comparisons require both real standard/mobile emulator roles")
    return images, source_sha, apk_sha
