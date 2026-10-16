# VEYLQUORIN M31 — Safe UV atlas preparation for mesh-derived baking

## Engineering milestone

VEILFORGE/VQ's M30 high-to-low mesh baker already transfers real high-poly
normal and signed displacement detail to a low-poly UV surface. Its major
practical blocker was **non-unique or tiled source UVs**: those can cause
overlapping islands and ambiguous texture pixels.

The new `vq_uv_atlas.py` prepares deterministic, source-preserving triangle-
local UV islands for any supported triangulated OBJ. It packs **two isolated
triangular charts in each square atlas cell**, with controlled outer mip-gutter
and a diagonal isolation gap, so independent triangles never write the same
texels. The face's 3D positions, normals, materials, object/group identifiers,
colors and topology remain unchanged.

It has hard texture-resolution limits; a mesh requiring smaller than 16-pixel
cells is rejected instead of silently creating unusable UVs. Input UVs that
tile beyond 0–1 can be replaced with this unique atlas, with full provenance.

### Tested workflow

```bash
python3 veilforge/vq_uv_atlas.py \
  --obj input/treasure_chest.obj \
  --out build/treasure_chest_unique.obj \
  --size 512 --padding 2

python3 veilforge/vq_adaptive_remesh.py \
  --obj build/treasure_chest_unique.obj \
  --recipe veilforge/vq_adaptive_remesh_demo.json \
  --out build/treasure_chest_refined.obj
```

Recipes need to match the actual model/material identifiers and region. The
dedicated M31 automated test exercises a **real UV preparation → adaptive
geometry refinement → bounded sculpt → high-to-low normal/height bake**
handoff, in addition to a real material-preserving treasure chest export.

## Quality and limitations

- All source files remain untouched. A SHA256 report records exact input and
  candidate OBJ bytes, triangle/island counts, pixel budget and gutters.
- Original source texture coordinates are deliberately replaced: **existing
  texture maps cannot simply be reused** and must be rebaked or reprojected.
- Triangle-local charts cause UV seams along every triangle. This is a safe
  baking foundation, **not professional distortion-minimized organic
  unwrapping or artist-authored charts**. Their per-face mapping can cause
  visible seams when production materials are sampled. Blender/DCC coherent
  island unwrap and chart stitching remain planned.
- Source geometry must be triangulated and non-degenerate; input faces without
  UVs are supported by generating a new atlas.
- M30's material screenshot verification remains valid for its own source
  sample; M31 candidates **are not automatically Android-approved**.
- Projection-cage raycasting from unrelated sculpt topologies, mirrored UV
  tangent conventions and filtered gutter dilation remain future work.
- No games are modified and no automatically generated appearance is
  declared photorealistic.

## Next development priority

Implement geometry-aware projection-cage baking between different high/low
topologies; move from triangle-local charts to contiguous low-distortion UV
islands, bake seam gutters, and verify full multi-material glTF + renderer
screenshots with the four Android workers.

## M31 compatible high-resolution UV correspondence

`vq_uv_transfer.py` maps a separate high-resolution OBJ onto its related
padded low-poly UV charts by projecting *each high triangle* onto exactly one
low face. UV corners interpolate with 3D barycentric coordinates; original
high-poly positions, normals and face material references are unchanged.

This is deliberately **strict**: a high triangle must fit entirely inside a
single low parent chart, share the material name and remain within a bounded
surface-normal offset (the default is 0.06 model units). Ambiguous stacked
parents, chart crossings and distant/unrelated high geometry are rejected.
The current exhaustive, bounded implementation limits its input to 1,800
low faces and 20,000 high faces; scaling requires a spatial index.

The M31 workflow now exercises actual M30 high-poly sculpted geometry
(3,200 triangles) projected onto a newly generated low UV atlas (32
triangles), then runs the existing geometry-derived normal/height baker.
That verifies a real multi-resolution source-to-texture handoff without
pretending a generic raycast cage exists.

```bash
python3 veilforge/vq_uv_transfer.py \
  --low build/source_low_unique.obj \
  --high build/source_high.obj \
  --out build/source_high_uv_matched.obj --cage-distance .06
python3 veilforge/vq_mesh_baker.py \
  --low build/source_low_unique.obj \
  --high build/source_high_uv_matched.obj \
  --out build/normal_baked --size 256
```

## M32 independent seam-continuity regression

The read-only `vq_uv_seams.py` counts continuous and discontinuous UV
edges using welded source geometry, rather than assuming matching OBJ
texture-coordinate indices. `test_vq_uv_seams.py` checks the actual M30
32-triangle low source: 40 continuous interior edges before M31 atlas
preparation, and 40 intentionally disconnected edges afterward. This is a
measurable prerequisite for future continuous organic chart unwrapping.
It does **not** implement the organic unwrap, fix visible seams, or grant
Android/artistic approval. The original M30/M31 baselines remain unchanged.
