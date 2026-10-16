package game.ashenveil.veilbound;

/** Actual per-vertex eight-pose motion checks; not animation-quality signoff. */
public final class M24AnimationLabTest {
    private static void require(boolean value,String reason){
        if(!value)throw new AssertionError(reason);
    }
    public static void main(String[] args){
        ArtKit.Model original=HumanAnatomy.buildM24Candidate(true);
        HumanSkeleton rig=HumanSkeleton.bind(original);
        M24BodyRetarget.alignBindJoints(rig);
        ArtKit.Model a=M24AnimationLab.frame(original,rig,0);
        ArtKit.Model b=M24AnimationLab.frame(original,rig,2);
        require(a.triangleCount==original.triangleCount &&
                b.triangleCount==original.triangleCount,
                "Animation must not change mesh topology or triangle count");
        float delta=0,maxDelta=0;
        for(int i=0;i<a.vertices.length;i+=9){
            float dx=a.vertices[i]-b.vertices[i];
            float dy=a.vertices[i+1]-b.vertices[i+1];
            float dz=a.vertices[i+2]-b.vertices[i+2];
            float d=(float)Math.sqrt(dx*dx+dy*dy+dz*dz);
            delta+=d;maxDelta=Math.max(maxDelta,d);
            require(Float.isFinite(d)&&d<1.0f,
                    "Rig stress test contains huge inter-frame mesh teleportation");
            float norm=(float)Math.sqrt(
                b.vertices[i+3]*b.vertices[i+3]+
                b.vertices[i+4]*b.vertices[i+4]+
                b.vertices[i+5]*b.vertices[i+5]);
            require(Float.isFinite(norm)&&Math.abs(norm-1)<.09f,
                    "Animated normal no longer normalized");
        }
        require(delta>20f&&maxDelta>.07f,
                "Motion study too subtle or frozen to assess deformation");
        require(M24AnimationLab.FRAMES==8,"Expected bounded 8-frame animation");
        System.out.println("VEILFORGE_M24_EIGHT_FRAME_MOTION_PASS delta="+delta+
                           " max="+maxDelta+" production_approved=false");
    }
}
