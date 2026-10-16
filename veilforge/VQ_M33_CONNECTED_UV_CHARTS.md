# VQ M33 — Connected near-planar UV charts (review-only)

This isolated milestone adds veilforge/vq_uv_charts.py. Unlike M31's safe
triangle-local atlas, it groups welded-edge-connected triangles with the same
source material and bounded face-normal deviation into continuous UV charts.
It chooses an oriented chart projection to reduce bounding-box waste, rejects
inverted, degenerate or positive-area overlapping projected triangles, and
packs chart rectangles at one world-to-texel scale with explicit 2–16 pixel
separation. Source OBJ positions, normals, materials and topology remain intact.

    python3 veilforge/vq_uv_charts.py --obj source_low.obj \
      --out build/source_low_coherent.obj --size 256 --padding 4

## Objective technical gates

CI generates real M30 32-triangle low and 3200-triangle high sculpt geometry.
Expected: one chart with 40 continuous internal UV edges (M31 atlas had 40
seams), area stretch <=1.08, minimum triangle area >100 texels at 256²,
high-to-low normal bake coverage >80% with nonflat detail, and 14 real
source-derived geometry views. The reports record SHA-256 provenance.

Regression tests also check material and dihedral seams, deterministic output,
invalid topology and unsafe settings. No renderer or shipped game asset is
changed. This is not Android approval of the M33 atlas; M30's independent
four-emulator GLES evidence is preserved as its own baseline.

## Deliberate limitations

Near-planar projection is not a general conformal/angle-preserving organic
unwrap for heads, hands, ears or folded creatures. Folded projections fail
closed. Mip gutter dilation, unrelated high/low projection-cage raycasting,
tangent-continuous glTF materials, Android PBR captures, and artistic/reference
approval remain outstanding. Old texture maps require rebaking onto new UVs.
No unlicensed assets or game repositories are modified.
