#!/usr/bin/env bash
set -euo pipefail
mkdir -p inspection_output/matrix_flap
APK=matrix-flap/app/build/outputs/apk/debug/app-debug.apk
adb wait-for-device
test "$(adb shell getprop sys.boot_completed | tr -d '\r')" = "1"
SDK_TOOLS=$(find "${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/usr/local/lib/android/sdk}}/build-tools" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -n 1)
test -x "$SDK_TOOLS/aapt"
"$SDK_TOOLS/aapt" dump badging "$APK" > inspection_output/matrix_flap/apk_badging.txt
"$SDK_TOOLS/apksigner" verify --verbose "$APK" > inspection_output/matrix_flap/apk_signature.txt
"$SDK_TOOLS/zipalign" -c -v 4 "$APK" > inspection_output/matrix_flap/apk_alignment.txt
python3 matrix-flap/scripts/test_matrix_flap.py
python3 inspector/visual_compare.py   inspection_output/matrix_flap/01_ready.png   inspection_output/matrix_flap/02_after_start.png   --output inspection_output/matrix_flap
