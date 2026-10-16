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
    public static ArtKit.Model buildWithSculptedHands(boolean lite){
        return buildWithSculptedHands(lite,ContinuousHuman.BASE);
    }
    public static ArtKit.Model buildWithSculptedHands(boolean lite,float[] controls){
        ContinuousHuman.validate(controls);
        return ShapeEngine.combine(ContinuousHuman.buildWithoutDigits(lite,controls),
                                   HumanHandSculpt.build(lite,controls[0]));
    }
}
