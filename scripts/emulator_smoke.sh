#!/usr/bin/env bash
set -euo pipefail
adb wait-for-device
adb shell input keyevent KEYCODE_WAKEUP || true
for attempt in $(seq 1 60); do
  [ "$(adb shell getprop sys.boot_completed | tr -d '\r')" = "1" ] && break
  sleep 5
done
test "$(adb shell getprop sys.boot_completed | tr -d '\r')" = "1"
sleep 10
adb shell getprop sys.boot_completed | tee inspection_output/boot_completed.txt
adb shell getprop ro.build.version.release | tee inspection_output/android_version.txt
adb devices -l | tee inspection_output/adb_devices.txt
adb shell screencap -p /sdcard/home.png
adb pull /sdcard/home.png inspection_output/emulator_home.png
adb shell am start -W -a android.settings.SETTINGS | tee inspection_output/settings_launch.txt
sleep 3
adb shell screencap -p /sdcard/settings.png
adb pull /sdcard/settings.png inspection_output/settings_screen.png
adb shell input keyevent KEYCODE_HOME
adb shell wm size | tee inspection_output/display_size.txt
adb shell wm density | tee inspection_output/display_density.txt
adb shell input keyevent KEYCODE_HOME
adb shell input swipe 250 700 250 300 350
sleep 2
adb shell screencap -p /sdcard/after-swipe.png
adb pull /sdcard/after-swipe.png inspection_output/after_swipe.png
.venv/bin/python inspector/visual_compare.py inspection_output/emulator_home.png inspection_output/settings_screen.png --output inspection_output
adb shell settings put system accelerometer_rotation 0 || true
adb shell settings put system user_rotation 1 || true
sleep 3
adb shell screencap -p /sdcard/landscape.png
adb pull /sdcard/landscape.png inspection_output/landscape.png
python3 inspector/navigate.py inspector/smoke_plan.json --output inspection_output/navigation
adb shell settings put system user_rotation 0 || true
adb shell settings put system accelerometer_rotation 1 || true
python3 - <<'PY'
import pathlib,struct,json
folder=pathlib.Path("inspection_output")
checks={}
for name in ("emulator_home.png","settings_screen.png","after_swipe.png","landscape.png"):
    data=(folder/name).read_bytes()
    assert data[:8]==bytes.fromhex("89504e470d0a1a0a"), name
    width,height=struct.unpack(">II",data[16:24])
    assert width>100 and height>100, name
    checks[name]={"width":width,"height":height,"bytes":len(data)}
(folder/"screen_checks.json").write_text(json.dumps(checks,indent=2))
PY
if [ -n "${APK_PATH:-}" ]; then
  python3 - <<'PY'
import os,pathlib,sys
p=pathlib.Path(os.environ["APK_PATH"])
if p.is_absolute() or ".." in p.parts or p.suffix.lower()!=".apk" or not p.is_file():
    sys.exit("Invalid APK_PATH: expected repository-relative existing APK")
PY
  python3 inspector/static_inspect.py "$APK_PATH" --output inspection_output
  adb install -r "$APK_PATH" | tee inspection_output/install.txt
  PACKAGE=$(python3 -c 'import json; print(json.load(open("inspection_output/static_report.json")).get("package") or "")')
  if [ -n "$PACKAGE" ]; then
    adb shell monkey -p "$PACKAGE" -c android.intent.category.LAUNCHER 1 | tee inspection_output/launch.txt
    sleep 3
    adb shell screencap -p /sdcard/launched.png
    adb pull /sdcard/launched.png inspection_output/launched.png
    adb logcat -d -t 500 | tee inspection_output/logcat.txt
  fi
  adb shell pm list packages -3 | tee inspection_output/packages.txt
  adb shell screencap -p /sdcard/installed.png
  adb pull /sdcard/installed.png inspection_output/after_install.png
fi
python3 - <<'PY'
import json,os,pathlib
out=pathlib.Path("inspection_output")
(out/"report.json").write_text(json.dumps({"api_level":35,"emulator_booted":(out/"boot_completed.txt").read_text().strip()=="1","screenshots_validated":(out/"screen_checks.json").exists(),"visual_comparison_generated":(out/"visual_comparison.json").exists(),"navigation_report_generated":(out/"navigation"/"navigation_report.json").exists(),"apk_requested":bool(os.getenv("APK_PATH"))},indent=2))
PY
