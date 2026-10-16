# Vesper V4 — rig-safe merge, pose stage and costume embellishment

Reference: original user-supplied 2D multi-view Vesper sheet; **no likeness signoff yet**.

## Actual generated candidate

- `Vesper_Base.glb`: glTF 2.0 skinned character from reproducible local V4 generator; 33 joints.
- V4 indexed triangles: **30,786** after conservative edge collapse, versus 31,320 before V4 collapse; 267 eligible edges collapsed, removing **534 triangles** in compatible skin and cloth/boot submeshes.
- Material/pinned-edge-aware Taubin smoothing remains active. The operation does **not** cross material boundaries, unwrap new UV islands, replace rigs, or decimate the character's highly visible eye, ear, hair, or wing geometry.
- Costume additions: corset chevron embroidery, small waist jewels, gilded chain, patterned stocking motifs.
- Animated GLB contains seven clips: `Idle_Bouncy_Ears`, `Walk_Springy`, `Ear_Wiggle`, `Hair_Sway`, `T_Pose_Review`, `Cute_Leg_Up`, `Cute_Dance_Shuffle`.
- Offline actual skinned-geometry movement checks: raised left foot +0.26977 m maximum from idle, dance foot 0.21826 m, dance left ear tip 0.36708 m, dance right hair tip 0.25806 m; clip rotation and position data are in GLB.
- 14 diagnostic orbit views, four pose-specific actual 3D CPU preview frames, geometry manifest, merge QA, smoothing QA and reproducible Python source in downloadable project-conversation V4 package.
- Standalone `Vesper_V4_Interactive_Pose_Stage.html` provides working buttons to inspect the baked 3D pose previews offline. It is **not** a live 3D renderer.

## Android integration (draft PR #24)

`ModelStudio` accepts 4 pose selections, the native HUD renders `IDLE`, `T-POSE`, `LEG UP`, and `DANCE` buttons for the imported-character slot, while preserving the existing controls elsewhere. `VesperGlb` now optionally reads these clips and prepares CPU-skinned meshes for selected studio poses. Legacy V3 GLB and two-joint synthetic fixture continue to work without new pose clips. Import remains via the Android document picker; no automatically embedded full V4 GLB has yet been used in Android CI.

The pipeline must still **verify the full V4 GLB on a real Android emulator**, inspect smoothing/cloth collisions in raised-leg/dance frames, check temporal smoothness, and obtain user approval before merging or replacing Bellwarden.

Technical testing is distinct from reference-likeness or production approval.
