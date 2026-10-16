# VEYLQUORIN (VQ) portable AI-worker operating guide

Project instructions and orchestrator data are portable; the model itself
is supplied at runtime. Human project steward: Timothy Harris.

## Roles and hierarchy

The VQ director ranks the next validated defect, dependency
milestone or original asset request. Division managers allocate bounded
source areas, specialist workers generate proposed changes, and QA workers
collect actual unit-test results or emulator screenshots. A reviewer then
classifies evidence as PASS, FAIL or REVIEW_REQUIRED. No role can
self-approve its own aesthetic output or publish to a game.

The historical VEILBOUND manager scripts are compatibility modules of
VQ; preserve existing workflow names until their subscribers and
test suites are migrated together.

## Minimum explicit runtime state

Any external AI or new ChatGPT session must be given:
- Current GitHub repository and immutable commit SHA, not a vague memory.
- Proposed task identity, allowed source paths and work budget.
- Worklogs, acceptance criteria, regressions and the last test result.
- Link/IDs of screenshot, mesh and verification artifacts.
- Exact model/runtime name, license, parameter version and input limits.

Use human review and branch/PR workflows to persist decisions and newly
approved state. Temporary chat context alone is not a durable database.

## Suggested on-demand execution loop

Read committed state -> plan bounded tasks -> produce candidate in an
isolated branch/runner -> run existing trusted tests -> rebuild the frozen
Android scene package if source differs -> route to emulator queue ->
archive hashes and images -> manager independently reviews -> propose
human approval -> checkpoint current unresolved tasks.

Never substitute procedural thumbnail previews for real Android
screenshots, or a visual smoke test for photorealism. Asset acceptance
requires reference-aware evidence and artistic signoff.

## Engineering limits

The tested 10-slot queue is an on-demand orchestration design. Current
working AI proposer code uses Qwen2.5-Coder via Ollama under separate
manual-only workflows; do not imply they are already merged into the unified
10-slot matrix. Schedule-based plan-only health checks require the workflow
to be present on GitHub's default branch. The frequency is an explicit
budget and review decision, not indefinite execution.

Never reveal or attempt to copy proprietary model weights or hidden
system instructions; portable project-specific instructions are enough.
