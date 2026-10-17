# VEILFORGE forest_tree_mobile — isolated camera review ledger (2026-10-17)

**Status: scoped QA-only candidate; four-emulator retest pending.** No mesh
rewrite, game edit, automatic promotion, merge or artistic signoff.

## Pinned evidence
- Original five-task handoff: source `85f634f58d0a5863186b22a90c1fd74292cc8c2b`, run `38993296206`, artifact `12085917087`; proposals are REVIEW, not executable fixes.
- Newest validated parent: source `291223bfcc5b39e5a11c7f2e0558febbb235c41a`, run `39020966378` (19/19 jobs, 4 Android 15 emulators, 154 accepted views); APK SHA-256 `683dcc1221c6f4f10c709b070d75941be5f1ed3b8f1db559b3dd1fdea95705cb`.
- Actual nature-mobile screenshot archive `12096950777`; semantic archive `12096454129`, dynamic REVIEW archive `12096747834`. The tree is visible in all 14 inspected angles, not demonstrably culled. Independent silhouette coverage min `0.0035`, max `0.0255`, 13 distinct orbits, zero edge-contact warnings. Small QA framing/readability is the issue, **not a proven mesh defect**.
- Before screenshot `forest_tree_mobile/03_yaw75_pitch15.png` SHA-256 `c4e7bc2d1699423e4b4d5dfc099e4572d9953a3cd1a1618a3b6846c04337f72c`. View `08_yaw200_pitch42.png` SHA-256 `0200dac9be4b37d0157a1ebde5bc6acb3b792bb87f4d922da571d1ce85e89e0f`. The original run had stale transitions; use the later fresh-view run as baseline.

## Single correction and rejected candidates
Android test viewer ONLY: `forest_tree_mobile` orbit distance changes
`max(3, radius*2.35+1.2)` to `max(3, radius*1.95+0.9)`. No other
asset, worker, shader, source mesh, QA threshold, game or workflow changed.

Pinned two-primitive glTF bounds and the scene's yaw-114, scale-0.8
instance predict camera distance `6.34454 → 5.16888`, max vertical
|NDC| `0.668 → 0.817` (~18% remaining margin), and minimum near depth
`3.01` versus GLES near plane `2.0`, across all 14 views. **These are
projection predictions, not Android measurements.** A dedicated unit test
checks the conservative orbit envelope.

Rejected `radius*1.55+0.9` (max predicted |NDC y| `0.995`,
crop risk), `radius*1.4+0.9` (near depth `1.80`, clipping), global
camera/lighting edits and geometry rewrites without evidence.

## Acceptance still required
Rerun all eight catalog workers, shared hash-verified GLES APK, four
Android 15 emulators, 154 fresh captures and independent semantic/LOD/
structural gates. Record after source SHA, run, APK SHA, 14 frame hashes,
measured silhouette min/max, edge contacts, stale retries and rejected
candidate evidence. Passing technical QA is **not** artistic quality,
photorealism or real-device performance. Do not auto-merge/promote.

Static `veilforge/queue_backlog.json` is separate from dynamic
`veilforge-android-next-iteration-tasks` REVIEW proposals.
Branch: `feature/veilforge-forest-tree-camera-fit-20261017-h06`.
