# VEILFORGE / VQ — M35 Mouth Sculpt Retry

## Aim

Create a recognizable **real 3D adult man's mouth** on the same unarmored Bellwarden-derived anatomy, following the user's T-pose and three-quarter references. Avoid pretending that a thin painted line is a functional mouth. Preserve the original armored knight as a playable history/Easter egg; all M20–M33 prior models and existing hair, eyes, hands, shorts, and game remain unchanged.

## What failed and what was recovered

- Initial **M33** four-region VQ normal/height baking runs failed because separate facial/hand source triangles touched the same UV island boundaries; the strict VQ M30 bake rejected overlaps. The repaired diagnostic atlas uses both exterior and diagonal texel-safe gutters. [Latest M33 run 38905827024](https://github.com/timmytwopointoh/Project-hail/actions/runs/38905827024) passed all four regional workers.
- Older **M28** mouth used three almost-flat colored strips and a very thin slit. M35 preserves that legacy construction under the existing `M28FaceSculpt.build(boolean)` API, while the new M35-only `M28FaceSculpt.build(boolean,false)` excludes the old lips.
- M35 adds `M35MouthSculpt.sculptConnectedSkin` around the philtrum, lip mounds and oral depression. Lip surfaces form a Cupid's bow, upper and lower vermilion, tapered corners and an actual shallow dark oral opening. An optional partly-open pose changes the visible oral aperture with the **same mesh topology**. Facial normals are derived from smooth surfaces; existing body skin normals use the M31 pipeline.
- Source body, hand digit count, dark shorts and hair are tested; all previous rendered and playable original actors stay unchanged.
- Separate Android Model Studio entries: **M35 MOUTH NEUTRAL** (25), **M35 MOUTH OPEN** (26), **M35 MOUTH T-POSE** (27); imported OBJ remains last. Neutral/open default to head closeup for lips; T-pose is fully framed. These models are lazy-loaded only for review.
- `HumanVariantCLI` now supports `--m35-neutral`, `--m35-mouth-open`, `--m35-tpose` for genuine OBJ exports, 14 body orbit views, 3 face closeups and 6 hand closeups.
- GitHub [M35 first VQ run 38983556738](https://github.com/timmytwopointoh/Project-hail/actions/runs/38983556738) passed M35 Java lip/face/rig tests, exported actual M35 neutral geometry (**61,009 triangles**, **0 nonmanifold edges**, **0 degenerate triangles**, **2,413 open boundary edges**) and reran VQ M30 normal/height baking on source face, shoulder, hand and foot patches. This is a **technical acceptance** only; no production-grade UV maps, teeth, tongue or skinned jaw yet.
- Actual source-model face pixel comparison across identical cameras (M32 baseline versus M35 neutral) showed differences: front 0.138, side 0.234, three-quarter 0.195 mean RGB pixel intensity. Neutral vs open-mouth change: front 0.107, side 0.013, three-quarter 0.059. These are *real source triangle projections*; pixel difference alone does not prove realism.
- Existing native game and worker compilation failed initially because the legacy source manifest did not list `M35MouthSculpt.java`. Registered source and tests in native CI, QA workers, AI worker and emulator workflow. [Worker QA at 38983660441](https://github.com/timmytwopointoh/Project-hail/actions/runs/38983660441) passed all three tracks. Most recent native app build, actual mouth screenshots and synchronized four-emulator farm must pass separately before Android success is claimed.

## Remaining visual problems

Review of the actual `face_front.png` and `face_side.png` shows **a real mouth**, but the face is still visibly stylized with hard triangular planes, simplified lower jaw, protruding eyes, and underdeveloped natural lip-to-cheek transitions. A shallow oral patch is not the same as a fully retopologized open oral cavity with gums/teeth/tongue and mandible articulation. VQ's baked normal is a *diagnostic UV patch*, not the finished whole-head UV atlas. We have **not** reached photorealism or anatomically perfect facial animation.

## Repeatable skill taught to VQ/VEILFORGE

1. Review actual image views and log evidence-backed defect; do not automatically promote surface edits based only on valid triangles.
2. Preserve the complete original M28 facial features except the inaccurate M28 mouth in an **opt-in builder**.
3. Sculpt subtle supporting continuous skin first, with bounded Gaussian displacement and inverse-Jacobian normals.
4. Attach custom upper/lower lofted lip volumes with smooth normals and anatomically tapered corners; avoid thin dark sticker/stripe shortcuts.
5. Test lip width, neutral vs parted opening, unchanged topology, normals, full-body cloth/hair material and five digits on each hand.
6. Export and compare identical real 3D front/profile/three-quarter cameras before labeling the model improved.
7. Bake isolated diagnostic face normal and height maps with strict VQ UV overlap checks, source hashes and zero automatic promotion.
8. Confirm native Android **actual face pixels**, logged mouth pose and camera orientation, both LODs and gameplay regression without replacing the historical knight.

**Approval**: test-only candidate; no automated final asset promotion. Next major work must focus on real facial retopology, skin UV/PBR, skeletal lower-jaw deformation and direct visual matching to the reference.
