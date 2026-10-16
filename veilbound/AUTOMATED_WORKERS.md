# VEILBOUND automated development workers

**Current system:** our own multi-manager, self-hosted AI coding system using
locally running open-weight Qwen2.5-Coder models. **No Gemini API key or
external inference subscription is required.**

Read [OWN_LOCAL_AI.md](OWN_LOCAL_AI.md) for precise model installation,
inference, safety guarantees, manual testing and the Moto G (2025) target.
Read [HIERARCHICAL_CI_AND_EMULATORS.md](HIERARCHICAL_CI_AND_EMULATORS.md)
for the job hierarchy and optional future multi-emulator farm.

## Operations

- **VEILBOUND - Master AI Worker Manager**: director → 3 division-manager
  jobs → 6 specialist-manager jobs → up to 50 independently reviewed coding
  task slots. Ordinary pushes run **only the planning and management stages**.
- Manual run `run_mode=plan_only`: plan/manager review only, no model.
- Manual run `run_mode=coding_proposals`: each selected coding worker starts
  Ollama privately on its own GitHub runner, downloads a reviewed
  `qwen2.5-coder:1.5b` quantized model, generates strictly scoped Java edits
  and runs real Java regression tests. Default concurrency is 2.
- **VEILBOUND - Own Local AI Real Inference Test**: actual text generation
  from 0.5B and 1.5B CPU models; does not modify game sources.
- **VEILBOUND - Parallel Worker QA**: deterministic tests of manager
  assignment, local model contract, scoped Java compilation and promotion.
- **VEILBOUND - Native 3D Android RPG**: Android 15 single emulator using a
  Moto G (2025)-oriented 1604×720 viewport and model-quality screenshots.
- **VEILBOUND - Parallel Android Emulator Farm**: retained as
  manual-only, for later multi-version checks.

## Limitations and safeguards

The model is **not developed or trained from scratch**; Qwen2.5-Coder is an
open-weight foundation model running inside VEILBOUND-owned inference and
agent logic. Managers are deterministic CI jobs, not separately trained LLMs.
50 coding slots are a **maximum capacity**, not 50 simultaneously running
AI models. On a GitHub runner, model downloads and CPU inference consume
compute minutes. GitHub provides the VM, not an inference API.

The workers can edit only their own allowlisted pure Java files, using
exact-match substitutions; generated commands/workflows are rejected.
Every patch is compiled/tested against the existing Java suite in a temporary
checkout and stored in an artifact. It is **not automatically merged** into
the working game. Multiple proposals in one source domain are alternatives
requiring manual integration and fresh emulator testing.

The coding model is currently **text-only**. Independent visual analysis is
based on deterministic screenshot metrics and a human view of actual PNGs.
A text AI cannot claim it directly understood image pixels.

The game APK itself remains fully **offline**: AI exists in the GitHub
development pipeline, not inside the installed Android app.
