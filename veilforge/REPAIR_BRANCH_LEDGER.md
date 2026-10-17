# VEILFORGE / VQ — evidence-preserving repair branch ledger

## 2026-10-17 candidate: ancient_tree dark-angle visibility

Baseline source commit: `85f634f58d0a5863186b22a90c1fd74292cc8c2b`.
Baseline factory run: `38993296206`, 18/18 successful jobs, 138
unit tests, four Android 15 emulators, 154 real-angle captures.

Immutable task artifact ID `12085917087`, SHA256
`231434d1a110794e257d3f9295f365b100e5c6eaa054d900a9d45201a3386a70`.
Nature-mobile screenshot artifact ID `12085179609`, SHA256
`761672df72e672f5f7e7a62d3fd87fb42b2fd715438ab4954fbf58813ae749c2`.

Original screenshot `ancient_tree/09_yaw225_pitch15.png`, SHA256
`4cf75563332004588fe20fa3574ac407d98b379afe8bd708ab73045a9561d01e`,
192x192 semantic foreground fraction 0.00079.
Original screenshot `ancient_tree/02_yaw50_pitch42.png`, SHA256
`9a501a3fbc98a79dad5fe5cac4d1a14132397b459eb56bcdc500599b690b07e6`,
semantic foreground fraction 0.01858.
Baseline semantic summary ancient_tree min 0.0008, max 0.0186.
These are heuristic visibility measurements, not aesthetic scores.

Rejected competing diagnosis: ceremonial_sword at yaw 0 degrees is
edge-on, so its thin silhouette alone does not justify mesh edits.
Keep all five review tasks distinct from static `queue_backlog.json`.

Candidate branch: `feature/veilforge-ancient-tree-visibility-fill-20261017`.
Candidate source SHA: branch HEAD; record the immutable Git commit and
Actions run in the subsequent validation report. Candidate state:
UNVALIDATED; do not merge or promote.

Bounded candidate: Android GLES probe fill only for selected ancient_tree
filter. Dark-surface ambient 0.22 -> 0.65, full diffuse unchanged.
All original assets, cameras, game code, independent QA thresholds,
source provenance, other asset lighting and scene rendering unchanged.

Acceptance: full factory, shared hash-verified GLES APK, four Android 15
emulators, 154 screenshots, independent semantic and LOD review.
Compare all 14 matching ancient_tree angles and screenshot SHA256 values;
require yaw 225 degrees coverage above 0.00079, no new technical
blockers or other-asset regressions, and separate human artistic
acceptance before promotion. If the experiment fails, preserve the
candidate branch and its screenshot artifact IDs; never conceal it by
rewriting source history.

Canonical 34-capability and 13-efficiency milestone JSON maps remain
unchanged. This ledger is a review trail, not an unrestricted automatic
self-repair system.

## 2026-10-17 isolated QA correction: duplicate camera screenshots

Parent source SHA: `9cf8ebdec2c6b40148bff2e105d9addc9495f6ab`; Android factory run `39040161933`
(18/18 jobs passed). The ancient_tree-only visibility fill improved the
independent 192x192 foreground mask at yaw225/pitch15 from 0.00079 to
0.03133, but the run still accepted byte-identical PNGs for different
adjacent labelled views: ancient_tree yaw0/yaw25 and yaw75/yaw100,
yaw125/yaw150, yaw250/yaw275, yaw300/yaw325 (five repeated pairs).
The screenshot capture gate on this isolated parent lacked the already
verified cross-asset compositor-freshness guard on the separate sword branch.
This is a camera evidence integrity defect, not evidence of a bad tree mesh.

New candidate branch: `feature/veilforge-tree-frame-freshness-20261017-h09`.
Bounded correction: propagate the prior accepted PNG SHA through all
camera/asset transitions, retry exact duplicate presented screenshots,
retain each rejected `_stale_presented_*.png` and fail closed on persistent
staleness. Reuses the technique independently proven in source
`291223bfcc5b39e5a11c7f2e0558febbb235c41a`, run `39020966378`.
No geometry, shaders, games, thresholds, workflow concurrency, or camera
parameters change. Tests cover retry, preserved rejected evidence,
persistent failure and digest propagation.

Status: UNVALIDATED until full 4-emulator, 154-labelled-view factory and
independent semantic/LOD checks complete. Require zero adjacent exact
duplicate accepted frames and preserve original screenshot evidence.
This improves *camera provenance*, not artistic appearance, photorealism,
or physical-device performance. Do not merge or promote automatically.
