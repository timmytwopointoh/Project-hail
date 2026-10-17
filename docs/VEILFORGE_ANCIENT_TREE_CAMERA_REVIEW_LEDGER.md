# VEILFORGE camera review ledger — ancient_tree (isolated QA branch)

Status: **candidate, Android retest pending**. No auto-promotion, model overwrite or merge.

## Evidence and decision
- Initial verified 18/18-job source: `85f634f58d0a5863186b22a90c1fd74292cc8c2b`; run `38993296206`, 154 emulator frames, review artifact `12085917087`.
- Additional passing frame-freshness baseline: `325ca6df457ee77a971ae2a4b1fde8a5c7223a6f`; run `38995400473`; independent semantic report `12087240835`; nature screenshots `12087082123`. The latter is the actual camera-change parent.
- `ancient_tree`: 14 real screenshot views contain two spaced trees; their scale is small even at broadside yaw. Latest semantic coverage min `0.0008`, max `0.0186`. This is a **framing/readability** candidate, not proven missing geometry.
- Baseline frame `ancient_tree/09_yaw225_pitch15.png` SHA-256 `f749a501b98ddf08d0799647a8b99fa858ef163673ff551696e9922822ba995e`. The object is present, but dark. Do not call darkness culling.
- `ceremonial_sword`: yaw 0/25 views are visibly edge-on and low-contrast; **rejected** as evidence of missing blade geometry. No sword mesh or camera changes.
- `queue_backlog.json` remains static and independent of screenshot-generated REVIEW proposals.

## Single scoped correction
Only `ancient_tree` Android-probe camera distance changes, from `max(3, radius*2.35+1.2)` to `max(3, radius*1.95+0.9)`. All other assets retain the original distance. No changes to model source, material shading, semantic thresholds, QA gates, workers, games, or acceptance flags.

The pinned glTF bounds from run `38993296206` analytically project to maximum absolute vertical NDC `0.669` before and `0.839` after across all 14 prescribed yaw/pitch pairs (margin ~16% to the top/bottom). This is a **projection prediction**, not an emulator measurement. Candidate `radius*1.75+0.9` was **rejected**: predicted max vertical NDC `0.964`, too close to cropping. Global ambient/lighting changes rejected as over-broad. The pinned-envelope unit test checks only the known assembled scene; 4-emulator CI remains mandatory.

## Retest and acceptance
Run the complete factory with 4 Android 15 roles, 154 screenshots, independent LOD and semantic reviews. Compare exact source SHA, APK SHA, per-angle screenshot SHA, tree median/min silhouette coverage, orbit uniqueness and edge contacts. Preserve any failed candidate evidence. A warning can persist for intentional low-light silhouettes without failing technical QA. Do not claim real-phone FPS, photorealism or artistic acceptance.

Branch: `feature/veilforge-ancient-tree-camera-fit-20261016-qa01`. The code commit SHA and run ID are filled only after actual GitHub evidence exists.
