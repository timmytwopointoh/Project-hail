# VEILBOUND Parallel QA and AI Worker Farm

This is an **additive**, opt-in development system. It does not replace the native
Android build, the Model Atelier, the emulator navigation, or the offline game.

## What actually runs

1. **Parallel Worker QA** (automatic on VEILBOUND feature-branch pushes):
   independent GitHub-hosted `combat`, `assets`, and `integrity` jobs.
   Each executes from one immutable commit with its own logs/artifacts. Failures
   in one lane do not stop the others (`fail-fast: false`). These are
   deterministic tests, not AI. The emulator test remains separate and real.
2. **Scoped AI Code Workers** (manual workflow dispatch in normal operation):
   three independent Gemini worker processes with nonoverlapping Java file
   ownership: combat, models, world. The AI suggests up to three exact-match
   source substitutions per lane. The tool applies them to a **temporary
   proposal copy**, runs the pure-Java test suite and uploads the patch and
   validation result. It never pushes, merges, executes generated shell
   commands, or edits Android resources. Human review is mandatory.
3. **Independent Vision AI** (automatically after a successful native Android
   workflow run, once this workflow is on the repository's default branch):
   downloads the screenshot artifact for that *exact* run and sends a small
   selection of resized game screenshots and QA metrics to Gemini. The result
   is a critique artifact, not a false claim of physical-device performance.

The base emulator workflow uses `cancel-in-progress: false` so later edits
cannot destroy the evidence being captured by a currently running test. GitHub
still queues jobs in its concurrency group, preventing unlimited emulator cost.

## Enabling the second AI

1. Create a **Google Gemini API key** in Google AI Studio. Check applicable
   quotas/billing and screenshot/data-sharing policies first.
2. Open GitHub repository **Settings → Secrets and variables → Actions**.
3. Create a repository secret named `GEMINI_API_KEY`. Never place the key
   into source code, app assets, GitHub issues, or ChatGPT messages.
4. Optionally set Actions **variable** `GEMINI_MODEL` to a supported text +
   image model. The default here is `gemini-2.5-flash`; verify availability
   for the connected Google project.
5. Go to **Actions → VEILBOUND - Scoped AI Code Workers → Run workflow**.
   Review the three `veilbound-proposal-*` artifacts and their
   `worker_result.json`, `changes.patch` and `validation.txt` files.

AI calls are **not made** when the key is absent. A workflow passing with
`skipped_no_gemini_key` means the provider was NOT exercised. Enabling the
secret may send the selected public game source and/or screenshots to Google
and can create API charges.

## File ownership

| Worker | Owned files | Outputs |
|---|---|---|
| Combat | CombatMotion, CharacterRig, WorldState | Scoped patch + Java tests |
| Models | ArtKit, CinematicArtKit, DetailArtKit, MaterialTextures, SurfaceAtlas, ObjMeshLoader | Scoped patch + Java tests |
| World | EnvironmentKit, ModelStudio | Scoped patch + Java tests |
| Integrity | Read-only Android manifest, workflow and module inventory | JSON checks |
| Independent Vision | Read-only gameplay / Model Atelier screenshots | Prioritized visual critique |

Workers never modify `ValeRenderer.java`, `WardenHud.java`, Gradle,
workflows, release artifacts or APK identity automatically. Those touch
important runtime boundaries and need a dedicated verified development pass.

## Safety and acceptance

- Each worker proposes changes in a scratch directory. No AI output is
  executed as a shell command or allowed to change CI permissions.
- Patch paths must match an explicit allowlist. Search text must have exactly
  one match. Only existing Java files can be changed.
- Patch validation recompiles the original pure-Java classes and executes
  existing tests; this does **not** replace Android emulator and real-phone QA.
- The AI vision workflow is read-only, uses a known run ID, and never runs code
  from screenshots or downloaded test artifacts.
- Green CI is a functional gate, not proof of photorealistic assets. Human
  visual review and on-device Moto G 2025 FPS/thermal testing remain required.
- Automatic code merges are intentionally not enabled. A reviewed patch goes
  into a normal feature branch/PR, and the native Android workflow must pass.

## Debugging

- Parallel test workers: Actions → **VEILBOUND - Parallel Worker QA**.
- APK/emulator screenshots: Actions → **VEILBOUND - Native 3D Android RPG**.
- AI suggestions: Actions → **VEILBOUND - Scoped AI Code Workers**.
- Visual critiques: Actions → **VEILBOUND - Independent Vision AI**.
- Native emulator still builds its exact commit independently, so coding the
  next version does not alter the APK being inspected.

## Expansion path

Next upgrades can be added safely in this order: baseline screenshot registry,
stable region-of-interest comparisons, test failure clustering, prioritized
issue creation, dynamic worker budgets, branch-per-approved-change, and
merge queues with required Android and physical-device acceptance. Real
autonomous code merging should only be considered after these safeguards.
