# VEYLQUORIN / VEILFORGE — M30 sculpt-to-texture baking and safe cleanup

**Purpose:** Add one missing reusable source-mesh tool, not reinvent a game. All
changes are isolated to `feature/vq-m30-sculpt-baking-cleanup` and preserve
original object files and game source.

## Completed capabilities under this development milestone

- **Real two-resolution geometry**: `vq_sculpt_detail_patch.py` emits a
  low-resolution 32-triangle UV-atlased stone test patch and a higher-resolution
  3,200-triangle wave-sculpted patch. The high-poly sample has real displaced
  vertices; it does not pretend that an unmodified mesh gained detail.
- **General-purpose mesh-derived texture baking**: `vq_mesh_baker.py`
  accepts two independently supplied triangle OBJ files with consistent,
  uniquely unwrapped `UV0` atlas in `[0,1]`. It rasterizes actual
  high-poly vertex normals into the low-poly tangent frame and also emits
  a calibrated signed height/displacement PNG, plus image hashes, UV coverage,
  detailed frame metrics and fail-closed source/budget checks.
- **No ambiguous tile baking**: procedural catalog meshes with tiling UVs
  outside `[0,1]`, stacked UV islands, missing UVs, inverted high-poly
  normals and mismatched UV coverage are rejected rather than faking normals.
  That means `rolling_terrain` currently requires proper UV unwrapping
  before high-to-low baking. This is a known limitation, not silently fixed.
- **Verified material export stays intact**: source-linked M29 multi-material
  glTF remains the supported output for original material textures. The
  refinement pipeline no longer generates an extra single-material diagnostic
  export when source materials are already available. This eliminates one
  truly redundant output without deleting an entrypoint still used by games.
- **Source health audit**: `vq_engine_health.py` parses and hashes twelve
  required Python modules, refuses missing/symlinked/duplicate-definition
  entrypoints, records its scope and does not delete apparently orphaned code.
  No other GitHub branches or Android games are modified.

## What the math does (rather than claims)

For every texel, a UV triangle gives interpolated low-poly position and an
orthonormal basis T/B/N. Corresponding **high-poly geometry** supplies a
smoothed interpolated high normal. The map stores the high normal projected
onto the low-poly T/B/N frame. A signed height texture stores the geometric
normal-direction difference at the same atlas UV, with an explicit world-unit
range. Pixels not covered by both meshes remain neutral. Source files are
hashed before export. Textures are 8-bit PNGs and limited to 64/128/256/512.

This is not a raycast high-to-low cage baker, AO solver, production atlas
unwrapper, full glTF normal-map attachment workflow, physically accurate
shader, or proof of photorealism. UV correspondence is required; overlapping
real-world textures must be unwrapped into a unique atlas first.

## Developer commands

```bash
python3 -m unittest discover -s veilforge/tests -v
python3 veilforge/vq_sculpt_detail_patch.py --out build/m30-sculpt
python3 veilforge/vq_mesh_baker.py \
  --low build/m30-sculpt/source_low.obj \
  --high build/m30-sculpt/source_high.obj \
  --out build/m30-baked --size 128
python3 veilforge/vq_model_tools.py \
  --obj build/m30-sculpt/source_high.obj --out build/m30-inspection
python3 veilforge/vq_engine_health.py --root . \
  --out build/m30-health.json
```

## Remaining production work (must not be marked done)

1. UV atlas unwrap / seam gutter generation, texture dilation and output
   normal baked from arbitrary asymmetrical, disconnected meshes using a
   projection cage when UV correspondence is unavailable.
2. Attach baked textures to specific glTF materials with correct tangent
   attributes, clear RGB linear/sRGB handling, and mip maps.
3. Validate production-quality tangent attributes, true linear/sRGB
   sample paths, calibrated glTF PBR BRDF and mipmap-quality material lighting.
4. Compare physically plausible lights / three camera rigs / different
   resolutions. Add high-to-low map comparisons against approved reference
   images, not a generic software-raster score.
5. Review anatomy, seam behavior and skin/stone detail visually; no asset
   is auto-promoted, even after all technical tests pass.

## M30 actual Android 15 visual bake test (verified)

The isolated renderer `android-probe` now binds glTF normal and AO textures
and constructs a UV-correct per-triangle tangent/bitangent basis. Its test
shader uses a light approximation, not a production glTF BRDF.

`.github/workflows/vq-m30-android.yml` builds a **separate test APK**
containing the low-resolution sample geometry plus its baked high-poly normal
texture. It launches four Android 15 emulator workers with 14 actual orbital
camera screenshots and three matched-angle shading-control frames each.
Each device must reject launcher/splash screenshots by checking the actual
GLES clear background, reject system modals, verify GL material-import logs,
and prove the actual normal-on/off pixel differences exceed same-angle render
jitter. The independent reviewer rehashes each image and rejects incomplete
devices. A failed run cannot silently promote an asset.

GitHub Actions run 38901241312 **passed 6/6 jobs**. Real screenshot
comparisons from the four emulators produced image change fractions of
0.011543, 0.011373, 0.012114 and 0.012091 (roughly 1.14–1.21%).
There were 68 actual screenshot files (56 orbit + 12 matched-angle controls).
These measurements establish genuine, subtle shading changes, not realistic
material appearance. The earlier run 38899915820 failed because it accepted
a launcher screenshot and used a too-coarse >12 RGB pixel difference
threshold. The stricter repeat-control and splash-screen checks fixed that.

No changes were made to Android game source or the main game baseline.
