# M32 VEILFORGE/VQ — Verified Anatomy Lessons

The user reference is the intended realistic adult male in a T-pose and a relaxed studio pose. This file records actual mesh outputs, not aesthetic perfection claims. Preserve the historical armored Bellwarden, hair and game.

## Proven technical execution

- [M32 anatomy worker run 38897287730](https://github.com/timmytwopointoh/Project-hail/actions/runs/38897287730): four independent specialty lanes for shoulders, face, hands and feet passed. Neutral human has **59,679 triangles, 0 nonmanifold edges, 0 degenerate faces, ~2,259 open boundary edges**.
- [VQ brush/remesh run 38898226859](https://github.com/timmytwopointoh/Project-hail/actions/runs/38898226859): actual M32 neutral source 59,679 triangles -> separate VQ-refined diagnostic mesh 59,979 triangles with 150 conforming interior edges subdivided; 14 actual mesh views; topology checks passed. No game replacement or artist approval.
- [Pose-aware hand camera run 38898463220](https://github.com/timmytwopointoh/Project-hail/actions/runs/38898463220): corrected old cropped/finger-only fixed hand screenshots. Camera bounds now follow selected actual palm, thumb and four digits in neutral and raised pose.
- [Android 15 farm run 38898171872](https://github.com/timmytwopointoh/Project-hail/actions/runs/38898171872): Pixel 4 passed native M32 model inspection and generated neutral, T-pose front/side/back/3/4 and relaxed game screenshots. Other selected device jobs were canceled and overall farm FAILED, so four-device validation remains outstanding.

## Visual findings and M32 corrective

- T-pose shoulder/armpit silhouette **still visibly pinches**, despite improved independent clavicle/humerus movement and safe measured strain. Pose-space underarm contour correction was added for a fresh before/after test; it does not constitute painted bone weights.
- Face remains mannequin-like: eye sockets, eyelids, nose, lips, cheek and jaw need real connected deformation topology, not extra floating patches or only shader effects.
- Hands now visibly present with separate thumb/fingers. Knuckle and web contours, lengths, nails and wrist require finer sculpt/skin-weight construction.
- Feet remain blunt/block-shaped, with inadequate visible toe/arch geometry. Small bounded arch and toe-gap adjustments are an early step, not final foot anatomy.
- Source reference pixels have not been committed as camera-calibrated annotation; numeric body-fit score is advisory.

## Repeatable VQ skill procedure

1. Keep M31 and playable historical knight immutable. Build M32 neutral/raised/relaxed candidate meshes.
2. Verify connected-shape normal validity, two LODs, ten digits, original hair/shorts colors, ribcage and thigh displacement limits, strain and topology.
3. Render real 14-angle source triangles plus 3 face and 6 hand close-ups, with SHA of source and each evidence image.
4. Run VQ source-preserving brush/smooth and conforming adaptive remesh in **isolated candidate artifact**. Reject nonmanifold/degenerate/open-edge regression and never auto-promote.
5. Compare body, true shoulder, facial profile, hands and foot silhouettes against the user reference manually; append grounded failures to the learning ledger rather than inventing positive aesthetic scores.
6. If candidate passes visual review, verify a real Android 15 APK on all emulator profiles, body pixels and yaw, performance and gameplay. A single Pixel 4 success is not the entire farm.
7. Release only by separate, approved PR. Earlier models remain inspectable in the Testing Grounds.

The M32 work is a meaningful technical improvement and learning system, **not yet a photorealistic human or final production rig**.
