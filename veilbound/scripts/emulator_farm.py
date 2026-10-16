#!/usr/bin/env python3
"""Plan independent Android emulator shards and aggregate their real QA reports.

Each shard runs in its *own GitHub-hosted VM* with its own emulator, ADB,
screenshots and logcat. No shared ADB port or filesystem; one APK is built once.
"""
import argparse
import json
from pathlib import Path

# PRIMARY: every worker tests Android 15, matching the physical Moto G target.
# 5-8 are independent repetitions to detect flaky interactions, never older OS.
CONFIGS = (
    {"id": "android35_pixel6_a", "api": 35, "profile": "pixel_6"},
    {"id": "android35_pixel7_a", "api": 35, "profile": "pixel_7"},
    {"id": "android35_pixel4_a", "api": 35, "profile": "pixel_4"},
    {"id": "android35_pixel5_a", "api": 35, "profile": "pixel_5"},
    {"id": "android35_pixel6_b", "api": 35, "profile": "pixel_6"},
    {"id": "android35_pixel7_b", "api": 35, "profile": "pixel_7"},
    {"id": "android35_pixel4_b", "api": 35, "profile": "pixel_4"},
    {"id": "android35_pixel5_b", "api": 35, "profile": "pixel_5"},
)
# Opt-in legacy compatibility track, preserving the original Android 13/14
# profiles without making them the production worker-loop default.
COMPAT_CONFIGS = (
    {"id": "compat_android35_pixel6", "api": 35, "profile": "pixel_6"},
    {"id": "compat_android34_pixel7", "api": 34, "profile": "pixel_7"},
    {"id": "compat_android35_pixel4", "api": 35, "profile": "pixel_4"},
    {"id": "compat_android33_pixel5", "api": 33, "profile": "pixel_5"},
    {"id": "compat_android34_pixel6", "api": 34, "profile": "pixel_6"},
    {"id": "compat_android33_pixel4", "api": 33, "profile": "pixel_4"},
    {"id": "compat_android35_pixel7", "api": 35, "profile": "pixel_7"},
    {"id": "compat_android33_pixel6", "api": 33, "profile": "pixel_6"},
)
MODES = ("synchronized", "compatibility")


def get_configs(mode):
    if mode not in MODES:
        raise ValueError("Unrecognized emulator farm mode")
    return CONFIGS if mode == "synchronized" else COMPAT_CONFIGS

MAX_EMULATORS = len(CONFIGS)

def make_matrix(count, mode='synchronized'):
    configs = get_configs(mode)
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= MAX_EMULATORS:
        raise ValueError("Requested emulator capacity must be between 1 and 8")
    chosen = [dict(item) for item in configs[:count]]
    return {"matrix": {"include": chosen}, "count": count, "mode": mode,
            "min_required": count,
            "note": "All shards test the same immutable APK/commit concurrently. Synchronized mode uses Android 15 for every shard."}

def summarize(root, expected, *, expected_sha=None, expected_apk_sha=None, mode='synchronized'):
    configs = get_configs(mode)
    if expected_apk_sha is not None and (
            not isinstance(expected_apk_sha, str) or len(expected_apk_sha) != 64 or
            any(c not in '0123456789abcdef' for c in expected_apk_sha.lower())):
        raise ValueError('Invalid shared APK SHA256')
    if expected_sha is not None and (not isinstance(expected_sha, str)
                                     or len(expected_sha) != 40
                                     or any(c not in '0123456789abcdef' for c in expected_sha.lower())):
        raise ValueError('Invalid expected source commit SHA')
    root = Path(root)
    if not 1 <= expected <= MAX_EMULATORS:
        raise ValueError("Invalid number of expected emulator reports")
    checked = []
    findings = {}
    for cfg in configs[:expected]:
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
        if quality_file.is_file():
            try:
                quality = json.loads(quality_file.read_text(encoding="utf-8"))
                row["quality_result"] = quality.get("emulator_test")
                row["quality_screenshots"] = len(quality.get("screenshots", []))
            except (ValueError, OSError, TypeError, AttributeError):
                row["quality_result"] = "malformed"
        else:
            row["quality_result"] = "missing"
        tasks_file = folder / "task_plan.json"
        if tasks_file.is_file():
            try:
                plan = json.loads(tasks_file.read_text(encoding="utf-8"))
                row["qa_release_gate"] = plan.get("release_gate")
                row["source_commit"] = plan.get("source_commit")
                row["qa_emulator_result"] = plan.get("emulator_status")
            except (ValueError, OSError, AttributeError):
                row["qa_release_gate"] = "malformed"
        if expected_sha is None:
            # Legacy fixture format is useful for unit tests, but live CI
            # passes a commit and requires all independently produced evidence.
            row["passed"] = (row["result"] == "passed" and row["quality_present"]
                             and row.get("screenshot_count", 0) >= 10)
        else:
            rows = report.get("screenshots", []) if report_file.is_file() and row["result"] == "passed" else []
            paths = [entry.get("path") for entry in rows if isinstance(entry, dict)]
            present = len(paths) >= 10 and all(
                isinstance(name, str) and (folder / name).is_file()
                and name.endswith(".png") and "/" not in name and ".." not in name
                for name in paths)
            row["verified_images_present"] = present
            row["source_matches"] = row.get("source_commit") == expected_sha
            row["passed"] = (row["result"] == "passed" and
                             row["quality_result"] == "passed" and
                             row.get("quality_screenshots", 0) >= 10 and
                             present and row["source_matches"] and
                             row.get("qa_release_gate") != "blocked" and
                             row.get("qa_emulator_result") == "passed" and
                             row.get("qa_release_gate") in ("clear", "needs-review"))
        if expected_apk_sha is not None:
            digest_path = folder / "apk_sha256.txt"
            digest = digest_path.read_text(encoding="utf-8").strip() if digest_path.is_file() else ""
            row["apk_digest_matches"] = digest == expected_apk_sha
            row["passed"] = row["passed"] and row["apk_digest_matches"]
        checked.append(row)
        if tasks_file.is_file():
            try:
                tasks = json.loads(tasks_file.read_text(encoding="utf-8")).get("tasks", [])
            except (ValueError, OSError, AttributeError):
                tasks = []
            for item in tasks:
                if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                    continue
                ident = item["id"]
                if ident not in findings:
                    findings[ident] = {
                        "id": ident, "priority": item.get("priority", "P3"),
                        "worker": item.get("worker", "qa"),
                        "title": item.get("title", "Unknown QA finding"),
                        "affected_emulators": []}
                if cfg["id"] not in findings[ident]["affected_emulators"]:
                    findings[ident]["affected_emulators"].append(cfg["id"])
        if not row["passed"] and not tasks_file.is_file():
            ident = "VB-EMULATOR-EVIDENCE-MISSING"
            item = findings.setdefault(ident, {
                "id": ident, "priority": "P0", "worker": "qa",
                "title": "Emulator failure without machine-readable repair plan",
                "affected_emulators": []})
            item["affected_emulators"].append(cfg["id"])
    ordered_findings = sorted(findings.values(),
                              key=lambda t: ({"P0": 0, "P1": 1, "P2": 2, "P3": 3}
                                             .get(t["priority"], 4), t["id"]))
    for item in ordered_findings:
        item["scope"] = ("cross-emulator" if len(item["affected_emulators"]) > 1
                         else "emulator-specific")
    return {"schema_version": 3, "mode": mode, "android_api": 35 if mode == "synchronized" else "mixed",
            "expected_source_commit": expected_sha, "expected_apk_sha256": expected_apk_sha,
            "expected": expected,
            "passed": sum(1 for row in checked if row["passed"]),
            "success": all(row["passed"] for row in checked),
            "instances": checked, "findings": ordered_findings}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int)
    parser.add_argument("--mode", choices=MODES, default="synchronized")
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--summarize", type=Path)
    parser.add_argument('--expected-sha', default=None,
                        help='Full immutable APK source SHA (required for strict real CI)')
    parser.add_argument('--expected-apk-sha', default=None,
                        help='Common artifact SHA256 for every independent emulator')
    parser.add_argument("--out", type=Path,
                        default=Path("inspection_output/emulator-farm"))
    args = parser.parse_args()
    if args.count is None:
        parser.error("--count is required")
    if args.summarize is None:
        result = make_matrix(args.count, mode=args.mode)
        if args.github_output:
            with args.github_output.open("a", encoding="utf-8") as file:
                file.write("matrix=" + json.dumps(result["matrix"], separators=(",", ":")) + "\n")
                file.write("count=" + str(result["count"]) + "\n")
                file.write("mode=" + result["mode"] + "\n")
    else:
        result = summarize(args.summarize, args.count, expected_sha=args.expected_sha,
                           expected_apk_sha=args.expected_apk_sha, mode=args.mode)
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
        text += ["", "## Grouped repair findings", "",
                 "| Priority | Responsible worker | Finding | Scope |",
                 "|---|---|---|---|"]
        for issue in result["findings"]:
            text.append("| " + issue["priority"] + " | " + issue["worker"] +
                        " | " + str(issue["title"]).replace("|", "/") +
                        " | " + issue["scope"] + " |")
    (args.out / "emulator_farm_report.md").write_text("\n".join(text) + "\n")
    if args.summarize is not None:
        # Worker-ready aggregation is inert data. Never automatically merge or
        # execute code generated from these findings.
        queue = {"schema_version": 1, "source_commit": args.expected_sha,
                 "apk_sha256": args.expected_apk_sha, "mode": args.mode,
                 "blockers_present": not result["success"],
                 "assignments": [
                    {"id": item["id"], "role": item["worker"],
                     "priority": item["priority"], "title": item["title"],
                     "affected_emulators": item["affected_emulators"],
                     "scope": item["scope"]}
                    for item in result["findings"]]}
        (args.out / "worker_repair_queue.json").write_text(json.dumps(queue, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if args.summarize is None or result["success"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
