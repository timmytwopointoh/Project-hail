# VEYLQUORIN (VQ) Studio — separate Android companion app

**Status:** early functional prototype. Separate app package
`com.trioncompasitor.vqstudio`. It does not replace, embed or silently
modify Trion Assistant or VEILBOUND. VQ is the consumer-facing project
name; the historical engine source remains under `veilforge/`.

## What it does now

- Shows an interactive illuminated 3D model against a near-black stage.
- Draws highlighted geometry outlines and supports touch orbit, rotation
  and bounded zoom.
- Loads genuine triangulated Wavefront OBJ from Android's file picker.
  The initial demonstration mesh is **not** a created model; loading a
  worker-generated OBJ replaces it.
- Polls GitHub Actions roughly every 15 seconds, foreground only. Job
  step names, status, and run identifiers reflect actual GitHub metadata.
  This is *near-live job telemetry*, not a live 30-fps remote GPU stream.
- Opens the selected job's real GitHub Action artifacts. New workers
  upload an OBJ/glTF early and the 14-view contact sheet next, so an
  intermediate source mesh is available while the job runs. Import that
  OBJ to view it interactively on the black stage.
- Opens Trion's VQ Controller as a separate Android activity. Trion's
  stored GitHub credentials are never sent to VQ.
- Does not silently approve, merge, ship or replace any game model.

## Companion controller (separate repository)

Trion's private `Trion-Assistant-Lab` repository:
`feature/vq-studio-bridge-v1`, file
`offline-assistant/app/src/main/java/com/trioncompasitor/assistant/VQBridgeActivity.java`.

Trion starts an explicit allowlisted public sample model job after a
confirmation. It can also issue a confirmed cancellation for the exact
GitHub run and save your next instructions privately. A correction
**does not mutate an already executing GitHub job**. To apply a change,
cancel/wait for cancellation, then review and run another job.

The local Qwen chat model is not currently a true free-form
text-to-3D neural generator. For now VQ executes existing 3D recipes,
and Trion's user prompt remains a local direction note.
Do not put sensitive creative prompts in a public repository run input.
A private authenticated worker and a real prompt-to-structured-asset planner
are separately required for confidential open-ended generation.

## App installation / execution

GitHub Actions > `VQ Studio - Standalone Android APK`, choose branch
`app/vq-studio-companion-v1`, download the successful APK artifact and
install it on your Android device. Build/install a compatible Trion
companion APK from its own private feature branch when available.
Existing installed Trion v0.2 does not automatically acquire this bridge.

In VQ Studio, choose `Trion controls`; in Trion, choose the `VQ`
tab. Tap start to launch a public preset. Return to VQ Studio to watch
actual workflow steps. `Open current model snapshots on GitHub`
shows early artifact downloads. Once downloaded/unzipped, tap
`Import OBJ` to inspect real source geometry.

This is a two-app workflow. It is not an unseen always-running model
and will not resume without a real GitHub job or device session.

## Screenshot retention and storage

`vq-studio/screenshot_gc.py` validates all 14 source previews and their
SHA-256 digests against the original VQ inspection report, records a
bounded human-review next action, then saves:
- the consolidated 14-angle contact sheet;
- the last orbit frame for immediate viewing;
- the full JSON model QA report;
- all original snapshot hashes and source OBJ identity.

**Only after that checkpoint is verified** does it unlink the 28
temporary individual orbit/mask PNG files from the runner's scratch
directory. The 3-day early-stage artifact and 7-day reviewed artifact
are separate lifecycle settings, not indefinite preservation.
Actual Android emulator captures used by an independent QA review
are NOT deleted by this tool prior to their verification. Source models
and important QA metadata remain stored as limited-retention artifacts.
Before anything is approved for production, save the immutable
chosen asset/source and its required evidence in longer-term storage.

## Live graphics roadmap

For a genuinely self-updating model (changes visible every few seconds,
not just imported milestones), implement a private worker result server
with scoped authentication, immutable incremental OBJ/glTF snapshots,
versioned revisions, and Trion user cancellation/correction checkpoints.
The Android app can then download only new model revisions, validate
source hashes, and replace the viewport model without resetting the
camera. A user-controlled refresh cadence and snapshot garbage collector
can bound phone storage.

Currently no claim is made that GitHub status polling itself
streams changing remote geometry.
