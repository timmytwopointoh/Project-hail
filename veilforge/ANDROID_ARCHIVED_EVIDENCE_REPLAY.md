# VEILFORGE / VQ — immutable Android REVIEW-task artifact replay

Date: 2026-10-17. This is a **read-only QA provenance improvement**, not an asset/model/renderer correction. It does not create new models, edit games, merge branches, or grant artistic approval.

## Pinned real Android evidence

- Source `de4b059aa8a9dbc665518f253be55d8ba345c7d6`, factory run `39054441812` (18/18 jobs, 144 unit tests, 4 Android 15 emulators, 154 accepted PNGs, independent semantic/LOD PASS).
- REVIEW handoff artifact `12109107468`, 4 tasks, each with 14 SHA256-linked yaw/pitch screenshots.
- Screenshot ZIP artifact IDs: scene-world `12108609571`, nature-mobile `12108951543`, props-equipment `12109266791`, characters `12109142133`.
- Independent read-only replay of all four ZIPs: **154/154 accepted PNG bytes match manifest SHA256**, **154 distinct accepted hashes**, **56/56 REVIEW-task angle hashes and independent 192×192 silhouette coverages reproduced**. All roles report one shared APK SHA256 `82845abc9e2ab91ef17c7f1511ec3311713f2b80f31169fccca6b38207db9a4e`.
- ZIP SHA256s: characters `19381ed67c681d5b53740d1a054d48c66a697bf22cdadaa289f88d971c890150`; nature-mobile `e3f02bbdc7bb598e813ae5997c7f09fdf5c623006601a32d9fd98b5eecff4737`; props-equipment `70420089cc166af73cd1334b85595ab8399c3e06d279d8bc855e44274bae156f`; scene-world `fb6eb3913509b82870b8a5d9694361341ec60793e4585de2b1618228d6a33d67`.

## Reusable technique

`veilforge/vq_android_artifact_replay.py` accepts the exact `next_iteration_tasks.json` plus **all four** downloaded original Android screenshot ZIPs. It independently checks source/run provenance, 11-asset allowlists, four Android 15 roles, shared APK SHA, 14 ordered camera labels per asset, 154 unique accepted PNG bytes, full manifest hashes, 56 REVIEW-task image hashes and recomputed foreground coverage, min/max consistency, and explicit no-auto-edit/no-artistic-signoff status. The companion `veilforge/tests/test_vq_android_artifact_replay.py` has three fail-closed tests covering clean replay, tampered screenshot references/coverage, missing roles, and unauthorized automatic promotion. Local tests: 3/3 PASS. Real artifact replay: PASS.

```bash
python3 veilforge/vq_android_artifact_replay.py \
  --tasks next_iteration_tasks.json \
  --role-zip scene-world=scene-world.zip \
  --role-zip nature-mobile=nature-mobile.zip \
  --role-zip props-equipment=props-equipment.zip \
  --role-zip characters=characters.zip \
  --out replay_report.json
```

The original `veilforge/queue_backlog.json` remains static and separate from the dynamic REVIEW handoff. A sword yaw0 edge-on silhouette is **intentional**, not a geometry defect. In an earlier isolated real-Android camera test (source `291223bfcc5b39e5a11c7f2e0558febbb235c41a`, run `39020966378`), sword broadside yaw75/pitch15 coverage increased `0.00301 → 0.00396`, but this replay changes **no camera code** and cannot claim that change on its own branch. An isolated renderer correction and full four-emulator retest remain separate work.

## Boundaries

Passing SHA and silhouette replay certifies **evidence consistency only**, not accurate anatomy, rigging, physically calibrated PBR, real-phone GPU performance, visual likeness, photorealism, or human artistic acceptance. Rejected stale/modal PNGs stay preserved in their original emulator artifacts. The canonical 34 capability and 13 efficiency milestone maps remain unchanged.