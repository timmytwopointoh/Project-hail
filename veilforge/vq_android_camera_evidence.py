#!/usr/bin/env python3
"""Read-only, pixel-provenanced before/after Android camera evidence comparator.

Consumes immutable GitHub Actions screenshot ZIPs, never rewrites them.
Rejects stale accepted pixels even if PNG compression/metadata changes.
Coverage is the existing semantic color-mask heuristic, NOT artistic quality.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import statistics
import zipfile
from pathlib import Path
from PIL import Image
from android_visual_qa import ROLES, VIEWS, BACKGROUND

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def audit_archive(path):
    path = Path(path)
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        report = json.loads(archive.read("emulator_visual_qa.json"))
        role = report.get("role")
        if role not in ROLES:
            raise ValueError("Unknown emulator role")
        if not HEX40.fullmatch(str(report.get("source_commit", ""))):
            raise ValueError("Invalid source SHA")
        if not HEX64.fullmatch(str(report.get("apk_sha256", ""))):
            raise ValueError("Invalid APK SHA")
        assets = report.get("assets", [])
        if tuple(x.get("asset") for x in assets) != tuple(ROLES[role]):
            raise ValueError("Missing, reordered or unexpected assets")
        if report.get("screenshot_count") != len(VIEWS) * len(assets):
            raise ValueError("Incorrect accepted screenshot count")
        seen_pixel = {}
        audited = {}
        for asset in assets:
            asset_name = asset["asset"]
            views = asset.get("views", [])
            if len(views) != len(VIEWS):
                raise ValueError(asset_name + ": incomplete camera views")
            coverages, frames = [], []
            previous_pixel = None
            for i, (meta, (yaw, pitch)) in enumerate(zip(views, VIEWS)):
                if (meta.get("yaw"), meta.get("pitch")) != (yaw, pitch):
                    raise ValueError(asset_name + ": wrong camera angle")
                name = meta.get("image", "")
                if (not isinstance(name, str) or name not in names or
                        not name.startswith(asset_name + "/") or
                        ".." in Path(name).parts):
                    raise ValueError(asset_name + ": missing or unsafe frame")
                raw = archive.read(name)
                byte_sha = hashlib.sha256(raw).hexdigest()
                if byte_sha != meta.get("sha256"):
                    raise ValueError(asset_name + ": screenshot SHA mismatch")
                with Image.open(io.BytesIO(raw)) as source:
                    image = source.convert("RGB")
                pixel_sha = hashlib.sha256(
                    image.width.to_bytes(4, "big") +
                    image.height.to_bytes(4, "big") + image.tobytes()
                ).hexdigest()
                if pixel_sha == previous_pixel:
                    raise ValueError(asset_name + ": adjacent pixel-identical camera view")
                if pixel_sha in seen_pixel and seen_pixel[pixel_sha][0] != asset_name:
                    prior = seen_pixel[pixel_sha]
                    raise ValueError("cross-asset pixel-identical screenshot: " +
                                     prior[1] + " and " + name)
                seen_pixel.setdefault(pixel_sha, (asset_name, name))
                previous_pixel = pixel_sha
                w, h = image.size
                sample = image.crop((int(w*.07), int(h*.08),
                                     int(w*.93), int(h*.92))).resize((192, 192))
                covered = sum(
                    max(abs(rgb[k] - BACKGROUND[k]) for k in range(3)) >= 35
                    for rgb in sample.getdata()
                ) / (192*192)
                coverages.append(covered)
                frames.append({"yaw": yaw, "pitch": pitch, "image": name,
                               "sha256": byte_sha, "pixel_sha256": pixel_sha,
                               "coverage": round(covered, 8)})
            audited[asset_name] = {
                "views": len(frames), "min": min(coverages),
                "max": max(coverages), "mean": statistics.mean(coverages),
                "frames": frames
            }
        rejected = sorted(n for n in names if n.endswith(".png") and
                          ("_rejected_duplicate_" in n or "_blocked_modal_" in n))
        return {
            "archive": path.name, "role": role,
            "source_commit": report["source_commit"],
            "apk_sha256": report["apk_sha256"],
            "accepted_views": sum(x["views"] for x in audited.values()),
            "rejected_candidate_paths": rejected,
            "assets": audited, "pixel_integrity_passed": True
        }


def compare(before_zip, after_zip, asset):
    before, after = audit_archive(before_zip), audit_archive(after_zip)
    if before["role"] != after["role"]:
        raise ValueError("Cannot compare different emulator roles")
    if before["source_commit"] == after["source_commit"]:
        raise ValueError("Before and after source commits must differ")
    if asset not in before["assets"] or asset not in after["assets"]:
        raise ValueError("Requested asset absent from source evidence")
    a, b = before["assets"][asset], after["assets"][asset]
    pairs = []
    for old, new in zip(a["frames"], b["frames"]):
        if (old["yaw"], old["pitch"]) != (new["yaw"], new["pitch"]):
            raise ValueError("Camera angles changed between runs")
        pairs.append({"yaw": old["yaw"], "pitch": old["pitch"],
                      "before_sha256": old["sha256"], "after_sha256": new["sha256"],
                      "before_coverage": old["coverage"],
                      "after_coverage": new["coverage"]})
    return {
        "schema_version": 1, "mode": "independent-real-android-camera-evidence",
        "asset": asset, "role": before["role"],
        "before_source_sha": before["source_commit"],
        "after_source_sha": after["source_commit"],
        "before_apk_sha256": before["apk_sha256"],
        "after_apk_sha256": after["apk_sha256"],
        "before_min": round(a["min"], 8), "after_min": round(b["min"], 8),
        "before_max": round(a["max"], 8), "after_max": round(b["max"], 8),
        "before_mean": round(a["mean"], 8), "after_mean": round(b["mean"], 8),
        "mean_coverage_ratio": round(b["mean"] / max(a["mean"], 1e-12), 5),
        "minimum_coverage_improved": b["min"] > a["min"],
        "mean_coverage_improved": b["mean"] > a["mean"],
        "before_rejected_candidates_retained": len(before["rejected_candidate_paths"]),
        "after_rejected_candidates_retained": len(after["rejected_candidate_paths"]),
        "angles": pairs, "all_14_views_verified": len(pairs) == len(VIEWS),
        "artistic_quality_approved": False, "phone_hardware_performance_verified": False,
        "limitation": "Color-mask occupancy is a framing heuristic, not mesh fidelity or art quality."
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--asset", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.before, args.after, args.asset)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("VEILFORGE_CAMERA_EVIDENCE", result["asset"],
          "mean_ratio", result["mean_coverage_ratio"],
          "14_frames", result["all_14_views_verified"])


if __name__ == "__main__":
    main()
