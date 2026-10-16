# VEILFORGE × VEYLQUORIN (VQ) M33 — Real Human Surface Baking

## Why M33 exists

The original knight and existing Android **Testing Grounds** remain intact. M32 independently corrected shoulder/clavicle weighting and added face, palm, foot and toe surface studies. M32 code and four-emulator Android workflow passed at [GitHub Actions 38899035158](https://github.com/timmytwopointoh/Project-hail/actions/runs/38899035158), while VQ's newer M30 normal-detail baking had not yet been applied to a **real human mesh**.

The reusable VQ engine gained a genuine, source-derived high-poly-to-low-poly **tangent-space normal and signed height-map baker**, with four Android 15 emulator material demonstrations, see [VQ M30 run 38901241312](https://github.com/timmytwopointoh/Project-hail/actions/runs/38901241312). Those Android screenshots show a sculpted stone demo, **not** the human. M33 consumes the actual VQ baker on isolated M32 human anatomy regions.

## Integrated proven tools and workflow

- M30's unchanged `vq_mesh_baker.py`, `vq_sculpt_detail_patch.py`, and the original `test_vq_mesh_baker.py` are imported from `feature/vq-m30-sculpt-baking-cleanup`.
- `vq_engine_health.py` source-audits the twelve selected VQ entries on this isolated branch; it checks the new M33-specific workflow rather than a different VQ-branch workflow.
- VQ's `factory.py`, `vq_quality_plan.py`, source provenance and machine-readable master plan are imported for missing dependencies; unrelated Android game source is never changed.
- The already working M29 VQ adaptive remesh, smooth/sculpt brushes, multimaterial glTF exporter and 14-angle inspector stay in place. These tools **cannot magically fix disconnected eyes/feet or create real facial edge loops**.
- `vq_human_region_bake.py` extracts actual M32 neutral body triangles, filters to skin pigment and four bounded anatomical regions: forehead skin (face), left and right deltoid (shoulders), **right hand only** (hands), both feet. No anatomical source triangles are silently edited.
- For each region the tool creates source-derived geometry `source_skin_low.obj` and an independent microsculpted `source_skin_high.obj`. It packs disconnected source faces in a temporary non-overlapping diagnostic UV grid so low/high have unambiguous matching texels. This is **not** a production connected face/hand/foot unwrap.
- The M30 original `vq_mesh_baker.py` then generates authentic tangent-space normal and signed height PNG maps. Hashes bind source OBJ, both region geometries and PNG outputs; no output can overwrite the source.
- Four bounded specialist workers export four anatomy patch artifacts and independent director confirms SHA256 for each emitted PNG, source and geometry.

## Recorded VQ quality lessons

1. **Reject texture tiling as a false unique atlas.** M32's current full-body procedural UVs are not a production non-overlapping atlas. VQ M30 intentionally rejects them. A separate diagnostic atlas enables safely testing the baker without claiming UV production quality.
2. **UV boundary ambiguity is a real bug.** First human bake trial packed unrelated triangles into two exactly adjoining atlas halves. The strict VQ rasterizer rejected them as overlapped. Added positive-width diagonal and exterior island gutters; do not weaken the overlap test.
3. **Face topology can flip during displacement.** Original M32 facial patch included disconnected curved orbital/nasal surfaces. The strict high-to-low baker rejected inverted normals. Restricted material diagnostic to the smoother connected forehead skin and reduced its motion. The eye, lips, jaw and nose still need real sculpt/topology workers.
4. **VQ normals on the character ≠ a photoreal human.** A 128-pixel human region normal image is a demonstrable surface baking exercise. It does not create natural skin albedo, reference likeness, UV continuity, expression topology, high-res hand art or properly rigged feet.
5. **Only Android proof for full body so far is M32 game rendering.** VQ M30 stone material shader test passed independently; the new M33 human-region maps have **not been wired into the human Android PBR shader**. Do not present M33 texture export as completed native human material validation.
6. **VQ Studio Android is a separate companion viewer.** Its current application can import a generated OBJ from the Android file picker and show actual 3D geometry, and report GitHub worker status. Export `human_candidate.obj` is compatible as a model input. There is no remote live body streaming and no automatic bridge to the playable knight.

## Acceptance gates

Geometry, production UVs, skin/material realism, limb deformation and device performance are distinct. The four M33 baking outputs count as technically verified only after the current GitHub Actions run passes all specialized workers and the independent director.

The user retains final artistic approval. A draft PR may include VQ engine additions, source hashes and real reports but must never auto-merge. The knight stays the game's historical character and the new human remains a review candidate. The next meaningful upgrade is a human-specific seam-aware UV unwrap and controlled facial/hand/foot retopology, followed by head/skin shader integration and four-device Android screenshot comparisons.
