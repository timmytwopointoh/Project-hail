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

## M34-09 — Observed factory CI and real APK/capture bytes (2026-10-16)

The source-only `vq_ci_benchmarks.py` checks the *actual* GitHub Actions
job timestamps, source SHAs, eight asset producers, four Android 15 roles,
single APK builder, both independent reviewers and required artifacts.
Adversarial tests fail closed on missing roles, incomplete pagination, bad
timestamps, unsuccessful jobs or absent screenshot evidence. The separate
`vq_ci_artifact_probe.py` checks downloaded artifact ZIPs, computes the
real uncompressed APK SHA256/byte length, distinguishes accepted 14-view
PNG captures from blocked-modal retries, and verifies every asset's fourteen
unique camera indices. It never labels blocked frames as accepted views.

Two verified full-factory runs are currently available:
- [38916145322](https://github.com/timmytwopointoh/Project-hail/actions/runs/38916145322):
  job-span **319 s**, APK payload **2,304,080 bytes**, **154 accepted** PNGs
  (**25,380,977 bytes**) and **7 blocked** modal retries.
- [38918040166](https://github.com/timmytwopointoh/Project-hail/actions/runs/38918040166):
  job-span **340 s**, APK payload **2,304,080 bytes**, **154 accepted** PNGs
  (**25,528,319 bytes**) and **9 blocked** modal retries.

The APKs are not byte-identical across these *different source commits*:
their SHA256 digests are pinned in
`veilforge/evidence/m34-09-artifact-payloads.json`. Each of the four
role archives has a pinned ZIP SHA256 for independent reproduction. Source
GitHub API job/artifact metadata is pinned in
`veilforge/evidence/m34-09-observed-runs.json`. The measured job span is
not billed compute time. **These two runs are not enough for a speedup
claim**; M34-09 stays partial pending at least three comparable clean runs
and controlled before/after methodology. Neither run demonstrates physical
Moto G hardware performance or artistic/photoreal reference signoff.

Source-only CI:
[38940863117](https://github.com/timmytwopointoh/Project-hail/actions/runs/38940863117)
passed on commit `eb33b174539f6290ee9b6eeb4b5f9052da2180b4`.
It did not launch new emulators or alter any playable game.

## M34-10 — Shared Android PNG truth gate (candidate, CI pending)

New `veilforge/vq_android_qa_sdk.py` centralizes conservative framebuffer
acceptance for the factory and M30 capture tools and independently reopens
actual PNG bytes in both reviewer paths. It rejects forged foreground metrics,
launcher backgrounds, blank frames, modal overlays, missing/altered hashes,
symlinks and out-of-root image paths. The reviewer must install pinned Pillow;
this is deliberate, since trusting a JSON assertion without recomputing pixels
could falsely approve a non-render screenshot. Keep the distinct M30 normal-on/
normal-off noise-control test and factory's 14-view per-asset identity gates.

This branch does **not** consolidate the M30 legacy logcat polling path or
prove Android performance improvements. Real emulator CI and independent
reviewer compatibility are mandatory before marking this candidate verified.

**Compatibility regression discovered and repaired:** the first candidate
CI run 38970974341 correctly failed because old test doubles omitted the
modal score and the static auditor matched an obsolete inline gate string.
Keep the stricter real-frame requirement; update synthetic fixtures and audit
the shared implementation instead of relaxing the screenshot policy.

## M34-10 factory verification

Factory Actions run 38971117494 passed 164 tests, eight producers, four Android 15 roles, 154 real captures, independent PNG pixel recomputation, and LOD/semantic reviews. Source commit 5aec7a0d681896996be9c58e88d6a493c6af4a5a. M30 Android shader comparison and physical device/artistic approval remain pending.

## GEO-02: Read-only connected-region topology audit (2026-10-16)

`vq_topology_regions.py` analyzes geometric welded-edge connected components
without editing OBJ data. Per-region evidence includes source SHA256, boundary,
nonmanifold, degenerate, exact-duplicate, material/UV semantic overlay and
inconsistent-winding counts. Do not delete material/UV overlays merely because
their geometric triangles coincide. Open cloth rims may be intentional.
This is diagnosis, not automatic hole repair or artist approval.

Five adversarial tests cover split UV seams, semantic overlays, same-direction
shared edges, disconnected/degenerate components and malformed source.
Commit `1aa75e88d53eb8bcd024c3faa92abc2290526e06`, factory run
`38979589571`: 176 tests, eight producers, four Android 15 roles,
154 real screenshots, independent LOD and semantic reviews. Five semantic
warnings remain. Factory CI verifies compatibility; the regional audit
is not yet integrated into every generated asset's workflow.

Keep failed experiment `feature/veilforge-geo02-safe-cap-20261016`
commit `debd682f4c568aec6757b4f4d6401e80216e8753`
(run `38979439195`, invalid Python syntax) separate and unmerged.
The verified audit lives on `feature/veilforge-geo02-regional-audit-20261016`.
GEO-02 remains partial pending material/UV-safe conservative repair,
real source-region audit integration and visual/hardware approval.


## GEO-02 semantic-safe topology repair (verified 2026-10-16)

Branch `feature/veilforge-geo02-semantic-repair-20261016`, source
`8fbaf9e686808138c68533f724602f0834a6959a`.
Full factory/Android run 38987380107 and six-team high-detail run
38987380176 both succeeded. The factory ran 181 unit tests, eight asset
producers, four Android 15 roles and independent LOD/semantic review.

Previously `topology.py` discarded same-geometry triangles even when UV,
normal, vertex-color, material or group attributes differed. Its candidate
OBJ also lost material/group tags. Now only semantic-exact duplicate
triangles are removed; distinct overlays and material/group face streams
are preserved. Hole caps must have one unambiguous rim material and use
a separate repair group. Existing candidate and evidence files cannot be
overwritten. Source and candidate SHA256 are recorded. Five new adversarial
tests include a real two-material glTF export.

These tests prove technical preservation, not visual improvement. The
repair path does not copy external MTL/texture files, preserve every OBJ
object/smoothing directive, generate full cage baking, or guarantee
watertight artistic geometry. GEO-02 remains partial; physical hardware
and manual artistic signoff are still required. Do not merge into games.

## PERF-01 — Candidate output capacity preflight (verified 2026-10-16)

Source branch `feature/veilforge-perf01-output-preflight-20261016`,
commit `2b37d42dc5ec1d1e64ae8fb8a936169bb6c07d8c`, full factory/Android Actions run
38989416581. The source QA ran **133 tests**; eight independent
asset producers, one Android test APK, four Android 15 emulator roles,
**154 accepted real frames**, the LOD reviewer and semantic reviewer passed.
The semantic reviewer still recorded **six warnings**; a green technical
result is not artistic approval.

**Important invariant:** one selected welded interior edge creates *two*
face-local midpoint OBJ vertices, one for each triangle, so independent
UV/normal corner streams survive seam boundaries. Counting only selected
unique edges would understate output capacity. Before constructing or writing
a candidate, `vq_adaptive_remesh.py` now computes the exact projected raw
vertex, UV and normal counts, rejects over-capacity output, and rejects mixed
corner attributes. After construction, the output counts must match the
preflight prediction. Adversarial tests prove that a rejected recipe leaves
the source unchanged, creates no partial candidate/report, and does not
overwrite an existing review candidate.

This closes **one bounded geometry allocation hazard**, not all PERF-01
acceptance criteria: there is no verified per-tier GPU memory limit, texture
memory accounting, timed job deadline or physical-device P95 frame-time
budget. PERF-01 remains **partial**. The patch is isolated and unmerged;
the refreshed Library snapshot combines this tested patch with the earlier
separately verified GEO-02 recovery tree, and must not be described as a
fully integrated factory CI pass on the combined commit.
