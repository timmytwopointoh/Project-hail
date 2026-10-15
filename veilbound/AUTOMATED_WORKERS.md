# VEILBOUND — Master Worker Manager and Concurrent Development

This infrastructure lives on `feature/veilbound-parallel-ai-qa` and is
submitted through draft PR #2. It is additive to the native Android game.
No game code, user controls, Android SDK or Model Atelier is replaced.

## Execution layers

1. **Master AI Worker Manager** is a real GitHub Actions planner. Every
   cycle assigns an independently scoped task matrix from
   `veilbound/worker_backlog.json` and, where supplied, the actual Android
   emulator `task_plan.json`. It dynamically creates up to **six independent
   concurrent code-proposal jobs**, limited by a selected budget of 2, 4 or 6.
   No two concurrent roles own the same source file.
2. **Parallel Worker QA** runs existing deterministic Java combat and
   geometry checks plus manifest/source integrity and management unit tests.
3. **Native Android QA** installs and plays the native APK through the Android
   15 emulator, screenshots real game scenes and Model Atelier assets,
   measures GL/FPS proxy metrics and generates a prioritized repair queue.
   The QA coordinator distinguishes real failures from software-GPU
   warnings. Infra-only edits no longer trigger a costly full emulator run.
4. **Independent Vision AI** can separately inspect selected Android emulator
   screenshots after a completed emulator run. This workflow only runs via
   automatic `workflow_run` after its configuration is present on the
   default branch, or via its manual run-ID workflow.
5. **AI coding workers** are OPTIONAL Gemini-backed proposal generators.
   Each receives a distinct allowed set of Java files, source text and a
   goal from the manager. They create up to three exact-match substitutions,
   rebuild and run existing trusted pure Java tests on temporary files,
   and upload a patch + JSON result for review. They do not push code,
   execute suggested shell scripts or bypass the native Android QA gate.

## Worker ownership

| Specialist | Allowed Java source | Roadmap focus |
| --- | --- | --- |
| combat | WorldState | Objective cap, target lock, RPG rules |
| animation | CombatMotion, CharacterRig | Real swing arc, pose/attack/dodge timing |
| models | CinematicArtKit, DetailArtKit, ObjMeshLoader | Sculpted silhouettes, detail |
| materials | ArtKit, MaterialTextures, SurfaceAtlas | Steel, leather, texture quality |
| world | EnvironmentKit | Ruins, flagstone, natural variation |
| studio | ModelStudio | Asset cycling and actual orbit/camera behavior |

The critical native `ValeRenderer.java`, Android HUD, APK identity and CI
workflows are **read-only to AI workers** until explicit dedicated test
coverage and controlled review is available. QA, performance and renderer
findings are retained as review tasks but never dispatched as arbitrary
privileged code-writing jobs.

## Run the manager

Open GitHub Actions → **VEILBOUND - Master AI Worker Manager** →
**Run workflow**, select 2/4/6 max workers, and optionally enter the run ID
of a completed native emulator test to prioritize its measured findings.

The planner produces `assignment_plan.json` and a GitHub job summary.
If the `GEMINI_API_KEY` secret is not configured, the model workers report
`skipped_no_gemini_key`; no AI model work has occurred.

To activate Gemini workers:
- Create a Google Gemini API key and review quota, pricing and data policy.
- In repository **Settings → Secrets and variables → Actions**, save a
  repository *secret* named `GEMINI_API_KEY`. Never paste it into chat.
- Optionally set `GEMINI_MODEL` as a repository *variable*.
- Use manual workflow dispatch to run actual Gemini jobs. For autonomous
  dispatches after pushes or successful emulator runs, explicitly create
  the repository variable `ENABLE_AUTO_AI_WORKERS=true`. Otherwise push
  events only run the master planner.
- Enable the workflow on GitHub's default branch for `workflow_run`
  triggering, which requires reviewing and merging the implementation.
  This branch's draft PR does not itself activate default-branch triggers.

Gemini runs can incur model API costs. There is a cap of six simultaneous
proposals in one manager run and one worker per role; **no automatic
recursive job creation, unmanaged loops or automatic merges**.

## Validation / approval

- Inspect GitHub Actions' separate manager and coder artifacts. A green
  workflow with `skipped_no_gemini_key` is **not** an AI coding success.
- Only `proposed_change_passed_java_tests` proposals should be considered
  for a controlled code review.
- A developer reviews the patch, integrates it through its own branch/PR,
  and runs full native Android/emulator QA on that exact commit.
- Physical Motorola G 2025 GPU FPS and thermal testing cannot be inferred
  from a software emulator. Visual screenshots also cannot prove that
  animations are production-quality.
- A generated patch is untrusted Java. Coding jobs have read-only repo
  permissions, disabled checkout credential persistence, and remove the
  AI API key from subprocess environments before compiling/running proposals.

## Useful GitHub Actions views

- **VEILBOUND - Master AI Worker Manager**: dynamically chosen assignments.
- **VEILBOUND - Parallel Worker QA**: fast regressions and worker scope tests.
- **VEILBOUND - Native 3D Android RPG**: playable Android screenshots and APK.
- **VEILBOUND - Independent Vision AI**: optional second-model visual critique.

Future controlled extensions: reviewed branch-per-worker promotion,
required-status-check merge gates, historical screenshots with masking and
perceptual-diff thresholds, budget/thermal benchmarks from real devices,
and tracked issue deduplication.
