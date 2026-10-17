# VEILBOUND M37 — Shoulder and foot reference landmarks

Date: 16 Oct 2026 (US Eastern). Scope: opt-in adult-male human anatomy **model**, not the original playable armored Bellwarden. Non-destructive source branch: `feature/veilbound-m37-shoulder-foot-reference-20261016`.

## Reference sources (used as geometry guidance, not imported assets)

- [Cleveland Clinic — deltoid muscles](https://my.clevelandclinic.org/health/body/21875-deltoid-muscles): the anterior deltoid arises around the clavicle, lateral fibers from the acromion, and posterior fibers from the scapula. Model the shoulder as an anatomical joint contour rather than a separate circular arm bump.
- [StatPearls / NCBI — arches of the foot](https://www.ncbi.nlm.nih.gov/books/NBK587361/): medial and lateral longitudinal arches plus a transverse arch; medial arch is higher. The calcaneus and metatarsal heads contribute ground contact; avoid a completely flat long foot slab.
- [Anatomy Atlases — medial left foot plate](https://www.anatomyatlases.org/atlasofanatomy/plate08/07lfootmedial.shtml): calcaneus, talus, navicular, first metatarsal and hallux landmarks in profile.
- [Cleveland anatomy references and individual human variation](https://my.clevelandclinic.org/health/body/21875-deltoid-muscles): reference landmarks, not a universal ideal proportion. Current 0.965 shoulder-span value is an aesthetic **candidate**, not a claim that everyone has those proportions.

All anatomy is original procedural geometry; no copyrighted reference image is used as a texture.

## Implementation

1. ContinuousHuman's new opt-in `buildM37WithoutDigits` narrows the shoulder source centers by 3.5% using a separate 12-value source control copy, while retaining 10 attached digits through `HumanHandSculpt.build(lite, 0.965)`.
2. `M32ShoulderRig.pose(source,type,0.965)` moves the shoulder joint pivot with the source shoulder width instead of rotating the new arms about the old pivot.
3. `ContinuousHuman` creates a shorter connected metatarsal base and five tapered toe rays (hallux inward, fifth toe outward), with a controlled mobile sampling grid so narrow rays do not disappear at low LOD.
4. `M37FootSurface` lifts the actual medial plantar surface in a bounded normal-preserving sculpt, retains the lower lateral column, shapes dorsum and heel transitions, and avoids changing face, trousers, eyes, or protected colors.
5. Existing `M35`, `M36`, original human, armored knight and game mechanics remain independently constructible. These additions have their own M37 Studio slots; use Focus Detail on `M37 FEET AND SHOULDERS` to frame the lower extremities.
6. `HumanVariantCLI ... --m37-neutral` and `--m37-tpose` export the real source OBJ and projected frames. `feet_top.png` is a dorsal projection; `feet_side.png` inspects the right foot from its medial side. Their cut boundaries are **inspection cropping**, not proof of source mesh holes.

## Verification and remaining quality gates

- The M37 geometry workflow compiles prior M32/M35/M36 tests and the M37 tests, exports real OBJ + screenshots and rejects blank or unchanged preview PNGs.
- The native Android workflow must pass actual install, render and controls before the Android version can be called emulator-verified. The real-device gate remains separate.
- Structural triangle and normal tests are not certification of realistic foot anatomy or photorealism.
- Next art pass: more explicit individual toe dorsal knuckles and web folds, metatarsal fan taper, cleaner ankle and calcaneus contour, production topology/UV skin normal details, and inspection in a hardware-shaded mobile scene.
