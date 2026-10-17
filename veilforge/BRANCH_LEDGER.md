# VEILFORGE branch ledger

2026-10-17 candidate: feature/veilforge-stale-frame-evidence-20261017

Base SHA: 85f634f58d0a5863186b22a90c1fd74292cc8c2b
Baseline run: 38993296206 (18/18 jobs; 138 tests; 4 emulators; 154 frames).
Observed: 28 of 143 adjacent camera transitions returned identical PNG SHA-256, despite distinct yaw and pitch.
Evidence artifact IDs: 12085179609, 12086056909, 12086640383, 12085664797.
Scope: reject and preserve stale camera captures, add independent hash review and regression tests.
Validation: PENDING full Android matrix. Require 0/143 duplicates, all original QA checks green.
No model or game promotion; no artistic or physical-phone performance signoff.
