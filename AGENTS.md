**Owner superseding scope, 2026-10-29:** Project-hail is legacy **technique history** only. VQ is the model/QA component of **VEILFORGE Studio**. Codex communicates through private `Trion-Assistant-Lab/veilforge-link` without GitHub Actions. Only latest Peks source is an active game. Extract genuinely reusable animation/anatomy/physics/inspection code after verifying versions and provenance; do not import or restart historical game builds and do not delete unverified unique model techniques. Older workflow/retention advice below is historical, overridden by current manual-only/no-hosted-compute directive.

# Worker Coordination — VEILFORGE / VQ / VEILBOUND

This repository participates in a shared multi-chat model, game, emulator, and Android development pipeline. **First read** the current coordination issue at https://github.com/timmytwopointoh/Project-hail/issues/29 for current tested changes and GitHub Actions storage status. ECHOFORM lives separately: https://github.com/timmytwopointoh/New-game-/issues/4.

## Storage and test integrity
- Never delete or overwrite original game/models, reference images, VQ recovery and backup files, candidate provenance, cross-worker dependencies, or durable repair tasks to save Actions storage.
- Use isolated branches and copy-on-write candidates. Do not merge generated assets into any game without quality acceptance.
- Before editing workflows, inspect the latest source branch, the live workflow, and current test status. Retention improvements from PR #27 and PR #28 were merged into separate specific feature branches; other branches may still use old rules.
- Keep automatic smoke tests for actual runtime/model changes. Do not launch the four-device Android visual farm or the full native3D emulator for docs, schedule or retention-only edits.
- Reuse one APK across emulator workers when possible. Avoid archiving the same APK both as successful unverified and verified builds.
- For fresh *temporary* artifacts, prefer 3 days for intermediary files, 7–14 days for screenshots, and up to 21 days for selected repair evidence. Preserve recovery backups and model references under their own policy.
- A protected storage-reclaim workflow was audited on maintenance/storage-reclaim-20261017. Its deletion allowlist applies only to superseded screenshot/inspection bundles and protects newest two per name/branch, newest successful output, and artifacts younger than three hours. **Do not broaden this allowlist** to VQ backups, unapproved candidates, repair plans, or tested native3D APKs.
- A passed emulator QA means that particular technical gate passed, **not** that a humanoid is photorealistic or artistically final.

Read the handoff issue before claiming cross-chat synchronization. Other ChatGPT conversations do not automatically receive messages from this repository.

## Repeatable storage relief
Use the **Storage recovery - safeguarded audit and reclaim** GitHub Actions workflow on `main`. It is manual only and defaults to `apply=false`, which inventories candidates without deleting anything. Review the candidate count and estimated bytes in the job summary. Select `apply=true` manually to remove at most 125 superseded allowlisted artifacts per invocation. Never add protected backups, source, latest emulator-tested APKs, or repair tasks to this delete allowlist.

## Shared VQ ecosystem contract — 2026-10-17-storage-and-nonregression-v1

Before any further changes read `ecosystem/vq_shared_rules_v1.json`, `docs/VQ_CROSS_REPO_HANDOFF.md`, and `ecosystem/repository_role.json`. The Generate Human work, Human 03 clean-room procedural geometry, and VQShape/1 universal language are existing achievements, not throwaway templates. Preserve their independent branches and QA; do not claim unimported GLB files exist in this repository. No generated mesh or game candidate gets user approval automatically. Keep procedural rebuild recipes, exact hashes, proven techniques, tests, and local offline portability. Only Engine-build may evolve the experimental emulator runtime settings on isolated branches. The other repos use manual/review-gated emulator testing. Never delete approved assets, knowledge, source, references, recovery files, or working game builds to save Actions space.
