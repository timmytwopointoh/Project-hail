# VEILFORGE M29 — Adult Male Reference Pose and Skin-Fidelity Study

## What we're building

VEILFORGE is the reusable asset/sculpt engine; Veilbound is its **Testing Grounds** for native Android 15, 3D pose, materials, geometry, lighting and playable regression tests. The original armored Bellwarden knight stays unchanged and visible as a historical Easter egg. Hair is frozen.

The user's new modeling reference set includes the original Bellwarden Base Body Test, a more polished front/back male reference, a side/three-quarter facial sheet, a **true forward-facing T-pose**, and a **relaxed three-quarter standing pose**. The character is an athletic adult male with believable skin, anatomical mass transitions, defined eyes, face, hands and feet, basic short dark hair, and plain dark shorts.

**Critical provenance limit:** The generated conversation image files are not committed or accessible as machine-readable pixel assets in this repository. We can use the established visual descriptions and pose types, but **cannot truthfully claim machine-computed image-to-mesh fitting or likeness percentages**. Future validated pixel correspondence requires those original images to be added as approved image assets, with rights/provenance, crop coordinates, and landmarks annotated. Avoid storing private conversation screenshots without permission.

## Real implementation

- `M29ReferencePose` computes physically different geometry for true symmetric outstretched T-pose and a relaxed three-quarter reference with shoulder/leg articulation. The unchanged M28 body and its exact ten digits are reused. The retargeted shoulder and hip pivots are checked, but this remains a preview study, not approved animation skinning.
- `M29SkinAtlas` generates a deterministic, tileable 128×128 RGBA skin-detail source. RG: subtle micro-normal slopes; B: matte roughness; A: low-frequency pigmentation. This is **procedural reference texture**, not photoscanned pores.
- The Android OpenGL renderer lazily uploads one small skin material texture on entering the unarmored model viewer; fragment shading applies it only to flesh pixels and leaves eyes with their own gloss ranges. It does not change the armored hero's gameplay material or starting performance.
- Separate studio slots: M28 baseline facial anatomy, M29 T-pose and M29 relaxed standing pose, each with front/side/back/three-quarter cameras and mobile/high detail mesh switching. The OBJ import slot remains last.
- Existing `HumanVariantCLI` exports actual source triangle meshes and 14 orbit views for M28, M29 T-pose and M29 relaxed, plus six hand and three face closeups per pose.
- Dedicated GitHub Actions creates real source OBJ and geometry reports for all three pose types simultaneously, followed by a manager review artifact. Fail on nonfinite/invalid normals, geometry budgets, missing views, broken digit invariant, nonmanifold and degenerate geometry. Human visual approval remains false.

## Quality priorities for attaining realism

1. **Reference alignment:** compare exact front/profile/three-quarter images from the supplied T and relaxed reference once pixels are available. Human-marked landmarks: pupils, ear centers, chin, shoulders, elbows, wrist, hip, knee, ankle, heel and toe; normalize to stature and evaluate pose-space angles, symmetry and A/T pose consistency.
2. **Anatomical retopology:** the current M28 face has orbited curved eyelid geometry and altered skin but still unresolved open edges. Add connected eye socket and lip loops; do not hide invalid topology with visual textures.
3. **Muscle structure:** high-frequency details do not replace deltoid/pectoral/abdomen/quad/foot geometry. Prioritize connected mass transitions while retaining readable fingers and feet.
4. **Materials:** upgrade from original procedural atlas to reference-authored UV-aligned PBR skin, measured roughness and subtle normal maps when actually available. Evaluate under STUDIO/MOON/EMBER/RIM lighting; never call current tiling atlas photographic.
5. **Animation:** T-pose establishes useful open-arm geometry; secondary relaxed pose checks shoulders, hip weight shift, wrist orientation. Run real walking and limb deformation and verify no clipping.
6. **Android and performance:** same APK SHA across four Android 15 emulator profiles; preserve responsive gameplay. M28 Pixel 6 had an unresolved *frozen M24 motion* screenshot test while the other three profiles passed. This remains an independent regression gate.

## Workers and promotion boundaries

Four review lanes: **face/topology**, **body silhouette**, **skin materials**, and **rig/Android QA**. Candidate loops stay finite per triggered GitHub workflow; current comparisons generate one M28 base and two real M29 pose meshes. VEILFORGE M26 lesson ledger and M27 non-destructive sculpt layers are available, but M27's triangle-center stone/terrain erosion is deliberately not applied indiscriminately to deforming facial skin.

No user-visible result should claim success until the relevant GitHub Actions result is complete. Never replace the armored knight or auto-merge the candidate. All generated renders should be labelled offline or Android as appropriate.

## Current target status

- Native Android and geometry checks: pending latest M29 jobs.
- Photoreal source material and final rig: **not yet achieved**.
- Visual reference similarity: requires actual reference image bytes and explicit manual/landmark review.
- Hair: out of scope, unchanged.
