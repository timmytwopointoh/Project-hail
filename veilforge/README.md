# VEILFORGE M2 — original high-detail 3D asset engine

**Status:** reusable **production and inspection pipeline**, not a finished photorealistic DCC or real-time rendering engine. Branch: \`feature/veilforge-asset-engine-v1\`, based on VEILBOUND M22. This directory and its CI workflow are isolated from the existing game and do not replace VEILBOUND, ECHOFORM, or Trion.

## Verified production capabilities

- Uses the *real* ContinuousHuman M22 mesh (including articulated hand geometry) without changing gameplay source.
- Exports human geometry as OBJ with normals, UVs and source vertex colors, and renders **14 distinct 3D camera views** plus a contact sheet in an independent Java software diagnostic viewer.
- Reuses the six original Project-hail production roles. The asset workflow exercises human, models, materials, animation, world and studio in separate GitHub Actions runners; combat is intentionally outside the asset pipeline.
- Reuses existing hierarchical worker-manager logic to plan up to 12 bounded role-specific proposals in M1, with the existing independent 50-slot anatomy exploration preserved. Slots are tasks/candidates, **not 50 trained autonomous AI models**. All proposals remain review-only.
- Exports indexed **glTF 2.0 + binary** meshes with normals, UVs, original vertex colors, and PBR material slots; human exports also carry embedded-relative procedural PBR texture references. No skin weights or LOD are claimed yet.
- Conservatively **repairs isolated exported geometry**: removes coincident front/back duplicate faces (most common source of false nonmanifold armor), and caps ONLY bounded small near-planar hole loops on the human source. Keeps raw OBJ and before/after audit, skips large openings and never modifies Android game code.
- Audits exported OBJ for missing geometry, bounds, degenerate faces, duplicate faces, UV and normal counts, boundary/nonmanifold topology, and content SHA-256.
- Bakes deterministic original tiled albedo (sRGB), normal, roughness, metallic, AO and height maps for skin/stone/steel/leather/cloth, 128–2048 px. These are **procedural placeholders for a future photoreal material pipeline**, not scans or finished skin shading.
- Publishes isolated job artifacts and consolidates six specialist reports in a review-only manager. No game files modified, no automatic asset promotion.

## Architecture and roadmap

\`\`\`text
M22 ContinuousHuman / ShapeEngine / TeamEngineCLI (read-only inputs)
              |
    VEILFORGE six specialist CI production runners
 human | models | materials | animation | world | studio
              |
    14-angle image / OBJ / PBR material artifacts
              |
      mesh QA + manager of managers
              |
       reviewer-controlled approval
              |
 future: retopology -> production UV baking -> skeletal skinning -> GLB
         -> artist-quality render comparisons -> desktop cinematic tier
         -> validated mobile LOD + normal/AO baking -> Android QA
\`\`\`

### Graphics quality gates planned for M2–M5

**M2 Sculpting:** repair hand knuckles, wrist creases, muscle flow and facial landmarks; vertex weld, watertight tests and semantic mesh region segmentation; dedicated source sculpt separate from runtime LOD.

**M3 Surfaces:** proper texture channels and tangent-space continuity; high-resolution layered skin/stone/fabric/metal and reference-based photographic review; no assumption procedural noise equals pores.

**M4 Deformation:** animation-ready indexed topology, skin weights, joint stress tests, blend shapes, deforming attachments and hair/cloth simulation (hair intentionally deferred until the human shape is strong).

**M5 Interoperability:** Blender DCC import, glTF 2.0 PBR/glb, visual comparison in consistent lighting, automated LOD/texture baking for mobile, GitHub Android 15 emulator farm and Moto G physical-device acceptance.

**No claim:** A clean CI run, a high triangle count or a 14-image sheet does not by itself establish game-quality realism.

## Run locally (JDK 17 + Python 3.11)

\`\`\`bash
python3 -m unittest discover -s veilforge/tests -v
python3 veilforge/manager.py plan --max-workers 12 --out build/manager
mkdir -p build/java build/human
javac -d build/java \
  veilbound/app/src/main/java/game/ashenveil/veilbound/{ArtKit,SurfaceAtlas,MaterialMapping,ContinuousHuman}.java \
  veilforge/ForgeHumanCLI.java
java -Xmx1500m -Djava.awt.headless=true -cp build/java \
  game.ashenveil.veilbound.ForgeHumanCLI build/human
python3 veilforge/engine.py inspect --obj build/human/human_source.obj --out build/human/mesh_quality.json
python3 veilforge/engine.py material --type skin --size 512 --out build/materials/skin
\`\`\`

Open the [VEILFORGE workflow](../../actions/workflows/veilforge-asset-engine.yml), choose \`feature/veilforge-asset-engine-v1\` to run M1 manually. Check the \`veilforge-human\` artifact for the full turnaround and mesh geometry; the review artifact will explicitly report anything missing.

## M2: topology repair and acceptance limitations

The \`veilforge/topology.py\` worker creates a separate \`*_repaired.obj\` candidate and detailed \`*_topology_report.json\`. Source geometry, 14 original diagnostic camera views and all engine source code are left unchanged. For the human, only small simple planar boundary loops (up to twelve vertices and 0.16 model units) are candidates for closure; large, open or non-planar surfaces are referred for manual retopology. Armor and scene assemblies only undergo exact coincident face deduplication: **individual hard-surface pieces and garment hems are not to be welded into one body**. glTF output now refers to the cleaned export geometry, with raw mesh preserved for comparison.

**Topology gate:** read \`before\` and \`after\` mesh edge metrics, source-vs-output hashes, capped triangles and skipped loops. A successful CI run proves reproducible export and tests, not good human anatomy, physical manifoldness at every geometric tolerance, photorealism, or handset performance.

Progress towards source-quality retopology and PBR/skin shader upgrades is tracked independently of the M1 Android release.

### M2 acceptance gates

The manager-of-managers now publishes separate **CI evidence gates** and **topology quality acceptance**. A green workflow does not silently classify outstanding nonmanifold edges or open human skin as approved: `unresolved_topology` includes the exact before/after counts and asset name. Back-to-back cloth triangles are removed from exported armor and studio mesh, and those mixed-material glTF exports are explicitly two-sided so the cape remains visible from either side. The Android source never changes.

## M3 universal asset library

The independent general-purpose 3D asset builders and world scene-pack system live in [ASSET_FACTORY.md](ASSET_FACTORY.md). This extends the engine beyond characters with six new procedural model families, a catalog, multi-material glTF exports, actual mesh previews, and reusable scene composition. Working game code is not changed.

## M4: Real Android Emulator Visual QA

The existing catalog generates real geometry, multi-material glTF 2.0 and a
multi-mesh scene. The isolated Android probe app under veilforge/android-probe
packages that EXACT generated scene and all binary meshes as APK assets.
It is not a game; no VEILBOUND runtime source files are touched.

The Universal Factory workflow builds one shared APK, then runs three
independent Android 15 virtual devices using the proven emulator farm
pattern (Pixel 6, 7 and 5 profiles, GLES2, SwiftShader GPU). Each renders
three asset or scene selections from 14 yaw/pitch views: a full cycle captures
126 actual device screenshots, archived by per-file SHA256. It also records
Android GLES renderer/load/draw logcat markers and process memory snapshots.

The manager veilforge/android_review.py independently checks every role,
all images, APK/source identity, 14 frames per asset, viewport silhouette
presence and visible camera changes. Missing or corrupted evidence fails
the workflow and creates android_repair_backlog.json for future workers.

A passing emulator test is NOT proof of photorealism, dynamic rigging,
correct PBR textures, measured target-phone FPS, physical hardware VRAM,
or artist/aesthetic signoff. Those remain open milestone acceptance gates.

Next priority: texture-backed GLES PBR comparison, image segmentation and
reference-aware silhouette regression, motion/LOD stress tests, then
target-hardware telemetry and artist signoff before game promotion.
