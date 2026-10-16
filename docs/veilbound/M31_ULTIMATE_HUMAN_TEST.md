# VEILFORGE M31 — Human photorealism research and ultimate test

## Scope and preserved history

The target is the same adult unarmored athletic man designed through the user's reference images, including a front-facing **T-pose** and secondary relaxed/three-quarter stance. The original `Bellwarden Base Body Test` defines the intended character. The playable armored Bellwarden must remain unchanged as the original historical Easter egg. Hair remains unchanged and out of the current sculpt budget.

The game is the **VEILFORGE Testing Grounds**, not the primary asset engine. This branch is an isolated review candidate from `feature/veilbound-m30-anatomical-rig-repair`, preserving M20 through M30 model history and the original gameplay. No new model is auto-promoted to the playable character.

## What the other VEILFORGE development added

- `feature/veilforge-m27-surface-layers`: non-destructive, material-scoped triangle-center sculpting and real-render visual diagnostics; **do not apply the stone/terrain displacement algorithm indiscriminately to deforming human skin**. We adapted the 14-view and silhouette validation to `veilforge/human_angle_review.py`.
- `feature/engine-queue-ten-20261016`: one optional ten-slot catalog-asset/emulator queue; a verified cap is 10 matrix jobs with at most four emulators. It **does not currently queue this new human-model job**, and no claim of a 10-job human worker farm is warranted.
- `feature/veilforge-vf004-attribute-dedup-20261016`: updated attribute/LOD work, inspected for interoperability. Shared production code was not overwritten or merged into this branch.
- Earlier VEILFORGE M26 learning engine: manually grounded defect descriptions and bounded sculpt dials, never autonomous photo-quality recognition or automatic source modifications.

## Actual M31 implementation

1. **M30 rig correction retained**: real T-pose/relaxed vertex deformation with separate arm-vs-torso weights and original colors, fingers, shorts intact; no player model changes.
2. **M31SkinSurfaceNormals**: seam/octant-aware smoothing only for skin-colored source triangle vertices; preserved exact geometry, vertex colors, eyes and clothing, across lite and full LOD. High resolution altered 588 real source normals; lite altered 347. This does not replace retopology.
3. **M31 studio integration**: optional neutral, corrected T-pose, and corrected relaxed model entries (19–21), four native camera orientations, one pose/LOD loaded on demand. Original knight remains entry 0, import remains last.
4. **Reference measurements**: `veilforge/human_reference_targets.json` records height-normalized T-pose spans measured from the generated reference image. `human_reference_fit.py` compares real exported OBJ cross-sections. This is an **advisory measurement**; camera, anatomy landmarks and identity are not photogrammetrically calibrated. No reference image binary is committed. The first attempt conflated occupied pixel count with width at lower-body rows; this was caught, corrected and rerun.
5. **Quality checks**: `human_angle_review.py` validates 14 actual orthographic source projections and 3 head closeups, models visible/not frozen, camera differences, and SHA for each image. It is adapted from the M27 real Android screenshot semantics. Independent source-geometry/rig strain, source-preserving hair/garment gates and Android 15 farm remain separate.
6. **Asset interchange**: conservatively repaired independent M31 OBJ with glTF 2.0 binary and original 512px procedural albedo, normals, AO and roughness outputs. This is not photoscanned skin, a final humanoid skeleton, or a finished character.

## Verified evidence

- `VEILFORGE M31 - Ultimate Human Anatomy and Skin` run [38890735339](https://github.com/timmytwopointoh/Project-hail/actions/runs/38890735339): all rig/skin preflight, four real reference model-angle jobs, and cross-variant director passed.
- Calibrated target correction run [38891164961](https://github.com/timmytwopointoh/Project-hail/actions/runs/38891164961): all geometry jobs and reference comparison passed. T-pose model span/height **1.00124**, uncalibrated image target **0.965**, difference **0.03624**; mean 10-slice absolute silhouette difference **0.06436**, measured relative to full model stature. Shoulder-row difference `-0.24975` is likely partly a vertical landmark/pose mismatch; do not let an automatic optimizer collapse shoulders based on this unverified anchor.
- Completed later run [38892230960](https://github.com/timmytwopointoh/Project-hail/actions/runs/38892230960): independent glTF 2.0 source artifact and all other M31 gates passed. **60,171 triangles**, **1,267 unresolved open boundary edges**, 0 detected nonmanifold edges or degenerates post conservative repair. Export not game-approved.
- Real M29 T-pose had **1,302** >3x-stretched triangle faces and **55** >10x; M30/M31 high-resolution has **146** >3x and **0** >10x, with zero leaking thigh and unchanged shorts (**88.79% reduction in >3x distortion**). Full relaxed pose 0 >3x. Mobile T-pose 67 >3x and 4 >10x: within the explicitly set numerical limits, **not an artistic or production rig approval**.
- M31 native Android app build and worker suite passed at [run 38890464007](https://github.com/timmytwopointoh/Project-hail/actions/runs/38890464007) and [worker run 38890464040](https://github.com/timmytwopointoh/Project-hail/actions/runs/38890464040). Earlier synchronized emulator test [38890464021](https://github.com/timmytwopointoh/Project-hail/actions/runs/38890464021) passed Pixel5 and Pixel6 but **failed Pixel4 material input and Pixel7 M31 view delayed-render gate**; still a blocker. Latest emulator verification [38891930803](https://github.com/timmytwopointoh/Project-hail/actions/runs/38891930803) was running when recorded and must be checked independently.
- Android screenshot tests now require current logged yaw AND updated **3D body pixels**, not only HUD changes or stale log state.

## Visual diagnosis against the T-pose reference

The user-generated T-pose is a natural muscular adult male, anatomically realistic hands, legs, feet, torso, eyes, jaw and skin. The current actual M31 offline mesh is **clearly not photorealistic**: the face is primitive/mannequin-like, muscle forms are overrounded, shoulders show unnatural volumes, arm/wrist connection is still rough, feet are rounded blocks and shorts have simplified topology. Small skin normal/pigment enhancements and a clean technical build cannot close that artistic gap. No likeness score has been established for the secondary three-quarter image.

## Next learning tasks to make the model visually convincing

- **Face retopology and source sculpt**: connected concentric eyelid and mouth loops, eye sockets with medically plausible placement, nose bridge/alae, coherent forehead cheek and mandible. Avoid adding floating colored plates. Required evidence: close front/profile/3/4 face views, normal/shading proof, controlled expressions.
- **Full-body sculpt**: replace SDF pill/blob deltoids and pectoral capsules with flowing clavicles, serratus, abdomen, hips, quadriceps, calves, tendons; corrected wrists/ankles and genuine toes. Constrain reference fitting to actual matched landmarks, not arbitrary pixel rows.
- **Rig deformation**: create real indexed vertex connectivity, bone indices and normalized bind weights or DCC/Blender skinning and retarget; final shoulder/elbow/hip/knee animation QA at T-pose, A-pose and moving frames.
- **Photoreal material**: real production UV islands, scan/reference-backed albedo, micro-normal/roughness maps, measured skin Fresnel/subsurface approximation and eye transparency/iris depth; current maps are **procedural only**.
- **Testing Grounds**: same SHA/APK on four Android 15 profiles, real 3D frame camera test, gameplay interaction, movement and performance; maintain both original armored hero and all unarmored comparison slots.
- All discoveries are recorded as reproducible learnings; **no endless autonomous modifying loops or source auto-merge**. Manual art and playable acceptance gates remain false.

This branch is a measured, reproducible improvement in **deformation safety, source evidence and reviewable 3D interchange**, not a claim that VEILFORGE has already achieved photographic realism.
