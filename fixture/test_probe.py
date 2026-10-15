#!/usr/bin/env python3
"""Install, launch, tap and visually verify the native Vision Probe APK."""
import argparse
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

PACKAGE = "dev.projecthail.visionprobe"
PNG_MAGIC = bytes.fromhex("89504e470d0a1a0a")

def adb(*args, timeout=60):
    return subprocess.run(["adb", *map(str, args)], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True, timeout=timeout).stdout

def hierarchy():
    adb("shell", "uiautomator", "dump", "/sdcard/probe-ui.xml", timeout=45)
    return ET.fromstring(adb("exec-out", "cat", "/sdcard/probe-ui.xml"))

def find_text(root, text):
    return next((node for node in root.iter("node") if node.get("text") == text), None)

def screenshot(path):
    data = adb("exec-out", "screencap", "-p")
    if not data.startswith(PNG_MAGIC):
        raise ValueError("Invalid emulator screenshot")
    path.write_bytes(data)

def main(apk, out):
    out.mkdir(parents=True, exist_ok=True)
    report = {"package": PACKAGE, "installed": False, "launched": False,
              "tap_verified": False, "screenshots": []}
    try:
        report["install_output"] = adb("install", "-r", str(apk)).decode("utf-8", "replace").strip()
        report["installed"] = True
        adb("shell", "am", "start", "-W", "-n", PACKAGE + "/.MainActivity")
        time.sleep(3)
        report["launched"] = True
        screenshot(out / "probe_before.png")
        report["screenshots"].append("probe_before.png")
        button = find_text(hierarchy(), "TAP TO TEST")
        if button is None:
            raise AssertionError("Button not visible in Android UI hierarchy")
        match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", button.get("bounds", ""))
        if match is None:
            raise AssertionError("Button lacks valid screen bounds")
        x1, y1, x2, y2 = map(int, match.groups())
        adb("shell", "input", "tap", (x1 + x2) // 2, (y1 + y2) // 2)
        time.sleep(2)
        screenshot(out / "probe_after.png")
        report["screenshots"].append("probe_after.png")
        if find_text(hierarchy(), "TAPPED 1 TIME") is None:
            raise AssertionError("Tap did not update native counter")
        report["tap_verified"] = True
        report["status"] = "passed"
    except Exception as exc:
        report["status"] = "failed"
        report["error"] = str(exc)
    (out / "native_probe_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("apk", type=Path)
    parser.add_argument("--output", type=Path, default=Path("inspection_output/native_probe"))
    args = parser.parse_args()
    raise SystemExit(main(args.apk, args.output))
