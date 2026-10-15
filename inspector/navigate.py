#!/usr/bin/env python3
"""Record repeatable Android emulator navigation with screenshots and UI snapshots.

Plans are JSON: {"steps":[{"action":"home"},{"action":"settings"},
{"action":"tap","x":300,"y":400},{"action":"back"}]}.
Only the documented actions are accepted.
"""
import argparse
import json
import re
import subprocess
import time
from pathlib import Path

PNG_MAGIC = bytes.fromhex("89504e470d0a1a0a")


def adb(*args, timeout=35):
    result = subprocess.run(["adb", *map(str, args)], capture_output=True,
                            timeout=timeout, check=True)
    return result.stdout


def screenshot(destination):
    data = adb("exec-out", "screencap", "-p", timeout=40)
    if not data.startswith(PNG_MAGIC):
        raise ValueError("ADB returned an invalid screenshot")
    destination.write_bytes(data)
    return len(data)


def dump_ui(destination):
    adb("shell", "uiautomator", "dump", "/sdcard/vision-window.xml", timeout=45)
    data = adb("exec-out", "cat", "/sdcard/vision-window.xml")
    if b"<hierarchy" not in data:
        raise ValueError("Android accessibility hierarchy was unavailable")
    destination.write_bytes(data)


def bounded_int(obj, key, limit=10000):
    value = obj[key]
    if type(value) is not int or not 0 <= value <= limit:
        raise ValueError(f"{key} must be an integer between 0 and {limit}")
    return value


def execute(steps, directory, pause=1.0):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if not isinstance(steps, list) or len(steps) > 100:
        raise ValueError("steps must be a list of at most 100 actions")
    report = []
    for index, step in enumerate(steps, 1):
        if not isinstance(step, dict):
            raise ValueError(f"step {index} is not an object")
        action = step.get("action")
        result = {"step": index, "action": action}
        try:
            if action in ("home", "back"):
                adb("shell", "input", "keyevent",
                    "KEYCODE_HOME" if action == "home" else "KEYCODE_BACK")
            elif action == "settings":
                adb("shell", "am", "start", "-W", "-a",
                    "android.settings.SETTINGS", timeout=60)
            elif action == "tap":
                adb("shell", "input", "tap", bounded_int(step, "x"),
                    bounded_int(step, "y"))
            elif action == "swipe":
                adb("shell", "input", "swipe",
                    bounded_int(step, "x1"), bounded_int(step, "y1"),
                    bounded_int(step, "x2"), bounded_int(step, "y2"),
                    bounded_int(step, "duration_ms", 10000))
            elif action == "wait":
                delay = step.get("seconds", 1)
                if type(delay) not in (float, int) or not 0 <= delay <= 10:
                    raise ValueError("Wait must be between 0 and 10 seconds")
                time.sleep(delay)
            elif action == "launch":
                package = step.get("package", "")
                if not isinstance(package, str) or not re.fullmatch(
                    r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+", package
                ):
                    raise ValueError("Invalid Android package name")
                adb("shell", "monkey", "-p", package, "-c",
                    "android.intent.category.LAUNCHER", "1", timeout=60)
            elif action not in ("screenshot", "dump_ui"):
                raise ValueError(f"Unknown action: {action}")
            if action != "wait":
                time.sleep(pause)
            if action != "dump_ui":
                name = f"step_{index:02d}_{action}.png"
                result["screenshot"] = name
                result["screenshot_bytes"] = screenshot(directory / name)
            if action in ("settings", "dump_ui"):
                name = f"step_{index:02d}_{action}.xml"
                try:
                    dump_ui(directory / name)
                    result["ui_hierarchy"] = name
                except Exception as exc:
                    result["ui_hierarchy_error"] = str(exc)
            result["status"] = "passed"
        except (KeyError, ValueError, subprocess.CalledProcessError,
                subprocess.TimeoutExpired) as exc:
            result["status"] = "failed"
            result["error"] = str(exc)
        report.append(result)
    (directory / "navigation_report.json").write_text(
        json.dumps({"steps": report, "passed": sum(
            row["status"] == "passed" for row in report)}, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", help="Path to JSON navigation plan")
    parser.add_argument("--output", default="inspection_output/navigation")
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text())
    results = execute(plan["steps"], args.output)
    print(json.dumps(results, indent=2))
    raise SystemExit(int(any(x["status"] == "failed" for x in results)))
