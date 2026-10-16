package game.ashenveil.veilbound;

/**
 * Full-body proportions from the reference sheet: leg length and hand
 * position improve while source M20 and historic Bellwarden stay untouched.
 */
public final class M24BodyRetargetTest {
    private M24BodyRetargetTest(){}
    private static void ok(boolean yes,String message){
        if(!yes)throw new AssertionError(message);
    }
    public static void main(String[] args){
        float floor=M24BodyRetarget.y(.20f,.0f);
        float hip=M24BodyRetarget.y(.20f,1.06f);
        float shoulder=M24BodyRetarget.y(.20f,1.82f);
        float hand=M24BodyRetarget.y(.554f,.614f);
        ok(floor<.05f,"Grounded feet cannot hover");
        ok(hip-floor>1.25f&&hip-floor<1.38f,"Legs insufficient length");
        ok(shoulder-hip>.50f&&shoulder-hip<.82f,
           "Torso no longer within reference proportions");
        ok(hand>.99f&&hand<1.25f,
           "Dangling hands not aligned to natural mid-thigh position");
        ArtKit.Model original=HumanAnatomy.buildWithSculptedHands(true);
        ArtKit.Model candidate=HumanAnatomy.buildM24Candidate(true);
        ok(candidate.triangleCount>=original.triangleCount*.80f,
           "Refinement accidentally discarded most mesh");
        for(int i=0;i<candidate.vertices.length;i+=9){
            float[] p=candidate.vertices;
            float sum=p[i+3]*p[i+3]+p[i+4]*p[i+4]+p[i+5]*p[i+5];
            ok(Float.isFinite(sum)&&Math.abs(sum-1f)<.09f,
               "Retarget broke skin vertex normal");
        }
        HumanSkeleton rig=HumanSkeleton.bind(candidate);
        M24BodyRetarget.alignBindJoints(rig);
        ok(Math.abs(rig.bind[7][1]-M24BodyRetarget.y(rig.bind[7][0],.85f))<.001f,
           "Wrist rotation pivot did not follow retargeted hands");
        System.out.println("VEILFORGE_M24_SILHOUETTE_AND_JOINT_ALIGNMENT_PASS"+
                           " review_only=true");
    }
}
