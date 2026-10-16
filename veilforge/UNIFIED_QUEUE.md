# VEYLQUORIN (VQ) M27 — Shared ten-slot development and emulator queue

**Boundary:** These are new, optional VQ infrastructure files (legacy VEILFORGE paths retained for running CI). Existing
VEILBOUND game source, Android visual QA, local AI coding worker manager, and
the existing VEILFORGE asset factory are preserved. No game assets are
silently promoted or merged.

## Actual resource ceiling

The unified dispatch workflow has **one** task matrix with an immutable
ten-job concurrency ceiling. GitHub Actions max-parallel=10 applies to that
matrix, not the whole GitHub account; other independent workflows count
against account runner limits. Each active matrix job is a separate
GitHub-hosted Ubuntu runner. Emulator jobs start one Android VM on their
runner. The script refuses budgets above 10 or emulators above 4.
Resource availability may queue jobs.

With the default backlog invoked at 10 jobs / 4 emulators, the planner
selects 4 emulator tests and 6 asset workers. The remaining 2 asset jobs
are deferred into the next_queue report. No idle placeholder jobs are made.

The separate VEILBOUND manager still has 50 *logical* AI coding slots and
a configurable maximum of 12 concurrent local model jobs. The new queue
does not secretly start those unrelated workflows or raise their limits.

## Pipeline

1. Push or manually run **VEILFORGE - Unified 10-Slot Queue**. Pushes on
   its feature branch run only planner unit tests; only workflow_dispatch
   runs expensive emulator/worker jobs.
2. Validate the queue, existing VEILFORGE unit tests and immutable matrix.
3. If any emulator is selected, generate a baseline recipe scene and
   human/armor assets into one Android test APK before starting the matrix.
4. Launch ONE matrix with max-parallel=10. Asset workers independently
   create OBJ, glTF, textures, QA manifest, topology and actual previews.
   Emulator workers share the identical SHA256-checked Android APK and
   capture fourteen-view screenshots with the existing GLES tooling.
5. The queue reviewer downloads each exact artifact and verifies content.
   If all four Android roles ran, it additionally calls the existing
   strict four-role Android reviewer. Missing evidence fails the workflow.
6. Publish the technical report and deferred/repair queue. Green technical
   checks do NOT constitute artistic approval, merge or game promotion.

The simultaneous asset tasks recreate the *same deterministic catalog
recipes* packaged in the shared APK. They do NOT inject unreviewed patches
into the test APK. Candidate-to-APK integration needs a future independent
review/rebuild/QA stage.

## Run on demand

On GitHub Actions select the branch, then the queue workflow and **Run
workflow**. Input job_budget can be 2, 4, 6, 8, 10; emulator_limit can be
0, 1, 2, 3, 4. Default is 10 total jobs, of which up to 4 are emulators.

Only existing catalog asset IDs and the four original Android specialist
roles are executable. Backlog text is never interpreted as shell commands.

Pending tasks are repeated until reviewers edit queue_backlog.json to
mark them done or to reprioritize. The report contains selected tasks,
review-needed completions, failures and deferred work. The workflow has
read-only repo access and does not mutate sources or auto-merge.

## Next measured extension milestones

- Reference-aware silhouette and material appearance comparisons
- UV island layout, textured PBR and accurate shadow benchmark evidence
- High-poly sculpt layers, topology, hair and cloth simulation
- LOD0–LOD3 regression and real-device performance reports
- Rig/skin/facial deformation and pose coverage
- Controlled local Qwen coding jobs with strict CPU/RAM/time budgets
- Reviewed candidate manifest -> test APK rebuild -> emulator QA ->
  human approval -> explicit import into game testing grounds

These are future milestones, not claims of currently working features.
See ENGINE_MASTER_PLAN.json for acceptance gates.
