# VEILFORGE M27 — Non-destructive source sculpt layers

The next quality milestone after the M26 visual-defect learning curriculum is a **real reusable sculpt-layer operator** for source geometry.

## What is implemented

`veilforge/sculpt_layers.py` takes any of the universal asset factory's `Mesh` objects and a schema-limited list of layer recipes. Each enabled micro-relief layer subdivides only targeted material faces, inserts a face-center vertex, displaces that vertex by bounded seeded smooth 3-D noise along the original normal, recalculates child face normals, and preserves the three original triangle edges and UV edge endpoints. Every layer produces a deterministic displacement/triangle/provenance report. The original source mesh is never mutated.

The three material/asset families exercised by default:

- `ancient_gate_standard` — stone and stone-trim localized chisel/erosion
- `rolling_terrain` — low-amplitude seeded terrain relief
- `treasure_chest` — subtle wood-grain relief, iron fittings preserved

The same geometry operator can be applied to additional universal asset families through bounded catalog recipes, not new specialized rendering code. The reviewed M26 human and historical knight models remain on their own development branches; M27 does **not** claim to solve anatomical retopology.

## Validation

- `python3 -m unittest discover -s veilforge/tests -v` includes deformation, UV-source invariants, malformed specs, budget rejection, determinism, and three independent asset families.
- The dedicated `surface-sculpt-audit` CI worker generates baseline and sculpted OBJ geometry, audits topology counts, and captures matched camera projections for each of the three families.
- The existing independent factory jobs, scene pack compiler, character exporter, four Android 15 virtual-device workers (14 views per asset) and visual-comparison/reviewer gates still run on the sculpted catalog outputs.
- Source changes are in isolated branch `feature/veilforge-m27-surface-layers`; the gameplay APK, game code, historical knight and M26 experiments are not modified.

A green unit test or geometry audit is **not** proof that the surface looks beautiful. Matched rendered before/after images and Android screenshots must still be reviewed; no candidate is automatically promoted to any game.

## Current limitations and next modeling priorities

M27's detail is **triangle-interior microrelief**, not freely editable high-poly sculpting, remeshing, deformable facial edge loops or skin-detail baking. It does not automatically recognize physical wear locations or fix pre-existing topology; source faces remain faceted, and displacement strength is deliberately restricted to protect seams and prevent inverted faces. A full DCC/Blender-capable stage, sculpt layer blending/masks driven by artist paint, adaptive remeshing, UV island-aware texture baking and reference-graded preview lighting are subsequent milestones.

The M26 curriculum continues to own reference-grounded anatomy proposals; M27 is its initial extension to non-human source assets.
