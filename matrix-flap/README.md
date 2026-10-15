# Matrix Flap — Neon Flight (Android emulator test)

This is the original **Matrix Flap** game from `Matrix-Flap-Forge-v7.json`, packaged as a genuine offline Android WebView APK for automated emulator testing.

- Preserves original `index.html` contents and Forge project JSON.
- Uses the original package ID `com.trioncompasitor.matrixflap`.
- Built with Android Gradle Plugin 8.7.3; targets Android SDK 29 and compiles against 35.
- Does not require Internet access; game HTML/JS/assets are embedded in the APK.
- The Android Activity supports a read-only diagnostics intent to report the game's own `matrixFlapStatus()` in logcat.
- GitHub Actions builds and signs the debug APK, installs it on Android 15, takes screenshots, taps the game, and verifies state changes.

Build: `gradle -p matrix-flap :app:assembleDebug --no-daemon`

This is a newly compiled APK from the **existing original game source**, not a previously downloaded phone-built APK. Debug signing is only for testing.
