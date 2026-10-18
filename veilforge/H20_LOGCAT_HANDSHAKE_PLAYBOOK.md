# H20 — bounded real Android logcat startup handshake

Observed on H19 run 39090364319: scene-world Android 15 emulator booted and installed the APK, then `LogcatStream.__enter__` failed after its one-time startup marker was never observed. Three other emulator roles passed. This is a **telemetry subscription race candidate**, not evidence that any particular asset silhouette failed. H19 run remains a rejected candidate, not a promoted baseline.

## Mechanism
`adb logcat` runs in a background process and a reader thread. An immediately following `adb shell log -t VEILFORGE_PROBE <unique nonce>` can succeed before the reader's live subscription begins. Waiting longer for that single lost event cannot help. Instead, emit the same unique nonce repeatedly on the actual Android device until the live reader observes it, or a bounded total deadline expires. Never synthesize log events, replay `logcat -d` as fresh frames, skip a camera, or approve screenshots on missing evidence.

## Verification
Synthetic deterministic tests: drop first device event then accept second real echo; lose all echoes and fail closed; inject `GL_ERROR` and fail immediately without retrying a fatal renderer error. CI acceptance: 18/18 full factory jobs, 4/4 independent Android 15 emulators, 154 accepted real views, unchanged origin/APK hashes, both independent semantic and LOD reviews. The startup fix itself does not certify visuals or hardware performance.

The original five next-iteration items in artifact 12085917087 remain review proposals separate from static `queue_backlog.json`. No automated asset rewriting, artistic approval, auto-merge or promotion.
