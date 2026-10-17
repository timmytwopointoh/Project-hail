# VQ Human 03 method notes

This clean-room character uses no previous human geometry or model references. Techniques reused: localized analytic SDF unions, marching cubes, conservative Taubin smoothing, separately modeled eyes and hair, temporary noncollapsed UV charts, and 14-angle real-mesh diagnostics.

Local results: 93 sculpt operations; 96,092 triangles; 48,048 vertices; 1 watertight connected body; zero degenerate faces; 100% technical UV-face coverage; 14 distinct diagnostic views. The first pass had 3 detached fingers; wider palms and inward finger roots repaired it. A second recipe produced a distinct 1.82m watertight character, confirming reusability.

Source recipe parameters: height=1.70m, voxel=0.009m; shoulder=.97; hips=1.045; waist=.975; calf=.98; head=.985; arm_extension=.80. Source mesh inputs=0.

These are local tests, not the official VQ GitHub pipeline or Android emulator. The user-delivered ZIP contains the full procedural generator and OBJ/GLB. This documentation branch preserves methods and evidence but does not include those files yet. Model is not rigged, skinned, likeness-checked or game-approved.
