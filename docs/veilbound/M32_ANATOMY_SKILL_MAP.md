# VEILFORGE / VQ M32 — Human Anatomy Perfection Study

This is an **experimental actual full-body character iteration**, not a claim of finished photorealism. VEILFORGE/VQ remains the reusable asset authoring engine; Veilbound remains the Android **Testing Grounds**. The original armored Bellwarden, all M20–M31 anatomy candidates, existing gameplay, shorts and basic hair are preserved. Human visual acceptance and live-game promotion are deliberately disabled.

## Reference targets

The user's front/back, 3/4, T-pose and relaxed studio references describe one intended adult athletic man. The latest recorded silhouette target is `veilforge/human_reference_targets.json`; the repository does not contain the original image bytes, and no pixel-perfect calibrated correspondence has been claimed. Original photos must be added to the engine only when explicitly authorized, with pose-aligned annotations.

## M32 hierarchy — real tasks and failure gates

| Worker | Implementation | Tests and acceptance |
|---|---|---|
| **Anatomy director** | `HumanAnatomy.buildM32Candidate` based on exact M31 source | Prior milestones load; vertex colors and unchanged game stay intact; no automatic promotion |
| **M32A Clavicle/shoulder** | `M32ShoulderRig.pose` with M30 bounded humerus weights and a separate gentle clavicle/scapula elevation zone | Exact T-pose armspan, torso and shorts stable, multi-angle armpit contour, rig strain <260 triangles above 3x and <18 above 10x |
| **M32B Face** | `M32AnatomySurface.sculpt` Gaussian cheek, jaw and nasal bridge shifts, analytic surface-normal propagation | Both sides move symmetrically; pupils/irises/hair unmodified; front/side/3/4 closeups; no fake detached features |
| **M32C Hands** | Local MCP knuckle and thumb-base surface corrections on the existing real 5-digit-per-side finger model | Four independent fingers and opposed thumb per side, accurate palm and wrist silhouettes, strain-safe T and relaxed poses |
| **M32D Feet** | Real underfoot arch elevation, heel transition and interdigital contour changes | Compare low side view, heel, arch and toes on both feet; no block-foot regression or dropped triangles |
| **VQ sculpt inspector** | Updated `vq_model_tools.py` actually reads each M32 OBJ, checks UVs, true geometry, masks, and 14 source-mesh camera angles | Detect collapsed UV, missing images, nonmanifold/degenerate geometry; no source model overwritten |
| **VQ bounded brush + remesh** | Latest `vq_brushes.py` and `vq_adaptive_remesh.py` are available for separate candidate studies only | Source UV/material ID and history preserved, no uncontrolled seam motion, topology budget reviewed manually |
| **VQ worker manager** | `veilforge-m32-human-anatomy.yml` 4-specialist bounded parallel matrix (shoulder, face, hands, feet) | Actual high-detail OBJ, 14 actual mesh angle renderings, six closeup hand views, three head views, source SHA, semantic angle checks |
| **Android Testing Grounds** | Optional viewer slots 22–24: M32 neutral, T-pose, relaxed; lazy load exact native renderer | Original playable knight unchanged, four angles, both detail levels, full character and hand/face/foot reviews; four-emulator Android 15 farm independently verified |

### Training records and lessons

- M29 T-pose admitted approximately 1,302 faces stretched more than 3x; M30 reduced this to approximately 146 at high detail. The new M32 clavicle rig must not reintroduce thigh-to-armpit tension or move shorts.
- Raw M31 facial feature components and feet still have known imperfections and over 1,000 unclosed topology boundaries. Local smoothing/geometry corrections are **not connected facial retopology**; true eyelid and lip edge loops, toe meshes, weight painting and UV atlas authoring remain necessary.
- Earlier T-pose reference measurement accidentally used foreground pixel COUNT instead of horizontal left/right pixel SPAN, producing incorrect lower-body proportions. Never optimize on faulty camera/reference data.
- VQ M29's conforming adaptive remesher, PBR material-preserving glTF export, UV and silhouette inspector and bounded sculpt brush library have been imported without modifying the old game or claiming artistic acceptance. Real 3D diagnostic views are separate from actual Android OpenGL screenshots.
- Technical quality, numerically low strain and camera integrity are necessary conditions, not a guarantee of photographic anatomy.

### Acceptance status and current behavior

M32 is always **review-only**. Four-specialist geometry jobs and native Android test runs require a green check **on the latest commit** before technical success can be claimed. The old knight remains playable and remains a collectible history artifact. The artist/user has final control of if/when the human is promoted.

### Next substantial realism milestones

1. Topology truly connected at facial orbital/lips/nose, shoulder/deltoid joint and toes, with exact bind weights and UV layout.
2. Reference-calibrated full-body front/profile/3/4 landmark annotation and human-perceived likeness critique across motion, not proxy thresholds only.
3. Multi-layer scanned/painted PBR skin, fine wrinkles/nails and convincing eye cornea/sclera/iris, rather than only algorithmically tiled pores.
4. Motion and performance qualification across all Android devices, no invalid model substitutions or gameplay regressions.
