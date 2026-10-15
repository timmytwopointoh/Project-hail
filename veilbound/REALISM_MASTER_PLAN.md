# VEILBOUND — REALISM TRANSFORMATION MASTER PLAN

**Base:** v0.9.0, Android native OpenGL ES 2.0, offline, deterministic assets, GitHub Actions emulator.
**Principle:** no assumption that a procedurally upgraded scene is photorealistic. Level of realism must be judged from actual captured screenshots and physical-device play. Borrow *principles*, not protected assets or animations: layered fallen architecture and fog depth (soulslike exploration), readable anticipation and impact (Sekiro-like combat), material storytelling from wear and age. See Khronos glTF metallic/roughness reference at https://www.khronos.org/gltf/pbr.
**Baseline observed:** block-shaped repeating paving, small rigid character articulation, white / unlayered surfaces, studio PBR isolated from gameplay; successful Android15 screenshot QA, but software GPU FPS sometimes <8.
**Non-negotiable:** preserve existing controls, combat, offline play, working atelier, native build and simulator tests. All assets original or properly licensed, source-backed, never imported gameplay screenshots from other titles.

## 140-item asset and render inventory
Each checkbox is a *specific* planned improvement, **not** a claim of completion. Items are marked only as tested. Each group includes distinct scope, test evidence and rollback in Git.

### 01 Character silhouettes (1–10)
- [ ] 001 Hero anatomy ratios and posture
- [ ] 002 Enemy scale consistency
- [ ] 003 Boss head and horn proportions
- [ ] 004 Boot-to-ground alignment
- [ ] 005 Hands positioned at sword grip
- [ ] 006 Layered armor shell thickness
- [ ] 007 Cloth outline asymmetry
- [ ] 008 Helmet face-plate depth
- [ ] 009 Readable damage silhouette
- [ ] 010 Distance LOD handoff

### 02 Character surfaces (11–20)
- [ ] 011 Steel roughness map
- [ ] 012 Leather grain and seams
- [ ] 013 Woven tabard cloth
- [ ] 014 Brass patina
- [ ] 015 Gilded engraving
- [ ] 016 Bone surface treatment
- [ ] 017 Weathered armor edges
- [ ] 018 Dirt near boot hems
- [ ] 019 Emissive foe eyes
- [ ] 020 Material consistency across closeup/gameplay

### 03 Character motion (21–30)
- [ ] 021 Idle breath phase
- [ ] 022 Exertion breath rate
- [ ] 023 Guard pose
- [ ] 024 Movement blend
- [ ] 025 Attack anticipation
- [ ] 026 Weapon impact timing
- [ ] 027 Hit reactions
- [ ] 028 Recovery followthrough
- [ ] 029 Dodge crouch
- [ ] 030 Foot planting

### 04 Combat VFX (31–40)
- [ ] 031 Contact-aligned hit sparks
- [ ] 032 Blade motion streak
- [ ] 033 Green blood spray
- [ ] 034 Floor stains
- [ ] 035 Blood dispersion scaling
- [ ] 036 Surface splatter decal fade
- [ ] 037 Foe recoil
- [ ] 038 Target reticle depth
- [ ] 039 Camera lock easing
- [ ] 040 Boss attack warning

### 05 World geology (41–50)
- [ ] 041 Ground elevation variation
- [ ] 042 Flagstone geometry variety
- [ ] 043 Stone chip corners
- [ ] 044 Mortar gap values
- [ ] 045 Missing flagstone patterns
- [ ] 046 Rock outcrop sculpt
- [ ] 047 Ash-soil palette
- [ ] 048 Moss distribution
- [ ] 049 Erosion channels
- [ ] 050 Distant rock silhouette

### 06 Buildings (51–60)
- [ ] 051 Chapel stone courses
- [ ] 052 Broken lintels
- [ ] 053 Funeral spires
- [ ] 054 Arches with keystones
- [ ] 055 Windows recessed depth
- [ ] 056 Gate ironwork
- [ ] 057 Crenellation rhythm
- [ ] 058 Rubble debris clusters
- [ ] 059 Foundation stones
- [ ] 060 Distinct landmark silhouettes

### 07 Foliage (61–70)
- [ ] 061 Tree taper variation
- [ ] 062 Root flares
- [ ] 063 Secondary branches
- [ ] 064 Dead ivy tendrils
- [ ] 065 Leafless twig breakup
- [ ] 066 Sedge silhouettes
- [ ] 067 Thorn bushes
- [ ] 068 Fungal clusters
- [ ] 069 Moss clumps
- [ ] 070 Wind motion policy

### 08 Set dressing (71–80)
- [ ] 071 Grave markers variation
- [ ] 072 Censer hangings
- [ ] 073 Tomb slabs
- [ ] 074 Iron reliquaries
- [ ] 075 Metal fence elements
- [ ] 076 Scattered pottery
- [ ] 077 Rope lashing
- [ ] 078 Broken bell shards
- [ ] 079 Pilgrim cairns
- [ ] 080 Ember braziers

### 09 Lighting (81–90)
- [ ] 081 Directional key angle
- [ ] 082 Moon fill color
- [ ] 083 Localized ember glow
- [ ] 084 Diffuse ambient
- [ ] 085 Metal specular response
- [ ] 086 Roughness energy balance
- [ ] 087 Fresnel rim
- [ ] 088 Shadows / occlusion strategy
- [ ] 089 Color grading and saturation
- [ ] 090 Avoid overexposed metal

### 10 Atmosphere (91–100)
- [ ] 091 Distance fog ramp
- [ ] 092 Ground mist depth
- [ ] 093 Sky/moon contrast
- [ ] 094 Volumetric-like light streaks
- [ ] 095 Ambient floating motes
- [ ] 096 Heat flicker
- [ ] 097 Far-scene atmospheric perspective
- [ ] 098 Dusk palette
- [ ] 099 Depth separation
- [ ] 100 Night visibility readability

### 11 Assets and studio (101–110)
- [ ] 101 Asset registry naming
- [ ] 102 World prop scale calibration
- [ ] 103 Studio model cycler
- [ ] 104 Material variation
- [ ] 105 Lamp light preset
- [ ] 106 Studio high-detail comparison
- [ ] 107 Low-detail asset inspection
- [ ] 108 Turntable view
- [ ] 109 Profile screenshot capture
- [ ] 110 World placement inspection

### 12 Runtime efficiency (111–120)
- [ ] 111 Draw-call batching
- [ ] 112 Static model instancing by merge
- [ ] 113 Distance-based LOD
- [ ] 114 Limit texture sampler count
- [ ] 115 Limit atlas GPU budget
- [ ] 116 Avoid runtime mesh rebuilding
- [ ] 117 Cull offscreen effects
- [ ] 118 Avoid overdraw
- [ ] 119 Hardware profiling
- [ ] 120 Fallback quality setting

### 13 QA and accessibility (121–130)
- [ ] 121 Automated Java geometry checks
- [ ] 122 Finite normals
- [ ] 123 Triangle/material validity
- [ ] 124 APK install smoke
- [ ] 125 GL error sampling
- [ ] 126 Screen captures
- [ ] 127 Visual difference gate
- [ ] 128 Performance baseline
- [ ] 129 Lock-on touch test
- [ ] 130 MOTO G field test

### 14 Later photoreal content (131–140)
- [ ] 131 Artist-authored hero retopology
- [ ] 132 PBR UV unwrap
- [ ] 133 Photogrammetry or CC0 textures
- [ ] 134 Physically based lighting calibration
- [ ] 135 Dynamic shadow maps
- [ ] 136 Skeletal skinning
- [ ] 137 Motion-captured locomotion
- [ ] 138 Animation state transitions
- [ ] 139 Particle pool and soft particles
- [ ] 140 Performance/thermal field profiling

## Milestones and acceptance gates

**M10 / foundation (now):** inspector-grade original prop assets (flagstone, cenotaph, reliquary, root cluster), world placement as a static batched mesh, repaired repetitive paving, consistent material lighting in gameplay, measurable QA loop. Keep a control screenshot pair and report asset counts and edge/brightness differences.
**M11 / cinematic material authoring:** per-part steel/leather/cloth texture sets, physically-based roughness and controlled specular, character topology improvement and per-vertex material channels, stage and world close-ups.
**M12 / physical space:** moon shadows (GPU-budget conditional), water/wetstone, light fixtures, layered volumetric fog, sky, believable destruction, grounded surface occlusion.
**M13 / character performance:** proper bone skinning, foot IK, acceleration/deceleration, cloth secondary motion and reactive contact effects.
**M14 / content and optimization:** revised encounter spaces and architecture; QA against real Motorola G 2025 hardware, adaptive quality, thermal checks and consistent 30+ FPS objective, release candidate.

**Loop for every milestone:** 1) inspect actual baseline images 2) choose limiting issues 3) modify source and asset kit 4) Java geometry test 5) compile Android 6) run real emulator navigation and screenshot set 7) automated brightness/detail/frame/GL metrics 8) visually inspect specific failing scenes 9) adjust and repeat. A green CI badge alone is not proof of photorealism.

**Performance warning:** target ES2-era devices without assuming HDR/PBR capabilities of modern desktop engines. Keep high-detail models near camera and atlas sampling limited; hardware FPS must be measured on the user's device, not inferred from emulator.
