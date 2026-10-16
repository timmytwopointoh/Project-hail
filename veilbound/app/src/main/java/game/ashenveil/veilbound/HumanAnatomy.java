package game.ashenveil.veilbound;

/**
 * Original unarmored adult prototype shown in the separate human Atelier slot.
 * M20 changes the actual geometry to ONE continuous fused anatomical surface;
 * M17/M19 disconnected loft variants remain preserved on their own branches.
 *
 * This is geometric continuity, not yet a film-quality sculpt, realistic
 * epidermal shaders, or production-ready weight-painted topology.
 */
public final class HumanAnatomy {
    private HumanAnatomy(){}
    /** Keep the proven M20 continuous-surface baseline unmodified. */
    public static ArtKit.Model build(boolean lite){
        return ContinuousHuman.build(lite);
    }
    /**
     * M23 review-only integration, selected in the Android Model Atelier.
     * Explicit opt-in until real front/side/3/4 device views and topology
     * inspection approve the replacement. The armored game is untouched.
     */
    /**
     * M25: gently smoothed whole-body study with independently inspectable
     * facial features and restrained palette work. The previous M24 mesh
     * remains separately constructible for before/after comparison.
     */
    public static ArtKit.Model buildM25Candidate(boolean lite){
        return buildM25Candidate(lite,ContinuousHuman.BASE);
    }
    public static ArtKit.Model buildM25Candidate(boolean lite,float[] controls){
        ContinuousHuman.validate(controls);
        ArtKit.Model composite=ShapeEngine.combine(
            ContinuousHuman.buildM25WithoutDigits(lite,controls),
            HumanHandSculpt.build(lite,controls[0]),
            M25FaceSculpt.build(lite));
        return M25SkinPolish.apply(M24BodyRetarget.transform(composite));
    }
    /**
     * M26 opt-in learning-sculpt candidate. Eight monotonic bounded dials
     * operate on the unchanged M25 source, preserving legacy hero assets.
     */
    public static ArtKit.Model buildM26Candidate(boolean lite,float[] dials){
        return buildM26Candidate(lite,ContinuousHuman.BASE,dials);
    }
    public static ArtKit.Model buildM26Candidate(boolean lite,float[] controls,
                                                   float[] dials){
        ContinuousHuman.validate(controls);
        M26SculptDials.validate(dials);
        return M26SculptDials.apply(buildM25Candidate(lite,controls),dials);
    }
    /**
     * M28 anatomy candidate: body, skull and 5-digit hands are real geometry.
     * Connected skin orbital recesses precede explicitly shaped eyelid rims;
     * M26's conservative shoulder/chest/ankle corrections remain applied.
     * M25 and M26 candidates are preserved as independently selectable tests.
     */
    public static ArtKit.Model buildM28Candidate(boolean lite){
        float[] learned={.42f,.34f,.38f,.24f,.43f,.39f,.38f,.35f};
        return buildM28Candidate(lite,ContinuousHuman.BASE,learned);
    }
    public static ArtKit.Model buildM28Candidate(boolean lite,float[] controls,
                                                   float[] learned){
        ContinuousHuman.validate(controls);
        M26SculptDials.validate(learned);
        ArtKit.Model continuous=M28SkinContinuity.refine(
            ContinuousHuman.buildM25WithoutDigits(lite,controls));
        ArtKit.Model composite=ShapeEngine.combine(
            continuous,HumanHandSculpt.build(lite,controls[0]),
            M28FaceSculpt.build(lite));
        ArtKit.Model retarget=M24BodyRetarget.transform(composite);
        return M26SculptDials.apply(M25SkinPolish.apply(retarget),learned);
    }
    /**
     * M31: reference-driven full-body appearance candidate.
     * The geometry and colors remain exactly M28; only source skin normals
     * gain seam-conscious smoothing. More demanding M30 shoulder weighting
     * applies to its T-pose and relaxed inspection meshes separately.
     */
    public static ArtKit.Model buildM31Candidate(boolean lite){
        return M31SkinSurfaceNormals.smooth(buildM28Candidate(lite));
    }
    public static ArtKit.Model buildWithSculptedHands(boolean lite){
        return buildWithSculptedHands(lite,ContinuousHuman.BASE);
    }
    /**
     * Whole-body M24 VEILFORGE candidate used by the Atelier and offline
     * asset factory only. No change to armored gameplay or M20 baseline.
     * Four separate fingers plus one opposed thumb are retained per hand.
     */
    public static ArtKit.Model buildM24Candidate(boolean lite){
        return buildM24Candidate(lite,ContinuousHuman.BASE);
    }
    public static ArtKit.Model buildM24Candidate(boolean lite,float[] controls){
        ContinuousHuman.validate(controls);
        return M24BodyRetarget.transform(ShapeEngine.combine(
            ContinuousHuman.buildM24WithoutDigits(lite,controls),
            HumanHandSculpt.build(lite,controls[0])));
    }
    public static ArtKit.Model buildWithSculptedHands(boolean lite,float[] controls){
        ContinuousHuman.validate(controls);
        return ShapeEngine.combine(ContinuousHuman.buildWithoutDigits(lite,controls),
                                   HumanHandSculpt.build(lite,controls[0]));
    }
}
