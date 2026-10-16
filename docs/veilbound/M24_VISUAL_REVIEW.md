# M24 full-body reference review and retained VEILFORGE lessons

## Ground truth
Reference: `image-gen-1(9).png` "Bellwarden Base Body Test" from the original unarmored character conversation. Main goals: natural anatomical proportions, authentic-looking adult male face, muscular chest/back/abdomen, shoulders/arms/legs, realistic five-digit hands and feet. Basic hair unchanged. Gameplay is the testing grounds; the original armored Bellwarden is an archive/Easter egg, **not a mesh we discard or overwrite**.

## Observed M24-01 baseline
Artifact: [38870225476](https://github.com/timmytwopointoh/Project-hail/actions/runs/38870225476) / `m24-anatomy-front_silhouette` / selected front, side, back, 3/4.
- All major anatomical regions physically exist, both hand meshes visibly have four fingers and one opposed thumb.
- Visually rejected as a final character: legs appear short, feet remain paddle/stump-like, arms and hands hang too low, deltoids/triceps are bulbous, pectoral/abdominal topology lacks natural muscle planes, head resembles a featureless mannequin. Existing procedural surfaces visibly facet in the offline software projection.
- Numeric proportion-score winners MUST NOT be approved for likeness on these results.

## Implemented correction (M24-02)
- `M24BodyRetarget` maps actual OBJ/GL mesh positions and normalized vertex normals: increases leg-to-body proportion, moves hands closer to mid thigh, shortens upper torso proportions while preserving overall stature. Also aligns the pose-preview bind-joint pivots.
- `M24BodyRetargetTest` checks leg height, hand pose anchor, normal validity, and unchanged source baseline.
- Offline four views after retarget show **materially longer-looking legs** and **more anatomically placed hands**, but head, foot/ankle transition, abdomen, shoulders and surface refinement are still visibly below the reference. Review-only, not photoreal.
- Gameplay remains the original knight, with historical viewer label; separate M24 full-body and deformation preview slots are for test, not production substitution.

## VEILFORGE topology lessons (actual pipeline evidence)
First asset bridge run 38870225476:
- Raw source: 1,094 boundary edges, 0 nonmanifold, 0 degenerate.
- First repair output: 132 boundaries, **7 new nonmanifold edges and 4 degenerate faces**; therefore rejected by VEILFORGE fail-closed guard.
- Root cause: candidate hole caps used planarity and positive area only, without guarding against existing/adjacent mesh incidences and nearly-degenerate quantized triangles.
Correction in `veilforge/topology.py`: validate every *complete proposed hole loop* against existing edge usages, duplicate signatures and quantized-area degeneracies **before** accepting its faces. Skip whole invalid loops; never modify input OBJ.
Verified run [38871081348](https://github.com/timmytwopointoh/Project-hail/actions/runs/38871081348):
- Raw candidate: **1,082** boundary edges, 0 nonmanifold, 0 degenerate.
- Corrected output: **452** boundary edges, 0 nonmanifold, 0 degenerate.
- 338 safe small-hole triangles inserted. VEILFORGE glTF 2.0 indexed binary and procedural skin maps exported. This is not fully closed topology and not an approved game-ready rig.

## Next specialized manager priorities
1. Face: eye socket depth, brows, lips, nasal silhouette, mandibular contour; realistic facial proportions. No hair work.
2. Feet: true heel, instep, arch, separate toes and ground contact, no club-like silhouette.
3. Torso: suppress swollen capsule muscles; sculpt coherent clavicle/pectorals/ribcage/rectus abdominal/serratus/obliques and scapula.
4. Arms: natural shoulder taper, elbow, forearm mass, real wrist/hand transitions and opposable thumb.
5. Deformation: actual moving pose comparison, correct transformed normals/tangents and weight painting; a finite reference CPU stress pose alone is not an animation-ready production rig.
6. Skin: finer UV and true tangent-space material/normal treatment; existing VEILFORGE skin maps are procedural placeholders, not pore realism.
7. Four synchronized Android 15 testing-ground emulators and physical handset performance. Compare stable old knight to new M24 preview to avoid gameplay regression.

## Approval policy
Up to 50 numeric candidate slots; no auto-promotion, no claims of photo-realism based on render-count or triangle count; no null screenshots. Keep actual four-angle screenshot cadence to once per day on meaningful new improvement or when requesting feedback. Require manual silhouette review and Android proof. Hair budget zero. 
