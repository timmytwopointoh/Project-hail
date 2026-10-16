# VEYLQUORIN (VQ) — unified engine charter

## Identity and project stewardship

Project identity: **VEYLQUORIN**. Short form: **VQ**. Historical name: **VEILFORGE**.
Named project steward and rights claimant: **Timothy Harris**.
Connected repository account: **timmytwopointoh**.
Original conception, direction, priority setting and acceptance feedback came from
Timothy Harris. AI assistance was used for drafting, software implementation,
analysis, model-generation pipelines and iterative testing. This records
collaboration and does **not** name an AI system as a legal co-author or rights
holder. Rights claims remain qualified by authorship, contracts and
third-party licenses, as described in docs/ownership/RIGHTS_AND_PROVENANCE.md.

VQ is the umbrella name for the complete development engine and workforce:
- Asset and model generation (characters, creatures, environments, props)
- Human topology and sculpting learning curriculum
- Material/texture preparation, mesh optimization and glTF export
- Work director, division managers, specialist managers and coding workers
- Emulator farm, visual QA, regression analysis and repair proposals
- Secure validation, provenance, artifact storage and promotion gates
- Continuation logs, prioritized backlog and reproducible checkpoints

**VEILBOUND** remains the name of the game/testing grounds, not the workforce
or asset engine. Existing legacy filenames and workflow display names prefixed
"VEILBOUND" are compatibility identifiers until a verified migration changes
their workflow_run dependencies; their management function belongs to VQ.

## Persistent operation without copying ChatGPT

The stable source-code identifier remains VEILFORGE until a separately tested code-and-workflow migration. All new public-facing references should use VEYLQUORIN (VQ).\n\nA ChatGPT conversation is not an exportable runnable language model. The
private weights, hosted runtime, hidden system instructions, retained memory,
and unrestricted persistent assistant execution cannot be packed into GitHub.
Instead store *explicitly project-owned instructions and state* so a separate
authorized AI model or future ChatGPT session can take the next deterministic
work item without reconstructing the project from conversation history.

The system of record is:
1. This charter and docs/ownership/** for governance.
2. ENGINE_MASTER_PLAN.json and queue_backlog.json for priorities.
3. steward_state.json for budget, non-automatic approval and boundaries.
4. Commit SHA, deterministic source recipes, job artifacts, and signed
   timestamp/provenance manifest for reproducibility.
5. CI and test outcomes as evidence; no green CI equals aesthetic approval.

A future AI worker must:
- Read the latest committed charter, roadmap, queue and review evidence.
- Compare the requested task to the actual latest source checkout.
- Create narrow changes on isolated branches or local scratch directories.
- Never disclose credentials, auto-publish protected assets, or exceed quotas.
- Run tests and emulators appropriate to the change, record all failures.
- Archive immutable QA artifacts and offer reviewable proposals.
- Require a human review for production promotion, licenses and payments.

## Checkpoint protocol

Each work cycle should record: task ID, source commit, UTC timestamp,
actual tool/model identity, allowed files, input SHA256, output SHA256,
test command, test conclusion, emulator screenshot artifact IDs,
known failures, and the explicit next action. This is a data contract,
not a claim that an invisible assistant continued running between runs.
Do not falsify benchmarks, 3D renders, provenance or ownership evidence.

## Operating modes

- **Plan-only**: cheap validation and next-task selection, no inference,
  emulator start, game mutation, source writes or automatic merge.
- **Manual 10-slot batch**: max 10 simultaneous matrix jobs, within GitHub
  runner availability; emulator slots included in that cap; proposals and
  test results are evidence, not approved changes.
- **Future recurring supervisor**: explicit opt-in to a schedule on default
  branch, rate limits and a spending cap; GitHub schedule is best-effort and
  may be delayed, skipped or disabled. Do not describe it as indefinite uptime.
- **Future model worker**: separately licensed model runtime with explicit
  compute budgets, scoped tools and recovery checkpoints; never "the full ChatGPT."

Release, human authorship, and third-party component review remain separate
and mandatory. See docs/ownership/THIRD_PARTY_REGISTER.md.
