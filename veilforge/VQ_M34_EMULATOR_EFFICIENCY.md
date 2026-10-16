# VEILFORGE / VEYLQUORIN M34 — Lean, evidence-preserving emulator QA

The new [13-milestone machine-readable plan](VQ_M34_EFFICIENCY_MAP.json)
is a continuation of the existing 34-capability engine-quality roadmap, not
a replacement. M34 focuses on eliminating duplicate worker work **without
lowering visual or geometric acceptance criteria**.

## Implemented in the first engineering pass

**1 — Four independent Android emulators in one wave.** The factory previously
configured `max-parallel: 3` for four emulator roles, so the fourth virtual
device waited for the first wave. M34 sets four concurrent independent GitHub
runners. This reduces the number of *configured scheduling waves* from 2 to 1
if GitHub provides four runners. It does **not** guarantee a particular clock
time or cheaper cloud compute; each worker is still a full Android emulator.

**2 — One setup and screenshot download, both visual algorithms.** The old
factory launched separate LOD and semantic screenshot-review jobs, with two
Python tool installations, two checkouts and two downloads of the same
captures. The new `extended-visual-review` job installs Pillow once,
downloads images once, and runs `visual_lod.py` and `visual_semantics.py`
as *separate independent analysis commands*. It runs the second reviewer
even if the first fails; a nonzero result from either fails the shared job.
The original LOD and semantic report artifact names and directories are
retained so downstream review isn't silently broken.

**3 — Don't download the APK as a screenshot.** Both reviewer jobs previously
used the overbroad `veilforge-android-*` artifact wildcard, which also
matched `veilforge-android-shared-probe-apk`. The downloader now selects
exactly the four role-specific screenshot archives with a brace-expansion
minimatch pattern. The shared APK is still built *once*, verified by SHA256,
and passed to all four emulator workers.

**4 — Standardized presented-frame safeguards.** `android_visual_qa.py`
now checks three independent actual GLES-background pixels in addition to
foreground/contrast and Android modal overlay detection. A launcher/splash
screen cannot pass simply because it contains visible pixels. The M30
material comparison reuses this exact shared predicate instead of carrying
a second copy. Regression tests include deliberately deceptive launcher
screenshots.

**5 — Make performance claims verifiable.** `vq_emulator_efficiency.py`
audits the CI workflow's configured roles, APK hash, max parallelism,
download scope, the independence and fail-closed behavior of both
reviewers, frame-validation integration and report artifact identities.
It writes a versioned JSON report with `runtime_speedup_measured=false`
until actual Actions timing measurements are collected.

## What stays unchanged

- Full **14-angle** real screenshots per source asset and all four
  emulator-role asset assignments; no fabricated or skipped views.
- Independent source and texture hashes, Android GLES build/import checks,
  screenshot hashes, camera movement, QA failures, separate semantic and
  LOD diagnostics, and later artistic review requirements.
- Reproducible source asset factory, Android test APK and other model/game
  branches, with no unreviewed merges or game APK modifications.

## Next stages

M34-06..M34-13 cover safe path-impact routing, evaluated AVD cache,
bounded ADB/logcat polling, measured cloud run and artifact byte costs,
eventual unified screenshot SDK across M30 and all factory/queue workers,
cross-repository import references before orphan code removal, physical
device budgets and final artistic acceptance.

The current technical success criterion is unit + static audit success,
followed by a **real successful factory Android farm and both visual
algorithms**. A green static audit by itself cannot certify emulator
behavior or a speed improvement.

To inspect the implementation in GitHub Actions:
```bash
python3 veilforge/vq_emulator_efficiency.py \
  --root . --out inspection_output/m34-efficiency-audit.json
python3 -m unittest discover -s veilforge/tests -v
```
