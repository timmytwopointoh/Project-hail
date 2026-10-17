# VEILFORGE / VQ A3: Open-reference anatomy integration (review-only)

**Scope:** This milestone adds the existing A1 continuous-SDF character builder, A2 original synthetic reference/repair loop, and a new A3 distal anatomy procedure into the VQ engine source branch. Existing Android games and workflows remain untouched. Do **not** promote the produced mesh to a shipping game without human artistic and runtime approval.

## Manual end-to-end command

From repository root (Python + numpy, scipy, scikit-image, trimesh, pillow, vtk for preview):

```sh
python3 veilforge/vq_anatomy_cli.py --prompt "human long legs teal tunic" --out build/a3-human --voxel .016 --preview
python3 -m unittest discover -s veilforge/tests -p 'test_vq_anatomy*.py' -v
python3 -m unittest discover -s veilforge/tests -p 'test_vq_distal_anatomy.py' -v
```

Outputs: real GLB + glTF/OBJ + original procedural PBR maps + `vq_a3_qa.json` (watertightness, connected body, symmetry, material identities, GLB reimport, SHA256), plus optional offline front/side/three-quarter screenshots. No Actions, emulator or network required. Run existing factory tests separately as usual.

## Techniques captured

- **A1:** smooth implicit/SDF torso/limb/neck/face blend; marching-cubes indexed body surface (rather than disconnected cylinders); bounded island cleanup; preserved VQ factory OBJ/glTF/material paths.
- **A2:** independent original synthetic 25-landmark reference targets; reproducible silhouette gating; held-out examples balanced by species; bounded corrective rebuilds; continuous PCHIP garment rings.
- **A3:** 4 non-thumb finger chains per hand, 2-segment opposable thumb, unequal finger lengths, 5 differentiated toe paths per foot, tapering phalange-like volumes, heel/instep/metatarsal transition; authored forehead/brow/malar/mandible/nose/lip/pinna mass; bilateral geometric checks. Digits are not yet individually rigged.
- **Offline learner:** deterministic NumPy 14-hidden-neuron MLP regression on synthetic semantic ratios, no claim of empirically trained anatomy. No external or user images/meshes used to create or train these models.

## Limitations and next acceptance gates

Technical QA does not prove anatomical correctness. Current models have visible proportion, face, fingers/feet, hairstyle, garment, UV and skin-texture shortcomings. Original synthetic reference data is **not** measured human anatomy. Imported biomedical book descriptions were used as descriptive design guidance only; no third-party models or anatomy photos were copied. Independently validate body/hand/foot landmark dimensions against suitable reference scans/measurements with explicit reuse rights, record provenance, improve hands/feet retopology and deformation, add weighted skeleton/facial blendshapes, and complete renderer/emulator QA before approving a production character.

Anatomy background: https://www.ncbi.nlm.nih.gov/books/NBK547684/ (hand bones / five digits); https://www.ncbi.nlm.nih.gov/books/NBK587361/ (foot arches); https://www.ncbi.nlm.nih.gov/books/NBK546698/ (foot/ankle structures).

Engine merge target: VQ source archive branch `feature/vq-library-snapshot-perf01-20261016`, not the policy-only `main`; this avoids uploading the entire engine into the game's default branch. No pre-existing engine/workflow files need replacement: these are additive modules.