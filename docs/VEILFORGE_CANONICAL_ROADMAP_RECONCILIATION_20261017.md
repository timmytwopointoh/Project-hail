# VEILFORGE / VQ branch ledger — canonical roadmap reconciliation (2026-10-17)

Branch: `feature/veilforge-canonical-roadmap-reconcile-20261017-h04`.
Parent: `17b5dd7b1b75b23038623ba4d03019a9e5aac34e`, factory run `39013219080`: 19/19 successful, 156 unit tests, 4 Android 15 roles, 154 frames, independent semantic/LOD gates. This entry describes the parent, **not** a passing run for this branch.

## Actual Android REVIEW evidence already inspected

Original immutable handoff artifact `12085917087` from run `38993296206`, source `85f634f58d0a5863186b22a90c1fd74292cc8c2b`, lists exactly five proposed REVIEW tasks. The original `ceremonial_sword` artifact `12086056909` contains 14 real angles: yaw 0/25 are thin edge-on views, while yaw 75/225 show broadside geometry. The minimum coverage `0.0006` does **not** prove missing mesh. Rejected candidate data remain unpromoted. No sword mesh change is authorized.

The actual `ancient_tree` framing issue was corrected earlier on isolated branch at source `27399138080f36cc133b85e927c0b5041a28f2a7`, run `38996754894`, by changing only its Android probe camera distance. Comparing original and corrected semantic screenshot masks gives minimum `0.0008 → 0.0014` (+75%) and maximum `0.0186 → 0.0290` (+55.9%). Both runs use 14 real views for this asset; warnings still require human review. This is measured visibility, not geometry quality or photorealism. The earlier camera correction is preserved unchanged here.

## One new bounded improvement: milestone reporting truthfulness

The project already contains **three different** maps:
- `VQ_ENGINE_QUALITY_PLAN.json`: canonical **34** quality milestones (not the legacy 24).
- `VQ_M34_EFFICIENCY_MAP.json`: **13** separate emulator/efficiency milestones.
- `ENGINE_MASTER_PLAN.json`: **24** older VF capability groups, which remain valid supplementary planning data.

Previously the factory emitted only the 24-group legacy report, potentially obscuring the canonical 34 and 13. A read-only, fail-closed reconciliation report now preserves all three original maps, validates counts, IDs, acceptance gates, status vocabularies, four emulators and 14 views, and emits `vq_canonical_milestone_tracks.json` and `.md` in the existing library-manager artifact. It never infers artistic approval, hardware performance, a status promotion, an automatic asset rewrite, or a merge. The original `roadmap.py` and its 24-group report remain unchanged.

The full factory, independent semantic/LOD review and four Android emulators must run on this **new** branch SHA before technical acceptance. Do not treat the older passing parent as proof that this new change passed. No game source, renderer, camera, geometry, QA threshold, static `queue_backlog.json` or dynamic REVIEW task is modified. Keep original screenshot and candidate artifacts immutable. Physical-phone performance and final human-artistic acceptance remain outstanding.
