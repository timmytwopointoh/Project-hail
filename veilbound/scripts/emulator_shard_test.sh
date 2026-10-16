#!/usr/bin/env bash
# Called by reactivecircus/android-emulator-runner as ONE shell command.
# Never embed a quoted multiline shell script inside action's 'script:' field;
# older action versions pass it through /usr/bin/sh -c and quoting can break.
set -euo pipefail
expected="${VEILBOUND_EXPECTED_API:?Missing expected Android API}"
observed="$(adb shell getprop ro.build.version.sdk | tr -d '\r')"
if [[ "$observed" != "$expected" ]]; then
  echo "Wrong Android system image: requested API=$expected, got API=$observed" >&2
  exit 3
fi
echo "Verified independent emulator API=$observed and source commit=${GITHUB_SHA:-not-provided}"
exec bash veilbound/scripts/emulator_test.sh
