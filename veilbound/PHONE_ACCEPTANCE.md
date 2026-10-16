# Motorola Moto G (2025) — Physical Release Acceptance

**Status:** Not yet tested by this GitHub-hosted pipeline on the user's
actual phone. Android 15 x86_64/SwiftShader and a 1604x720 landscape viewport
approximate the display size, **not** Dimensity/Mali GPU speed, device
temperature, battery life or touch feel. This gate remains outstanding
until someone installs the app on the physical device.

## Safe phone-only smoke test

1. In GitHub Actions, choose a **successful** `VEILBOUND - Native 3D
   Android RPG` run or a successfully emulator-tested reviewed-patch
   run. Download its `TESTED-apk` artifact ZIP, extract the debug APK
   and install the app. Do not treat `UNVERIFIED` APKs as release-tested.
   Installing from outside the Play Store may require granting your file
   manager permission to install unknown apps. Turn that permission off
   again when finished.
2. Disconnect Wi-Fi and cellular data temporarily. VEILBOUND should
   launch and be playable **offline** (no AI model or network required).
3. Start at the title screen. Open **Model Atelier** by touch, inspect
   the hero, perform three camera orbit drags, toggle close-up/mesh
   detail, and switch model, material and lighting. Record which
   interactions visibly work, and capture screenshots where safe.
4. Return to title and enter the prologue. Walk, rotate the camera,
   attack, dodge and encounter a foe. Confirm the blade swing aligns
   with damage and the character does not float or sink into ground.
   Capture a screenshot of idle, moving and sword contact.
5. Test at least ten minutes of active gameplay. Note warmth, stutter,
   touch lag and any crash. Never infer actual game FPS from the phone
   refresh-rate indicator; it may reflect only screen refresh.

## Objective checks when ADB/PC is available

The package is `game.ashenveil.veilbound`.
Collect observations with the **Android SDK platform-tools** on a
computer connected to your own phone in USB-debug mode:

```bash
adb devices
adb shell getprop ro.product.model
adb shell getprop ro.build.version.sdk
adb shell pidof game.ashenveil.veilbound
adb logcat -d -s VEILBOUND_STUDIO:I VEILBOUND_STATE:I '*:S'
adb shell dumpsys meminfo game.ashenveil.veilbound
```

Never post private device serials, accounts, unrelated logcat data or
device identifiers. Renderer `FRAME_QA` log entries, when present,
are a better basis for frame statistics than a screenshot or refresh
rate icon. Keep physical-device FPS evidence distinct from emulator
SwiftShader FPS. A failed interaction must have recorded steps and
evidence before the manager assigns a code-repair task.

## Actual acceptance threshold

- APK installs, launches and returns from Studio without crash.
- Every Studio touch control changes its intended state and a
  corresponding 3D stage image (not only a debug variable).
- Basic 3D movement, sword strikes, dodging, checkpoint/gameplay state
  and control HUD are visibly functional.
- No severe lag, major texture corruption or reproducible overheating.
  Record frame-time distribution under real gameplay before choosing
  any numerical FPS target.
- The new character mesh/animation must be inspected on the phone at
  rest, in locomotion and during combat before claiming a realism jump.

**Do not mark final device verification completed automatically.**
Only screenshots, recorded observations and phone-side instrumentation
from an actual test satisfy this last release criterion.
