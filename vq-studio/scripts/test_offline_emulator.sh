#!/usr/bin/env bash
set -euo pipefail
mkdir -p inspection_output/vq-offline
adb install -r vq-studio/app/build/outputs/apk/debug/app-debug.apk
adb shell svc wifi disable || true
adb shell svc data disable || true
adb shell am start -W -n com.trioncompasitor.vqstudio/.OfflineActivity
sleep 4
adb shell pidof com.trioncompasitor.vqstudio
adb shell uiautomator dump /sdcard/offline-ui.xml >/dev/null 2>&1
adb exec-out cat /sdcard/offline-ui.xml > inspection_output/vq-offline/ui.xml
python3 vq-studio/scripts/find_create_button.py inspection_output/vq-offline/ui.xml > inspection_output/vq-offline/tap.txt
read -r x y < inspection_output/vq-offline/tap.txt
adb shell input tap "$x" "$y"
sleep 7
adb exec-out screencap -p > inspection_output/vq-offline/real-offline-model.png
test "$(wc -c < inspection_output/vq-offline/real-offline-model.png)" -gt 7000
adb shell run-as com.trioncompasitor.vqstudio ls files/model_repository > inspection_output/vq-offline/revisions.txt
grep -q -- '-r1.obj' inspection_output/vq-offline/revisions.txt
grep -q -- '-r2.obj' inspection_output/vq-offline/revisions.txt
adb shell run-as com.trioncompasitor.vqstudio ls databases > inspection_output/vq-offline/databases.txt
grep -q 'vq_models.sqlite' inspection_output/vq-offline/databases.txt
echo VQ_OFFLINE_CREATED_TWO_MODELS_NO_NETWORK_PASS
