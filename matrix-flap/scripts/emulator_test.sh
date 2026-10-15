#!/usr/bin/env bash
set -euo pipefail
mkdir -p inspection_output/matrix_flap
APK=matrix-flap/app/build/outputs/apk/debug/app-debug.apk
adb wait-for-device
test "$(adb shell getprop sys.boot_completed | tr -d '\r')" = "1"
aapt dump badging "$APK" > inspection_output/matrix_flap/apk_badging.txt
apksigner verify --verbose "$APK" > inspection_output/matrix_flap/apk_signature.txt
zipalign -c -v 4 "$APK" > inspection_output/matrix_flap/apk_alignment.txt
python3 matrix-flap/scripts/test_matrix_flap.py
python3 inspector/visual_compare.py   inspection_output/matrix_flap/01_ready.png   inspection_output/matrix_flap/02_after_start.png   --output inspection_output/matrix_flap
