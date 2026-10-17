# VEILFORGE emulator loop — verified and auditable next-iteration handoff

The asset factory CI workflow runs **source-mesh workers → assembled glTF →
single shared APK → four Android 15 emulators → 154 real screenshot checks →
independent LOD and semantic reviewers**.

The Android gate is *fail-closed*: missing source hashes, APK digests, required
devices/angles, graphics/material logs or real screenshot evidence fails the
CI check. An Android-emulator pass is NOT target-phone performance or an
artist's reference-likeness signoff.

## Finding from October 16, 2026

GitHub Actions run **38989416581** successfully completed **18/18 jobs**,
**133 unit tests** and **154 screenshots** at pinned commit
`2b37d42dc5ec1d1e64ae8fb8a936169bb6c07d8c`. The Android review
reported four devices and no missing/blank evidence. The *separate* semantic
review, however, recorded six nonblocking visibility warnings (human,
armored human, sword, cart and two trees); minimum silhouette coverage for
a few cameras was small. LOD review of the two ancient-gate variants found
mean silhouette IoU **0.4571** and min **0.0478**. These are quantitative
diagnostics, not evidence of an artistic defect on their own.

The old factory recorded `semantic_repair_queue.json`, but that information
was not reliably presented to the *next* model iteration. The base
`queue_backlog.json` has static allowlisted `pending` entries and no
automatic connection to those warnings. Passing Android QA **did not close
a self-correcting edit/retest loop**, contrary to that possible impression.

## This change — durable, non-executing defect handoff

`vq_android_repair_handoff.py` validates all four expected roles and eleven
assets, 14 camera views for each asset, a successful semantic report,
provenance, and that each warning appears in the reviewer's original repair
queue. It then produces:

- `next_iteration_tasks.json`: stable scoped task IDs, source commit,
  GitHub Actions run ID, role-specific screenshot-artifact names, minimum
  foreground coverage and suggested inspection action.
- `next_iteration_tasks.md`: clear next-iteration summary for the next
  VQ specialist.
- CI artifact `veilforge-android-next-iteration-tasks`: kept independently
  from the existing semantic/LOD/Android evidence artifacts.

Warnings remain **review tasks**, not permission to rewrite meshes. CI still
runs the same four emulators and the same full 154-view camera set; no
additional emulator instance or expensive duplicate screenshot download is
introduced. The new handoff runs locally within the already-installed
Pillow/reviewer job and preserves every original report artifact.

## How to use the loop without confusing its stages

1. Open the most recent passing **VEILFORGE - Universal Game Asset Factory**
   Actions run on the intended engine branch.
2. Download `veilforge-android-next-iteration-tasks` and the appropriate
   `veilforge-android-<role>` actual screenshot artifact.
3. Examine the flagged camera views, including whether a tiny silhouette is
   intentional (e.g. thin sword edge-on) or actual culling/camera clipping.
4. Create a versioned, isolated **model-specific** repair branch only for
   confirmed defects. Keep source SHA and before/after views.
5. Retest source geometry, glTF, same 14 camera views, and the complete
   Android device matrix where changed assets/renderer require it.
6. Accept only verified and reference-reviewed improvements; do not
   automatically merge, overwrite originals or mark models photorealistic.

### Offline/standalone review replay

```bash
python3 veilforge/vq_android_repair_handoff.py \
  --semantic build/semantic-review/semantic_visual_review.json \
  --out build/next-iteration-review \
  --source-sha <40-character-commit-sha> \
  --run-id <GitHub-Actions-run-number>
```

This command does **not** run Blender, rewrite geometry or dispatch another
costly emulator farm. The separate scheduled development loop remains
responsible for reading findings and implementing scoped changes; human
aesthetic acceptance remains required. This is an honest evidence-backed
feedback handoff, not autonomous artistic self-perfection.

The source modules remain under `veilforge/`, with a versioned recovery ZIP
and instructions in ChatGPT Library `/App creation/VEILFORGE - VQ Engine`.

## October 17, 2026 — measured stale camera screenshots

At verified baseline commit `85f634f58d0a5863186b22a90c1fd74292cc8c2b`,
run `38993296206` had 154 actual captures on four Android 15 emulators.
Reading all four screenshot artifacts revealed **28 byte-identical adjacent
captures out of 143 camera transitions**, across 11 assets. For example,
`ceremonial_sword` yaw 0/pitch 15 and yaw 25/pitch 25 were identical,
as were `ancient_tree` yaw 0/pitch 15 and yaw 25/pitch 25.
This is a genuine **presented-camera-frame evidence defect**: the existing
logcat `FRAME_OK` only certifies a draw callback, not that the new buffer
has been presented by the Android compositor. It is not evidence that
an edge-on sword or small tree silhouette is geometrically defective.

Isolated candidate branch `feature/veilforge-stale-frame-evidence-20261017`
retries a visually unchanged adjacent camera capture (threshold 0.0006
at 240x135 pixels, RGB difference >=12), preserves each rejected real
image as `*_rejected_duplicate_<attempt>.png`, and fails closed after
the existing eight attempts. The independent Android reviewer also
rejects adjacent identical screenshot SHA-256 values. Regression tests
cover rejection, evidence retention and fail-closed behavior.

The 28 original duplicates remain preserved in immutable baseline
artifacts: nature-mobile `12085179609`, props `12086056909`,
characters `12086640383`, scene-world `12085664797`.
Acceptance requires a fresh 4-emulator 154-frame run with **0/143**
adjacent duplicates and unchanged semantic/LOD and source-hash gates.
This fix does not edit models, weaken semantic heuristics, certify
photorealism or imply real-phone FPS or human artistic acceptance.

## H14 independent cross-asset Android screenshot check (2026-10-17)

A previously successful Android run 39071499467 had a verified stale
frame: the last treasure-chest PNG was byte-identical to the first sword
PNG. The capture path now retries that situation, but the independent
reviewer had only checked repeated views within a single asset.

H14 adds a role-scoped, cross-asset SHA-256 collision check to
android_review.py. It reports the asset names and yaw/pitch angles.
New synthetic tests verify that 154 distinct frames pass and a copied
chest-to-sword frame fails. No models, cameras, games or acceptance
thresholds change.

Before H14, the latest verified run 39071961941 passed 18 jobs, four
Android 15 emulators and 154 frames. Its four screenshot manifests had
zero cross-asset accepted collisions. Full H14 emulator and independent
semantic/LOD verification is pending. Preserve rejected evidence.
These are integrity gates, not artistic approval or real-phone benchmarks.

### H14 independent full Android verification (2026-10-17)

Executable source commit 44bff23aa7f7bc9874a97d147868b1b0c4752ed9
completed run 39072830533: 18/18 jobs, 148 passing tests,
8 catalog workers, four Android 15 emulators, 154 actual SHA-verified
frames and one identical hash-verified GLES APK. The new independent
cross-asset SHA check passed with zero collisions; zero adjacent accepted
duplicates. All 49 rejected duplicate attempts remain archived in the
emulator artifacts. Structural and semantic gates passed; five semantic
warnings remain REVIEW proposals. Independent LOD passed, silhouette
IoU mean 0.5944, min 0.4269. No camera or model edits were made in H14.
The sword 14-view silhouette coverage remains min 0.00152, mean
0.010929, max 0.02542, as in H13. This is a validated evidence
integrity correction, not a realism, PBR, phone-FPS or artistic approval.
Preserve the rejected earlier green-run evidence. Full source and
verification playbook are pinned in the VEILFORGE VQ Engine Library.
This post-validation documentation-only commit does not change tested
executable code and must not be mistaken for a new emulator-tested SHA.
