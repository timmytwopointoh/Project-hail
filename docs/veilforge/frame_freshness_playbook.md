# Android frame freshness technique

The 2026-10-17 baseline, run 38993296206 at commit 85f634f58d0a5863186b22a90c1fd74292cc8c2b, has 154 real emulator frames. SHA256 comparison found 28 byte-identical adjacent frames in 143 distinct camera transitions. Six of the assets were checked first (16/78); the remaining roles added 12/65. A new renderer log does not prove a new screenshot has reached the emulator compositor.

Fix scope: the Android capture harness compares the next PNG hash to the previous accepted view for that asset, retries exact duplicates, preserves rejected bytes, and fails after the existing bounded attempt budget. No geometry, camera FOV, worker topology, semantic thresholds, or quality approvals were changed.

The sword's low visibility at yaw 0 (0.00062 mask coverage) and higher coverage at yaw 250 (0.01039) are consistent with an edge-on view; no mesh deformation was approved. Preserve the separate unapproved candidate from run 38994170126 artifact 12086911566.

Require 4 emulator roles, 154 images, SHA integrity, independent semantic and LOD gates, and zero exact adjacent duplicates to validate this scoped fix. This is a technical capture improvement, not an artistic or real-phone performance result.
