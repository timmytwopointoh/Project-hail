# Matrix Flap — Iterative Quality Gate (v1.1)

Work from the original `Matrix-Flap-Forge-v7.json` and the previously emulator-tested Android WebView APK. Preserve the package name, game rules, score saving, and offline play. Do **not** substitute an unrelated prototype.

## Goals and acceptance checks

| ID | Goal | Acceptance test / evidence |
|---|---|---|
| G1 | Keep the original playable | Android 15: APK builds, signing/alignment verify, installs, starts, and `ready → playing` on touch |
| G2 | Make the game visually distinctive | Screenshots visibly show readable cockpit/score, refined ship, parallax skyline, neon gates, and polished menu; compare multiple sizes |
| G3 | Make controls complete | Tests cover start, flap, pause, resume, restart, main menu and settings; collision still ends a run |
| G4 | Respect different phone screens | No off-screen primary controls at 320×640, 390×844, 430×932 CSS pixel viewports; test responsive layout |
| G5 | Persist meaningful preferences | Sound, effects, haptics, and optional FPS counter toggle; settings and best score persist via localStorage in Android WebView |
| G6 | Run predictably | Animation uses capped timestep and pixel ratio; backgrounding pauses play; no uncaught JS errors in local QA |
| G7 | Keep the new APK genuinely installable | Android SDK `aapt`, `zipalign`, `apksigner`, and ADB tests succeed; artifact only published on green run |
| G8 | Preserve diagnostics and honest evidence | Save snapshots, JSON diagnostics and regression results in GitHub Actions artifacts, mark unverified goals honestly |

## Improvement loop

1. Observe existing emulator screenshots and source; write down a specific defect.
2. Make the smallest code change to resolve it without discarding functioning systems.
3. Run JavaScript syntax, three-viewport UI regressions, and compare screenshots.
4. Package as an Android APK; run the emulator install/launch/touch test and collect artifacts.
5. Diagnose failure using GitHub Actions logs, correct it, and rerun.
6. Advance to the next goal only with evidence; report any unverified cases to the phone tester.

## Observations from the verified v1.0 baseline

- Main menu, launch, `ready → playing`, and two screenshots already passed on the emulator.
- Gameplay had limited world depth, a small player sprite, and no settings/pause controls.
- The original main menu screenshot was visually readable at 1080×2400.

## Boundaries

- The emulator can verify compatibility and interaction, not subjective fun, all device GPU drivers, battery use, or the experience on a physical phone.
- The final user-on-device test is required before calling this a production release.