#!/usr/bin/env bash
# Run inside Android emulator with validator-produced inputs. Preserve diagnostics on failure.
set -euo pipefail
APK_FILE="$1"
EXPECTED_PACKAGE="${2:-}"
OUT="${3:-worker-results}"
mkdir -p "$OUT"
test -s "$APK_FILE"
command -v adb >/dev/null
command -v aapt >/dev/null
trap 'adb logcat -d -t 1500 > "$OUT/logcat.txt" 2>&1 || true; adb shell pm list packages -3 > "$OUT/installed_packages.txt" 2>&1 || true' EXIT
adb wait-for-device
for _ in $(seq 1 120); do
  test "$(adb shell getprop sys.boot_completed | tr -d '\r')" = 1 && break
  sleep 2
done
test "$(adb shell getprop sys.boot_completed | tr -d '\r')" = 1
PACKAGE="$(aapt dump badging "$APK_FILE" | sed -n "s/^package: name='\([^']*\)'.*/\1/p" | head -n 1)"
[ -n "$PACKAGE" ] || { echo 'Unable to identify APK package' >&2; exit 2; }
if [ -n "$EXPECTED_PACKAGE" ] && [ "$PACKAGE" != "$EXPECTED_PACKAGE" ]; then
  echo "Package mismatch: found $PACKAGE expected $EXPECTED_PACKAGE" >&2
  exit 2
fi
printf '%s\n' "$PACKAGE" > "$OUT/package.txt"
if ! adb install -r "$APK_FILE" 2>&1 | tee "$OUT/install.txt"; then
  echo 'FAIL: Android rejected APK installation' >&2
  exit 1
fi
grep -q 'Success' "$OUT/install.txt" || { echo 'FAIL: adb did not report success' >&2; exit 1; }
adb shell pm path "$PACKAGE" > "$OUT/package_path.txt"
test -s "$OUT/package_path.txt"
adb shell monkey -p "$PACKAGE" -c android.intent.category.LAUNCHER 1 2>&1 | tee "$OUT/launch.txt"
grep -q 'Events injected: 1' "$OUT/launch.txt" || { echo 'FAIL: launcher not found' >&2; exit 1; }
sleep 5
adb shell screencap -p /sdcard/worker_game.png
adb pull /sdcard/worker_game.png "$OUT/game.png" >/dev/null
test -s "$OUT/game.png"
if adb logcat -d -t 600 | grep -A 14 'FATAL EXCEPTION' | grep -q "$PACKAGE"; then
  echo 'FAIL: fatal exception in app' >&2
  exit 1
fi
echo 'PASS: APK installed, package found, launched, screenshot captured' | tee "$OUT/summary.txt"
