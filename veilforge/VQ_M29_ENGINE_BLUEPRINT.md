# VEYLQUORIN + VEILFORGE — Complete Modeling Engine Improvement Blueprint (M29)

## Objective and non-negotiable standard

Build a **universal reusable 3D asset authoring, sculpting, material, optimization
and QA engine**. It should make anything a game needs—characters, creatures,
props, architecture, entire worlds, vehicles, vegetation, animation sources,
interactive objects and visual-effects source assets. The engine is NOT an
individual game, and does not edit or replace existing games.

**"Perfect" is a direction rather than a measurable automatic state.**
Actual acceptance requires geometry correctness, realistic or deliberately
stylized reference-matching appearance, target-engine import, lighting and
animation stability, device-specific performance, license/provenance and
the user's artistic signoff. More polygons or a green GitHub build alone are
not evidence of beauty or photorealism.

The machine-readable source of truth for all **34 named milestones** and their
measurable acceptance criteria is
[`VQ_ENGINE_QUALITY_PLAN.json`](VQ_ENGINE_QUALITY_PLAN.json).
`vq_quality_plan.py` ensures that milestones cannot be declared "verified"
without attached evidence and that essential review gates are never omitted.

## Priority 0 — Build a reliable authoring foundation

**Geometry:** source-preserving sculpt, smooth and detail stamp; triangle-
conforming adaptive subdivision; protect UV seams, open edges, hard creases,
material borders; diagnose and repair nonmanifold, duplicated and degenerate
faces; test geometry budgets before execution. The target is a real geometry
tool, not just a report.

**Visual/material:** inspect UV continuity, texel ratios and source material
references; produce albedo, roughness/metallic, AO and normal maps with
correct colorspace/channel handling; compare 14 actual model angles; submit
render results to independent reviewer workers and real Android GLES emulators.

**Control:** reproducible source hashes, bounded parallel workers and
untrusted-input parsing; no hidden self-modifying commits, no automatic game
promotion, no game repository mutations, no false photorealism claims.

## Priority 1 — Produce attractive production-ready detail

Region-aware adaptive remesh and retopology for expressive human faces, joints
and creatures; purpose-built skin and hair/cloth handling; source-to-LOD normal
baking and UV atlases; headless Blender interoperability; tangent-space correct
normal/AO material rendering and physically based BRDF; animation weighting;
mobile/desktop LOD; multi-asset modular world authoring; approved golden-view
regression and reference-image alignment.

These require renderer/artist evidence, not just geometry counts.

## Priority 2 — Broaden quality across entire games

License-grounded photoreal material libraries, physics and navigation packages,
cloth/hair/fur solvers, water and biomes, scene streaming and GPU budgeting,
target physical-phone performance, optional DCC plug-ins and style-preserving
generative refinement. Each capability must include implementation, tests,
recorded constraints and a reviewable sample asset.

## Worker roles and handoffs

| Worker | Input | Output and gate |
|---|---|---|
| Director / queue | Quality plan and defect ledger | Priority, bounded assignment, no overlapping jobs |
| Sculpt specialist | Immutable OBJ and region recipe | New OBJ, per-stroke SHA and pinned-boundary audit |
| Remesh specialist | Sculpt candidate and adaptive selection | Conforming subdivided OBJ + edge-budget/topology report |
| UV/material specialist | Indexed geometry/material regions | UV-map report, authored texture maps and hashes |
| Rig / animation specialist | Approved topology and poses | Joint deformation recordings and clipping evidence |
| Renderer specialist | Candidate + standardized camera/light rig | 14 actual geometry views and source-image hashes |
| VQ independent inspector | Source OBJ, glTF and reference when available | UV/geometry/glTF defects, comparison and review status |
| Android farm | Properly packaged, reviewable multi-material asset | Four emulator GLES renders with integrity/camera/texture checks |
| Release steward | Complete evidence and signed-off review | Versioned reusable asset package; never automatic game changes |

Technical failures become explicit scoped repair tasks. Visual warnings are
review tasks, not automatic declaration of aesthetic improvement. No worker
should silently rewrite artist-approved mesh features.

## M29 implemented experiment: conforming adaptive subdivision

The tool `vq_adaptive_remesh.py` selects **interior shared edges only**
based on actual geometric length, curvature, material selection, spatial
region, crease angle and triangle/edge budgets. Every chosen edge is marked
for **both** incident faces. It uses consistent patterns for zero, one, two
and three split edges, so adjacent UV-seamed faces cannot develop an unshared
T-junction.

- Does not change existing source vertices, material IDs or UV corner data.
- Inserts additional edge midpoint vertices and interpolated per-side UVs,
  normals and colors; duplicate UV-side vertices still share geometric space.
- Protects open edges, nonmanifold joins, material discontinuities and strong
  hard-surface creases.
- Rejects triangle flips/collapse and any post-export topology regression.
- Records exact before/after OBJ hashes, mesh budgets and all edge counts.
- The new `vq_refinement_pipeline.py` runs VQ sculpt, smooth and stamp
  strokes, then adaptive subdivision, a **single-material diagnostic**
  glTF export, plus 14 real source-mesh images and independent OBJ/glTF QA.
  **The diagnostic glTF is not a correct multi-material finished game export.**

This is production *infrastructure*, not completed photoreal artistry.
Smooth/subdivide alone does not repair bad underlying topology or guarantee
texture/detail continuity, and edge splitting by itself does not make a
silhouette more accurate. The source image and artistic reference still matter.

### Repeat locally

```bash
python3 -m unittest discover -s veilforge/tests -v
python3 veilforge/vq_quality_plan.py
python3 veilforge/factory.py \
  --catalog veilforge/catalog.json --id rolling_terrain --out build/source
python3 veilforge/vq_refinement_pipeline.py \
  --obj build/source/rolling_terrain.obj \
  --brush veilforge/vq_brush_demo.json \
  --refine veilforge/vq_adaptive_remesh_demo.json \
  --out build/vq-refinement
```

The VQ GitHub Actions job independently tests malformed recipes, original
UV index preservation, cross-material edge safeguards, budgets, determinism,
topology integrity, glTF byte linkage and 14 source camera views. Artifacts
are archived with the precise head commit. No game source is edited.

## Definition of done for any milestone

1. Real implementation and documented source/data licensing.
2. Deterministic unit and adversarial tests against independently checked
   baseline assets; no source-data or game-code mutation.
3. Semantic mesh and material checks (including no unexplained topology
   regressions, UV seams or incorrect normal frame).
4. Accurate exporter/importer roundtrip in a real engine.
5. Actual before/after reference views and camera/light-specific diagnostics.
6. Android/emulator checks and target-device benchmarks where applicable.
7. Artist reviews actual samples; signs off or creates the next repair task.
8. Release steward publishes an immutable, provenance-linked asset version.
   Without all applicable gates, the milestone remains partial.

## Immediate successors after M29

- **GEO-03:** refine surface smoothing to protect anatomy/sharp edge semantics
  and compare before/after roughness with calibrated thresholds.
- **UV-01 / MAT-02:** verify UV distortion, tangent frame, bake high-to-low
  source detail and visibly sample normals/AO in Android renderer.
- **GEO-04 / GEO-06:** DCC-assisted production retopology and artist-directed
  sculpt layers, eventually adaptable to characters, creatures and worlds.
- **QA-03/04:** package real multi-material glTF with the refined geometry,
  run full four-emulator inspection and obtain explicit visual signoff.

None of these future stages should be marked verified merely because they are
listed here.
