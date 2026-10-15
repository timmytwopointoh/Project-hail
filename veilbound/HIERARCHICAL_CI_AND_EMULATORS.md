# VEILBOUND: Director of Divisions and Parallel Emulator Farm

This infrastructure is proposed in draft PR #2. It changes the development
pipeline, not the game APK or gameplay code. The shared native build remains
offline-capable and does not depend on Gemini at runtime.

## Four organizational levels

```text
DIRECTOR (1: evidence, priorities, global task budget)
  ├─ GAME SYSTEMS DIVISION MANAGER
  │    ├─ Combat specialist manager ── ≤10 isolated coding tasks
  │    └─ Animation specialist manager ── ≤10 isolated coding tasks
  ├─ VISUAL ART DIVISION MANAGER
  │    ├─ Models specialist manager ── ≤10 isolated coding tasks
  │    └─ Materials specialist manager ── ≤10 isolated coding tasks
  └─ WORLD TOOLS DIVISION MANAGER
       ├─ Environment specialist manager ── ≤10 isolated coding tasks
       └─ Studio specialist manager ── ≤10 isolated coding tasks
                               Global cap: 50 jobs
```

The director creates a data plan for exactly the requested workers. Three
division managers **run in separate GitHub Actions jobs** and each independently
reconstructs and checks its part of that plan. Six specialist-manager jobs
check their parent division's approved artifact, then approve task ID, goal,
Java ownership and immutable slot ID for each individual worker.

Coding workers start only after their manager jobs succeed and their
specific role + slot + task match the specialist's approved artifact. Each
worker reads one immutable checkout, emits its own source patch and tests
into one uniquely named artifact, and never directly modifies or merges the
working game branch. Multiple proposals against a single Java file are
**alternatives** requiring explicit integration and fresh tests; they cannot
be automatically combined.

The manager hierarchy supports up to 50 coding task slots per cycle.
Model calls remain optional, require `GEMINI_API_KEY`, and can incur usage
charges. Manual worker matrix parallelism can be set to 2/4/8/12. The
automatic non-manual budget remains six slots and four concurrent model
workers if model auto-mode is explicitly enabled. Without opt-in Gemini,
only director/division/specialist validations run.

## Parallel Android emulator farm

Workflow: `.github/workflows/veilbound-parallel-emulators.yml`
(under GitHub Actions: **VEILBOUND - Parallel Android Emulator Farm**).

The emulator director selects **1, 2, 4 or 8 independent Android VMs**.
A separate build job constructs the real VEILBOUND APK **only once**.
GitHub Actions then distributes that exact, immutable APK to different
GitHub-hosted Ubuntu VMs. Each VM separately starts an Android SDK emulator
(API 33, 34 or 35 with a distinct Pixel hardware profile combination).

Every emulator independently:
- installs the real APK and verifies its package/signature and alignment;
- navigates real Model Atelier touch controls and world assets;
- explores, attacks, dodges and attempts target lock using ADB input;
- records PNG screenshots, recent logcat and OpenGL FPS/error metrics;
- emits a deterministic repair-task report with its own artifact name.

A final aggregation job requires **all selected emulators** to produce a
passing gameplay smoke result, sufficient real screenshots and a
`visual_quality_metrics.json`. Missing evidence fails the farm.

Default on its workflow-configuration push or when manually run without
changes: **2 emulators**. Optional manual maximum: **8 emulators running
in parallel**, subject to GitHub-hosted runner availability and minutes.
Emulator hardware is software/virtualized; these metrics are not proof of
FPS or thermal behavior on a physical Motorola phone.

Use small parallel batches for regular CI, a larger matrix before a release.
This farm is separate from the existing single-emulator native Android
workflow, which remains intact. No emulator runs need paid Gemini access,
and none has permission to merge source automatically.

## Where to see results

- [VEILBOUND draft automation PR](https://github.com/timmytwopointoh/Project-hail/pull/2)
- GitHub Actions: **VEILBOUND - Master AI Worker Manager** for the 10-manager hierarchy
- GitHub Actions: **VEILBOUND - Parallel Android Emulator Farm** for
  independent platform tests and the aggregate verification report
- GitHub Actions: **VEILBOUND - Parallel Worker QA** for deterministic unit tests

A passing manager unit test validates scheduling and handoffs, **not**
that model-authored gameplay improvements have been merged. A passing
emulator job validates Android smoke automation, **not photorealistic
assets or physical-device performance**.
