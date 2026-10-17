# VEILFORGE M30/M31 UV atlas overlap QA — 2026-10-17

Status: **isolated candidate, Android retest pending**. No merge, asset promotion, source replacement or artistic acceptance.

## Pinned source and original Android finding
Parent SHA `428719aeed1d3a6efd2210a88977dab4fc9ab7b5`, factory run `39007746984`: 19/19 jobs passed including four Android 15 emulator roles and independent semantic/LOD review. Original five REVIEW tasks remain linked to source `85f634f58d0a5863186b22a90c1fd74292cc8c2b`, run `38993296206`, artifact `12085917087`. The tiny ceremonial_sword yaw 0/25 silhouette is intentional edge-on, **not** proven missing geometry.

The separately verified ancient_tree camera change `27399138080f36cc133b85e927c0b5041a28f2a7`, run `38996754894`, improved measured foreground coverage min `0.00079→0.00138`, median `0.00792→0.01277`, max `0.01858→0.02905` across 14 real emulator views. These are image metrics, not artistic quality.

## One scoped issue and correction
Existing M30 raster checks reject UV overlaps only when the sampled 3D points differ by >0.001 world units. Fully coincident stacked geometry/UVs and positive-area overlaps smaller than one output texel could escape the uniqueness check. A new bounded UV-space separating-axis audit detects these cases without relying on pixels or world positions. Shared edges/corners are legal. Pathological grid/pair workloads fail closed instead of claiming uniqueness.

Both low and high bake sources and M31 newly generated UV atlases now run this audit. Regression tests cover legal shared edges, a subpixel intersection wedge, coincident stacked UV triangles, and legal adjacent OBJ faces. The source OBJ is immutable and existing thresholds, games, worker catalog, Android cameras, static queue_backlog.json and dynamic REVIEW proposals remain unchanged.

This audit does **not** establish mip padding, continuous UV islands, realistic PBR, real-phone performance, photorealism or human artistic approval. Full factory, 4-emulator and independent LOD/semantic QA are mandatory before technical acceptance. Rejected/failed candidates must remain auditable.

## Verified result — immutable tested code commit
- Code SHA: `17b5dd7b1b75b23038623ba4d03019a9e5aac34e`; complete factory run: `39013219080`, **19/19 jobs successful**. The manager log reports **156 passing tests**, no failures. This post-test ledger update is documentation-only and does not alter the tested code.
- Android gate artifact `12094200520`: four API 35 Android emulator roles, **154 screenshots**, identical APK SHA-256 `ca3b0d35243a4e82d55d2c827715d2d2339a53ac6f577f9ef9c45330afe03321`, zero structural gate problems.
- Independent LOD artifact `12093946018`: 14 paired samples, mean silhouette IoU `0.5944`, minimum `0.4269`; quality heuristic, not human artistic approval. Semantic artifact `12094135726`: 11 assets, 154 frames, no technical problems; **six** visibility REVIEW warnings persist and remain proposals, not auto-fixes. The next-iteration handoff artifact `12093567490` carries 14 SHA-linked camera frames per proposal.
- Candidate report `12093971080`: **zero eligible model rewrites**, original source protected, no promotion. The static backlog remains separate. This UV-only change intentionally does not alter camera metrics; the previously measured tree before/after values above remain the authoritative camera comparison.
- The emitted roadmap `12094255046` currently contains **24** technical milestones (4 verified, 10 partial, 10 planned). The requested canonical **34** milestones and separate **13** efficiency milestones are **not yet reconciled**, and must not be declared completed or silently conflated.
- Final acceptance: **not achieved**. No physical-phone GPU/FPS validation, no photorealism validation, no artistic signoff. Preserve rejected candidates and screenshot evidence.
