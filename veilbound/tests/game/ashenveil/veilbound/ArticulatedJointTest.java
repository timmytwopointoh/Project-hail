package game.ashenveil.veilbound;

/** M16 true parent-child elbow and knee articulation acceptance. */
public final class ArticulatedJointTest {
    private static void require(boolean value,String why){
        if(!value)throw new AssertionError(why);
    }
    public static void main(String[] args){
        ArtKit.Model full=CinematicArtKit.bellwarden();
        ArtKit.Model lite=CinematicArtKit.bellwardenLite();
        for(ArtKit.Model m:new ArtKit.Model[]{full,lite}){
            CharacterRig.Parts p=CharacterRig.split(m,false,false);
            require(p.vertices()==m.vertices.length/9,
                    "A geometric triangle was lost during eleven-part splitting");
            require(p.leftForearm!=null&&p.rightForearm!=null,
                    "The player elbow children are not real meshes");
            require(p.leftShin!=null&&p.rightShin!=null,
                    "The player knee children are not real meshes");
            require(p.leftForearm.triangleCount>45&&
                    p.rightForearm.triangleCount>45,
                    "Elbow links must own substantial forged steel");
            require(p.leftShin.triangleCount>65&&
                    p.rightShin.triangleCount>65,
                    "Knee links must own the modeled greave and boot");
            require(p.leftArm.triangleCount>55&&p.rightArm.triangleCount>55,
                    "Upper arms vanished when the forearms separated");
            require(p.leftLeg.triangleCount>55&&p.rightLeg.triangleCount>55,
                    "Upper thighs vanished when shins separated");
            require(Math.abs(p.shoulderY-p.elbowY)>.2f&&
                    Math.abs(p.hipY-p.kneeY)>.2f,
                    "Parent and child joint pivots overlap");
        }
        CharacterRig.Parts foe=CharacterRig.split(DetailArtKit.hushed(),false,true);
        require(foe.leftForearm==null&&foe.rightForearm==null&&
                foe.leftShin==null&&foe.rightShin==null,
                "M16 must not change the proven foe limb hierarchy");
        HeroPose.Frame pose=new HeroPose.Frame();
        float lastElbow=0,lastKnee=0;
        for(int i=0;i<=320;i++){
            float phase=3.14159265f*i/160f;
            float swing=i<150?CombatMotion.DURATION*(1f-i/150f):0f;
            HeroPose.sample(pose,i/60f,phase,.90f,.15f,swing,0,0);
            for(float v:new float[]{pose.leftElbowPitch,pose.rightElbowPitch,
                    pose.leftKneePitch,pose.rightKneePitch})
                require(Float.isFinite(v)&&Math.abs(v)<100f,
                        "Joint pose contains nonfinite or broken angle");
            if(i>0){
                require(Math.abs(lastElbow-pose.rightElbowPitch)<9f,
                        "Sword elbow snaps between animation samples");
                require(Math.abs(lastKnee-pose.leftKneePitch)<5f,
                        "Support knee snaps between gait samples");
            }
            lastElbow=pose.rightElbowPitch;
            lastKnee=pose.leftKneePitch;
        }
        HeroPose.sample(pose,1f,1.122f,1f,0f,0f,0,0);
        require(pose.leftKneePitch>20f&&pose.rightKneePitch<10f,
                "Knees do not alternate during the swing phase");
        HeroPose.sample(pose,1f,3.366f,1f,0f,0f,0,0);
        require(pose.rightKneePitch>20f&&pose.leftKneePitch<10f,
                "Right knee fails to bend on its lift phase");
        System.out.println("VEILBOUND_M16_HIERARCHY_PASS 11_pieces "+
                           "elbow_knee_continuity dual_lod untouched_foes");
    }
}
