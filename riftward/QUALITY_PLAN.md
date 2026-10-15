# RIFTWARD: ECLIPSE — premium offline Android roguelite

## Core vision
A complete, original portrait-space action survival game: become a Riftwarden aboard a luminous solar skiff, survive escalating invader waves in an infinite celestial arena, fire automatically at nearby threats, unleash an area-clearing NOVA ability, collect energy, and choose powerful upgrades between waves. Dark indigo / deep-copper / electric turquoise palette, original procedural artwork, layered animation and music generated with Web Audio. No borrowed IP, no advertisements, no network calls.

## Inspirations and why
- **Vampire Survivors / Brotato:** immediate controls, escalating enemy density, distinct upgrades and brief sessions (structural inspiration, not copied art/code).
- **Archero:** clear between-wave upgrade decisions and readably telegraphed threats.
- **Android Game Level Up:** design for smooth 60 FPS, stability, responsive screens, and input-safe areas; the reference is a target rather than claimed certification.

## Definition of done (quality gates)
1. Real signed debug Android APK, installed and launched successfully on Android 15 emulator.
2. Responsive layout for 320x640, 390x844, 430x932; safe-area UI is visible; no overlapping buttons or clipped upgrade cards.
3. Playable input via pointer/touch joystick and keyboard WASD/arrows; smooth auto-targeting and continuous enemy waves.
4. Three or more distinct enemy types, at least one multi-attack boss, upgrades that change mechanics, escalating difficulty.
5. Pause/resume, wave-end upgrades, defeat, retry, menu, settings, sound and particle controls, FPS toggle, best run saved locally.
6. High-contrast original procedural graphics: seamless infinite parallax starfield and arena grid, distinct silhouettes, impact effects, screen shake (optional), transition animations.
7. Accelerated **real animation-loop clock** tests: menu, gameplay, upgrade selection, boss appearance, defeat and restart; no mock enemies, fake attacks, or hidden test-only bypass of gameplay logic.
8. JavaScript error-free local browser automation plus emulator screenshot and interaction report; pixel change verified.
9. Target >=55 FPS typical Android 4GB+ hardware. Measure during QA; do not claim on unmeasured devices.
10. Keep known good build intact and add improvement branches; review output screenshot and failure logs after each run.

## Release phases
- M0: Initial game vertical slice — controls, combat, effects, native APK, onboarding, no external dependencies.
- M1: Multiple waves, upgrades, boss, persistent progress, audio, menus and presentation.
- M2: Automated screenshot and interaction tests at multiple resolutions; Android emulator build / install / touch test and repair loop.
- M3: Visual and performance refinements based on results; ship a downloadable tested APK with an evidence report.

## Explicit exclusions
No network services, multiplayer, monetization, copyrighted music/assets, app permissions other than vibration, guaranteed Play Store production compliance, or background development outside the active session.

### Loop refinements after first test
- Treat combat activity as enemy presence **or eliminations**: an empty screen after auto-fire can be success, not failure.
- Browser visual QA and long-wave/boss gameplay tests are independent, both required; Android install, launch and tap remains a separate quality gate.
- Source and workflow changes are committed on the development branch while the successful APK artifact remains recoverable.

- Native Android review found the bottom navigation bar overlap and a false-positive blank startup screenshot. Version 1.1 enables immersive sticky fullscreen and rejects unrendered frames by testing real screenshot brightness.
