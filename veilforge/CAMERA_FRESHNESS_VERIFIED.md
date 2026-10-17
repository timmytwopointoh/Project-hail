# VEILFORGE camera-frame freshness — verified

Source branch: feature/veilforge-tree-frame-freshness-20261017-h09
Source SHA: 1a9986d3f63da9ebd30879e3642c38d7897de531
Successful full Android factory run: 39044408914 (18/18 jobs).

The parent source 9cf8ebdec2c6b40148bff2e105d9addc9495f6ab, run
39040161933, accepted 31 exact byte-identical adjacent screenshot pairs
despite distinct yaw/pitch labels. The scoped QA-only correction carries
the previous accepted screenshot SHA256 through camera and asset transitions,
retries stale compositor frames, preserves rejected PNG bytes and fails closed
if a fresh view cannot be obtained. No model geometry, camera parameters,
shader, game code, or QA thresholds were changed.

Four Android 15 emulators now accepted 154 real labelled screenshots with
zero adjacent exact duplicates. Thirty-four rejected stale PNGs were preserved.
Every accepted PNG digest matched its original emulator role report.
Shared GLES APK SHA256:
c9db8a2bb46e8a6175ee8f2cf9d8c8e704adb1cd2aa25f9d36800eff76a9169a.

Independent semantic and LOD reviews passed. Semantic review: 11 assets,
154 frames, zero blockers, four outstanding REVIEW proposals. Ancient-tree
minimum semantic foreground coverage remained 0.0254. LOD mean silhouette
IoU 0.4070 to 0.5944, minimum IoU 0.1222 to 0.4269. These are camera-
sensitive diagnostics, not evidence of artistic or photorealistic quality.

Android evidence artifact IDs: characters 12105292400; props 12105770398;
scene 12104738823; nature 12105550765; semantic 12104673957;
LOD 12105481168; final gate 12105024176; review handoff 12105337467.

Source backups, accepted screenshot hashes, 31 original duplicate-pair
hashes and 34 preserved rejected PNGs are indexed in the user's
VEILFORGE Library file VEILFORGE_VQ_camera_freshness_verified_20261017.zip.

No merge, promotion or automatic model rewrite. Human artistic signoff
and physical-device FPS/thermal/battery testing remain pending. Dynamic
REVIEW proposals are separate from static queue_backlog.json. Canonical
34-capability and 13-efficiency milestone maps remain unchanged.
