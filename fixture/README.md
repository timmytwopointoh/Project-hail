# Native Android Vision Probe

This fixture builds a genuine Java Android APK, independent of a browser or JSON package.

Build with Android SDK and Gradle 8.9:

```bash
cd fixture
gradle :app:assembleDebug --no-daemon
```

The output is `fixture/app/build/outputs/apk/debug/app-debug.apk`.

Run the end-to-end test against a running emulator:

```bash
python3 fixture/test_probe.py fixture/app/build/outputs/apk/debug/app-debug.apk
```

The test installs the app, opens its launcher Activity, captures a screenshot, reads the UIAutomator accessibility tree, taps the native button, verifies the tap counter changed, and writes a JSON test report and another screenshot.
