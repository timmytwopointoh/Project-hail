# VEILFORGE H16 isolated branch ledger

Branch: feature/veilforge-nonadjacent-frame-replay-gate-20261017-h16
Parent SHA: 4c954152084215c8dbc4cb33499ecea827fcecd1 (run 39074518817).
Origin: review task artifact 12085917087, run 38993296206.

Inspected original and latest real sword screenshots. Narrow yaw0/25 is an intentional edge-on view, not a mesh defect. H13 already measured a bounded camera framing improvement. Selected one remaining **real** source-level defect: nonadjacent same-asset screenshot replays escaped independent verification.

Changes: same-asset all-angle byte SHA duplicate check in android_review.py; all-angle decoded-pixel duplicate check in vq_android_camera_evidence.py; two negative replay tests. No renderer, camera, geometry, game, gate threshold or auto-repair changes. Original rejected artifacts preserved.

Status: PENDING fresh full four-emulator Android/semantic/LOD run; no artistic approval or real-phone performance claim. Never auto-merge or auto-promote.
