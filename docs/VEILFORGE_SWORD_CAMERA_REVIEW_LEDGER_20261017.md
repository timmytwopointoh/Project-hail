# VEILFORGE Android QA camera review — ceremonial_sword

Status: **isolated candidate; full four-emulator retest pending**. Never auto-merge, overwrite the mesh, or claim artistic approval.

## Pinned evidence and distinction
- Initial immutable REVIEW handoff: commit `85f634f58d0a5863186b22a90c1fd74292cc8c2b`, run `38993296206`, artifact `12085917087` (five non-executing review tasks).
- Verified parent: `27399138080f36cc133b85e927c0b5041a28f2a7`, run `38996754894`, actual Android 15 props screenshots artifact `12087183453`, semantic artifact `12087831486`.
- Broadside screenshot `ceremonial_sword/03_yaw75_pitch15.png`: SHA-256 `603ee6f9cd911fd0dbbe91dd038b8bd593b5d857a6ffc20ced2e00a731cfa234`. Edge-on `00_yaw0_pitch15.png`: `ce99bb188b9a14a4ea14856a4307f6cc3fcf318752f74022c08d24334cd41c4a`.
- The thin edge-on silhouette is **intentional**, not evidence of missing blade geometry. Broadside inspection framing is small. Baseline independent semantic coverage: min `0.0006`, max `0.0104`, 13 distinct orbits, zero frame-boundary warnings. These are visibility diagnostics, not aesthetic scores.

## One scoped correction
- Android test viewer ONLY: for `ceremonial_sword`, eye radius changes from generic `max(3, radius*2.35+1.2)` to `max(3, radius*1.75+0.9)`. For pinned `sword_drop` geometry, distance `3.46457 → 3.00000`. Existing ancient-tree override and all other cameras remain unchanged. No model, game, shader, QA threshold or worker edits.
- Analytical transformed-glTF bounding-box projection across all 14 required yaw/pitch views predicts max |vertical NDC| `0.5722 → 0.6708`, minimum projected vertical span `0.8987 → 1.0463`, conservative nearest depth `2.1791` against GLES near plane `2.0`. These predictions **are not Android results**.
- Rejected `2.7` camera distance: conservative near depth `1.8791`, risking clipping. Rejected a global zoom, lighting tweaks and any mesh rewrite based on an edge-on screenshot.

## Acceptance
Require full factory, shared hash-verified GLES APK, four Android 15 emulators, 154 fresh real screenshots, independent LOD and semantic review. Record resulting SHA/run/APK digest, per-angle sword image hashes and measured coverage, plus before/after comparisons. Do not treat a passing technical gate as photorealism, real-phone FPS, or human artistic signoff. Dynamic next-iteration REVIEW tasks remain separate from static `veilforge/queue_backlog.json`.
