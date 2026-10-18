# VEILFORGE H18 isolated branch ledger

Branch: feature/veilforge-camera-manifest-binding-20261017-h18
Parent SHA: b1b3be1f3d064efde6867607daf8995cc5b51e3b
Before run: 39080109415 (18/18 successful jobs, 4 Android 15 roles, 154 screenshots, independent semantic/LOD passed).
Original handoff: 38993296206 / artifact 12085917087 / source 85f634f58d0a5863186b22a90c1fd74292cc8c2b.
Screenshot evidence: original props 12086056909; H17 props 12118412446; H17 structural 12118184441; semantic 12118334137; LOD 12118254298.
Real yaw0 sword silhouette is intentionally edge-on; broadside yaw225/250 visible and larger after H13. Do not infer missing mesh.
Selected source defect: independent structural reviewer lacked yaw/pitch and filename-to-view binding. A distinct mislabeled screenshot could pass its structural gate.
Scoped fix: exact canonical camera metadata and PNG path, with three synthetic regression tests. No renderer/camera/geometry, thresholds, queue backlog or games changed.
After SHA and run: PENDING. Require 18/18, 154 accepted distinct real frames, all four emulators and independent semantic/LOD passes.
Measured target: canonical synthetic 154-frame manifest passes; two malformed manifest cases fail closed. Foreground coverage intentionally unchanged; no artistic/phone-performance claims.
Preserve all rejected candidates and prior branches; no auto-merge or asset promotion.

H18 candidate 1 REJECTED: SHA 37040225aaedeaeed3dde2069cccff982b16bbaf,
run 39087340024. Library-manager failed 3/159 unit tests, and all
downstream emulator jobs correctly skipped. Root cause: historical synthetic
cross-asset fixture used abbreviated image filenames (index-only), incompatible
with newly enforced production naming. Fix only that fixture to canonical
index/yaw/pitch naming; preserve original duplicate/replay assertions.
No weakening of the new production camera binding. Rerun complete factory.
