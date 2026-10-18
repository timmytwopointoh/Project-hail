# VEILFORGE H19 isolated branch ledger

Branch: feature/veilforge-lod-frame-provenance-20261017-h19
Parent SHA: fd1b3da746c2671396578736b401e3a23b6daed2
Before run: 39087432244 (18/18 success; four Android 15 roles, 154 real frames, independent semantic and LOD passed).
Original review: 38993296206 / 12085917087, source 85f634f58d0a5863186b22a90c1fd74292cc8c2b.
Actual screenshot artifacts examined: original props 12086056909; H18 props 12121147743. yaw0 sword is intentionally edge-on; yaw225/250 broadside. Do not label narrow yaw0 as geometry failure.
Selected issue: independent LOD comparison accepted unchecked image paths and lacked direct screenshot SHA and source/APK agreement checks.
Scope: new vq_lod_evidence.py, integrate into visual_lod.py, synthetic positive and negative regression tests; no camera, geometry, renderer, IoU threshold, queue, game, APK or workflow edits.
Before: zero per-frame LOD digest comparisons; after target: 28/28 validated SHA/camera/path pairs, same APK and source on both roles. IoU value and real foreground coverage intentionally unchanged.
After SHA/run: PENDING. Require full 18/18 Android factory and independent semantic/LOD gates.
Keep original and rejected artifacts; no automatic promotion/merge or human artistic/real-phone performance acceptance.
