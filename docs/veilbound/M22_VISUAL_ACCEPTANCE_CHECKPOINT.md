# M22 visual acceptance checkpoint — 2026-10-16

Baseline: M22 commit `49f4d2c13b493bad0eac43db21e989942699fee4`.
- Parallel Worker QA run 38858091422: SUCCESS (combat, integrity, assets).
- Native 3D Android RPG run 38858091465: SUCCESS (build-and-test).
- Actual Android 15 emulator inspection report from native run: status passed; GPU scene visible; no GL error; human hand-focus capture exists.
- The hand-focus screenshot `01_human_five_finger_closeup.png` genuinely frames both hands, unlike the previous M21 native-run hand-focus screenshot that showed feet. The thumbs and elongated finger geometry are visible, but finger overlap prevents reliable confirmation of four individually separated fingers plus one opposable thumb on EACH hand. Do not mark five-digit visual acceptance complete.
- The front/side/back/three-quarter screenshots exist in the native inspection archive; they do not by themselves prove detailed hand topology or animation weighting.
- The Actions run list for the exact M22 branch has only the Worker QA and Native 3D Android RPG workflows. **No M22 four-emulator farm run was found**. Android 15 four-emulator synchronized validation remains BLOCKED/NOT RUN for M22; do not substitute M21's earlier farm pass.
- Preserve M21 and main; do not auto-promote M22 to M23 as finished anatomy.
Next: run M22 four-emulator farm with identical Android 15 images, capture each hand from front/side/three-quarter with finger-level zoom and inspect finger joint deformation, topology, skin weights. Fix any actual failures before further anatomy promotion.
Evidence: https://github.com/timmytwopointoh/Project-hail/actions/runs/38858091422 and https://github.com/timmytwopointoh/Project-hail/actions/runs/38858091465.
