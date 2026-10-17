# VEILFORGE review-gated geometry candidates — 2026-10-17

## Real Android evidence
The 18/18 baseline run 38993296206 (source 85f634f58d0a5863186b22a90c1fd74292cc8c2b) produced 154 screenshots and five immutable REVIEW tasks (artifact 12085917087). The ceremonial_sword views in artifact 12086056909 show a real blade: yaw 0/25 are thin edge-on views, while yaw 75/225 reveal broadside blade geometry. Minimum/maximum silhouette coverage 0.0006/0.0104; framing warnings 0. A tiny edge-on silhouette is NOT proof of missing mesh.

The ancient_tree was a separately verified camera-framing correction, not geometry repair. Original silhouette min/max 0.0008/0.0186; after the isolated camera-distance correction at SHA 27399138080f36cc133b85e927c0b5041a28f2a7, run 38996754894: 0.0014/0.0290 (75.0% and 55.9% higher, respectively). This is measured screenshot coverage, not photorealism or artistic acceptance.

Latest full factory baseline: SHA fbc0f70f3e4bb16606981fda0fa4fd6f5ab69f08, run 39005500395, 19/19 jobs, 150 unit tests, four Android 15 emulator roles, 154 hash-verified screenshots, independent semantic and LOD review passed. Artifact 12090723241 links each of the five REVIEW tasks to 14 exact camera frame hashes.

Prior auto-generated sword candidate artifact 12091176795 used Z-axis gain 1.08 and max vertex shift 0.00913014, retaining 792 triangles. This is **rejected as an unproven geometry response** to an edge-on warning. Keep it for audit; it was never Android candidate-validated, promoted, merged, or artistically approved.

## One scoped correction
Branch feature/veilforge-review-gated-candidates-20261017 is based on fbc0f70f3e4bb16606981fda0fa4fd6f5ab69f08. The geometry candidate generator now requires a separately supplied specialist verdict with exact source SHA, run ID, original task artifact SHA-256, all 14 original screenshot SHA-256 values, at least two non-edge-on view indices, and a written geometry-versus-camera decision. Normal CI provides no verdict, so REVIEW warnings yield an empty candidate report. An explicit review can still generate a bounded, copy-on-write candidate; never auto-promote it.

Regression tests exercise the no-review default, explicit opt-in candidate topology preservation, mismatched screenshot hashes and source manifest rejection. This is a fail-closed provenance gate, not cryptographic reviewer authentication.

## Boundaries
Do not change game source, source OBJ, worker catalog, semantic/LOD thresholds, static queue_backlog.json, or four-emulator QA. The dynamic next-iteration tasks are REVIEW proposals only. Continue canonical 34 milestone and 13 efficiency milestones (UV atlases, tangents/baking, retopology, anatomy/rigs, world assets, PBR, real-phone performance) without asserting their completion. CI source SHA/run/QA result must be appended from observed evidence, never guessed. Human artistic acceptance remains outstanding.
