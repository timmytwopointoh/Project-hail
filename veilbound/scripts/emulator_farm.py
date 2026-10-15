#!/usr/bin/env python3
"""Plan independent Android emulator shards and aggregate their real QA reports.

Each shard runs in its *own GitHub-hosted VM* with its own emulator, ADB,
screenshots and logcat. No shared ADB port or filesystem; one APK is built once.
"""
import argparse
import json
from pathlib import Path

CONFIGS = (
    {"id": "android35_pixel6", "api": 35, "profile": "pixel_6"},
    {"id": "android34_pixel7", "api": 34, "profile": "pixel_7"},
    {"id": "android35_pixel4", "api": 35, "profile": "pixel_4"},
    {"id": "android33_pixel5", "api": 33, "profile": "pixel_5"},
    {"id": "android34_pixel6", "api": 34, "profile": "pixel_6"},
    {"id": "android33_pixel4", "api": 33, "profile": "pixel_4"},
    {"id": "android35_pixel7", "api": 35, "profile": "pixel_7"},
    {"id": "android33_pixel6", "api": 33, "profile": "pixel_6"},
)
MAX_EMULATORS = len(CONFIGS)

def make_matrix(count):
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= MAX_EMULATORS:
        raise ValueError("Requested emulator capacity must be between 1 and 8")
    chosen = [dict(item) for item in CONFIGS[:count]]
    return {"matrix": {"include": chosen}, "count": count,
            "min_required": count,
            "note": "Each emulator runs separately on its own Ubuntu runner and checks one immutable APK."}

def summarize(root, expected):
    root = Path(root)
    if not 1 <= expected <= MAX_EMULATORS:
        raise ValueError("Invalid number of expected emulator reports")
    checked = []
    for cfg in CONFIGS[:expected]:
        folder = root / ("veilbound-emulator-" + cfg["id"] + "-inspection")
        report_file = folder / "emulator_report.json"
        quality_file = folder / "visual_quality_metrics.json"
        row = {"id": cfg["id"], "api": cfg["api"], "profile": cfg["profile"],
               "report_present": report_file.is_file(),
               "quality_present": quality_file.is_file()}
        if report_file.is_file():
            try:
                report = json.loads(report_file.read_text(encoding="utf-8"))
                row["result"] = report.get("status", "unknown")
                row["screenshot_count"] = len(report.get("screenshots", []))
                row["error"] = str(report.get("error", ""))[:300]
            except (ValueError, OSError, TypeError):
                row["result"] = "malformed"
        else:
            row["result"] = "missing"
        row["passed"] = (row["result"] == "passed" and row["quality_present"]
                         and row.get("screenshot_count", 0) >= 10)
        checked.append(row)
    return {"schema_version": 1, "expected": expected,
            "passed": sum(1 for row in checked if row["passed"]),
            "success": all(row["passed"] for row in checked),
            "instances": checked}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--summarize", type=Path)
    parser.add_argument("--out", type=Path,
                        default=Path("inspection_output/emulator-farm"))
    args = parser.parse_args()
    if args.count is None:
        parser.error("--count is required")
    if args.summarize is None:
        result = make_matrix(args.count)
        if args.github_output:
            with args.github_output.open("a", encoding="utf-8") as file:
                file.write("matrix=" + json.dumps(result["matrix"], separators=(",", ":")) + "\n")
                file.write("count=" + str(result["count"]) + "\n")
    else:
        result = summarize(args.summarize, args.count)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "emulator_farm_report.json").write_text(json.dumps(result, indent=2) + "\n")
    text = ["# VEILBOUND parallel Android emulator farm", ""]
    if args.summarize is None:
        text += ["Allocated **" + str(result["count"]) + "** independent emulator jobs", ""]
    else:
        text += ["Verified **" + str(result["passed"]) + "/" + str(result["expected"]) +
                 "** emulator instances", "",
                 "| Emulator | Android API | Result | Screenshot count |",
                 "|---|---:|---|---:|"]
        text += ["| " + row["id"] + " | " + str(row["api"]) + " | " + row["result"] +
                 " | " + str(row.get("screenshot_count", 0)) + " |"
                 for row in result["instances"]]
    (args.out / "emulator_farm_report.md").write_text("\n".join(text) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if args.summarize is None or result["success"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
