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

## Verified complete CI result — no change to tested source

- Tested code commit: `344478f77c2d24a8b76e7040afc20895a10d988f`; complete factory run `39015926327`: **19/19 jobs successful** and **161 unit tests passed**.
- Manager artifact `12094951285` contains both `vq_canonical_milestone_tracks.json` and `.md`, with exactly 34 canonical quality, 13 M34 efficiency and 24 distinct legacy groups. Quality statuses: 1 in progress, 16 partial, 17 planned. Efficiency: 4 verified, 1 verified_prior, 2 partial, 6 planned. None is automatically promoted.
- Four Android 15 emulator roles completed. Independent structural gate artifact `12095251008`: zero problems. Independent semantic artifact `12095340522`: 11 assets, 154 genuine frames, zero technical problems, **six unresolved visual REVIEW warnings**. Independent LOD artifact `12094608551`: 14 paired samples, mean silhouette IoU 0.5944 and minimum 0.4269 (heuristics only). Handoff artifact `12095330595`: all 154 frame hashes verified; six proposals, no automatic model rewrite, no artistic signoff.
- This post-run ledger update is **documentation only**. The code SHA above is the tested source; a later documentation-only branch head is not a new tested renderer or a new Android run. The original 5-task handoff and separate static backlog remain unmodified.

Final release and human artistic acceptance remain **not achieved**; physical-phone FPS/GPU budgets remain unverified.
