package game.ashenveil.veilbound;
/** Continuous animated pose + six-segment hero geometry acceptance gates. */
public final class HeroPoseTest {
    private static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    private static float[] angles(HeroPose.Frame f){
        return new float[]{f.bob,f.rootPitch,f.rootYaw,f.rootRoll,
            f.leftArmPitch,f.rightArmPitch,f.leftArmRoll,f.rightArmRoll,
            f.leftLegPitch,f.rightLegPitch,f.mantlePitch,f.mantleYaw};
    }
    public static void main(String[] args){
        ArtKit.Model sculpt=CinematicArtKit.bellwarden();
        CharacterRig.Parts rig=CharacterRig.split(sculpt,false,false);
        check(rig.vertices()==sculpt.vertices.length/9,"Hero segmentation lost source triangles");
        check(rig.mantle.triangleCount>100,"Separate fluttering mantle missing");
        check(rig.torso.triangleCount>0&&rig.leftArm.triangleCount>0&&
            rig.rightArm.triangleCount>0,"Hero armor joints are missing");
        check(sculpt.triangleCount>DetailArtKit.bellwarden().triangleCount+2000,
            "Gameplay hero must show the premium sculpt jump");
        HeroPose.Frame f=new HeroPose.Frame();
        float previousYaw=0,maxDelta=0;
        for(int i=0;i<=320;i++){
            float t=CombatMotion.DURATION*i/320f;
            HeroPose.sample(f,t,2f*t,.55f,.4f,CombatMotion.DURATION-t,0f,0f);
            float[] attrs=angles(f);
            for(float value:attrs)check(Float.isFinite(value)&&Math.abs(value)<110,
                "Unstable pose or unacceptable articulation");
            if(i>0)maxDelta=Math.max(maxDelta,Math.abs(f.rootYaw-previousYaw));
            previousYaw=f.rootYaw;
        }
        check(maxDelta<2.1f,"Attack twist contains a discontinuous jerk");
        HeroPose.sample(f,3.5f,2.3f,0f,0f,0,0,0);
        float idlePitch=f.rootPitch,idleCape=f.mantlePitch;
        HeroPose.sample(f,3.5f,2.3f,.9f,.8f,0,0,0);
        check(Math.abs(f.rootPitch-idlePitch)>.1f,"Exertion must change posture");
        check(Math.abs(f.mantlePitch-idleCape)>1f,"Mantle must react to locomotion");
        HeroPose.sample(f,3.5f,2.3f,.3f,.4f,0,.20f,0);
        check(f.rootPitch>7f,"Dodge should visibly lower stance");
        System.out.println("VEILBOUND_HERO_M11_PASS cinematic_hero cloak_6_parts gait_idle_attack_dodge");
    }
}
