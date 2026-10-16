# VEYLQUORIN / VESPER V5 — Eight-worker surface and aura gate

**Source**: user-provided character sheet; V4 reviewed asset, refined locally to `Vesper_V5.glb`. Source, GLB, QA JSON and reproducible scripts are packaged in the current conversation's `Vesper_V5_Surface_And_Shader_Package.zip`. The binary V5 GLB has **not yet been committed or installed by the GitHub emulator workflow**.

## Actual local V5 geometry evidence

- GLB SHA-256: `fcb5c41e063ebc288e0eeec95da5ce4ad0eb54a840546a816eedc3bb6766b8cd`
- Triangles: **30,786**, identical to V4. Added GLB triangles: **zero**.
- Smoothed **4,867 existing vertices** across skin and clothing only using bounded pinned normal-direction Taubin lambda/mu. Maximum 0.00426131 m shift.
- **33 joints**, **7 animation clips**, **22 glTF material primitives** unchanged; UV coordinates, indices and weights unchanged.
- BaseColor/metallic/roughness factors tuned for deeper plum-black velvet, warmer natural skin, deep mahogany hair, restrained crimson irises, and softer violet accents.
- Eight-lane independent QV-compatible material audit: **22/22 primitives passed**, 30,786 triangles inspected; **zero** degenerate faces, incomplete vertex streams, bad weights or nonfinite positions. 164 open indexed edges and 14 nonmanifold indexed edges are **warnings** (layered garments/membranes are intentionally not watertight), not artistic signoff.
- Seven real skinned animation poses checked. Sample displacement: leg-up left foot 0.26977 m; dance left foot 0.21814 m; dance left ear tip 0.36708 m; dance right hair tip 0.25806 m.
- The local glow comparison and four-pose stage are CPU projections of the actual skinned mesh, **not Android screenshots**.

## Game-side change

On feature branch `feature/veilbound-vesper-playable-v1`, the Android renderer emits a Vesper-specific ring of 12 floating violet/magenta motes using the existing GLES2 octahedron primitive; no new GLB geometry, no new model triangles. This is a material-and-rendering effect (limited dark coloring, glow uniform, sine-orbit/bob). It appears in the pose stage when Vesper is imported and in gameplay when Vesper is selected. A debug-only synthetic GLB stage intent and an emulator screenshot/log smoke test verify the effect draw path without altering the original Bellwarden character.

The most recent base Android run before the new debug inspection was [#38922786400](https://github.com/timmytwopointoh/Project-hail/actions/runs/38922786400) (successful). New native effect-stage run [#38923610912](https://github.com/timmytwopointoh/Project-hail/actions/runs/38923610912) must be checked for completion. Its fixture is a *two-joint triangular test*, **not** the full V5 GLB.

## Blocking release gates

1. Stage the **full V5 binary GLB** in an actual Android APK or import it through the device file picker, then capture front/side/back and idle/walk/leg-up/dance screenshots, checking ear and hair movement. No claim of such a test yet.
2. Compare geometry to original reference facial silhouette and hair volumes with calibrated camera, not just triangle counts.
3. Check skin and clothing deformation boundaries, 14-angle visual QA, actual GPU cost, smooth transitions and FPS on target hardware.
4. Require user visual approval before promoting assets into production/gameplay.

**No auto-merge.** The user can still import the separate V5 GLB manually to the Atelier while staging automation improves.