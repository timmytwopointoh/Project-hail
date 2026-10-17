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

## October 17, 2026 — sword broadside inspection candidate

Review of immutable handoff artifact `12085917087` and actual Android
screenshots distinguishes intentional edge-on sword geometry from a
separate broadside framing/readability concern. The scoped Android-probe
camera candidate, conservative near-plane regression and rejected zoom
are documented in `docs/VEILFORGE_SWORD_CAMERA_REVIEW_LEDGER_20261017.md`.
This is a non-promoting, non-executing candidate; full emulator validation
and human artistic review remain required.
