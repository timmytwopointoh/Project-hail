# Matrix Flap v1.2 — Cinematic quality plan

Baseline: original stable Matrix Flap APK, verified Android 15 GitHub Actions #4.
Candidate branch: feature/matrix-flap-cinematic-v12. Never overwrite known-good version before regression tests.

## Graphics objectives and acceptance gates

1. **Menu depth:** visible layered holo frame, animated rotating emblem, multi-layer shadows and subtle levitation. Test menu screenshot at 320×640, 390×844, 430×932; real tap should start game.
2. **Animated atmosphere:** distant orbital body, twinkling stars and moving light shafts without hiding obstacles. Compare menu and gameplay screenshots.
3. **Combat-free flight spectacle:** ship engine trail follows movement and score triggers concentric energy shockwave. Existing collision envelope must be unchanged.
4. **Controls preserved:** tap-to-start, tap-to-flap, pause/resume, game over, retry, settings and Android Back all remain functional.
5. **Legibility:** HUD and obstacle gaps remain readable. No menus covered by navigation bars or camera cutouts; narrow viewport screenshots reviewed.
6. **Accessibility and battery:** reduced-motion removes CSS animation; Effects OFF disables decorative layers; automatic render resolution reduction preserves playability on slower GPUs.
7. **APK authenticity:** Android Gradle Plugin build, APK signature and alignment verify, ADB install, game launch and JS ready state on Android 15.
8. **Interaction + proof:** ADB starts game, verifies `playing` or `over`, captures 2 PNGs; visual comparison is materially different (>0.5% changed pixels). GitHub artifact retains logs and screenshots.
9. **No false release status:** only successfully completed emulator workflow may publish a `tested` APK; a separately named candidate can be attached on failure for debugging.

## Iteration log

- Pass 1: v1.1 preserved, local gameplay and scoring tested. Emulator intermittently failed due Pixel Launcher and ADB stalls; keep working baseline.
- Pass 2: v1.2 visual improvements: CSS dimensional deck, ring animation, orbital glow, stars, motion parallax, trails, score feedback and Fx OFF compatibility.
- Pass 3: APK rebuild + emulator test; inspect failed stage, correct and rerun until a verified result exists or identify the specific blocker.

## Manual sign-off remaining

Real-phone feel, battery use, sound/haptics, hardware-specific frame pacing and long-session gameplay cannot be guaranteed from emulator screenshots alone.
