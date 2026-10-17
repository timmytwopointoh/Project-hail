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

## H13 first real Android attempts — correctly rejected, camera still promising
The first full run 39070812414 at source 81e94b957927c867540ea3625fbda4c0a8c473eb
passed 12 pre-emulator jobs and 3 of 4 Android emulator roles. Pixel 5
props-equipment aborted; structural Android gate failed closed and semantic
and LOD review did NOT run. Re-running failed jobs once still failed.
Do not claim full validation. Preserve failed props artifacts 12115192686
(attempt 1) and 12114428965 (attempt 2).

At attempt 2 yaw75/pitch15, the screenshot visibly contains the enlarged
sword with genuine GLES background. Pixel at old QA sky probe (.50,.08)
was (28,31,33), 11 levels away from required (17,21,29) (limit 9);
pixels at (.20,.08), (.30,.10), (.65,.12) were ALL exactly (17,21,29).
The old center-top probe landed on the actual blade tip. This was a
false-negative sky-location assumption, not a reason to lower thresholds.
Across the prior successful run's 154 accepted actual screenshots, the new
(.20,.08) point is clear in 154/154. Three independent sky probes and
their exact <=9 threshold remain enforced; no blank, launcher, modal or
stale-frame gates are weakened. Add synthetic regression checking a genuine
sword tip is accepted but an off-axis non-background pixel is rejected.

Partial real sword evidence (not full validation): first four angles
old vs candidate foreground fractions:
yaw0 0.000624 -> 0.001519,
yaw25 0.001465 -> 0.004747,
yaw50 0.002252 -> 0.005778,
yaw75 0.003011 -> 0.006538 (attempt 1).
The H13 candidate remains isolated pending a complete fresh 154-frame run.

## H13 18/18 run 39071499467 — source-provenance rejection
The full run at SHA 2d66086713f55acd55db9f25835054bbcaed3fec
passed 18/18 technical jobs, 4 Android 15 roles, 154 files and independent
LOD/semantic gates. Nevertheless, manual screenshot inspection discovered
an invalid accepted FIRST sword angle. Exact PNG SHA-256
5af86de2a82e1a08d85cc9f88a9767db4e8c00bdd0d21d47125b9a7ae940b7d7
is IDENTICAL between treasure_chest/13_yaw325_pitch25.png and
ceremonial_sword/00_yaw0_pitch15.png in props artifact 12115067670.
The displayed object is a CHEST, not the sword. This invalidates any claim
of 14 valid sword views, despite green automated gates; reject that run
for sword visual acceptance. Previous-frame comparisons were reset by the
per-asset shots list, so a cross-asset stale compositor buffer escaped.

Fix: retain previous_presented_frame outside the asset loop and pass it
to every capture_visible_frame, including the first frame of each new
asset. On each accepted screenshot, update that reference. Existing
change_fraction threshold .0006, retries, immutable rejected PNG archive,
source SHA, modal checks, three sky probes and all other QA gates remain
unchanged. Add a source-wiring test and a real-image synthetic cross-asset
rejection regression. Re-run the FULL matrix and inspect cross-asset SHA
collisions before any visibility gain is accepted. Do not erase the
rejected green-run evidence.
