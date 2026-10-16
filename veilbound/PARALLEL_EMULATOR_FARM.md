# VEILBOUND — Parallel Android Emulator Farm

## Verified October 15, 2026

The existing native Android game has passed **four independent GitHub Actions
emulators at the same time**, with separate virtual machines, KVM, Android
SDK/ADB instances, screenshot directories, logcat and QA reports. This is
parallel execution, not four emulators pretending to run in one GitHub VM.

- [Two-device successful run #38834534661](https://github.com/timmytwopointoh/Project-hail/actions/runs/38834534661)
- [Four-device successful run #38835395387](https://github.com/timmytwopointoh/Project-hail/actions/runs/38835395387)
- [Draft integration PR #5](https://github.com/timmytwopointoh/Project-hail/pull/5)
- [Manual Actions workflow](https://github.com/timmytwopointoh/Project-hail/actions/workflows/veilbound-parallel-emulators.yml)

The four verified profiles were Android 15 Pixel 6, Android 14 Pixel 7,
Android 15 Pixel 4 and Android 13 Pixel 5. **Every device passed**:
APK install, game launch, Model Atelier opening, actual orbit gesture,
mesh detail and character/material/lighting switching, inspection of
world assets, combat movement/touch checks and machine screenshot/GL QA.

Each emulator archived **19 real in-game PNG files** (76 total). The
summary validated 20 QA image entries per emulator and each shard's
exact source commit and shared APK SHA256. Identical APK binaries were
installed on all four Android variants.

**Known follow-up:** each software-rendering VM yielded `P2
VB-SLOW-EMULATOR` warnings. Those do not represent measured physical
Moto G (2025) frame rates. Hardware FPS, device thermals, GPU behavior
and final visual approval still require the actual Motorola phone.

## Run manually

Open [VEILBOUND - Parallel Android Emulator Farm](https://github.com/timmytwopointoh/Project-hail/actions/workflows/veilbound-parallel-emulators.yml),
select **Run workflow**, choose the branch
`feature/veilbound-parallel-emulator-reliability`, then choose the number
of `emulator_instances`:

| Workers | Coverage |
|---:|---|
| 1 | Android 15 / Pixel 6 |
| 2 | Above + Android 14 / Pixel 7 |
| 4 | Above + Android 15 / Pixel 4 + Android 13 / Pixel 5 |
| 8 | Adds four more Android 13–15 Pixel configurations (configured, not yet fully tested) |

The default manual request is **2**. Four is a useful release-candidate
cross-version check; 8 should be used selectively because eight separate
runner machines consume more GitHub Actions minutes and may queue
depending on account concurrency limits. There is **no automatic multi-VM
push trigger** after the initial validation.

## How the farm is built

1. Director prepares an exact stable matrix, assigning different API
   levels and Pixel profiles to independent job slots.
2. Build worker compiles a **single** native debug APK, computes its
   SHA256 and uploads it exactly once.
3. Every emulator job downloads that shared APK, verifies its SHA256
   and checks the actual booted Android API before accepting game input.
4. Each worker runs the real `emulator_test.sh` script with app
   installation, ADB touches, screenshots and game/GL log inspection.
5. Every job creates its own `emulator_report.json`,
   `visual_quality_metrics.json`, `task_plan.json`,
   `apk_sha256.txt`, screenshots and logcat.
6. The fan-in auditor requires all jobs' screenshots to actually exist;
   confirms original source commit, quality outcome, status and matching
   binary fingerprint; and blocks the farm when any device has a P0/P1
   QA finding or absent/contradictory evidence.
7. Findings are grouped as **cross-emulator** or **device-specific**
   to help managers prioritize the underlying cause.

The controls only select GitHub Actions development environments.
They do **not** add an emulator to the offline APK or turn the phone
into an emulator server.

## Root-cause repair

The first two-device run mistakenly treated the Android 14 immersive
tutorial as a failed game swipe. The overlay screenshot showed
`Viewing full screen`, with the button rendered as uppercase
`GOT IT`; the old handler only recognized `Got it`.
The code now case-folds Android-owned button text, recognizes
`android:id/ok`, and confirms the popup disappeared before
proceeding. It never dismisses game UI as a system overlay.

The four-emulator pilot also exposed an Actions shell quoting error
in a multiline `script:` block. The runner action passes commands
through `/usr/bin/sh -c`; the farm now invokes the checked-in,
single-command `emulator_shard_test.sh` instead, with separate
syntax and API checks. Both repairs have regression coverage.

## Versioning caveat

These successful runs tested the **immutable commit used to build
their respective shared APKs**. The draft PR is based on the M13
game-development branch at that point in time. When new character or
world changes land in M13, the farm workflow changes should be
reviewed and integrated into that branch before running the release
matrix against the newest game revision. The completed 4/4 run is
not a claim that later M13 commits were tested.
