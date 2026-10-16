package game.ashenveil.veilbound;

/** Acceptance gate for 4 fingers plus opposable thumb per hand. */
public final class HumanHandsTest {
    private static void yes(boolean b,String why){
        if(!b)throw new AssertionError(why);
    }
    public static void main(String[] args){
        for(int side:new int[]{-1,1}){
            float[] p=ContinuousHuman.digitSeparationProbe(side);
            yes(p.length==9,"Expect 4 fingertip, 3 gap, 1 thumb, 1 web probes");
            for(int finger=0;finger<4;finger++)
                yes(p[finger]<-.001f,"Missing fingertip "+finger+
                    " on "+(side<0?"left":"right")+" hand, SDF "+p[finger]);
            for(int gap=0;gap<3;gap++)
                yes(p[4+gap]>.001f,"Adjacent fingertips have fused into a mitten "+
                    gap+" on "+(side<0?"left":"right")+" hand, SDF "+p[4+gap]);
            yes(p[7]<-.001f,"Missing actual opposable thumb tip");
            yes(p[8]>.001f,"Thumb merged with index into a single appendage");
        }
        System.out.println("VEILBOUND_M21_HANDS_PASS 4_separate_fingers_1_thumb "+
                           "left_right_mirrored_gaps");
    }
}
