# VEILBOUND M23 hand sculpt — evidence-led refinement journal

## Baseline and safeguards
- Approved source baseline: M22, four fingers plus one opposable thumb on each hand, original `ContinuousHuman.build()` preserved.
- New mesh is review-only in `HumanAnatomy.buildWithSculptedHands()`; armored playable game is unchanged.
- M23 OBJ export uses `HumanVariantCLI`, while `ObjMeshLoader` provides independent Android OBJ round-trip verification.
- Candidate ranking is a *proxy*, not a visual pass or automatic game promotion.

## Visual review: M23 first pass (rejected for art quality)
- Source: 50-slot anatomy wave run 38865363644, `m23-anatomy-hands_forearms` artifact.
- Actual offline three-dimensional hand views inspected: `selected/right_hand_front.png` and `selected/right_hand_three_quarter.png` (NOT Android captures).
- Positive: four digits clearly separated, thumb angled away from index finger, existing palms remain present, model is physically triangulated.
- **Defects observed**: overly pointed finger tips; dominant, cylindrical thumb silhouette; strongly visible faceted surfaces; hard-looking nail patches. This is stylized/prototype anatomy, **not photorealism**.
- **Decision**: reject first-pass surface appearance for final approval. Do not merge as production character merely because the tests pass.

## M23 corrective modeling pass
- `HumanHandSculpt`: shaped rings for little, ring, middle and index fingers plus separately opposed thumbs; update distal tip curvature and nail palette.
- `ShapeEngine.loftSmoothCapped`: analytic smooth vertex normals and properly oriented top/bottom cap geometry for future soft-surface asset profiles. Existing armor loft keeps its sharp edges.
- Standalone hand variant includes palm/wrist contours. Embedded human variant uses existing implicit palms instead to avoid doubled palms.
- New `M23 HAND SCULPT` Model Atelier slot enables independent Android camera inspection. Full human preview uses sculpted digits only in the review path.
- High-detail + mobile LOD, OBJ export, 14 off-device viewing angles and six per-hand closeups per anatomy manager.
- Native Android 15 emulator test now requests four actual game renders of new standalone hand asset and a close-up.

## Testing and human approval gates
- Confirmed early unit output before smooth-surface pass: `VEILBOUND_M23_HAND_SCULPT_PASS ultra=10090 lite=2890 obj=2890 attached=16864 ten_distinct_digits` from run 38865064309 (run subsequently failed on an older Atelier index assertion; that test was corrected).
- Concurrent deterministic parallel QA success after M23 worker class registration: run 38865508379.
- The smooth-shaded capped tip revision (commit `fd26d520`) still requires separate final render and Android 15 verification; **do not mark visually accepted** without inspecting real current screenshots.
- Do not spend budget on hair. Continue hand topology, knuckle scale and nail positioning review and preserve existing armored gameplay.
