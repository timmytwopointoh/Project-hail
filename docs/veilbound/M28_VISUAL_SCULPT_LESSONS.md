# VEILFORGE M28 — Anatomical facial sculpt learning journal

## Reference and preservation

Reference remains the original Bellwarden Base Body Test male anatomy reference sheet. M26 is the valid prior unarmored model. VEILFORGE continues to make isolated candidate assets; VEILBOUND remains the in-game Testing Grounds. The original armored Bellwarden remains playable and labelled as a historical model/Easter egg. Hair is frozen and unchanged. The existing four separate fingers and opposable thumb per hand are mandatory invariants.

## Evidence-backed M26 versus first M28 candidate

Real GitHub Actions producer: [M28 geometry run 38881786907](https://github.com/timmytwopointoh/Project-hail/actions/runs/38881786907). Output artifact: `m28-real-facial-anatomy-14-views-and-reference`, with `m26-baseline/face_front.png`, `face_side.png`, `face_three_quarter.png` and identically framed `m28-candidate` views. **These are actual mesh software projections, not Android screenshots.**

- Replaced many floating flattened eye accents by a physically different orbital skin and sculpted upper/lower eyelid set.
- Eye shape and placement remain simplified and stylized; mouth, cheek, jaw and ear profile still need major retopology and natural transitions.
- The first M28 proof showed a side-profile problem: the eyebrow appeared as a slab projecting forward rather than a skin-integrated form. **Reject brow appearance**; soften color/width and move it beneath the skin orbital ridge. Reduce sclera/iris/pupil and nostril footprint without hiding the eyeball.
- A change in the M26 vs M28 render proves actual geometry changed; camera pixel difference alone is not proof of greater realism or identity to the reference.
- First M28 source triangle counts: M26 59,951 vs M28 59,679; boundary edges M26 1,941 vs M28 2,147; both reported 0 nonmanifold. More open boundaries in M28 are a **topology regression to investigate** even with zero nonmanifold edges. Extra curved eyelid/eye accents are not considered contiguous watertight facial topology. VEILFORGE conservative export repair is not permission to alter the playable model.

## Second bounded correction

File `M28FaceSculpt.java` now puts brow geometry behind the orbital ridge to avoid a floating front-profile bar, reduces eye and iris widths, tones down nostril contrast, and retains the curved upper/lower lids. This must be inspected in real software renders and native Android screenshots before calling it an improvement.

## Lessons to reuse

1. **Patch geometry is not automatically fused anatomy.** Orbital and facial feature geometry should become part of a retopologized facial surface with concentric deformation-friendly eyelid loops; our current curved eyelids are source-study triangles, not connected final topology.
2. **Eye realism requires anatomy and shading together.** Correct pupil count and geometry checks are structural; eyelashes, tear ducts, eye socket sclera recess, skin subsurface response and eyeball orientation need visual inspection.
3. **Side profile is a mandatory failure mode.** Flat facial strips can appear plausible front-on while projecting visibly from the side. Never accept a frontal-only face test.
4. **Whole-body safety remains independent.** Preserve exact hand digits, proportion baseline, historic armored knight, rig and gameplay, and frozen hair while testing eyes and lips.
5. **Honest topology metrics.** Report open boundary edge changes even if the new mesh retains zero nonmanifold edges. No auto-merge based on green CI.
6. **Android proof is separate from source quality.** Four synchronized Android 15 emulators load the exact same APK; manually inspect actual M28 head closeup and animated body, then compare stable original knight gameplay.

## Current approval status

- M28 first software geometry and glTF/PBR pipeline: **PASS** (run 38881786907), with outstanding topology limitation.
- M28 corrected brow/eyes variant: **pending its latest workflow completion and screenshot inspection**.
- Synchronized Android 15 M28 game test: **pending**; unchanged M26 test already passed all four devices (run 38879647975).
- Visual likeness, retopology, polished skin texture and believable facial expressions: **not approved**.

## Verified result of corrected M28 render and mesh repair

GitHub Actions [38882167668](https://github.com/timmytwopointoh/Project-hail/actions/runs/38882167668) completed successfully after the brow and pupil correction. True mesh evidence artifacts: `m28-real-facial-anatomy-14-views-and-reference` and `m28-veilforge-glTF-skin-and-topology-review`.

- M26 raw baseline: **59,951 triangles, 1,941 boundary edges, 0 nonmanifold**.
- Corrected M28 raw: **59,679 triangles, 2,147 boundary edges, 0 nonmanifold**.
- Conservative isolated M28 export repair: **60,171 triangles, 1,267 boundary edges, 0 nonmanifold, 0 degenerate**, with 492 added safe cap triangles.
- **1,267 open edges still remain.** Repair output is an unapproved interchange artifact, not a fixed production mesh.
- Corrected M28 software front/side/three-quarter images show the previous prominent eyebrow slab largely tucked beneath the skin. Eyes and jaw still look stylized/mannequin-like; human visual approval remains false.
- Ten provenance-backed manual observations are now in `veilforge/feedback/sculpt_lessons.json`, including two M28-specific defects. These are data lessons, **not a claim of automated reference image interpretation**.
- Latest native Android 15 farm [38882858869](https://github.com/timmytwopointoh/Project-hail/actions/runs/38882858869) and native game build [38882858816](https://github.com/timmytwopointoh/Project-hail/actions/runs/38882858816) remain separate release gates and must report success before device claims can be made.
