# VEILFORGE H17 — live retry of delayed Android frame replays

Date: 2026-10-17. Branch: feature/veilforge-live-replay-retry-20261017-h17.
Parent: 9b24153018d061a76530e48f04e98978f445676e; factory run 39077062255 passed all 18 jobs.
Immutable origin: 85f634f58d0a5863186b22a90c1fd74292cc8c2b, run 38993296206, review artifact 12085917087.

## Verified context
Downloaded and inspected original props screenshot ZIP 12086056909 and latest 12117621089.
Sword yaw 0/25 is a genuine edge-on silhouette, not missing geometry. Broadside yaw 225/250 is larger after the bounded H13 QA camera fit. H16 independent reviewer rejects delayed same-asset replays, but the live capture worker still retries only the immediately preceding frame. A nonadjacent compositor replay could therefore waste an entire 4-emulator run before downstream rejection.

## Single bounded change
The capture worker retains decoded-pixel SHA-256 fingerprints for all previously accepted frames in its Android role (including prior assets). An exact repeat at any later yaw is archived as *_rejected_replay_N.png and retried within the existing 8-attempt limit; a genuinely new frame is accepted. Hashes include dimensions; PNG metadata changes cannot evade the check. Similar-looking edge-on frames are NOT rejected on appearance alone. The existing adjacent 0.0006 change threshold, all 14 angles, sky checks, modal checks, GLES checks and independent structural/semantic/LOD audits remain unchanged. A new report count and independent ZIP comparator count preserve replay evidence.

Tests cover a delayed yaw0-to-yaw75 replay, evidence preservation, and cross-asset state wiring. This is a source-level evidence-integrity fix, not geometry or artistic improvement.

## Acceptance / provenance
Require one new 18/18 factory run with 8 catalog workers, one hash-verified GLES APK, 4 Android 15 emulators, 154 accepted distinct frames and independent structural/semantic/LOD passes. Record run ID, source SHA and rejected candidate count. Keep all historical rejected candidates and branches. Do not merge/promote, edit queue_backlog.json, or claim physical phone FPS, photorealism or artistic signoff.
