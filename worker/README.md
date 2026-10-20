# AI-controlled Android worker (contract v1)

This is a **review-gated** bridge from any AI controller to GitHub Actions. The model outputs a small versioned JSON command; a separately authorized controller validates the action and opens a PR containing a single request file under `worker/requests/<job_id>.json`. Approval and merge into `main` initiates one CI worker run, rather than an unbounded background agent. This follows the repository's storage and QA rules in `AGENTS.md`.

**Capability discovery:** `worker/capabilities.json` describes the supported version, commands, and project allowlist. A future offline AI needs only that file and the JSON contract, never runner-specific commands, tokens, or hidden shell instructions.

A cheap contract probe (not an emulator test):

```json
{"protocol":"vq.worker.v1","job_id":"health-001","command":"protocol.validate"}
```

Build, sign with Android's debug configuration, and test a project (replace source_sha with a real pinned commit):

```json
{"protocol":"vq.worker.v1","job_id":"echoform-001","command":"android.build_test","project":"echoform","source_sha":"0000000000000000000000000000000000000000","expected_package":"com.echoform.game"}
```

Install an APK already committed under the trusted staging directory:

```json
{"protocol":"vq.worker.v1","job_id":"peks-audio-001","command":"android.install_test","apk_path":"worker/staging/PeksPlunder.apk","expected_package":"com.peckscove.test34"}
```

**Important:** Neither the latest Pek's Plunder APK nor its own source repository is present in Project-hail yet. The install request above is an example, not a completed test. To test the cooking game, securely stage its actual APK or create its own repository and add its identity to the audited allowlist. `New-game-` is Echoform, **not** Pek's Plunder; do not overwrite it.

Successful CI produces the install result, Android 35 screenshot, package path, logcat and a built APK for `android.build_test`. A successful emulator install is not proof of audio quality or perfect gameplay. The workflow uses **one** device (not a device farm), read-only GitHub permissions, pinned source commits, no arbitrary shell commands, and temporary artifacts. Do not merge test requests indiscriminately because runners consume billable Actions minutes.

The AI is only a planner; a controller with limited GitHub rights authenticates and submits requests. The same JSON contract works for future local models. To extend capabilities, release `vq.worker.v2` without silently changing v1.

Run offline unit tests using `python3 -m unittest discover -s worker/tests -v`.
