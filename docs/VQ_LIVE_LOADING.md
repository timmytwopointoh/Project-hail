# VQ Studio — automatic verified 3D model loading

**Status:** implemented in two independent Android apps, pending an end-to-end authenticated two-app device acceptance test.

## What happens while a VQ job runs

1. In **Trion Assistant**, open the **VQ** tab. Select an existing asset and optionally a bounded size correction. Confirm a new worker job. Trion saves private artistic direction *locally*, outside the public GitHub workflow inputs.
2. Open **VQ Studio**. It polls the running GitHub job through Trion's authenticated, caller-restricted Android provider, while VQ retains its own black-background interactive 3D renderer.
3. The worker generates a real OBJ and publishes `vq-studio-snapshot-r001-<request-id>` containing `model.obj` and a SHA-256/commit/run-bound `vq_snapshot.json` after structural mesh checks. This stage is labeled **geometry integrity**, not artistic approval.
4. After 14-angle inspection and glTF checks pass, the worker publishes `vq-studio-snapshot-r002-<request-id>` with matching source SHA and **technical review** status. The geometry may be identical at this stage; only its verification status is higher.
5. Trion downloads the selected latest artifact through GitHub Actions using **its existing encrypted GitHub token**. It verifies the originating run, source commit, request ID, revision number, SHA-256, byte count and independent QA status where applicable.
6. Trion keeps at most two cache files and gives only a read-only mesh URI to the actual VQ Studio app. A UID check rejects requests from unrelated applications.
7. VQ Studio verifies the OBJ bytes' SHA-256 again, parses only bounded triangulated geometry and **swaps the mesh without resetting yaw, pitch, zoom, auto-orbit or edge-highlight mode**. On failure it keeps the previously displayed mesh.

**Near-live means worker milestones and job-step updates, usually at roughly 15-second intervals while VQ Studio is open.** It is not a remote video stream or 30-fps streaming GPU geometry. Actual update timing is bounded by GitHub artifact publication, network delays and runner scheduling.

## Phone controls

- **Trion controls** switches apps to approve work, request cancellation, save corrections or submit new jobs.
- **Automatic verified mesh loading ON/OFF** determines whether newly published versions replace the current viewport mesh.
- **Import OBJ** lets you manually inspect another file and automatically disables replacement until you explicitly re-enable it.
- **Rotate / stop**, **Glow edges** and touch orbit/zoom continue to work across automatic model changes.
- Without a connected Trion companion, VQ's public status fallback checks less often (about every 3 minutes) to respect GitHub's anonymous API limits, and genuine authenticated auto-loading is unavailable.

## Privacy, security and storage limits

- The GitHub credential stays in Trion's existing Android Keystore vault.
- Public worker inputs are limited to catalog ID, an opaque 16-character request ID, and a bounded size setting.
- Private free-form modeling prompts are never put in public workflow runs by this implementation.
- Trion follows only limited HTTPS GitHub artifact delivery hosts, checks ZIP member names/counts, caps the unpacked OBJ at 8 MB, validates revision metadata and avoids downloading unchanged artifacts again.
- VQ checks the mesh hash independently before rendering. A SHA check is **integrity evidence**, not a legal authorship certificate or artistic quality guarantee.
- Source geometry has a 120,000-triangle budget for this lightweight Android viewer. The viewport samples triangle faces to protect mobile performance and reports that it is a diagnostic preview.
- After VQ's engine finishes 14-angle checks and writes a durable next-step checkpoint, the worker deletes transient screenshot frames but preserves the contact sheet, latest view, model report and checksums.
- Intermediate GitHub artifacts use limited retention (3 days); the final audited artifact lasts 7 days. Trion's local transient mesh cache holds no more than two source objects.

## Reproducibility and acceptance

Source: `timmytwopointoh/Project-hail`, branch `app/vq-studio-companion-v1`.
Companion: `timmytwopointoh/Trion-Assistant-Lab`, branch `feature/vq-studio-bridge-v1`.

Technical validation consists of VQ snapshot-manifest unit tests, the existing 14-view inspector regression tests, a real generated-model two-revision workflow smoke test, VQ Android emulator install/launch and Trion Java/Android bridge builds. A **real paired-device end-to-end test using a user-connected GitHub session and a manually dispatched job** remains required before we can certify live artifact transfer in production.

No screenshot or self-verification automatically promotes a model to production. Trion's STOP control requests GitHub cancellation and must wait for GitHub confirmation before claiming that the process actually stopped.
