# Vesper — reference-driven quality and integration gate (review only)

**Reference:** user-provided full character design sheet, Vesper (adult bat-themed chibi) with front/left/back/right, expressions, and clothing variants. The sheet is the visual target; the 3D model is original geometry.

## Actual model revisions
- V1: GLB skinned 3D character, 19,874 triangles, 10,201 indexed vertices, 22 material primitives, 33 joints and four clips.
- V2: GLB skinned 3D character, 24,082 triangles, 12,479 indexed vertices, 22 material primitives, same 33 joint hierarchy and four clips.
- V2 work: narrower anime eyes, more detailed face-framing curls, individual fringe/strands, modest layered skirt/peplum, glove and stocking details, refined ear tips.
- Both preserve independent ear base and tip bones, hair segment bones, wing and tail bones. Animation is keyframed, **not** verified physically simulated spring bones.
- Independent local glTF/mesh checks reported 0 degenerate faces under 1e-9 square meters, 0 non-finite vertex coordinates, UV present on all 22 material primitives, and 14 geometry previews. These metrics do **not** establish likeness.

## Android implementation
- On `feature/veilbound-vesper-playable-v1`, VesperGlb.java parses bounded GLB 2.0, skinning and idle/walk clips, converting them to eight sampled frames per clip for the established GLES2 mesh renderer.
- Model Atelier lets the user import the actual Vesper GLB via Android document picker, then choose PLAY AS VESPER; original Bellwarden remains default/fallback.
- Baseline Android 15 build and original game smoke run `38913284008` completed successfully. That run **did not** import Vesper.
- A tiny separate two-joint synthetic `vesper_import_smoke.glb` fixture verifies Android GLB/skin parse+sampled animation on a subsequent full emulator workflow. Fixture is **not** the supplied Vesper.
- Actual Vesper Android QA requires real V2 asset availability on emulator, front/side/back game screenshots, idle/walk ear deformation, frame-time, and reference-aware evaluation.

## Required improvement queue (ranked)
1. **High:** exact front/side facial and hair silhouette reconstruction (current V2 is still notably too toy-like, eyes overly geometric; curls and fringe under-specified).
2. **High:** official VQ compare with calibrated pose-matched 2D masks and multi-view image segmentation rather than unsupported similarity claims.
3. **High:** ship/import actual revised Vesper GLB on emulator; capture 14 orbit views plus idle/walk ear/hair test and ensure no UI clutter.
4. **High:** ear springs using a stable bounded critically damped response with base and tip joints plus motion-based lag. Validate no inversion/exploding movement; keep keyframe fallback.
5. **Medium:** rigged gothic outfit layering, bow/ribbon geometry, necklace, legwear, hair ornaments; add alternative costumes only after V2 base reaches likeness acceptance.
6. **Medium:** dedicated UV atlas, facial gradients and soft shaded materials; glTF/GLB texture and normal import support (current game renderer uses mesh vertex colors).
7. **Medium:** neutral/happy/excited/laughing/surprised/angry/sad/worried/flirty/sleepy expression blendshapes.
8. **Before release:** animation deformation, geometry topology, material seam and LOD checks; measured target-device FPS and user artistic signoff.

## No unverified completion
A green build or baseline emulator does NOT mean the Vesper GLB has appeared in the actual game. Likewise 24k triangles do not imply final source-art quality. Keep this PR draft until the V2 GLB is imported in an emulator, seen in real screenshots, its animation deformation tested, QA passed, and reference likeness approved by the user.

The local download package `Vesper_Refined_V2_Game_Package.zip` contains the reproducible V2 GLB, source generator, OBJ, 14 views and audit; it is **not yet** checked into the repository as a binary asset. The APK's file picker intentionally requires the supplied GLB file.
