package game.ashenveil.veilbound;

/** Arc direction and collision tolerance must match the sword's visible motion. */
public final class CombatMotionTest {
    private static void check(boolean b,String msg){if(!b)throw new AssertionError(msg);}
    public static void main(String[] args) {
        check(CombatMotion.progress(CombatMotion.DURATION)==0f,"Attack begins at zero");
        check(CombatMotion.progress(0)==1f,"Attack finishes at one");
        check(CombatMotion.bladeBearing(.34f)>0,"Windup from sword-hand side");
        check(CombatMotion.bladeBearing(.72f)<0,"Follow-through crosses left");
        check(CombatMotion.hits(1.6f,0,.31f,.77f),"Center front is hit");
        check(CombatMotion.hits(2.5f,.65f,.31f,.77f),"Front-right hit");
        check(CombatMotion.hits(2.5f,-.65f,.31f,.77f),"Front-left hit");
        check(!CombatMotion.hits(1.5f,(float)Math.PI,.31f,.77f),"Back cannot be hit");
        check(!CombatMotion.hits(4f,0,.31f,.77f),"Beyond blade tip");
        check(!CombatMotion.hits(1.5f,0,.01f,.15f),"Windup is not damage");
        check(!CombatMotion.hits(1.5f,0,.84f,.98f),"Recovery is not damage");
        System.out.println("VEILBOUND_SWORD_ARC_PASS forward_only continuous_angular_sweep");
    }
}