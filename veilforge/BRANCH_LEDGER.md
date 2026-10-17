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
