package game.ashenveil.veilbound;

/**
 * Bounded geometric retarget of the M24 unarmored source, informed by real
 * reference-sheet visual review. This modifies actual mesh vertex geometry
 * and normals, NOT game actors, the old knight, or the original M20 human.
 *
 * Primary defects corrected: shortened-looking legs, overly long dangling
 * forearms/hands, high bulky torso silhouette. No hair material touched.
 */
public final class M24BodyRetarget {
    private M24BodyRetarget(){}
    private static float clamp(float x){return Math.max(0f,Math.min(1f,x));}
    private static float smooth(float x){x=clamp(x);return x*x*(3f-2f*x);}
    private static float armWeight(float x){
        return smooth((Math.abs(x)-.34f)/.115f);
    }
    private static float legsAndTorso(float y){
        // 25% longer legs and a compact, anatomically plausible ribcage
        // preserve overall stature rather than inflating height arbitrarily.
        if(y<=1.06f)return y*1.255f;
        if(y<=2.02f)return 1.3303f+(y-1.06f)*.802f;
        return 2.10022f+(y-2.02f)*1.07f;
    }
    private static float torsoScale(float y){
        return y<1.06f?1.255f:y<2.02f?.802f:1.07f;
    }
    private static float arm(float y){
        if(y<=1.28f)return 1.065f+(y-.60f)*.80f;
        if(y<=2.02f)return 1.609f+(y-1.28f)*.664f;
        return 2.10036f+(y-2.02f)*1.07f;
    }
    private static float armScale(float y){
        return y<=1.28f?.80f:y<=2.02f?.664f:1.07f;
    }
    /** The same piecewise retarget used for positions and bind joints. */
    public static float y(float x,float y){
        float mix=armWeight(x);
        return legsAndTorso(y)*(1f-mix)+arm(y)*mix;
    }
    private static float verticalScale(float x,float y){
        float w=armWeight(x);
        return torsoScale(y)*(1f-w)+armScale(y)*w;
    }
    public static ArtKit.Model transform(ArtKit.Model original){
        if(original==null||original.vertices.length%27!=0)
            throw new IllegalArgumentException("Invalid source geometry");
        float[] data=original.vertices.clone();
        for(int i=0;i<data.length;i+=9){
            float px=data[i],py=data[i+1];
            float scale=verticalScale(px,py);
            data[i+1]=y(px,py);
            // Inverse transpose of the vertical stretch, approximating
            // local Jacobian; preserve normal unit length for GL + glTF.
            float nx=data[i+3],ny=data[i+4]/scale,nz=data[i+5];
            float len=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(!Float.isFinite(len)||len<1.e-7f)
                throw new IllegalArgumentException("Nonfinite retarget normal");
            data[i+3]=nx/len;data[i+4]=ny/len;data[i+5]=nz/len;
        }
        return new ArtKit.Model(data);
    }
    /**
     * HumanSkeleton's default static M18 joint coordinates require the same
     * anatomical-space remapping in our *review-only* pose preview.
     */
    public static void alignBindJoints(HumanSkeleton skeleton){
        for(float[] joint:skeleton.bind)joint[1]=y(joint[0],joint[1]);
    }
}
