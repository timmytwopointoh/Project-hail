# VEILFORGE M3 — Universal game asset factory

**Project boundary:** VEILFORGE is an independent asset authoring, verification,
and exporting toolkit. VEILBOUND, Trion, and all other games are consumers of assets.
No gameplay or APK feature is developed as part of this asset factory.

## What M3 builds

The schema-versioned, deterministic catalog (veilforge/catalog.json) drives isolated
specialist jobs. Each generates real original geometry (OBJ with normals, UVs and
vertex colors), multi-material glTF 2.0 with binary buffers, material PBR factors,
source SHA256, measured bounds/triangle budgets, four software-rendered 3D angles
and a contact sheet. Previews are NOT Android screenshots or photorealistic renders.

| Builder family | Real source asset | Future extension |
|---|---|---|
| Architecture | Ruin gate with profiled pillars and curved arch | Buildings, bridges, castles, interiors |
| Terrain | Seeded heightfield and stones | Mountains, biomes, caves, rivers |
| Vegetation | Branching tree with foliage | Forests, flowers, roots and vines |
| Props | Layered chest with metal bands | Furniture, tools, containers, machinery |
| Weapons | 3D longsword with fittings | Shields, axes, armor and tools |
| Vehicles | Cargo cart with wheels | Carts, ships and cars |

Existing character and creature foundations, materials, rigs, human-hand
inspection and Android QA remain available through VEILFORGE M2/VEILBOUND.
The M3 pipeline extends that system without touching the working games.

## Engine-wide architecture

New specialized builders plug into the same lifecycle:
recipe -> scoped worker -> source geometry -> materials -> visual/geometry
QA -> reviewed asset -> optimized exports -> target-game importer test.

Future build domains include:
- Characters, faces, creatures, monsters, hair, clothing, animation, rigging
- Worlds, buildings, roads, water, foliage, terrain, caves, destructibles
- Furniture, weapons, armor, vehicles, modular props, interactive items
- Particles/VFX, UI graphics, decals, collision, navmeshes, world layouts
- Sound and music require distinct audio tools, not a geometric mesh renderer

These are future expansion directions, NOT claims that M3 implements them all.
A DCC/high-resolution stage will use proper sculpting, UV unwrapping,
retopology, high-to-low baking, texture authoring, rigging, shader testing,
LOD authoring, visual comparison and target-device performance gates.

## Safety and reproducibility

- Original or properly licensed content; no copies of proprietary game models.
- Recipes are data: bounded IDs, seeds, tiers, uniform scales and tags.
- Isolated runner for each recipe; at most 24 bounded concurrent candidates.
- Every output includes provenance, hashes and material names.
- Production promotion remains disabled; human aesthetic review is required.
- Open architectural edges, vegetation or terrain are not automatically closed.
- The base geometry uses Y-up meter units and glTF 2.0 interoperability.
- Current material factors and simple diagnostic lighting are NOT scans, full
  texture baking or demonstrated cinematic PBR.

## Run

~~~bash
python3 -m unittest discover -s veilforge/tests -v
python3 veilforge/library_manager.py plan --out build/library-manager
python3 veilforge/factory.py --catalog veilforge/catalog.json --id ceremonial_sword --out build/sword
python3 -m pip install pillow==11.3.0
python3 veilforge/preview.py --catalog veilforge/catalog.json --id ceremonial_sword --out build/sword/previews
python3 veilforge/engine.py inspect --obj build/sword/ceremonial_sword.obj --out build/sword/mesh_quality.json
~~~

The workflow at .github/workflows/veilforge-factory.yml dynamically launches
eight initial asset jobs, each with distinct CI artifacts, then aggregates the
evidence into a fail-closed manager report. The factory does not modify Android
source or merge candidates into any game.

## Next quality milestones

M4: semantic topology and segmented material/mesh region inspection; safer
UV layouts and editable instance variants.
M5: Blender/headless true high-poly sculpt and normal/AO/roughness baking,
LOD chains and verified glTF/GLB.
M6: actual game importer + automated visual benchmark on multiple GPUs,
retaining artistic sign-off.
