# VQ / VEILFORGE — Engineering Techniques That Must Not Be Lost

This playbook records **working techniques**, their justification, commands,
verification and known failure cases. Update it when subsequent tests prove
better methods; do not erase failed experiments or mistake diagnostics for art.

## Geometry and sculpture

**Selective adaptive edge subdivision:** \`vq_adaptive_remesh.py\`.
Select interior *shared* edges by length, locality, crease angle, material
scope and hard triangle budgets. Split BOTH incident faces with conforming
one-/two-/three-edge patterns to avoid T-junctions. Protect open borders,
nonmanifold attachments, creases, and cross-material seams. Reject inverted
faces or increased topology defect counts. More triangles alone do not
improve anatomy or silhouette.

**Three targeted brushes:** \`vq_brushes.py\`. Sculpt to raise/carve,
smooth to relax uneven areas, stamp to reuse relief patterns. Use stable
material/region masks, edge/boundary protection and review candidate hashes
without modifying the source. Smoothing initially exaggerated a bump;
regression tests were retained while tuning the brush. Do not 'fix'
appearance by relaxing a real geometry quality gate.

**Independent source geometry + QA:** \`factory.py\`,
\`gltf_export.py\`, \`vq_model_tools.py\`, \`topology.py\`,
\`vq_refinement_pipeline.py\`. Produce actual OBJ/glTF vertex data and
camera views from that geometry, not synthetic screenshots or image-only
stand-ins. Source-object SHA256 anchors outputs; isolated branches prevent
game regressions.

## UV, texture and material preservation

**UV atlas strategy:** \`vq_uv_atlas.py\` creates padded unique triangle
charts for mesh-derived baking, rejects too-small texel cells and does not
silently reuse tiled old textures. M32/M33 separate source branches advanced
continuous/coherent charts and must be audited before integrating.

**High/low correspondence:** \`vq_uv_transfer.py\` projects compatible
high-resolution triangles through exactly one low parent triangle and
interpolates chart UVs. Reject UV-chart crossings, ambiguous stacked parents,
out-of-cage displacement and mismatched materials. NOT arbitrary character
raycast cage projection.

**Real geometry-derived normal/height bake:** \`vq_mesh_baker.py\` samples
true high-mesh geometric normals in the low mesh's tangent frame, stores
signed height with bounded world range and checks UV overlap, mismatch,
inversion and measured variation. Flat or negligible detail must fail.
The authored sample had 3,200 high-poly triangles versus 32 low-poly
triangles; the M31 source-to-bake test achieved thousands of curved normal
texels. This is not AO, arbitrary cage baking or exact MikkTSpace.

**Material-safe glTF:** \`vq_multimaterial_export.py\` retains OBJ material
groups, UVs, colors, source normals, and referenced albedo, normal, AO and
metallic/roughness textures. Copy local PNGs only after source/manifest hash
verification. Reject unsafe relative path traversal and false finished-asset
claims. The old diagnostic glTF intentionally used one material;
the material-preserving export supersedes it for real asset packages.

## Emulator QA without wasted work

**One shared APK, four real Android 15 roles, independent checks:** the
asset factory builds the test APK once, records SHA256, and runs the same
binary in \`scene-world\`, \`nature-mobile\`, \`props-equipment\`, and
\`characters\` worker roles. Maintain 14 actual orbit views *per asset*,
not merely 14 for the entire factory. All reports must include real screenshot
SHA, GPU/GLES import markers and no fake launcher frames.

**Presentation vs. GPU callback:** a FRAME_OK log can precede the compositor
showing the actual frame. The capture tool checks GLES background color at
three independent sky points, nontrivial foreground/contrast and system
modal overlays. If it sees the Android launcher or an ANR dialog, retry only
a bounded number of times, preserve failure evidence and never approve it.

**Normal-map visual proof:** M30 compares identical low-poly geometry at the
same camera angle with baked normal-map shading on/off, plus a repeated
normal-on control to estimate renderer noise. Four emulators previously
reported a real 1.14–1.21% localized screenshot-pixel change, not a
photorealism score. Test rendering is simplified lighting, not full PBR.

**Avoid redundant emulator overhead:** M34 uses four independent runners in
parallel rather than three-plus-one, downloads screenshot artifacts once
for both LOD and semantic reviewers, installs Pillow once for these reviews,
and retains both fail-closed review results and historical artifact names.
The latest M34 bounded logcat stream replaces repeated whole-log reads with
bounded streaming; keep no lost GL errors, correct frame sequencing and
verified regression tests. Performance savings require timed comparable
runs; don't invent a speedup factor.

**Never skip review by classifying a change as "just documentation" without
checking dependencies.** The high-detail six-team workflow now has narrower
source triggers, while material, asset, renderer and emulator changes still
require relevant full tests.

## Workers, library and recovery

Use \`veilforge/queue.py\` and \`veilforge/library_manager.py\` for bounded
work assignment, immutable artifacts, independently checked source provenance,
and no unauthorized game promotion. The universal factory covers architecture,
terrain, vegetation, props, weapons and vehicles; game-specific
human/creature pipelines live on separate pinned branches.

When new lessons are learned:

1. Keep the code change, deterministic regression test, QA evidence, exact
   Git SHA, observed failure and final repaired outcome.
2. Update \`docs/vq-library/TECHNIQUE_PLAYBOOK.md\` and
   \`docs/vq-library/BRANCH_AND_BUILD_LEDGER.json\`.
3. Generate a new full tracked-source archive via
   \`veilforge/library_archive.py build\` and verify it.
4. Upload the source ZIP to ChatGPT Library (the GitHub artifact expires),
   and preserve a release tag/Git SHA before any risky refactoring.
5. Keep separate model/project branches named; never imply they merged
   merely because an experiment passed elsewhere.

**Unfinished capabilities:** continuous low-distortion unwrap and padding,
general projection-cage baking, production tangent conventions, convincing
anatomy, deforming facial rigs, hair/cloth physics, calibrated PBR and real
target-phone frame-time measurements. Those remain roadmap goals.
