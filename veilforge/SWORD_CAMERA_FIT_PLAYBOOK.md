# VEILFORGE — H13 ceremonial_sword Android QA camera-fit candidate

Date: 2026-10-17. Status: isolated candidate, full Android verification pending.
This document records a camera-inspection improvement, not a mesh repair.

## Evidence and diagnosis
Immutable initial review handoff: run 38993296206, commit
85f634f58d0a5863186b22a90c1fd74292cc8c2b, artifact 12085917087.
Latest parent: 350151ad86264b26ac5980babe870872d0999e61,
successful 18/18-job run 39067049952.
Source screenshots: props-equipment artifact 12114185198, Pixel 5 API 35,
14 accepted views, 6 discarded stale/blocked candidates retained.
Source APK SHA-256: 0ef00ef8d03213b205c1a7fa5af860be6d1564eeb7b866b98aee2ae431795ae4.
Frame 00 yaw0/pitch15: SHA-256 566f1246b9978a49f57063a3d97d84751252b1cc3913b00dea1bfca200e79641.
Frame 10 yaw250/pitch25: SHA-256 91598d1e0f74e5c0413f72f8341a328cd12682b64b3d0a01aaedd7f1e6da9a20.
The edge-on blade at yaw 0 is expected, NOT missing/culling geometry.
Broadsides remain small in the QA viewport. This is a framing issue only.
Independent color-background silhouette heuristic: min 0.000624,
max 0.010390, mean 0.004420 over all 14 accepted Android screenshots.

## Bounded change
Only the Android glTF QA probe uses frustumScale=0.65 for ceremonial_sword.
The already-measured ancient_tree QA setting remains 0.75 and all other
filters retain 1.0. Near plane=2; eye distance and 14 yaw/pitch pairs stay
unchanged. No source model, material, shader, scene instance, game, QA gate,
asset promotion or backlog execution is changed.

Using the exact sword_drop transform (translation [0.2,1,-0.2], scale .5,
quaternion Y=.6626200482, W=.7489557208), POSITION bounds
[-.562,-.9,-.11412678] to [.562,2.78,.11412678], and 2340x1080
viewport, all 14 QA camera angles were projected using the Android probe's
center/radius/distance/frustum formulas. Conservatively including all
eight rotated bounding-box corners, candidate 0.65 predicts
max |NDC y| 0.88033, max |NDC x| 0.14302,
min forward depth 2.64365 (near 2.0). At 0.55 the box could
reach or cross the vertical clip edge; reject that more aggressive zoom.
These are source-geometry estimates, NOT emulator measurements.

## Acceptance and rollback
Require 18/18 jobs, all unit tests, eight catalog workers, one identical
hash-verified GLES APK on four Android 15 emulators, 154 accepted source
frames, independent structural/semantic/LOD gates, no new framing/culling
problems, no stale or blocked frames counted as accepted, and an actual
14-angle measured coverage gain for ceremonial_sword. Preserve rejected
candidates and per-angle source SHA in the immutable run artifacts.
If any gate fails, retain evidence and leave this isolated branch unmerged.
Technical success never proves photorealism, actual phone FPS, PBR quality,
or human artistic approval. Dynamic review tasks are separate from
veilforge/queue_backlog.json and cannot auto-edit assets.
