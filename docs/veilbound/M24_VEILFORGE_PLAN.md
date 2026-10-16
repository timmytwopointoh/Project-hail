# VEILFORGE M24 — Reference human and full-body gameplay test

## Source of truth and roles
- Original reference: user-provided `image-gen-1(9).png` / Bellwarden Base Body Test. Athletic, realistically proportioned adult man in simple modest shorts; broad anatomically convincing shoulders; well-developed but not superhero-inflated chest, abdomen, back, arms, glutes, thighs and calves; credible face, hands and bare feet. No attempt to copy non-reference clothing/props.
- Hair is frozen entirely; unchanged basic hair and **zero hair refinement budget** until user asks otherwise.
- VEILFORGE is the reusable character/asset engine. VEILBOUND is the **VEILFORGE TESTING GROUNDS** for real animation, renders, import, combat-play performance and regression.
- Preserve playable armored Bellwarden hero and level intact. Existing original knight remains accessible in the model viewer, labeled as a historical Easter egg. No automatic hero replacement.
- Geometry origin: M23 controlled `ContinuousHuman` + physically separate `HumanHandSculpt` digits. M24 introduces additive SDF volumes across entire body; never touch baseline HumanAnatomy.build().
- VEILFORGE tooling pinned to `feature/veilforge-asset-engine-v1` at `b08a4ada9b4b3b3df1cdaa4547a5dcb8a7f1bb14`. Vendored tools: `engine.py` mesh+PBR, `topology.py` conservative cleaning, `gltf_export.py` interoperability, `manager.py` review; independent tests included.

## Work partition — 50 candidate slots
One isolated run, 10 regional anatomy managers, 5 deterministic candidate slots per manager, each evaluating 64 bounded numeric micro-edits. Regions: front silhouette, side silhouette, skull, jaw, shoulders, torso, pelvis, hands/forearms, thighs/calves, feet. These are candidate generators, not 50 simultaneous AI minds. Numeric scores are rank hints only. 14 mesh angles plus both-hand closeups and manual human review remain mandatory.

## Geometry work and acceptance
- Anatomical silhouette and body ratio matching to the provided picture precedes skin shading detail.
- Refine pectoral/ribcage transition, abdominal and oblique mass, scapula/erector muscles, deltoids/biceps/triceps/forearm, pelvic/glute/upper thigh insertions, quadriceps/knees/calves/Achilles and foot arch/toes, cranium/jaw/cheeks/brow.
- Exact digit constraints: 4 separated mesh fingers plus one opposed thumb PER hand; both hands, all camera angles, open web gaps, knuckle transition.
- Preserve stable high and mobile LODs. Run normals, UV, topology, duplicate/nonmanifold edges, seam and material checks. VEILFORGE cleanup is **offline only**, not applied to game meshes without manual review.
- VEILFORGE procedural skin maps are **placeholders** not photorealistic skin. GLTF exports are unrigged reference interchange, not Android-ready game packs.
- M24 deformation preview is a separately viewed **test pose** in testing grounds using existing 15-joint CPU weighting. No production quality claim; investigate normals and real joint-pinch artifacts visually.

## How to measure real progress
1. Establish M23/M22 baseline: known smooth gameplay, legacy hero unchanged. Verify play, camera, combat and performance first.
2. Make M24 candidate anatomy and independent VEILFORGE export; inspect actual geometry.
3. Run 50-slot worker matrix with per-team journals and original reference-aligned proportion priors; manually assess at least front/side/back/3/4 and closeups, reject unnatural silhouettes and poorly modeled feet/face.
4. Reconcile only accepted cross-region changes into one integrated M24 candidate; **do not auto-promote** the proxy-scored winner.
5. Run actual in-game Android 15 at the same APK SHA over four synchronized emulators; capture actual four-angle unarmored human, hand and deformation screenshots. Compare gameplay scene and animation against prior smooth baseline; fail on regressions.
6. Publish only verified screenshot evidence and honest defects; one meaningful verified four-angle set per day or on review request.
7. Preserve original playable knight and Easter egg slot throughout development; attach armor to the improved human only after anatomy/rig is ready, explicitly reviewed and regression-tested.

## Current acceptance state
This branch is a **review candidate**. Geometry code and VEILFORGE workflow were implemented. Until each job returns success and visual evidence is inspected, no claim of photorealism, approved retopology, realistic deformation, or playable human replacement is justified. Worker candidate outputs never edit project source.
