# VQ / VEILFORGE — Start Here (Library Quick Reference)

**Saved on October 16, 2026.** This file belongs to a reproducible snapshot of
the reusable VEYLQUORIN (VQ) / VEILFORGE 3D-asset engine, **not** a completed
photorealistic game or the Android VQ Studio companion app.

## Find and recover the code

- **GitHub project:** https://github.com/timmytwopointoh/Project-hail
- **Pinned verified source base:** commit \`6481720458f99258e19f1ed1fe16071adc508e73\`,
  branch \`feature/veilforge-m34-bounded-logcat-stream\`. Its eight worker/model
  asset families and four-emulator factory passed run
  https://github.com/timmytwopointoh/Project-hail/actions/runs/38918040166.
- **Archive build branch:** \`feature/vq-library-snapshot-20261016\`.
  The archived source copy contains *one exact commit*, plus a JSON index of
  hashes for every included tracked file. This is the place to begin using VQ.
- **Separate, not automatically merged:** M33 connected planar UV chart work,
  VQ Studio offline APK app bridge, and project-specific Kaiyu rigs. Their
  exact branch names and build evidence are in \`BRANCH_AND_BUILD_LEDGER.json\`.

**Recover from Library without Git:** download \`VQ-VEILFORGE-FULL-SOURCE-*.zip\`,
open the ZIP, extract the \`vq-veilforge-source-*.zip\` it contains, then
extract that inner ZIP. Run the included \`veilforge/library_archive.py verify\`
against the inner ZIP. The ZIP contains every tracked source file and GitHub
workflow from the source branch, so both the engine and its Java/Android build
dependencies are available offline. Third-party SDKs, Gradle dependencies,
app signing credentials and Git history are not included.

**Recover with Git (preferred for ongoing development):**
\`\`\`bash
git clone https://github.com/timmytwopointoh/Project-hail.git
cd Project-hail
git fetch origin feature/vq-library-snapshot-20261016
git switch -c vq-recovered origin/feature/vq-library-snapshot-20261016
python3 -m pip install pillow==11.3.0
python3 -m unittest discover -s veilforge/tests -v
\`\`\`

You can see the source without installing anything:
\`veilforge/\` contains mesh creation, sculpting, UVs, materials, 3D inspection,
model exports and Android QA. \`.github/workflows/\` contains GitHub CI and
the four-emulator workers. \`veilforge/tests/\` is the regression-test suite.

## How to create and inspect an asset

From the **repository root** after installing Python 3 and Pillow:

\`\`\`bash
# 1. Generate an actual source 3D mesh + PBR textures.
python3 veilforge/factory.py \
  --catalog veilforge/catalog.json \
  --id rolling_terrain --out build/terrain

# 2. Apply targeted non-destructive sculpt / smooth / detail stamps.
python3 veilforge/vq_brushes.py \
  --obj build/terrain/rolling_terrain.obj \
  --recipe veilforge/vq_brush_demo.json \
  --out build/refined/brushed.obj

# 3. Conforming, budget-limited adaptive triangle subdivision.
# Change the recipe's region and material names for other assets.
python3 veilforge/vq_adaptive_remesh.py \
  --obj build/refined/brushed.obj \
  --recipe veilforge/vq_adaptive_remesh_demo.json \
  --out build/refined/subdivided.obj

# 4. Run VQ's 14 real-source-view technical inspection.
python3 veilforge/vq_model_tools.py \
  --obj build/refined/subdivided.obj \
  --out build/refined/inspection
\`\`\`

**Normals/height baking (two compatible meshes with aligned unique UV
coordinates):**
\`\`\`bash
python3 veilforge/vq_sculpt_detail_patch.py --out build/example-sculpt
python3 veilforge/vq_mesh_baker.py \
  --low build/example-sculpt/source_low.obj \
  --high build/example-sculpt/source_high.obj \
  --out build/example-sculpt/baked --size 128
\`\`\`

**UV preparation if the asset uses tiled or overlapping coordinates:**
\`\`\`bash
python3 veilforge/vq_uv_atlas.py \
  --obj input.obj --out build/unique_uv.obj --size 1024 --padding 2
\`\`\`
This is a **triangle-local UV preparation atlas**, not final contiguous
artist-quality organic unwrapping. Old texture maps must be rebaked. The
strict \`vq_uv_transfer.py\` handles only compatible high/low meshes that
fit corresponding low faces within a bounded projection distance.

## Run the complete model/visual testing process

- **Fast source checks:** \`python3 -m unittest discover -s veilforge/tests -v\`
- **VQ geometry/14-angle worker:** GitHub Actions
  \`.github/workflows/vq-model-tools.yml\`.
- **Entire reusable asset factory, glTF scene assembly and 4 Android 15
  workers:** \`.github/workflows/veilforge-factory.yml\`.
- **High-poly normal-map on/off comparison:**
  \`.github/workflows/vq-m30-android.yml\`.
- **Bounded queue (up to ten total workers, maximum four emulators):**
  \`.github/workflows/veilforge-unified-queue.yml\`.
- **Reports:** workers save geometry/UV/material QA, 14 source-view
  screenshots, verified Android frames, hashes, logcat, LOD/semantic
  warnings and machine-readable artifacts. GitHub Actions artifacts are
  time-limited, so retain important ones separately.

**Review gate:** code passing tests does not mean a character resembles a
reference, is fully realistic, deforms perfectly or meets a phone's frame
budget. Preserve manual artistic, hardware and source-license review.

## A practical mantra

**Reference → immutable source → inspect → localized edit → safe remesh →
UV/tangent/material bake → glTF → 14-angle VQ → Android 4-role import/screens →
repair only measured defects → independent QA → artist approval.**

Never overwrite original meshes, auto-merge unreviewed changes, disable failed
tests, mislabel emulator screenshots as actual mobile hardware tests or promote
a game asset from a technical report alone. Work on a new versioned feature
branch and retain an exact source SHA and artifact digests.

## Newer verified factory source and backup

M34-10 shared Android screenshot truth gate passed factory Actions run
38971117494 on commit 5aec7a0d681896996be9c58e88d6a493c6af4a5a:
164 tests, four real Android 15 emulator roles and 154 PNG frames. The
source branch is feature/veilforge-m34-shared-android-qa-20261016;
the refreshed archive branch is feature/vq-library-snapshot-m34-10-20261016.
The older pinned recovery base remains valid. Separate M30 Android normal-map
comparison, physical-device performance and artist signoff remain open.


## UV-01 source distortion audit (new verified source-only milestone)

Latest independent source QA: Git commit
`cfe85d30cea6ff6efae09f2b73adaa0b32f7e823`, branch
`feature/vq-uv01-distortion-gates-20261016`, GitHub Actions
[run 38974882647](https://github.com/timmytwopointoh/Project-hail/actions/runs/38974882647)
(**171 tests passed**, real source OBJ SHA256 pinned in the playbook).
The new recovery branch is `feature/vq-library-snapshot-uv01-20261016`.
Prior M34-10 Android source backup remains a separate last-known-good version.

After preparing a source OBJ with valid UVs, run:

```bash
python3 veilforge/vq_uv_distortion.py --obj input.obj \
  --out build/uv01_audit.json --texture-size 1024
```

Use `--strict` to reject triangles exceeding the default 4:1 Jacobian
anisotropy or 2:1 area-equivalent density deviation; tune thresholds only
for a documented asset target. The audit never changes the OBJ. It is
**not** an overlap, pixel seam, normal-map lighting, Android screenshot,
real-hardware FPS or artistic approval test. See the playbook and ledger
before adopting its output as a release gate.
