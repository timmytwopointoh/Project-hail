package game.ashenveil.veilbound;

/** Ensure segmented detailed armor keeps every painted triangle and each joint. */
public final class CharacterRigTest {
    private static void check(boolean b,String msg){if(!b)throw new AssertionError(msg);}
    private static void inspect(ArtKit.Model original,boolean boss,boolean revenant){
        CharacterRig.Parts p=CharacterRig.split(original,boss,revenant);
        check(p.vertices()==original.vertices.length/9,"Art triangles were lost");
        check(p.torso.triangleCount>0,"Torso is missing");
        check(p.leftArm.triangleCount>0&&p.rightArm.triangleCount>0,"Arm missing");
        check(p.leftLeg.triangleCount>0&&p.rightLeg.triangleCount>0,"Leg missing");
        check(p.shoulderY>p.hipY,"Shoulders must be above hips");
    }
    public static void main(String[] args){
        inspect(DetailArtKit.bellwarden(),false,false);
        inspect(DetailArtKit.hushed(),false,true);
        inspect(DetailArtKit.ashKnight(),true,false);
        System.out.println("VEILBOUND_ARTICULATED_RIG_PASS all_vertices all_limbs");
    }
}