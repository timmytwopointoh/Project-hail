# VEILFORGE — bounded multi-instance tree inspection camera
Date: 2026-10-17
Status: candidate pending full real-Android verification

## Source and observed defect
Original completed factory run 38993296206 at 85f634f58d0a5863186b22a90c1fd74292cc8c2b
published review task 12085917087. The subsequent verified source SHA
43ea85d29e345379aec58c0960316435f5c3ad8c, run 39061003603, nature-mobile artifact 12111113964,
retained the same camera FOV while adding rejected-stale-frame preservation.
Both ancient_tree instances appear in the original 14 screenshot angles;
there is no evidence of missing geometry or culling. The measured issue is
small apparent size for *both* trees when inspecting their shared asset ID.
Semantic foreground mask coverage: min 0.00079, max 0.01858,
mean 0.00875 across 14 real Android Pixel 7 screenshots.

## Scoped correction
Only the independent Android QA probe's ancient_tree filter uses
frustum top/bottom +/-0.75 instead of +/-1.0 at near=2.0;
left/right remain proportional to viewport aspect. This narrows vertical FOV
from 53.13 degrees to approximately 41.11 degrees. Eye distance, look-at,
all 14 yaw/pitch inputs, the two scene instances, source mesh, PBR materials,
all game runtimes and all other asset filters remain unchanged.

For the pinned glTF scene geometry, projected all source positions at
the 14 QA orbit angles (including two rotated/scaled instances) using the
probe camera's exact midpoint and bounding-radius math. Predicted maximum
absolute normalized device coordinates: Y=0.805 (before 0.604),
X=0.403 (before 0.302). Minimum forward depth=11.643 (near plane=2).
These are geometry-based safety estimates, not measured Android results.
Use the real Android semantic review to establish the actual after coverage.

## Acceptance and rollback
Require full existing unit suite, 8 catalog workers, shared APK hash,
four Android 15 emulators, 154 fresh frames, structural Android gate,
independent semantic and LOD reviewers, and screenshot-source SHA matching.
Compare all 14 ancient_tree views, not just the best angle. Require measured
coverage improvement with no clipping or new review blockers. If this fails,
retain failed screenshots/logs and revert the isolated branch only.
Preserve rejected duplicate capture candidates. Do not weaken any threshold.
Even a passing gate is not artistic, PBR realism, or physical-phone approval.
