> **Latest architecture:** See [HIERARCHICAL_CI_AND_EMULATORS.md](HIERARCHICAL_CI_AND_EMULATORS.md) for the director → 3 division managers → 6 specialist managers → 50 worker hierarchy and optional 1/2/4/8-emulator farm.

# VEILBOUND — Hierarchical AI Teams and Concurrent Development

This infrastructure lives on `feature/veilbound-parallel-ai-qa` and is
submitted through draft PR #2. It is additive to the native Android game.
No game code, user controls, Android SDK or Model Atelier is replaced.

## Management hierarchy (verified in GitHub Actions)

The director creates only the division and specialist manager jobs needed by the queue. Up to **three division managers** independently review the director's plan; up to **six specialist managers** receive a division-approved assignment and each controls no more than **ten children**. Workers verify their exact approved team, role, task ID and slot before Gemini is called. Every level is a separate GitHub Actions job:

```text
Director / QA backlog priority
  ├─ Game Systems division → Combat manager + Animation manager
  ├─ Visual Art division   → Models manager + Materials manager
  └─ World Tools division  → Environment manager + Studio manager
                 ↓
    Scoped patch + trusted Java tests
                 ↓
    Human-reviewed promotion to draft PR
                 ↓
    Full Android emulator / physical device tests before merge
```

The hierarchy is *bounded, depth three* (director -> division manager -> specialist manager -> worker).
It can vary the number of **active managers** and workers dynamically, but
cannot create unrestricted recursive managers, bypass allowed Java file ownership, or
run more than the selected 50-worker ceiling.

## Opt-in capacity: 50 distinct workers

The repository includes **50 concrete improvement tasks** in
`veilbound/worker_backlog.json`: 9 combat, 8 animation, 8 models,
8 materials, 9 world, and 8 studio tasks. Selecting a smaller budget runs
only the highest-ranked subset. Selecting **50** allocates all fifty task
slots (provided no higher-priority QA evidence replaces assignments).

The director distributes assignments fairly across six specialties, three
division-manager jobs and six specialist-manager jobs, each with at most ten children.
Workers that share a Java specialty are **alternative independent proposals**:
they do not concurrently edit one shared branch. Each has an immutable
checkout, unique `w001` through `w050` slot ID, its own artifact and
Java test results. A reviewer can promote only a specific slot to a
separate **draft PR**, never mass-merge all proposals.

GitHub Actions' matrix supports 256 jobs, but actual runner concurrency
depends on account quotas. The manual control allows `max_workers`
6/12/24/50 and `max_parallel` 2/4/8/12. **The default remains six
task slots and four simultaneous code jobs.** Gemini usage can incur charges
and per-project request/token limits: choose a small trial first. An
automatically triggered manager run uses the safe default of six workers.

## Gemini integration

The `gemini_client.py` module implements Google's `generateContent` HTTP
API with native JSON-schema patch outputs, prompt/image size limits,
short retry/backoff for temporary failures, explicit HTTP error statuses,
and per-worker model/token usage metadata. Real code workers remain gated
by the `GEMINI_API_KEY` GitHub Actions secret.

The default model is `gemini-3.8-flash`, configurable through the
`GEMINI_MODEL` Actions repository variable. Run the *manual*
**VEILBOUND - Gemini Connection Check** workflow after configuring the key.
It checks a tiny, non-source health prompt, not game code, to verify Gemini
credentials and model access. This call can incur model usage charges.

Model source edits are still **untrusted code**. They are isolated in
temporary copies for Java validation, promoted only after explicit review,
and never automatically merged into the game. The PR promoter also
verifies that the reviewed text patch exactly matches replacement files.


## Execution layers

1. **Master AI Worker Manager** is a real GitHub Actions planner. Every
   cycle assigns an independently scoped task matrix from
   `veilbound/worker_backlog.json` and, where supplied, the actual Android
   emulator `task_plan.json`. It dynamically creates up to **three independent team managers and fifty
   isolated code-proposal jobs**, limited by a selected budget of 6, 12, 24, or 50.
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
**Run workflow**, select 6/12/24/50 max workers, and optionally enter the run ID
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

Gemini runs can incur model API costs. There is a cap of 50 proposed tasks per manager cycle and 18 child tasks
per team. Only 2, 4, 8, or 12 model jobs run at once, based on the explicitly
selected concurrency budget; **no recursive jobs or automatic merges**.

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
