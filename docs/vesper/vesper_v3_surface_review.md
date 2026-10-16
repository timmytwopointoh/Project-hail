# Vesper V3 / VEYLQUORIN Surface-Smoothing Gate

**Review-only candidate.** Built 2026-10-16 from the existing user-reference-inspired V2 skinned GLB. V2 remains intact. This document is an inspection record; the downloadable V3 GLB, editable generator, and smoothing script are in the Vesper V3 package attached to the project conversation (not committed to this repository).

## Independent local evidence

| Measurement | V2 | V3 |
| --- | ---: | ---: |
| Triangle faces | 24,082 | 29,514 |
| Indexed vertices | 12,479 | 15,191 |
| GLB byte length | 1,032,932 | 1,250,100 |
| Smoothed vertices | — | 5,112 |
| Maximum actual vertex movement | — | 0.0063873 meters |
| UV missing mesh primitives | 0 | 0 |
| Degenerate triangles | 0 | 0 |
| Skinned joints | 33 | 33 |
| Animations | 4 | 4 |
| CPU-view angles | 14 | 14 |

VEYLQUORIN-inspired constrained Taubin normal-only smoothing with positive/negative relaxation was applied to the skin (2,758 vertices), black fabric (1,081), trim (47), boots (620) and blush skin (606). Material creases, open boundaries, coincident shell edges and large bone-weight changes were pinned. Position displacement was limited to 18 mm, with an observed maximum of about 6.4 mm. Recomputed normals are exported with the same weights, UVs, indices and bone hierarchy. The static OBJ is derived directly from the refined skinned GLB geometry.

V3 passed offline GLB integrity, UV/triangle and deformation tests: real ear-tip, hair-sway, foot/walk and auxiliary motions checked against bind matrices and clip keyframes; no observed degenerate triangles or non-finite coordinates. This **does not establish** reference likeness, photoreal skin, cloth physics, smartphone FPS or game approval.

## Actual Android status

GitHub Actions run [#38914849958](https://github.com/timmytwopointoh/Project-hail/actions/runs/38914849958) **succeeded** on the isolated playable-character development branch at commit `aa500cf3470884e3779c0c966f149cf14113cb98`. Its emulator report includes `vesper_synthetic_glb_import_smoke_pass: true`. This validates a **two-joint synthetic fixture** and baseline Android scene—not import/rendering of the *full* V3 GLB.

## Next acceptance gates

1. Import the full reviewed V3 GLB through Model Atelier's GLB picker and capture real Android emulator screenshots while idle and walking.
2. Inspect skin/cloth cracks, outfit penetration at hips and shoulders, ear tip and hair bounce at motion extremes, and face/head silhouettes.
3. Compare 14 views with calibrated reference-aligned silhouettes; require subjective artist acceptance.
4. Measure performance on target Android device and supply an optimized LOD variant if required.

No merge, asset promotion or game release is authorized by this report.
