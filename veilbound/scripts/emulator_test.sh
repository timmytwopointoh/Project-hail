#!/usr/bin/env bash
set -euo pipefail
mkdir -p inspection_output/veilbound
adb wait-for-device
# Moto g (2025): Android 15, 1604x720 landscape, 263 ppi, 4GB RAM.
# Match the device VIEWPORT, not its physical MediaTek/Mali GPU: CI remains
# x86_64 software-rendered and must not claim real hardware FPS.
adb shell wm size 1604x720
adb shell wm density 263
cat > inspection_output/veilbound/target_device.json <<'JSON'
{
  "target": "Motorola moto g (2025)",
  "android_api": 35,
  "orientation": "landscape",
  "resolution_pixels": [1604, 720],
  "pixel_density_dpi": 263,
  "physical_ram_gb": 4,
  "real_gpu": "Mali-G57 MC2 (not emulated)",
  "real_cpu": "MediaTek Dimensity 6300 (not emulated)",
  "emulator_is_hardware_proof": false
}
JSON
sleep 3
test "$(adb shell getprop sys.boot_completed | tr -d '\r')" = "1"
APK="veilbound/app/build/outputs/apk/debug/app-debug.apk"
SDK_TOOLS=$(find "${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/usr/local/lib/android/sdk}}/build-tools" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -n 1)
"$SDK_TOOLS/aapt" dump badging "$APK" > inspection_output/veilbound/apk_badging.txt
"$SDK_TOOLS/apksigner" verify --verbose "$APK" > inspection_output/veilbound/apk_signature.txt
"$SDK_TOOLS/zipalign" -c -v 4 "$APK" > inspection_output/veilbound/apk_alignment.txt
python3 veilbound/scripts/emulator_test.py
