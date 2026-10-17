# VEILFORGE / VQ — verified ancient_tree Android probe visibility experiment

Baseline source SHA: 85f634f58d0a5863186b22a90c1fd74292cc8c2b
Baseline full factory run: 38993296206 (18/18, 138 tests, 4 Android 15 emulators, 154 screenshots).
Candidate source SHA: 9cf8ebdec2c6b40148bff2e105d9addc9495f6ab
Candidate full factory run: 39040161933 (18/18, 140 tests, 4 Android 15 emulators, 154 screenshots).
Candidate branch: feature/veilforge-ancient-tree-visibility-fill-20261017

## Measured before / after

Real nature-mobile Android screenshot artifact IDs: 12085179609 -> 12103133910.
Independent semantic artifact IDs: 12085952120 -> 12104051392.
Independent LOD artifact IDs: 12086410451 -> 12104305516.
Task artifact IDs: 12085917087 -> 12104200889.

Ancient_tree semantic foreground coverage over 14 matched angles:
minimum 0.0007867 -> 0.0253906; maximum 0.0185818 -> 0.0313314.
Yaw 225 degrees / pitch 15 degrees: 0.0007867 -> 0.0313314.
Original screenshot SHA256:
4cf75563332004588fe20fa3574ac407d98b379afe8bd708ab73045a9561d01e
Candidate screenshot SHA256:
84be7f28d8f61b8c981cea856bb15e861feca6f5674b32328383472ffc19a370

The ancient_tree visibility warning cleared. Semantic warnings: 5 -> 4.
No semantic technical blockers. LOD mean IoU: 0.4123 -> 0.4070;
minimum IoU: 0.0478 -> 0.1222. These are heuristics only.

## Bounded change and remaining gates

Android GLES inspection renderer only: when the ancient_tree filter is selected,
shadow ambient floor increases 0.22 -> 0.65 while full-diffuse remains 1.0.
Other asset filters and the scene retain original lighting; no game, geometry,
texture, camera, strict provenance hash or QA threshold was changed.

Forest_tree_mobile still has a visibility warning; emulator frame timing causes
some unrelated coverage differences. The sword edge-on case was not changed.
No physical-device performance, photorealism, or artistic acceptance is claimed.
No merge or asset promotion is authorized.

Full before/after original screenshot and source-geometry backup with SHA manifest:
ChatGPT Library /App creation/VEILFORGE - VQ Engine Library/
VEILFORGE_VQ_ancient_tree_visibility_verified_20261017.zip

Disposition: technical validation PASS, visibility IMPROVED, human artistic review PENDING.
