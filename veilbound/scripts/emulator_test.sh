#!/usr/bin/env bash
set -euo pipefail
mkdir -p inspection_output/veilbound
adb wait-for-device
test "$(adb shell getprop sys.boot_completed | tr -d '\r')" = "1"
APK="veilbound/app/build/outputs/apk/debug/app-debug.apk"
SDK_TOOLS=$(find "${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/usr/local/lib/android/sdk}}/build-tools" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -n 1)
"$SDK_TOOLS/aapt" dump badging "$APK" > inspection_output/veilbound/apk_badging.txt
"$SDK_TOOLS/apksigner" verify --verbose "$APK" > inspection_output/veilbound/apk_signature.txt
"$SDK_TOOLS/zipalign" -c -v 4 "$APK" > inspection_output/veilbound/apk_alignment.txt
python3 veilbound/scripts/emulator_test.py
