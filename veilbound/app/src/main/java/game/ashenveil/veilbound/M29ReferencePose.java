package game.ashenveil.veilbound;

/**
 * M29 two real geometry poses for matching user-directed T-pose and relaxed
 * three-quarter studio references. Existing historical knight and source mesh
 * remain untouched. This is a bounded deformation study, not a production
 * retargeter or a motion-capture solution.
 */
public final class M29ReferencePose {
    public static final int T_POSE=0;
    public static final int THREE_QUARTER_RELAXED=1;
    private M29ReferencePose(){}
    private static float clamp(float x){return Math.max(0f,Math.min(1f,x));}
    private static float smooth(float x){
        x=clamp(x);return x*x*(3f-2f*x);
    }
    private static float[] rotate(float x,float y,float nx,float ny,
                                  float pivotX,float pivotY,float angle){
        float c=(float)Math.cos(angle),s=(float)Math.sin(angle);
        float dx=x-pivotX,dy=y-pivotY;
        return new float[]{pivotX+c*dx-s*dy,pivotY+s*dx+c*dy,
                           nx*c-ny*s,nx*s+ny*c};
    }
    public static ArtKit.Model build(ArtKit.Model source,int pose){
        if(source==null||source.vertices.length%27!=0)
            throw new IllegalArgumentException("Source is not triangles");
        if(pose!=T_POSE&&pose!=THREE_QUARTER_RELAXED)
            throw new IllegalArgumentException("Unsupported posed human");
        float[] v=source.vertices.clone();
        for(int i=0;i<v.length;i+=9){
            float x=v[i],y=v[i+1],z=v[i+2];
            float nx=v[i+3],ny=v[i+4],nz=v[i+5];
            int side=x<0f?-1:1;
            float ax=Math.abs(x);
            // True geometric upper arm elevation around the retargeted
            // shoulder socket. Fade through the deltoid; do not rotate the
            // ribcage, neck or hair.
            float shoulderY=M24BodyRetarget.y(side*.445f,1.82f);
            // All four fingers, the thumb, palm and forearm must rotate
            // together: weighting individual digits by lateral X used to
            // produce stretched ribbons even when the welded edge audit
            // passed. Start the blend INSIDE the chest, complete by x=.35.
            // At low Y the torso/pelvis/shorts also reach x=.30.
            // Taper the X influence inward only near the shoulder, keeping
            // the fingers coherently rotated while hips remain planted.
            float lowerBodyGuard=1f-smooth((y-1.48f)/.17f);
            // The inner skin of the forearm reaches x≈.41; keeping it
            // fixed created hanging strip artifacts along the wrist. A
            // narrow .34→.415 blend protects x≈.30 thigh/torso skin while
            // moving the entire radial cross-section with the fingers.
            float threshold=.265f+.075f*lowerBodyGuard;
            float band=.085f-.010f*lowerBodyGuard;
            float arm=smooth((ax-threshold)/band)*
                      smooth((y-.80f)/.12f)*
                      // Stop the high-deltoid movement before the fixed chest/neck
                      // junction; otherwise identical welded seam edges
                      // become four-face nonmanifold pairs in a strict T-pose.
                      (1f-smooth((y-shoulderY+.22f)/.18f));
            // Modest dark shorts are a separate retained material, not a
            // component of the rotating arm skeleton.
            boolean shorts=v[i+6]<.29f&&v[i+7]<.28f&&v[i+8]<.28f
                &&y<1.68f;
            if(shorts)arm=0f;
            if(arm>.0001f){
                float radians=pose==T_POSE?side*1.39f:
                    side*(side<0?.24f:.39f);
                float[] q=rotate(x,y,nx,ny,side*.445f,shoulderY,
                                 radians*arm);
                x=q[0];y=q[1];nx=q[2];ny=q[3];
            }
            // Secondary reference: subtle contrapposto with one leg planted
            // and the opposite slightly rotated at the hip. No raised or
            // crossed feet in the strict T-pose silhouette.
            if(pose==THREE_QUARTER_RELAXED){
                float hipY=M24BodyRetarget.y(side*.205f,1.045f);
                float leg=smooth((ax-.105f)/.092f)*
                          (1f-smooth((y-hipY+.09f)/.23f))*
                          (1f-smooth((ax-.355f)/.10f));
                if(leg>.0001f){
                    float angle=(side<0?-.055f:.085f)*leg;
                    float[] q=rotate(x,y,nx,ny,side*.205f,hipY,angle);
                    x=q[0];y=q[1];nx=q[2];ny=q[3];
                }
            }
            float norm=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(!Float.isFinite(norm)||norm<1e-7f)
                throw new IllegalArgumentException("Invalid posed normal");
            v[i]=x;v[i+1]=y;v[i+2]=z;
            v[i+3]=nx/norm;v[i+4]=ny/norm;v[i+5]=nz/norm;
        }
        return new ArtKit.Model(v);
    }
}
