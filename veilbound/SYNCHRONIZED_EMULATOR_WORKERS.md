# VEILBOUND M14 — Synchronized emulator workers

**Primary purpose:** test the latest character/game development *version* on
multiple independent Android 15 emulators at the same time. This is the
standard worker feedback loop, **not primarily an Android-version
compatibility sweep**.

## Identical code, binary and OS for the worker loop

For every GitHub Actions farm run:

1. A single, immutable git commit of the current M14 development branch is
   checked out by the director, APK builder, every emulator and auditor.
2. The APK is compiled **once**, and its SHA256 is recorded. Every worker
   downloads this *same* APK and independently proves the bytes match.
3. By default every Android VM boots **API 35 (Android 15)**, matching the
   user's Motorola Moto G (2025) target OS. The emulators use independently
   hosted Pixel 6/7/4/5 profiles, all set to 1604×720 landscape and 263 dpi
   by the game test script.
4. Four distinct runner jobs launch concurrently as capacity permits.
   Each executes the same full Studio, combat, camera, environment and GL
   screenshot/touch acceptance path. There is no cross-device ADB or port
   interference.
5. When four successes or failures finish, a strict auditor checks their
   Android version, APK digest, original git SHA, real PNGs, visual QA and
   machine-produced repair plans. Any missing or P0/P1-blocked result fails
   the aggregate.
6. The artifact `worker_repair_queue.json` groups findings by specialist,
   lists the affected emulator jobs, and retains the exact source commit and
   APK fingerprint. Model workers can use those verified artifacts to
   improve code **for that exact version**; they must not mix evidence from
   different game commits.
7. The game remains installed and tested locally inside the GitHub VMs; no
   APK contains the AI model or GitHub dependency.

## Configuration

The [GitHub Actions parallel emulator farm](https://github.com/timmytwopointoh/Project-hail/actions/workflows/veilbound-parallel-emulators.yml)
supports these options when selecting the current feature branch
`feature/veilbound-m14-synchronized-emulator-workers`:

| Setting | Default | Other choices |
|---|---|---|
| `emulator_mode` | `synchronized` | `compatibility` (older Android 13/14/15 release sweep) |
| `emulator_instances` | `4` | `1`, `2`, `8` |

In primary synchronized mode, **every single job uses Android 15**.
With 8, four phone profiles run twice on separate VMs, making it useful to
detect intermittent AI-generated visual/interaction regressions.

After this farm is reviewed and integrated into the **M14 game branch**,
edits to the game source or emulator harness automatically queue a new
four-device test of that new M14 revision. Each workflow run pins its
own commit, so later worker changes cannot alter an in-flight APK.
GitHub-hosted runner capacity may queue some jobs; the system does
not promise literal same-millisecond start times.

Compatibility mode remains useful as a manual optional validation step,
but is not part of default worker iteration. Four independent Android
15 emulators still **do not simulate the physical Moto G's Mali GPU**
or prove actual phone frame rate.

## Validation records

- [Prior 2/2 parallel version sweep](https://github.com/timmytwopointoh/Project-hail/actions/runs/38834534661)
- [Prior 4/4 parallel version sweep](https://github.com/timmytwopointoh/Project-hail/actions/runs/38835395387)
- The newer M14 same-version, all-Android-15 run is recorded in the
  Actions workflow history; verify its final aggregate before merging.
