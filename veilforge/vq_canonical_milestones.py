#!/usr/bin/env python3
"""Read-only, fail-closed reconciliation of three DIFFERENT VQ milestone tracks.

The canonical 34-item quality plan and 13-item M34 efficiency track are not
interchangeable with the older 24-item VF capability-group roadmap. No status
is promoted by this report and no model/game source is modified.
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path
from roadmap import validate as validate_vf

QUALITY_STATUSES = frozenset({"planned", "partial", "in_progress", "verified"})
EFFICIENCY_STATUSES = frozenset({"planned", "partial", "verified_prior", "verified"})


def _load_track(path: Path, expected: int, allowed: frozenset[str], *, quality: bool):
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = document.get("milestones")
    if not isinstance(rows, list) or len(rows) != expected:
        raise ValueError(f"{path.name}: expected exactly {expected} milestones")
    ids = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{path.name}: invalid milestone")
        ident = row.get("id")
        if not isinstance(ident, str) or not ident or ident in ids:
            raise ValueError(f"{path.name}: duplicate/invalid milestone ID")
        ids.add(ident)
        if row.get("status") not in allowed:
            raise ValueError(f"{ident}: unrecognized milestone status")
        if not isinstance(row.get("name"), str) or len(row["name"].strip()) < 8:
            raise ValueError(f"{ident}: missing milestone name")
        if not isinstance(row.get("acceptance"), str) or len(row["acceptance"].strip()) < 16:
            raise ValueError(f"{ident}: missing measurable acceptance")
        if quality and row.get("automatic_game_approval") is not False:
            raise ValueError(f"{ident}: no automatic game approval")
    if quality and document.get("scope", {}).get("excluded") is None:
        raise ValueError("Quality plan must state excluded automatic changes")
    if not quality:
        requirements = document.get("success_requirements", {})
        if (requirements.get("artistic_approval") is not False or
                requirements.get("game_source_modification") is not False or
                requirements.get("android_devices") != 4 or
                requirements.get("per_asset_angles") != 14):
            raise ValueError("Efficiency track may not bypass existing Android or human gates")
    counts = dict(sorted(Counter(row["status"] for row in rows).items()))
    return {"source": path.name, "milestone_count": expected,
            "status_counts": counts,
            "verified_in_this_track": counts.get("verified", 0),
            "all_technical_gates_verified": counts.get("verified", 0) == expected,
            "items": [{"id": r["id"], "status": r["status"],
                       "name": r["name"], "acceptance": r["acceptance"]} for r in rows]}


def summarize(root: Path):
    root = Path(root)
    quality = _load_track(root / "VQ_ENGINE_QUALITY_PLAN.json", 34, QUALITY_STATUSES, quality=True)
    efficiency = _load_track(root / "VQ_M34_EFFICIENCY_MAP.json", 13, EFFICIENCY_STATUSES, quality=False)
    legacy_path = root / "ENGINE_MASTER_PLAN.json"
    legacy_plan = json.loads(legacy_path.read_text(encoding="utf-8"))
    legacy = validate_vf(legacy_plan)
    if len(legacy) != 24:
        raise ValueError("Legacy VF roadmap count changed: reconcile explicitly, never silently relabel")
    if legacy_plan.get("release_policy", {}).get("automatic_merge") is not False:
        raise ValueError("Legacy roadmap must not authorize automatic merges")
    if {row["id"] for row in quality["items"]} & {row["id"] for row in efficiency["items"]}:
        raise ValueError("Canonical and efficiency IDs must be disjoint")
    return {"schema_version": 1, "engine": "VEILFORGE / VQ",
            "canonical_quality": quality, "m34_efficiency": efficiency,
            "legacy_vf_capability_groups": {
                "source": legacy_path.name, "milestone_count": len(legacy),
                "status_counts": dict(sorted(Counter(x["status"] for x in legacy.values()).items())),
                "is_canonical_34_map": False},
            "tracks_are_not_additive_release_approvals": True,
            "human_artistic_acceptance": False, "real_phone_performance_acceptance": False,
            "auto_merge_or_model_promotion": False,
            "note": "34 quality milestones, 13 efficiency milestones and 24 legacy capability groups are distinct maps; CI green is not artistic/device approval."}


def write_report(root: Path, out: Path):
    result = summarize(root)
    out.mkdir(parents=True, exist_ok=True)
    (out / "vq_canonical_milestone_tracks.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = ["# VEILFORGE / VQ canonical milestone reconciliation", "",
             "Tracks are separate, not a combined release percentage.", ""]
    for key, title in (("canonical_quality", "Canonical quality"),
                       ("m34_efficiency", "M34 efficiency"),
                       ("legacy_vf_capability_groups", "Legacy VF capability groups")):
        row = result[key]
        lines.append(f"- {title}: {row['milestone_count']} items; statuses {row['status_counts']}")
    lines += ["", "No automatic status promotion, source rewrite, merge, artistic signoff or physical-phone performance claim."]
    (out / "vq_canonical_milestone_tracks.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("veilforge"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = write_report(args.root, args.out)
    print("VEILFORGE_MILESTONE_TRACKS", report["canonical_quality"]["milestone_count"],
          report["m34_efficiency"]["milestone_count"],
          report["legacy_vf_capability_groups"]["milestone_count"])
