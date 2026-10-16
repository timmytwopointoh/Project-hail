# VEILFORGE M25 — Face, Surface, Material and Alignment Refinement

Target reference: `image-gen-1(9).png` ("Bellwarden Base Body Test"), the user-provided concept sheet showing a realistically proportioned athletic adult man. M24 is our gameplay-testing baseline; VEILFORGE remains the model-and-asset engine. The original armored Bellwarden remains intact as a playable history piece and Easter egg. Hair is frozen.

## Four independent manager groups, subordinate review lanes
- **Face**: real left/right eye geometry, iris/pupil visibility, eyelid/brow profile, nose/nostril and lips, bilateral side/three-quarter consistency. Use `M25FaceSculpt`, M25 face camera, and original full-body SDF.
- **Soft tissues**: continuous SDF blend radius changes for torso/shoulder/knees. Preserve separated fingers and toes; clean up bulges without shrinking anatomical contours to a featureless mannequin.
- **Materials**: `M25SkinPolish` changes only confirmed skin vertex colors; the native shader uses soft continuous tonal breakup, matte skin, controlled eye gloss. It must never alter hair, modest shorts, historic armor or the playable hero, and must not claim photographic pores.
- **Alignment and rig**: `M25AttachmentAuditTest` measures eye, shoulder, wrist, hip and ankle anchors in actual mesh coordinates under four rotations; verify symmetric joint locations. Pose/rig deformations remain testing-ground only. An internal anchor check does not certify future armor-piece or third-party plugin placement, which still requires graphical review.

Ten anatomical manager lanes each generate five bounded numeric candidates with existing worker code: front silhouette, side silhouette, skull, jaw, shoulders, torso, pelvis, hands/forearms, thighs/calves and feet. The top-scoring proxy is only a *candidate for visual inspection*, never the approved character. All ten lanes must export 14 genuine 3D viewpoints plus six hand views and three face closeups.

## Core source
- `ContinuousHuman.buildM25WithoutDigits`: selective smoother signed-distance unions, with tight face/toe radii and finger preservation.
- `M25FaceSculpt.build`: 3D sclera, irises, pupils, eyelids, brows, nostril accents and subtle lips. Not a finished facial rig.
- `M25SkinPolish.apply`: subtle albedo variation with unmodified hair, clothing, armor.
- `HumanAnatomy.buildM25Candidate`: preserve baseline `build` and `buildM24Candidate`, compose M25 and retarget without changing player model.
- Model Atelier item 11 remains the unarmored human; item 14 is M25 full-mesh face closeup with calibrated front, side, back and 3/4; original Bellwarden retains item 0.
- `HumanVariantCLI`: true triangle-based OBJ plus 14 orbit previews, both hand closeups and front/profile/3/4 face closeups.
- `VEILFORGE` topology and glTF/PBR outputs are separate unapproved export candidates until reviewed; maintain the fail-closed repair rules learned from M24.

## Acceptance gates
1. Pure Java face/skin tests: symmetric eyes/iris/pupils, real geometry count, high/low detail integrity, exact five fingers+thumb on each hand, unmodified baseline/knight, nonfinite and normal safety.
2. Attachment axes: head, wrist, shoulder, hip, ankle anchors. Surface-distance checks distinguish a joint *inside* the tissue from an external floating prop. Actual socket/armor fixture placement requires visual validation.
3. Screenshot evidence: actual Android 15 on a single synchronized APK across four emulators, with four face angles, one detail shot, full human and motion pose, unchanged gameplay. A screenshot is only evidence when file and run are verified.
4. VEILFORGE export: no unacknowledged nonmanifold or degenerate output, preserve source OBJ, identify remaining open edges.
5. Manually inspect face angle match to concept reference, eyes not floating, correct shadows, muscle flow and natural skin. Never declare photorealism based on a code test.
6. Do not merge into playable mainline automatically. One substantial verified screenshot set per day or by user request. No background work promise beyond actual CI triggers.

## Status
M25 is an experimental, independent review branch. Real geometry/material code is committed; this document is not proof of visual acceptance or Android runtime success. The stable game and historical armored knight remain unchanged.
