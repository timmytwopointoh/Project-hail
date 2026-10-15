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

def screen(name, timeout=40):
    data = adb("exec-out", "screencap", "-p", timeout=timeout)
    if not data.startswith(PNG_MAGIC):
        raise AssertionError("Invalid PNG from emulator: " + name)
    w, h = struct.unpack(">II", data[16:24])
    if w < 200 or h < 200 or len(data) < 10000:
        raise AssertionError("Screen image too small or empty: " + name)
    (OUT / name).write_bytes(data)
    return {"name": name, "width": w, "height": h, "bytes": len(data)}

def state():
    """Read Java-forwarded WebView state without launching extra Activities."""
    lines = adb("logcat", "-d", "-s", "MATRIX_FLAP_STATUS:I", "*:S",
                timeout=14).decode("utf-8", "replace").splitlines()
    lines = [line for line in lines if "MATRIX_FLAP_STATUS:" in line]
    if not lines:
        return None
    result = re.search(r"MATRIX_FLAP_STATUS: (ready|playing|over)", lines[-1])
    return result.group(1) if result else None

def hierarchy():
    adb("shell", "uiautomator", "dump", "/sdcard/matrix-flap-system-ui.xml", timeout=45)
    return ET.fromstring(adb("exec-out", "cat", "/sdcard/matrix-flap-system-ui.xml"))

def dismiss_launcher_anr():
    """Recover from transient Pixel Launcher ANR without masking game crashes."""
    try:
        root = hierarchy()
        texts = [n.get("text", "") for n in root.iter("node")]
        if not any("launcher" in text.lower() and
                   ("isn't responding" in text.lower() or "not responding" in text.lower())
                   for text in texts):
            return False
        button = next((n for n in root.iter("node") if n.get("text") == "Close app"), None)
        if button is None:
            return False
        m = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", button.get("bounds", ""))
        if not m:
            return False
        left, top, right, bottom = map(int, m.groups())
        adb("shell", "input", "tap", (left + right)//2, (top + bottom)//2)
        time.sleep(2)
        adb("shell", "am", "start", "-n", ACTIVITY)
        return True
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ET.ParseError):
        return False

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
        report["launcher_recoveries"] = 0
        # Avoid synchronous UIAutomator and clearing logcat: both can freeze
        # software-rendered Android 15 emulators while the launcher is busy.
        for _ in range(6):
            report["initial_state"] = state()
            if report["initial_state"] == "ready":
                break
            time.sleep(1)
        if report["initial_state"] != "ready":
            raise AssertionError("WebView did not report ready state: " +
                                 str(report["initial_state"]))
        first = screen("01_ready.png")
        report["screenshots"].append(first)
        # The centered Start control occupies roughly 57-65% screen height.
        # Try a real ADB touch before expensive UIAutomator introspection.
        positions = [(first["width"] // 2, int(first["height"] * y))
                     for y in (0.60, 0.62, 0.58, 0.65, 0.55)]
        for attempt, (x, y) in enumerate(positions):
            if attempt > 1 and dismiss_launcher_anr():
                report["launcher_recoveries"] += 1
            adb("shell", "input", "tap", x, y, timeout=30)
            report["tap_coordinates"] = [x, y]
            time.sleep(0.5)
            report["post_tap_state"] = state()
            if report["post_tap_state"] in ("playing", "over"):
                report["touch_start_verified"] = True
                break
        if not report["touch_start_verified"]:
            raise AssertionError("Touch did not start Matrix Flap: " +
                                 str(report["post_tap_state"]))
        report["screenshots"].append(screen("02_after_start.png"))
        # Required acceptance criteria are complete: installed, launched, ready,
        # touchscreen start verified, and ready/gameplay screenshots captured.
        report["status"] = "passed"
        # Additional flap/capture is nonessential and can time out if the
        # software-rendered emulator becomes temporarily unresponsive.
        try:
            adb("shell", "input", "tap", first["width"] // 2,
                first["height"] // 2, timeout=12)
            time.sleep(0.5)
            report["screenshots"].append(screen("03_after_flap.png", timeout=15))
            report["after_second_tap_state"] = state()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
                AssertionError, ValueError) as error:
            report["optional_extra_capture_warning"] = str(error)
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
