# VEILFORGE M1 — original high-detail 3D asset engine

**Status:** initial reusable **production and inspection pipeline**, not a finished photorealistic DCC or real-time rendering engine. Branch: \`feature/veilforge-asset-engine-v1\`, based on VEILBOUND M22. This directory and its CI workflow are isolated from the existing game and do not replace VEILBOUND, ECHOFORM, or Trion.

## What actually works in M1

- Uses the *real* ContinuousHuman M22 mesh (including articulated hand geometry) without changing gameplay source.
- Exports human geometry as OBJ with normals, UVs and source vertex colors, and renders **14 distinct 3D camera views** plus a contact sheet in an independent Java software diagnostic viewer.
- Reuses the six original Project-hail production roles. The asset workflow exercises human, models, materials, animation, world and studio in separate GitHub Actions runners; combat is intentionally outside the asset pipeline.
- Reuses existing hierarchical worker-manager logic to plan up to 12 bounded role-specific proposals in M1, with the existing independent 50-slot anatomy exploration preserved. Slots are tasks/candidates, **not 50 trained autonomous AI models**. All proposals remain review-only.
- Exports indexed **glTF 2.0 + binary** meshes with normals, UVs, original vertex colors, and PBR material slots; human exports also carry embedded-relative procedural PBR texture references. No skin weights or LOD are claimed yet.
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
