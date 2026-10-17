# VEYLQUORIN shape-only GLB refinement (review-only)

**Purpose:** Adjust face, hair, gill, tail or outfit vertex positions on an existing GLB without new triangles, remeshing, changing skin weights, or discarding animations. Complements the OBJ brushes and Kaiyu material-batched Android preview. This is not reference-image matching, automated photorealism, or Android artistic approval.

## Local workflow

```bash
python3 veilforge/vq_glb_shape_refine.py --glb kaiyu_source.glb --list-meshes
python3 veilforge/vq_glb_shape_refine.py --glb kaiyu_source.glb \
  --recipe shape_recipe.json --out kaiyu_shape_candidate.glb \
  --report kaiyu_shape_review.json
python3 -m unittest discover -s veilforge/tests -p 'test_vq_glb_shape_refine.py' -v
```

Use the exact mesh names and **local-space** coordinates from `--list-meshes`; do not guess global face or tail coordinates. Kaiyu's prototype uses meters. Example template, **not** a verified Kaiyu face location:

```json
{
  "schema_version": 1,
  "layers": [{
    "id": "example-facial-shape",
    "mesh": "REPLACE_WITH_EXACT_GLTF_MESH_NAME",
    "center": [0.0, 0.0, 0.0],
    "radius": 0.25,
    "delta": [0.0, -0.005, 0.0],
    "strength": 0.4
  }]
}
```

Up to 16 bounded falloff layers are supported. Single-layer translation is limited to 45 mm; total point displacement is capped at 55 mm (hard limit 60 mm). Candidate output is written to a separate file; a missing mesh, invalid accessor, reversed/collapsed triangle, or zero effective movement is rejected. New POSITION/NORMAL accessor streams preserve the original binary payload, UV references, triangle indices, materials, joints, weights, skins, animation metadata and node structure.

The displacement is **baked into mesh-local base positions**. It is not a facial animation clip, reusable blend-shape controller, or substitute for a calibrated sculpt.

## Kaiyu feedback loop

1. Preserve the latest Kaiyu source and turnaround sheet. Enumerate mesh names, inspect head/gill/tail bounds and measure target offsets from the actual reference at comparable camera angles.
2. Edit one region per small recipe, recording source/recipe hashes and candidate report. Keep triangle count constant.
3. Compare original and candidate at 14 real geometry angles and in idle/swim/dance/raised-leg poses. Record silhouette, pupil alignment, gill feathering, tail-root attachment and boot/hand visibility.
4. Require GLB structural checks, actual game-viewer import, native Android front/side/back screenshots and deformation/frame-time checks **before** promoting. The existing M12 batched preview is static and cannot prove skinned Android playback.
5. Put reusable passed recipes in the VQ technique library after review. Do not auto-merge or replace the working game.

**Limitations:** GLB 2.0 with one embedded buffer, float32 VEC3 positions/normals, triangle-list primitives and non-sparse indices only. Not compressed/sparse GLB accessors, reference-photo reconstruction, actual Android import QA or photorealistic facial likeness. After normal recomputation, any supplied tangent-space maps need independent review.
