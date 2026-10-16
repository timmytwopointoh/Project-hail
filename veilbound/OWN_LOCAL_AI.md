# VEILBOUND — Our Own AI Worker System (No Gemini)

VEILBOUND now owns the AI *system*: task allocation, manager hierarchy,
worker prompts, scoped code-edit format, test gates, promotion and QA. The
underlying language model is an **existing open-weight Qwen2.5-Coder model**
loaded into our own private Ollama process. We have **not trained a new
foundation model** or recreated ChatGPT; we own its deployment and agent
logic, and no third-party inference service is required.

## Architecture

```
GitHub Actions director (reads backlog and measured Moto G emulator QA)
  |--> game systems division manager
  |--> visual art division manager
  |--> world tools division manager
              |--> six specialty managers total
                       |--> up to 50 isolated coding job slots
                                |
                                v
                       Official Ollama executable
                          localhost:11434 ONLY
                                |
                        Qwen2.5-Coder 1.5B
                                |
                        schema-constrained JSON
                                |
                      scope checks and exact-match edits
                                |
                        javac and trusted Java tests
                                |
                       patch + report artifact
                                |
                        HUMAN REVIEW REQUIRED
```

The game APK itself remains fully **offline** and does not bundle the AI.
CI workers execute the model on independent GitHub runner VMs. You can
choose to run the same model on your own compatible computer in the
future; the initial implementation is GitHub-runner-hosted, not AI running
on the phone. Each job does briefly download an open-weight model from the
Ollama registry when first launched. The *model download* needs Internet,
but the subsequent **inference is local**. All operations are bounded by
GitHub runner availability, CPU RAM, time and build minutes.

## Run the genuine inference test

Go to [GitHub Actions: VEILBOUND - Own Local AI Real Inference Test](https://github.com/timmytwopointoh/Project-hail/actions/workflows/veilbound-local-ai-smoke.yml).

The smoke runner installs Ollama in a temporary Ubuntu VM, pulls
`qwen2.5-coder:0.5b` (~400 MB), starts a local loopback service, runs
a harmless schema-constrained prompt and requires real generated text.
This is not a fixture or mocked model. The result is saved in
`veilbound-local-ai-actual-inference-proof`. The small model is a smoke
test for the inference plumbing, not the larger default coding model.

## Run AI code workers

When the worker workflow is available and manually dispatchable in
GitHub Actions, open **VEILBOUND - Master AI Worker Manager**, select
`feature/veilbound-parallel-ai-qa` (until integrated), and choose:

- `run_mode: plan_only` — director + 3 division managers + up to 6 team
  managers; no model downloads and no inferred code changes.
- `run_mode: coding_proposals` — launch the allocated coding workers
  with self-hosted inference.
- `max_workers: 6` by default; choose 12, 24 or 50 for bounded proposals.
- `max_parallel: 2` by default to control runner pressure and downloads.

Coding jobs pull `qwen2.5-coder:1.5b` (~986 MB) onto **their own** VM
and run Java proposals/tests. Workers never automatically commit or
merge code to the game. The manager jobs perform deterministic review
logic; they are **not** additional simultaneously loaded AI models.

There is **no Gemini key, paid model subscription or inference API**.
GitHub Actions compute minutes and network downloads are still subject
to account limits.

## Security and verification

- Local inference URL is hardcoded `127.0.0.1:11434`; no model response
  can choose a new inference server or shell command.
- The model is never given repository write credentials, Android signing
  keys, or tokens. Checkout uses `persist-credentials: false`.
- Only 11 trusted Java logic/art/asset sources distributed over six
  disjoint roles can be changed, never CI workflows or render/HUD code.
- Every response must be a JSON object with maximum 3 exact-match
  replacements. Each target string must occur exactly once in its file.
- Proposed Java is compiled and checked against the repository's trusted
  tests in a temporary copy. Output is a patch/report, not a merge.
- No claims of pixel vision: the initial Qwen coder is text-only, so
  visual analysis remains in deterministic screenshot/quality metrics.
  Local AI can discuss those numbers, but does not pretend to have
  interpreted the images themselves.
- `test_local_ai.py` checks localhost-only transport, schema, boundaries,
  missing-server error and no images; `worker_pipeline_selftest.py`
  checks the exact same Java compilation/promotion pathway using a
  deterministic fixture, not a paid AI call.

## Target device and emulator

Only **Motorola Moto G (2025)** is the current acceptance target,
Android API 35 (15), 1604x720 landscape, display density 263,
virtual 4 GB RAM. The primary existing workflow
`VEILBOUND - Native 3D Android RPG` remains active, while the
multiversion 1/2/4/8-device farm has been left manually dispatchable
for later. GPU FPS in an x86_64 SwiftShader emulator is not actual
Motorola hardware FPS. Use a signed physical-device APK test to validate
thermal, battery, input responsiveness and real-world frame pacing.

## Practical limits

The initial 1.5B open-weight model is small enough for standard CI CPU
inference but can be less precise than hosted large coding models.
Real-life editing quality is not proven by smoke tests. More capable
models may require stronger memory/CPU/GPU runners or a dedicated
inference host. Multiple isolated proposals against the same Java
file are alternatives, not automatically mergeable patches.

## AI quality loop (new gates)

The current code worker runs **up to two model attempts** on a single
authorized task. It first checks an exact-schema, 1-3-edit JSON proposal,
blocks no-op or dangerous new Java features (including process/network/file
bridges), compiles the proposed Java in a temporary copy and runs all existing
Java regression suites. If the source match is wrong, the model output is
truncated or Java compilation/tests fail, a **second bounded attempt** can
read the real diagnostic and repair the proposal. No third attempt runs.
A failed final status blocks the GitHub coding job and remains in artifacts
as explicit evidence; it cannot pass as a normal review-only patch.

For manually selected emulator runs, `evidence_guard.py` rejects a missing,
malformed or contradictory `task_plan.json`. A failed Studio model/material/
light interaction is now routed to its own named Studio specialty work item
instead of the generic smoke-test queue. Source-run and source-commit
identifiers are retained for traceability.

Manual `coding_proposals` dispatches now include a downstream **independent
worker-auditor**. Its `worker_scorecard.json` requires every allocated job to
present the exact slot, task, role, approved path list, actual local model
metadata and genuine `proposed_change_passed_java_tests` status. Missing,
duplicated or failing results block the aggregate gate. An accepted score is
not authorization to auto-merge.

The manual **Approve Worker Patch Into Draft PR** workflow now applies the
reviewed exact patch to an isolated checkout **without persisting GitHub write
credentials**, builds a real APK, installs it on the Android 15 emulator at
the Motorola Moto G (2025) viewport, runs actual studio/gameplay touch tests
and saves screenshot/GL evidence. It only opens a draft PR after success.
GitHub write authentication is provided only to the final push step,
following all model-authored Java execution.

Proof hierarchy:
1. **Mocked source selftests** verify planner, exact-match proposal and
   compile/test/promotion mechanics without claiming AI intelligence.
2. **Actual local inference smoke** proves the Qwen 0.5B and 1.5B model can
   run and return valid structured text.
3. **Actual hierarchical local Studio pilot** tests the model generating
   and repairing a real Java candidate. A failed pilot must be reported
   as failed, not as a successful model improvement.
4. **Manual reviewed-patch Android gate** proves the selected candidate
   also built, installed and passed real emulator touch tests.
5. **Physical Moto G (2025)** remains necessary for real graphics speed,
   thermals, interaction feel, battery and final visual acceptance.
