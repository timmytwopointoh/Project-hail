# VEILFORGE human camera — verified review ledger

Branch: feature/veilforge-human-camera-fit-20261017-h07
Source: 790b813bf8984eed3cc45f7fa140f2b861cab37a
Factory: 39032474382 — 19/19 jobs passed, 155 tests, four Android 15 emulators, 154 accepted screenshots. Independent Android, semantic and LOD gates passed.

Only the human_repaired QA viewer orbit changed: max(3,radius*2.35+1.2) to max(3,radius*1.85+0.9). The original fourteen images showed intact geometry with excessive framing margins. Side-on views remain intentionally thin. Meshes, shaders, other cameras, games and gates are unchanged.

Conservative AABB projection: distance 4.84144 to 3.76667, max vertical NDC 0.67454 to 0.89304, minimum near depth 2.28657 versus plane 2.0. Rejected 1.65 factor: conservative depth 1.97666 crosses the near plane.

Actual 14-angle human screenshot silhouette coverage (before to after): min 0.003255 to 0.005127; max 0.042752 to 0.069499; mean 0.019717 to 0.032697 (+65.8%); median 0.015367 to 0.025865. No edge contacts. All 154 accepted frame digests independently verified across four roles. Source screenshot archives: 12098876954 before, 12100059624 after.

Five nonblocking semantic REVIEW proposals remain. The static queue_backlog.json is separate. No auto-repair, merge, artistic approval, PBR, rigging, or real-phone performance claim. See Library backup for complete evidence and rejected candidate calculations.
