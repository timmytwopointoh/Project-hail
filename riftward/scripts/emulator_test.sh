#!/usr/bin/env bash
set -euo pipefail
mkdir -p inspection_output/riftward
APK=riftward/app/build/outputs/apk/debug/app-debug.apk
adb wait-for-device
test "$(adb shell getprop sys.boot_completed | tr -d '\r')" = "1"
SDK_TOOLS=$(find "${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/usr/local/lib/android/sdk}}/build-tools" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -n 1)
"$SDK_TOOLS/aapt" dump badging "$APK" > inspection_output/riftward/badging.txt
"$SDK_TOOLS/apksigner" verify --verbose "$APK" > inspection_output/riftward/signature.txt
"$SDK_TOOLS/zipalign" -c -v 4 "$APK" > inspection_output/riftward/alignment.txt
python3 riftward/scripts/emulator_test.py
python3 inspector/visual_compare.py inspection_output/riftward/01_menu.png inspection_output/riftward/02_playing.png --output inspection_output/riftward
