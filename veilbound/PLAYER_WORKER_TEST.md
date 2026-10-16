# VEILBOUND M11 — Player-only AI workers proof
This trial uses the newly installed **local Qwen2.5-Coder 1.5B**, not a paid API, to execute *three* isolated specialist proposals under the repository's director → division → team validations. The official native Android emulator validates gameplay separately.

- **Scope:** Bellwarden model, Bellwarden-only player animations, player material logic. Do not alter foes, world, quest logic, controls, global lighting, native workflow, or APK runtime AI.
- **Workers:** models, animation and materials (3 independent offline inference processes on GitHub runners). Each job uses a single task from `player_worker_backlog.json`.
- **Workflow:** `veilbound-player-worker-trial.yml`, executed once when this marker is committed and archived per-worker; no worker source is auto applied.
- **Integration:** review all proposals and reject unsafe/weak ones. A coordinator may implement stronger changes directly as a separate reviewed source commit; do not claim a machine-generated result was merged unless an actual worker artifact passes review and integration.
- **Acceptance:** model studio close-up differs visibly, player gameplay model noticeably improves, limbs/cloak animate with coherent smooth movement and combat swing, no Java/GL/emulator regressions. Document measured FPS and compare gameplay screenshots under same camera.
- **Rollback:** stable v0.10 stays on `feature/veilbound-m10-realism-foundation`; m11 changes isolated.

## Iteration 2 — bounded automated repair
The actual first 1.5B local inference jobs generated source proposals but failed exact-match and Java signature/compilation gates. We now retry at most 3 times with trusted compiler/validation feedback and unchanged safe-file allowlists; all outputs remain review only. This commit is an explicit follow-up trigger for the scoped three-worker test.

## M12 physical-phone realism trial
Three manager-approved local Qwen specialist jobs (models, animation, materials) use the upgraded exact-edit proposal guard and real Java suite. This is a strictly bounded user-requested experimental run; generated code remains in review-only artifacts and does not silently change the release APK. Device release uses separately tested v0.12 Android emulator build and visual screenshots. Focus on helmet articulation, planted-feet gait, fitted plate proportions and stable LOD.
