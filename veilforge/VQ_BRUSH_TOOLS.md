# VEYLQUORIN (VQ) — Adaptive sculpt, smooth and stamp tools

VQ now has **three review-only, non-destructive OBJ geometry tools**:

1. **Sculpt** (`op: sculpt`) moves selected source-mesh vertices a small
   bounded distance along the mesh normal. `kind: raise`, `carve`, or
   `roughen` controls the direction/pattern. Center, radius, strength,
   material whitelist and random seed are explicit; unselected faces remain
   untouched.
2. **Smooth** (`op: smooth`) uses a bounded two-phase Taubin-style
   neighborhood relaxation, along the original normal, with 1–4 iterations.
   This helps remove small bumps without aggressively shrinking the object.
3. **Stamp detail** (`op: stamp`) replays an earlier sculpt brush's
   procedural pattern in a new region, in the target surface's own normals.
   This is safer than raw geometry copy-paste. It intentionally **does not
   duplicate faces or copy UV islands, materials, hair, muscles, or rigs**.

The tool works on **actual triangulated OBJ files** from VQ, VEILFORGE or
other modelers, including UV-split meshes with duplicated position records.
It welds coincident positions for geometry operations but preserves their
distinct OBJ vertex/UV/normal indices and material groupings. Vertices
along open, nonmanifold, cross-material, or sharp edges are pinned to
prevent damaging seams or sharp architectural edges.

All strokes have explicit maximum strengths. VQ also clamps geometric
displacement based on the incident mesh edge length, limits the total
movement relative to the unmodified source, and rejects any change to
the source's triangle count, topology defect counts, duplicated face count,
or face orientation. UV coordinates, face references and original source
bytes are never rewritten.

## CLI

```bash
python3 veilforge/vq_brushes.py \
  --obj path/to/source.obj \
  --recipe veilforge/vq_brush_demo.json \
  --out output/refined.obj

python3 veilforge/vq_model_tools.py \
  --obj output/refined.obj \
  --out output/vq_inspection
```

The committed demo applies all three operations to the real catalog's
`rolling_terrain` source and produces a `*_brush_review.json` audit plus
14 actual software-rendered OBJ viewpoints. GitHub Actions exercises these
with the complete existing VQ unit suite. All results are candidates only.

## Deliberate boundaries

- **No unlimited copy/paste:** stamp carries only a bounded procedural motif,
  not a chunk of polygons, which could disconnect surfaces or break animation.
- **No miraculous smoothing:** open edges, hard creases, and material borders
  remain pinned. A model with poor initial topology might allow little or no
  displacement, and then the tool rejects the no-op.
- **Not adaptive remeshing or sculpt layers in a full DCC:** strokes move
  existing vertex positions and do not add polygons or create face loops.
  Small triangles may limit the visible strength. Higher-resolution
  source geometry and production UV unwrapping are separate priorities.
- **No visual perfection claim:** diagnostic 14-angle raster images and
  topology checks do not prove anatomical likeness or photorealism.
  A separate game importer and real Android emulator approval are required
  before promoting anything into VEILBOUND or another game.
- **No automatic game changes:** VQ's branch and workflow only generate
  isolated candidate models and evidence; reviewed playable game baselines
  remain untouched.

## Subsequent quality work

Combine M27 non-destructive triangle-interior layers with VQ's brushes in
an explicit orchestrator, then add region-aware adaptive remeshing with
UV preservation, proper bilateral anatomy masks for faces and limbs, and
normal/AO baking into mobile LODs. Do not use generic terrain brushes on
human skin unless they have purpose-built anatomy-specific guards.
