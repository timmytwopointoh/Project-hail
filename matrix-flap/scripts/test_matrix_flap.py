#!/usr/bin/env python3
"""Verify actual original Matrix Flap gameplay through Android on an emulator."""
import json
import re
import struct
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

PACKAGE = "com.trioncompasitor.matrixflap"
ACTIVITY = PACKAGE + "/.MainActivity"
INSPECT = PACKAGE + ".INSPECT"
OUT = Path("inspection_output/matrix_flap")
APK = Path("matrix-flap/app/build/outputs/apk/debug/app-debug.apk")
PNG_MAGIC = bytes.fromhex("89504e470d0a1a0a")

def adb(*args, timeout=60):
    result = subprocess.run(["adb", *map(str, args)], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=timeout, check=True)
    return result.stdout

def screen(name):
    data = adb("exec-out", "screencap", "-p", timeout=40)
    if not data.startswith(PNG_MAGIC):
        raise AssertionError("Invalid PNG from emulator: " + name)
    w, h = struct.unpack(">II", data[16:24])
    if w < 200 or h < 200 or len(data) < 10000:
        raise AssertionError("Screen image too small or empty: " + name)
    (OUT / name).write_bytes(data)
    return {"name": name, "width": w, "height": h, "bytes": len(data)}

def state():
    adb("shell", "am", "start", "-n", ACTIVITY, "-a", INSPECT,
        "--activity-single-top", timeout=30)
    time.sleep(0.5)
    lines = adb("logcat", "-d", "-s", "MATRIX_FLAP_STATUS:I", "*:S").decode(
        "utf-8", "replace").splitlines()
    lines = [line for line in lines if "MATRIX_FLAP_STATUS" in line]
    if not lines:
        return None
    result = re.search(r"\b(ready|playing|over|unavailable)\b", lines[-1])
    return result.group(1) if result else None

def find_start_button():
    try:
        adb("shell", "uiautomator", "dump", "/sdcard/matrix-flap-ui.xml", timeout=50)
        xml = adb("exec-out", "cat", "/sdcard/matrix-flap-ui.xml")
        (OUT / "ui_hierarchy.xml").write_bytes(xml)
        root = ET.fromstring(xml)
        for item in root.iter("node"):
            label = item.get("text", "") + " " + item.get("content-desc", "")
            if "INITIALIZE RUN" not in label:
                continue
            match = re.fullmatch(
                r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",
                item.get("bounds", ""))
            if match:
                x1, y1, x2, y2 = map(int, match.groups())
                return (x1 + x2) // 2, (y1 + y2) // 2
    except (ET.ParseError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired) as error:
        (OUT / "ui_tree_warning.txt").write_text(str(error))
    return None

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"package": PACKAGE, "apk": str(APK), "installed": False,
              "launched": False, "initial_state": None, "post_tap_state": None,
              "touch_start_verified": False, "screenshots": []}
    try:
        if not APK.is_file():
            raise FileNotFoundError(APK)
        report["install_output"] = adb("install", "-r", str(APK), timeout=120).decode(
            "utf-8", "replace").strip()
        report["installed"] = True
        report["launch_output"] = adb("shell", "am", "start", "-W", "-n",
                                       ACTIVITY).decode("utf-8", "replace").strip()
        report["launched"] = True
        time.sleep(5)
        adb("logcat", "-c")
        for _ in range(10):
            report["initial_state"] = state()
            if report["initial_state"] == "ready":
                break
            time.sleep(1)
        if report["initial_state"] != "ready":
            raise AssertionError("WebView did not report ready state: " +
                                 str(report["initial_state"]))
        first = screen("01_ready.png")
        report["screenshots"].append(first)
        button = find_start_button()
        positions = ([button] if button else []) + [
            (first["width"] // 2, int(first["height"] * y))
            for y in (0.60, 0.62, 0.58, 0.65, 0.55)
        ]
        for x, y in positions:
            adb("shell", "input", "tap", x, y, timeout=30)
            report["tap_coordinates"] = [x, y]
            report["post_tap_state"] = state()
            if report["post_tap_state"] in ("playing", "over"):
                report["touch_start_verified"] = True
                break
        if not report["touch_start_verified"]:
            raise AssertionError("Touch did not start Matrix Flap: " +
                                 str(report["post_tap_state"]))
        report["screenshots"].append(screen("02_after_start.png"))
        adb("shell", "input", "tap", first["width"] // 2,
            first["height"] // 2, timeout=30)
        time.sleep(1)
        report["screenshots"].append(screen("03_after_flap.png"))
        report["after_second_tap_state"] = state()
        report["status"] = "passed"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = str(error)
    finally:
        try:
            logs = adb("logcat", "-d", "-t", "500", timeout=30).decode(
                "utf-8", "replace")
            (OUT / "recent_logcat.txt").write_text(logs)
        except Exception:
            pass
        (OUT / "gameplay_report.json").write_text(
            json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1

if __name__ == "__main__":
    raise SystemExit(main())
