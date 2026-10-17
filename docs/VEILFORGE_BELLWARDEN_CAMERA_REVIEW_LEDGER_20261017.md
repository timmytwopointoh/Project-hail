# VEILFORGE Bellwarden camera experiment

Base SHA: 790b813bf8984eed3cc45f7fa140f2b861cab37a
Before screenshots: run 39032474382, artifact 12100059624 (14 views).
Task source: run 38993296206, artifact 12085917087.

Baseline Bellwarden coverage: minimum 0.00336, maximum 0.04015, mean 0.01694. Fourteen images inspected. Dark rear views do not prove a mesh defect. No crop warnings.

Scoped QA camera distance 4.50175 to 4.24910. Conservative near depth 2.73730 to 2.48465, vertical NDC bound 0.86507 to 0.92671. Rejected distance 3.95050: bound 1.01192 risks clipping. No mesh or other asset changes.

After screenshots, source SHA, independent QA results and human artistic approval remain pending.

## Verified Android result (2026-10-17)

Source commit aa9b5ba4913007873993f54bb161c53456b47213, full factory run 39036792271: 19/19 successful jobs, 157 passing unit tests, 4 Android 15 emulators, 154 accepted real-angle frames. Shared GLES APK SHA256 43247247cd71b79403b7fec24e32443574132c0ed439ce9991bd434e9636223c. Android structural gate passed, independent semantic gate passed with zero blocking problems, independent 14-angle mobile LOD review completed with no quality warning. Android gate artifact 12102806620, semantic 12102358279, LOD 12102248495, Bellwarden screenshots 12102756887, APK 12102905652.

Source-image silhouette coverage before (artifact 12100059624) to after (12102756887): minimum 0.00336 to 0.00372; maximum 0.04015 to 0.04411; mean 0.01694 to 0.01891 (+11.61%). All 14 angle fractions increased; screenshot bytes verified against their SHA256 manifest, with stale/modal attempts excluded and preserved in artifact. No crop warnings. The five nonblocking semantic review proposals remain, including dark/edge-on Bellwarden views. This is measured QA framing improvement, not improved anatomy or certified artistic quality. No game/model assets promoted, no changes to static queue_backlog.json, no physical-phone performance claim.
