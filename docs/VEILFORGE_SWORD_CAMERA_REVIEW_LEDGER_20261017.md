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

## First Android retest — rejected capture, preserve as evidence
- Candidate source `90c112a7a4b50036412acedb83bb8b993f637a67`; run `39020510351`, **19/19 CI jobs successful**, four Android emulators and 154 screenshot files, shared APK SHA-256 `de50a87344105a1459ece1c0bbf011bbc68d4f3dd79538b39741f692978ec872`. Independent semantic report artifact `12096970165`; props screenshot artifact `12096771769`.
- **Do not accept this run as 14 valid sword views.** `ceremonial_sword/00_yaw0_pitch15.png` SHA-256 starts `a1bf758b7a428920` and is **byte-for-byte identical** to `treasure_chest/13_yaw325_pitch25.png` from the same artifact. The image visibly shows a chest, not a sword. This is a compositor/asset-transition stale frame that the previous-frame check missed because its digest reset at each asset boundary.
- As a result, the reported sword max coverage `0.0196` is contaminated by the chest and cannot be claimed as a sword improvement. The valid broadside `03_yaw75_pitch15.png` did increase measured silhouette coverage `0.00301 → 0.00396` without edge contact, but full 14-view acceptance remains blocked.
- Corrective **capture-evidence gate** on the same isolated candidate branch: carry the last accepted screenshot SHA across asset transitions, retry an exact stale presented frame, preserve the rejected PNG, and fail closed if no fresh screenshot arrives. Add unit regression for the cross-asset boundary. Do not change semantic thresholds or hide the invalid run. Full 4-emulator and independent semantic/LOD rerun is mandatory.

## Verified full retest — technical acceptance only
- Source `291223bfcc5b39e5a11c7f2e0558febbb235c41a`, run `39020966378`: 19/19 jobs passed, four Android 15 emulators, 154 accepted frames, 8 workers, shared APK SHA-256 `683dcc1221c6f4f10c709b070d75941be5f1ed3b8f1db559b3dd1fdea95705cb`. Independent Android, semantic and LOD checks passed.
- Evidence: props `12097220163`, semantic `12096454129`, LOD `12096792564`, Android gate `12096656998`, REVIEW tasks `12096747834`. All four real screenshot archives independently checked: zero adjacent-asset last/first accepted SHA duplicates. 41 stale retry screenshots preserved (props 10, characters 9, nature 9, scene 13).
- Same 14 sword views and silhouette algorithm, baseline run `38996754894` versus final: min coverage `0.00062 → 0.00087` (+40.3%), max `0.01039 → 0.01367` (+31.6%), mean `0.00442 → 0.00599` (+35.5%), zero edge contacts. Broadside yaw75/pitch15 `0.00301 → 0.00396` (+31.6%). The corrected yaw0 screenshot SHA begins `4eff29b62c2194c7` and shows a sword, not the stale chest.
- Rejected run `39020510351` remains preserved; its sword first frame and cart first frame repeated the previous asset's last image. Five nonblocking semantic REVIEW warnings remain; the camera change does not prove better geometry, photorealism, real-phone performance, or artistic acceptance. No merge/promotion.
