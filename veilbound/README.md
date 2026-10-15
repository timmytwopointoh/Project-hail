# VEILBOUND: ASH OF THE BELLS

**Original native-3D Android dark-fantasy action RPG.** Not a browser/WebView game.

> The seven ward bells held back the Hollowing. One night they fell silent.
> The Warden was sent to relight the last ember beneath Mourning Vale—only to
> learn that the bells were built to imprison a living god, not protect mankind.

## Playable prologue (milestone M1)
- Landscape, over-the-shoulder 3D third-person camera with touch movement and camera orbit
- Native OpenGL ES renderer with dynamic lighting, stylized masonry, layered fog and ruins
- Deliberate stamina-based melee, dodge roll, enemies with telegraphed attacks
- Checkpoint, recovery on defeat, objective tracking, interactable story inscriptions
- First small boss encounter, ending hook for the next region
- Entirely offline, source-controlled and reproducible Android APK build

## Build
```bash
gradle -p veilbound :app:assembleDebug --no-daemon
```
APK: `veilbound/app/build/outputs/apk/debug/app-debug.apk`

## Controls
Left thumb: move. Right drag: rotate camera. ATTACK: sword strike.
DODGE: roll with invincibility window. INTERACT: investigate or rest at nearby structures.
Touch to dismiss dialogue. All graphics are native GL, menus/HUD drawn with native Android Canvas.

## Important
This is an ambitious *vertical slice*, not a claim that an indie APK already
matches a high-budget open-world RPG in asset fidelity, hours of narrative or
animation quality. We will judge progress against the measurable plan below,
with real-phone testing after emulator and automated checks.
