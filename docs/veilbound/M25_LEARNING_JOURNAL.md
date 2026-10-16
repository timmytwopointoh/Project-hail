# VEILFORGE M25 — Visual-refinement learning journal

## Visual comparison, first generated review candidate
Source: [M25 anatomy wave 38875627662](https://github.com/timmytwopointoh/Project-hail/actions/runs/38875627662) / `m25-anatomy-head_cranium` artifact, selected real 3D mesh projections `face_front.png` and `face_side.png`. **These are offline mesh renders, not Android screenshots.**
- Mechanical face tests passed for two modeled sclera, irises/pupils; skin and clothing protection passed; 50-slot anatomy worker wave and VEILFORGE mesh/PBR/glTF bridge passed.
- Manual visual verdict: **not approved**. Face resembles a stylized mannequin, with eyes too round and protruding, brows too stark, nostrils like dots, lips too uniform, puffy cheek and jaw volume; visible triangulation and an unrealistic side profile. Do not call this photorealistic or final.
- Lesson: confirmed feature presence and candidate proxy scores cannot substitute for visually credible feature shapes. Uniform convex capsules, color patches and coarse surface sampling produce a toy-like face despite correct markers.

## Corrective changes M25-02
- Reduced sclera width/height and forward projection, downsized iris/pupil, lightened brow/lid color and narrowed facial accents so they sit more naturally against cheek/nose.
- Opt-in M25 SDF has narrower jaw, cheek/nose and ears, leaving M24 baseline untouched.
- Increased face/body mesh sampling from `0.039` to `0.035` unit grid in high detail and `0.062` to `0.055` in mobile M25 only. Preserve fingertip/air-gap rule.
- Native fragment shader uses smoother continuous epidermal tone and separate iris/sclera specular behavior, but NOT authored photorealistic skin pores or a final atlas.
- Re-evaluate *actual* front/profile/three-quarter visuals and rig deformations, reject floating skin plates, painted-on mouths, interpenetrating eye geometry, mesh seams and aliasing.

## Alignment review
- Bilateral head/eye, shoulder, wrist, hip and ankle landmark points are tested in source mesh coordinates and through 0/90/180/315-degree review rotations; mirrored skeleton pivots are checked. The first run incorrectly classified an internally embedded pelvic joint as detached because nearest surface distance was 0.1583 versus a flat 0.15 threshold. Corrected the geometric interpretation for bone origins inside healthy tissue without weakening eye/wrist limits.
- This is **not** proof that every future armor plugin or socket is perfectly weighted or aligned during animation. Full visual socket fitting remains a manual gate.

## Preserve and test
- Hero gameplay model and armor baseline unchanged; original knight stays an accessible Easter egg. Hair untouched.
- M25 face closeup item in VEILFORGE Testing Grounds has native angle switching, no separate app/game.
- 50 candidate slots = 10 scoped manager lanes × 5 bounded numeric proposals, NOT 50 trained autonomous AI workers.
- M25 pipeline separately runs VEILFORGE mesh topology, skin material bake and glTF candidate export. Never automatically repair production mesh or accept an aggregate score.
- First 50-slot revision completed all structural gates; revised face geometry, Android 15 four-emulator performance and visual pass still require independent evidence and human acceptance.

## Second candidate: post-correction visual review
Evidence: [M25 corrected 50-slot run 38876111750](https://github.com/timmytwopointoh/Project-hail/actions/runs/38876111750), head_cranium `face_front.png`, `face_side.png`, `face_three_quarter.png`.
- Compared to the first revision, eyes are narrower and less protruding, brow/lip patches less dark, lower face a little narrower, and high-detail head sampling denser.
- **Still visually rejected for final realism**: eyes remain simple colored convex plates with little surrounding eyelid anatomy, cheeks/jaw are overly faceted, lower-face transition is still puppet-like, and true facial expression/eyelid rigging is missing. Some ragged crop borders in the offline camera are software-render clipping artifacts, not proof of mesh holes.
- Need localized orbital sockets, naturally shaped eyelid rims, real upper/lower lip geometry, improved nasal alae and bridge, connected higher-resolution facial edge loops, retopology and texture coordinates before likeness approval. Do not solve this by adding isolated dot decals or indiscriminately increasing SDF capsules.
- Current VEILFORGE export source: 59,861 triangles, 1,869 open boundary edges, zero nonmanifold and degenerate. Conservative export repair adds 438 safe triangles, reduces boundary edges to 1,073, still zero nonmanifold/degenerate. **Not closed/watertight; not automatically game-approved.**
- M25 technical gates passed on the corrected wave: geometry, 10 candidate managers, offline 14-view meshes, three facial closeup angles, glTF and PBR skin export, manual-approval flag remains false.
