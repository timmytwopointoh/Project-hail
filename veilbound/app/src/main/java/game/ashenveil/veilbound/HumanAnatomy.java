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
    /**
     * M32 experimental human anatomy. New facial, muscle, finger-joint and
     * foot sculpt adjustments are applied only to the separate review mesh.
     * Source M31/M30 and the original playable historical knight stay intact.
     */
    public static ArtKit.Model buildM32Candidate(boolean lite){
        return M32AnatomySurface.sculpt(buildM31Candidate(lite));
    }
    /**
     * M35 opt-in real adult male mouth rebuild. Reuses the original neutral
     * human body and eye anatomy, removes ONLY the old thin legacy lip strips,
     * sculpts supporting continuous facial skin, then adds genuine separate
     * upper/lower vermilion volume and a shallow dark oral opening.
     *
     * The mouth-open diagnostic does not claim production speech/jaw bones.
     * M20-M33, gameplay, hair, 10 fingers, and original knight are unchanged.
     */
    public static ArtKit.Model buildM35Candidate(boolean lite,boolean mouthOpen){
        float[] learned={.42f,.34f,.38f,.24f,.43f,.39f,.38f,.35f};
        ArtKit.Model skin=M35MouthSculpt.sculptConnectedSkin(
            M28SkinContinuity.refine(
                ContinuousHuman.buildM25WithoutDigits(lite,ContinuousHuman.BASE)));
        ArtKit.Model composed=ShapeEngine.combine(
            skin,
            HumanHandSculpt.build(lite,ContinuousHuman.BASE[0]),
            M28FaceSculpt.build(lite,false),
            M35MouthSculpt.build(lite,mouthOpen?1f:0f));
        ArtKit.Model retargeted=M24BodyRetarget.transform(composed);
        ArtKit.Model coloured=M25SkinPolish.apply(retargeted);
        ArtKit.Model learnedBody=M26SculptDials.apply(coloured,learned);
        return M32AnatomySurface.sculpt(
            M31SkinSurfaceNormals.smooth(learnedBody));
    }
    public static ArtKit.Model buildM35Candidate(boolean lite){
        return buildM35Candidate(lite,false);
    }

    /**
     * M36 opt-in expression-aware human. Original M35 neutral is identical;
     * only an open mouth additionally deforms the actual connected cheek and
     * chin skin. Existing M35, historical knight and animation remain intact.
     */
    public static ArtKit.Model buildM36Candidate(boolean lite,float openness){
        if(!Float.isFinite(openness)||openness<0f||openness>1f)
            throw new IllegalArgumentException("M36 expression range 0..1");
        float[] learned={.42f,.34f,.38f,.24f,.43f,.39f,.38f,.35f};
        ArtKit.Model skin=M36PerioralSkin.deform(
            M35MouthSculpt.sculptConnectedSkin(
                M28SkinContinuity.refine(
                    ContinuousHuman.buildM25WithoutDigits(lite,ContinuousHuman.BASE))),
            openness);
        ArtKit.Model combined=ShapeEngine.combine(
            skin,HumanHandSculpt.build(lite,ContinuousHuman.BASE[0]),
            M28FaceSculpt.build(lite,false),
            M35MouthSculpt.build(lite,openness));
        ArtKit.Model colored=M25SkinPolish.apply(
            M24BodyRetarget.transform(combined));
        return M32AnatomySurface.sculpt(
            M31SkinSurfaceNormals.smooth(
                M26SculptDials.apply(colored,learned)));
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
