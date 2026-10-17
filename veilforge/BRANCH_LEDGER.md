# VEILFORGE branch ledger

2026-10-17 candidate: feature/veilforge-stale-frame-evidence-20261017

Base SHA: 85f634f58d0a5863186b22a90c1fd74292cc8c2b
Baseline run: 38993296206 (18/18 jobs; 138 tests; 4 emulators; 154 frames).
Observed: 28 of 143 adjacent camera transitions returned identical PNG SHA-256, despite distinct yaw and pitch.
Evidence artifact IDs: 12085179609, 12086056909, 12086640383, 12085664797.
Scope: reject and preserve stale camera captures, add independent hash review and regression tests.
Validation: PENDING full Android matrix. Require 0/143 duplicates, all original QA checks green.
No model or game promotion; no artistic or physical-phone performance signoff.

2026-10-17 isolated candidate: feature/veilforge-tree-frustum-fit-20261017-h12
Parent SHA: 43ea85d29e345379aec58c0960316435f5c3ad8c (completed run 39061003603, 18/18 jobs).
Origin handoff: run 38993296206, artifact 12085917087, task review-ancient_tree-view_visibility.
Freshest before artifact: run 39061003603, nature-mobile 12111113964.
Visual inspection: two real trees remain visible at all 14 angles, but both are
small due to wide multi-instance QA framing; NOT an edge-on missing-geometry defect.
Before: semantic coverage min 0.00079, max 0.01858, mean 0.00875.
Correction: QA-only ancient_tree frustumScale=0.75, unchanged geometry/instances/
other cameras, predicted 14-angle maximum projected |NDC y| 0.805 and
|NDC x| 0.403; minimum near depth >11.6 (2-unit near plane).
After: PENDING real Android 15 four-emulator run + independent LOD/semantic review.
Reject candidate if any clipping, loss of angles, provenance mismatch, or QA failure.
Dynamic handoff tasks remain REVIEW proposals; queue_backlog.json is separate.
Never auto-promote, auto-merge, or assert phone FPS, realism or artistic approval.

2026-10-17 independent verification of H12 (no merge/promotion):
Source SHA: 350151ad86264b26ac5980babe870872d0999e61
Run 39067049952: 18/18 jobs passed, 4 Android 15 emulators, 154 final frames,
8 catalog workers, independent LOD and semantic gates passed.
Actual ancient_tree 14-view screenshot mask (pre-H12 run 39061003603 vs H12):
min 0.000787 -> 0.001980; max 0.018582 -> 0.034180;
mean 0.008752 -> 0.016030. The two tree instances remain visible.
The visibility heuristic warning remains, so this is a measured inspection
framing improvement, NOT resolved artistic quality or physical-phone signoff.
Nature artifact 12113746679; next-iteration task artifact 12113862187.
Rejected capture attempts are preserved in emulator artifacts.

2026-10-17 isolated candidate: feature/veilforge-sword-frustum-fit-20261017-h13
Parent SHA: 350151ad86264b26ac5980babe870872d0999e61 (run 39067049952).
Origin task: 38993296206 / 12085917087 review-ceremonial_sword-view_visibility.
Before: run 39067049952, props-equipment artifact 12114185198,
14 accepted real Pixel 5 angles, source SHA and APK SHA in screenshot manifest.
Semantic mask coverage min 0.000624, max 0.010390, mean 0.004420.
Edge-on yaw 0 and 25 are intentional narrow blade silhouettes; broadside
yaw 225 and 250 still occupy little image area, a QA camera framing concern.
Correction: ONLY ceremonial_sword Android QA frustumScale 1.0 -> 0.65.
Tree stays 0.75, all other filters 1.0; geometry, materials, orbit,
emulators, tests, gates and all games unchanged. Conservative pinned glTF
bounding-corner 14-angle estimate max |NDC y| 0.881, max |NDC x| 0.144,
minimum forward depth 2.644 (near 2.0). Reject 0.55 (clipping risk).
After: PENDING full four-emulator and independent semantic/LOD validation.
Require measured mean coverage gain, all 14 frames, no clipping, no source
SHA mismatch or stale-frame acceptance. Retain any rejected evidence.
No automatic model rewrite, promotion, merge, or human-artistic signoff.

2026-10-17 H13 fail-closed follow-up (same sword-camera candidate):
Run 39070812414 attempt 1 failed props-equipment after 4 sword angles;
attempt 2 failed props-equipment after 3 sword angles. Three other Android
roles passed; final Android gate rejected 3/4 roles and 112/154 frames;
independent semantic/LOD job correctly skipped. Preserve failed screenshot
artifacts 12115192686 and 12114428965. Real yaw75 sword screenshot was
visible; old sky probe (.50,.08) struck legitimate enlarged blade tip,
RGB (28,31,33) vs (17,21,29), diff 11 > unchanged limit 9.
Move only that strict sky probe to (.20,.08), which passed 154/154
accepted prior Android frames, and keep all three sky probes, modal,
stale-frame, origin SHA, GLES, structural, semantic and LOD gates.
First 4 partial sword views showed coverage improvement but are NOT
complete proof. Retest all four Android roles; candidate still unmerged.

2026-10-17 H13 independent manual audit rejected an apparently green run:
Run 39071499467 SHA 2d66086713f55acd55db9f25835054bbcaed3fec
had 18/18 jobs PASS and 154 recorded frames, but its FIRST accepted sword
screenshot was byte-identical to treasure_chest final yaw325 frame:
SHA-256 5af86de2a82e1a08d85cc9f88a9767db4e8c00bdd0d21d47125b9a7ae940b7d7.
Artifact 12115067670. The screenshot shows the CHEST. Therefore measured
14-view sword coverage for that run is INVALID, regardless of green CI.
Preserve all evidence, reject visual acceptance, no auto-promote/merge.
Repair strictly the cross-asset stale-frame handoff: keep last accepted
presented frame outside asset loop, enforce existing .0006 change threshold
on every first frame, archive/retry duplicates. New regression tests added.
All other technical gates and 14 yaw/pitch angles unchanged. Full rerun
and independent SHA audit REQUIRED before marking sword camera verified.


H14 2026-10-17: feature/veilforge-cross-asset-evidence-gate-20261017-h14
Base 14b26b973d29473db45a8c652222a0883d0b3a00 (run 39071961941).
Confirmed stale chest-to-sword screenshot in rejected run 39071499467.
Independent Android reviewer now rejects identical hashes across assets
within one emulator role. Synthetic tests include a positive 154-frame
fixture and a negative cross-asset replay. No model or camera edits.
Full four-emulator, semantic and LOD verification pending; no merge.
