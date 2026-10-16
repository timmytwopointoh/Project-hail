package game.ashenveil.veilbound;

/**
 * VEILFORGE M30: source-aware shoulder skin weights for an opt-in adult male
 * reference rig. A coarse procedural body is NOT a production skinned mesh:
 * this experiment keeps connected triangle source geometry and deforms its
 * shoulder/arm regions with two normalized weights (torso + arm), anchored
 * to retargeted shoulder joints, without treating the thighs as forearms.
 *
 * The earlier M29 pose remains available as a control. No gameplay actor,
 * original knight, source model, garment, hair or final asset is mutated.
 */
public final class M30ReferenceRig {
    private M30ReferenceRig(){}
    public static final int T_POSE=0;
    public static final int RELAXED=1;

    private static float clamp(float x){
        return Math.max(0f,Math.min(1f,x));
    }
    private static float smooth(float x){
        x=clamp(x);
        return x*x*(3f-2f*x);
    }

    /**
     * Pose-independent weights evaluated in the BIND pose, never on an
     * already-deformed mesh. Every vertex has torso=1-arm and arm in [0,1].
     * The .39..415 range is OUTSIDE the thigh silhouette at y < 1.54, and
     * the wider shoulder blend happens close to the shoulder's pivot.
     * This separation is grounded in M29's 59,679-triangle strain audit:
     * 1,302 stretched triangles / 55 >10x, mostly y=1.15 / x=.37 thigh.
     */
    public static float armWeight(float x,float y,float red,
                                  float green,float blue) {
        float ax=Math.abs(x);
        float low=1f-smooth((y-1.54f)/.17f);
        float threshold=.27f+.12f*low;
        float width=.20f-.175f*low;
        float w=smooth((ax-threshold)/width);
        w*=smooth((y-.82f)/.12f);
        float shoulderY=M24BodyRetarget.y(.445f,1.82f);
        w*=1f-smooth((y-shoulderY+.22f)/.18f);
        // The historic short pants and props do not inherit the arm bone.
        boolean modestShorts=red<.29f&&green<.28f&&blue<.28f&&y<1.68f;
        if(modestShorts)return 0f;
        return clamp(w);
    }

    public static ArtKit.Model pose(ArtKit.Model source,int pose) {
        if(source==null||source.vertices==null||
           source.vertices.length%27!=0)
            throw new IllegalArgumentException("Expected valid triangle mesh");
        if(pose!=T_POSE&&pose!=RELAXED)
            throw new IllegalArgumentException("Unknown reference rig pose");
        float[] out=source.vertices.clone();
        for(int i=0;i<out.length;i+=9) {
            float x=source.vertices[i],y=source.vertices[i+1],
                  z=source.vertices[i+2];
            float nx=source.vertices[i+3],ny=source.vertices[i+4],
                  nz=source.vertices[i+5];
            float weight=armWeight(x,y,source.vertices[i+6],
                                  source.vertices[i+7],source.vertices[i+8]);
            if(weight<=0f)continue;
            float side=x<0f?-1f:1f;
            float degrees=pose==T_POSE?1.39f:
                (side<0f?.24f:.39f);
            // Shoulder pivot follows exact M24 retarget transform.
            float ax=side*.445f;
            float ay=M24BodyRetarget.y(ax,1.82f);
            float a=side*degrees*weight;
            float c=(float)Math.cos(a),s=(float)Math.sin(a);
            float dx=x-ax,dy=y-ay;
            out[i]=ax+c*dx-s*dy;
            out[i+1]=ay+s*dx+c*dy;
            // Rotation preserves normal magnitude. Normalize after
            // blending to avoid geometric shading seams on mobile GPUs.
            float rx=c*nx-s*ny,ry=s*nx+c*ny;
            float len=(float)Math.sqrt(rx*rx+ry*ry+nz*nz);
            if(!Float.isFinite(len)||len<1.e-7f)
                throw new IllegalArgumentException("Invalid skinned normal");
            out[i+3]=rx/len;out[i+4]=ry/len;out[i+5]=nz/len;
        }
        return new ArtKit.Model(out);
    }
}
