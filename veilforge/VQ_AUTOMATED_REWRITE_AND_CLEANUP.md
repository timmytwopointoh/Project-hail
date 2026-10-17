# VEILFORGE automated rewrite loop: bounded, proven and reversible

## Engineering strategy

Automate *candidate generation*, not approval or uncontrolled rewriting.
This extension consumes `veilforge-android-next-iteration-tasks`,
which is only emitted when all four actual Android 15 emulator roles,
154 hashed real screenshots, the independent LOD reviewer and semantic
diagnostic reviewer have passed.

A newly isolated job `bounded-auto-model-candidates` downloads exactly the
source sword production artifact and the verified visual repair backlog;
there is no extra Android VM, duplicate APK build or secondary asset generation.
The task's pinned source commit must match the current GitHub workflow.
No screenshot captions, model IDs or external text can execute arbitrary code.

## Phase 1: controlled source-geometry rewrite

`vq_auto_model_rewriter.py` currently allows exactly one cautious operation:
for a `ceremonial_sword` `view_visibility` warning, produce a separate
`ceremonial_sword_candidate.obj` with <=8% gain on the thinner horizontal
axis and vertex movement capped at 0.8% of the model's largest dimension.
Other objects, including human faces, hands, feet and trees, are only
queued for inspection. A tiny camera silhouette is *not* automatically
evidence a mesh needs deformation.

The original OBJ + manifest hashes are validated and original bytes are
left intact. Positive scaling preserves face winding, 3D connectivity,
UVs and material groups; referenced normals get inverse-transpose
adjustment. The candidate's actual OBJ and source are both rendered from
14 angles using the existing VQ inspection system and fail if topology or
validity is lost. The candidate is stored as a download-only unapproved
artifact. **This is a real vertex rewrite**, not an image-only edit.

## Mandatory acceptance boundary

The present workflow does **not** automatically insert the candidate into
the Android APK. Full renderer import, real Android screenshots, independent
semantic/LOD comparison and reference-artistic acceptance must occur in a
separate reviewed experiment before anyone prefers the candidate to the
baseline. If no eligible actual defect exists, emit an empty candidate report
and do nothing.

## Next iterations / missing capabilities

1. Compare candidate-vs-baseline **same-angle Android 15** screenshots with
   accurate camera metadata, SHA and measured coverage; reject regressions.
2. Add genuine per-region sculpt, topology-preserving smoothing and coherent
   UV/normal baking as *isolated candidates* when the actual defect warrants
   them; never scale a face or character without anatomical reference checks.
3. Feed verified improvements to a manager-driven retry budget (max 1
   candidate per asset/run initially). Carry source SHA, report and rejection
   reasons; never let a code loop fork endless emulator runs.
4. Track smoke-test time, uploaded bytes and CPU cost across comparable
   runs; maintain four emulators only when changed renderer/assets warrant
   it. Share a single APK and evidence downloads.
5. Cleanup must be evidence-based: only remove confirmed dead variables or
   duplicate generated intermediate files; preserve externally callable
   modules, SDK entrypoints and experimental branches.

## Run

```bash
python3 -m unittest discover -s veilforge/tests -v
python3 veilforge/vq_auto_model_rewriter.py \
  --tasks inspection_output/candidate-feedback/next_iteration_tasks.json \
  --source-dir inspection_output/candidate-source \
  --out inspection_output/auto-model-candidates \
  --source-sha <full-github-commit-sha>
```

**Technical pass does not establish photorealism, visual resemblance or
physical-device FPS.** No game or original source model is modified.
