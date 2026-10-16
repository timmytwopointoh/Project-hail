#!/usr/bin/env python3
"""Fail-closed budget and evidence validator for six independent team engines."""
import argparse
import csv
import json
from pathlib import Path

OUTPUTS = {
    "models": ("bellwarden_forged_armor.obj",),
    "world": ("carved_cenotaph.obj",),
    "studio": ("bellwarden_studio_preview.obj",),
    "animation": ("hero_pose_180_frames.csv",),
    "combat": ("combat_swing_phases.csv",),
    "materials": ("material_albedo.png", "material_normal_roughness.png"),
}
MAX_BYTES = 30_000_000


def inspect(team, root):
    if team not in OUTPUTS:
        raise ValueError("Unsupported team engine")
    report_path = root / "engine_report.json"
    if not report_path.is_file() or report_path.is_symlink():
        raise ValueError("No genuine isolated engine report")
    record = json.loads(report_path.read_text())
    if (record.get("team") != team or record.get("status") != "passed"
            or record.get("engine") != "isolated-java-production"
            or record.get("requires_review") is not True):
        raise ValueError("Engine result status or ownership invalid")
    for name in OUTPUTS[team]:
        file = root / name
        if not file.is_file() or file.is_symlink():
            raise ValueError("Missing team-owned artifact: " + name)
        length = file.stat().st_size
        if not 100 < length <= MAX_BYTES:
            raise ValueError("Invalid engine output size: " + name)
        if name.endswith(".obj"):
            with file.open(encoding="utf-8") as f:
                prefix = [f.readline() for _ in range(4)]
            if not any(line.startswith("v ") for line in prefix):
                raise ValueError("No real shape vertex data in OBJ")
        elif name.endswith(".png"):
            if file.open("rb").read(8) != b"\x89PNG\r\n\x1a\n":
                raise ValueError("Rendered material map is not PNG")
        elif name.endswith(".csv"):
            with file.open(newline="") as f:
                reader = csv.reader(f)
                columns = next(reader)
                rows = sum(1 for _ in reader)
            if len(columns) < 4 or rows < 85:
                raise ValueError("Animation/physics engine output too short")
    return {"team": team, "status": "validated", "artifacts": list(OUTPUTS[team]),
            "manual_review_required": True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--team", choices=OUTPUTS, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(inspect(args.team, args.out), indent=2))


if __name__ == "__main__":
    main()
