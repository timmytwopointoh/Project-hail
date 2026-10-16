# VEILFORGE — Agent continuation instructions

This file is the portable and non-secret project handoff for future ChatGPT,
Codex, GitHub coding agents, locally deployed Qwen/Ollama, and human maintainers.
It does NOT contain a copy of any proprietary ChatGPT model, system prompt,
hidden reasoning, or access token.

Project steward (self-reported): **Timothy Harris**.
Project engine identity: **VEILFORGE**. Legacy VEILBOUND filenames and Android
game modules are downstream compatibility targets, not an engine rebrand.
The name is a provisional internal working mark; external trademark clearance
is not complete (see docs/ownership/BRAND_NAME_CLEARANCE.md).

## Before undertaking development

1. Read veilforge/VEILFORGE_CHARTER.md.
2. Read veilforge/steward_state.json and the latest GitHub source commit.
3. Read veilforge/ENGINE_MASTER_PLAN.json, veilforge/queue_backlog.json, and
   veilforge/UNIFIED_QUEUE.md before assigning expensive work.
4. Read docs/ownership/RIGHTS_AND_PROVENANCE.md and THIRD_PARTY_REGISTER.md.
5. Review latest test and QA artifacts where available. Failure to find an
   artifact is NOT evidence that it passed.
6. Run Python unit tests, then narrowly scoped Android/emulator tests as
   required, and record both actual results and unresolved limitations.
7. Create a checkpoint in structured artifacts: source_sha, UTC timestamp,
   task ID, domain, proposed change, validation evidence, next actions.
8. Do not merge, publish or promote generated models into games without
   explicit source review, QA and user approval.

## Resource and security rules

- One optional manual unified queue: maximum 10 concurrent work jobs, with
  emulator jobs counted inside that limit; no unlimited worker spawning.
- Use source allowlists, isolated runners, timeouts and immutable artifacts.
- Plan-only steward uses ZERO remote model requests, AI model downloads,
  emulator starts, repository writes or automatic game promotions.
- Never place passwords, user private data, personal signed agreements,
  model/API keys or server credentials into GitHub source or CI logs.
- Third-party code and model weights retain original licenses; do not
  blindly assert all resources belong to the project steward.
- Timestamped source hashes and attestation are evidence of code identity,
  NOT copyright registration, notarization or a signed legal assignment.
- This is not permission to run ongoing paid compute jobs without a
  separately reviewed and explicitly enabled compute schedule.

## Agent continuation protocol

For each new work session, report:
- Last verified source revision / tests / attached artifacts
- Immediate priority from the project's real recorded roadmap
- Proposed minimal scoped edit, rollback path and verification steps
- Open defects and expected manual approval

At the end of work, save that summary as a reviewable artifact or issue/PR.
Do not claim to have continued thinking or making changes between sessions.
