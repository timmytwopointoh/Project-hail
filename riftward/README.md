# RIFTWARD: ECLIPSE

A brand-new original **offline Android space survival roguelite** developed using the APK Vision Inspector pipeline. Android package: `com.trioncompasitor.riftward`.

## Gameplay
- Portrait space survival with automatic targeting; drag the left virtual joystick to steer.
- Activate **NOVA** to clear nearby enemies and projectiles. Charged on cooldown, not pay-to-win.
- Four distinct hostile classes (wisp, skitter, prism, bulwark) and a multi-attack Eclipse Sentinel boss.
- Survive each 25-second wave to choose one of three randomly offered upgrades; combine orbital glaives, piercing bolts, shields and nova effects.
- Save best wave, eliminations and record shards offline. Pause, retry and upgrade between waves.
- Premium procedural art, no borrowed assets, no external APIs, no advertising.

## Build APK

`gradle -p riftward :app:assembleDebug --no-daemon`

APK: `riftward/app/build/outputs/apk/debug/app-debug.apk`

## Tests

`python3 riftward/scripts/browser_qa.py` runs UI/graphics tests across 320×640, 390×844 and 430×932 (Chromium/Playwright required). `bash riftward/scripts/emulator_test.sh` performs Android 15 signing, alignment, install, launch, tap and screenshot checks.

Refer to [QUALITY_PLAN.md](QUALITY_PLAN.md) for objective targets and remaining physical-phone checks.
