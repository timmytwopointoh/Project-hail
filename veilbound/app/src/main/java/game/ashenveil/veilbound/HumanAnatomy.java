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
    public static ArtKit.Model build(boolean lite){
        return ShapeEngine.combine(ContinuousHuman.buildWithoutDigits(lite),
                                   HumanHandSculpt.build(lite));
    }
}
