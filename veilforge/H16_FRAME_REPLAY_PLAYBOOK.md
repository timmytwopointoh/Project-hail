# VEILFORGE H16 — delayed screenshot replay integrity gate

Date: 2026-10-17. Isolated branch: feature/veilforge-nonadjacent-frame-replay-gate-20261017-h16.
Parent: 4c954152084215c8dbc4cb33499ecea827fcecd1; successful factory run 39074518817.

## Real Android evidence and scope

Immutable original review handoff: run 38993296206, source 85f634f58d0a5863186b22a90c1fd74292cc8c2b, artifact 12085917087. Its five semantic warnings are REVIEW proposals, never automatic mesh changes. Inspected the original sword PNGs in props artifact 12086056909 and current PNGs in 12116820893. The yaw0/25 thin profiles are intentional edge-on views, not missing geometry. H13 camera framing already improved broadside occupancy, verified by H15.

The independent structural reviewer rejected adjacent duplicates and cross-asset SHA collisions but could accept a delayed same-asset replay, e.g. yaw0 reappearing at yaw75. H15's immutable ZIP comparator also checked only adjacent same-asset pixel equality. This is a real QA evidence-integrity gap: a replay can masquerade as one of 14 unique camera angles.

## Bounded source correction

The structural reviewer now rejects any repeated byte SHA within an asset, reporting first/replayed yaw/pitch; its cross-asset check remains. The independent camera comparator now rejects any repeated decoded-pixel SHA within an asset, including re-encoded PNGs with changed metadata. Two negative synthetic regression tests cover yaw0-to-yaw75 delayed replay and PNG re-encoding. The previous cross-asset and source-hash tests remain.

No asset geometry, renderer, camera, game, performance threshold, semantic threshold or backlog semantics changed. Rejected candidates and historical false-green run 39071499467 / artifact 12115067670 remain immutable.

## Acceptance

Require a single full factory run: 18/18 jobs, 8 catalog workers, shared hash-verified GLES APK, four Android 15 emulators, 154 distinct accepted real-angle screenshots, independent structural/semantic/LOD passes, no weakened gates. Record actual run ID, source SHA and retained rejected candidates. No auto-merge, asset promotion or claims of human-artistic approval, real-phone FPS, or photorealism.
