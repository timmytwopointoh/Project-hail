# VEYLQUORIN (VQ) — Universal 3D Model Tools

Use this branch: brand/veylquorin-20261016.
The engine name is VEYLQUORIN (VQ); the source directory remains
veilforge/ for compatibility with previously successful Android builds.
The VEILBOUND game and its sources are not renamed or overwritten.

## Model chat: try an actual character/asset export

From the repository checkout:

    python3 -m pip install pillow==11.3.0
    python3 veilforge/vq_model_tools.py \
      --obj /path/to/model.obj \
      --gltf /path/to/model.gltf \
      --out inspection_output/vq-model

--gltf is optional. The actual Wavefront OBJ needs triangular faces.
The script never edits or converts the model file itself.

Outputs:
- vq_model_report.json (mesh SHA256, UV and geometry checks, texture linkage)
- vq_model_report.md (repair-oriented summary)
- views/contact_sheet.png (14 real source-mesh diagnostic angles)
- views/orbit_00_yaw_000.png through views/orbit_13_yaw_325.png
- views/mask_00.png through views/mask_13.png (binary silhouettes)
- Verified SHA-256 for every generated orbit image and mask.

The code can be imported from Python as the inspect function in
vq_model_tools, for model chat integrations or standalone modeling workers.
No Android emulator or GPU is needed for the offline inspection.

## Compare against a user-approved reference

Provide a *prepared binary black/white reference silhouette*, NOT a
background-containing portrait photograph:

    python3 veilforge/vq_model_tools.py \
      --obj /path/to/model.obj \
      --reference-mask /path/to/front_approved_mask.png \
      --out inspection_output/vq-reference

Reference comparison reports intersection-over-union for the first angle.
A high score does NOT establish artist likeness, calibrated camera, correct
anatomy, skin quality, photorealism, animation or physical-device behavior.
No reference supplied means likeness is not verified; no score is invented.

This tool does simple CPU raster previews of actual triangle geometry,
not Unreal/Blender PBR. To keep shared runners bounded, each view can sample
up to 4,500 source triangles; the result reports the sampling ratio.
The reports always say production_approved=false and require human review.

## GitHub Actions on-demand smoke test

Open Actions > VQ - Universal 3D Model Tools, select branch
brand/veylquorin-20261016, then choose any existing 3D catalog asset.
The workflow builds actual geometry, PBR input maps and glTF, runs all
Python tests, scans the exported model and archives the 14 real views
and reports as GitHub artifacts.

The existing 10-job queue now invokes this inspector for every
deterministic asset worker, and its reviewer verifies each image hash
and source identity. The full 10-job workload itself remains manual.
The integration should not be called end-to-end verified until a
successful manually launched queue run actually occurs.

## Modeling quality improvements still pending

- Production UV unwrapping and high-poly/low-poly normal baking
- Blender/Unreal material reference lighting and shadow comparison
- Calibrated pose-matched reference cameras for anatomy/face detail
- Skinning, facial blend shapes, realistic hair and cloth deformation
- LOD0–LOD3 export validation on actual hardware, not only static previews
- Human artistic acceptance and explicit reviewed promotion into games

Keep the existing game, source geometry, prior GitHub artifacts and manual
review gates intact. Never claim that preview images prove AAA realism.
