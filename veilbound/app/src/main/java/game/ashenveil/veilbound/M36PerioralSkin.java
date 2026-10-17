package game.ashenveil.veilbound;

/**
 * M36 opt-in expression corrective for connected facial skin, BEFORE the
 * M24 height retarget. Mouth interior and vermilion remain M35 source meshes.
 * Small real vertex displacements move the skin surrounding the parted lips,
 * philtrum and chin rather than leaving a rigid mask behind an open slit.
 *
 * This is an offline CPU study, not a jaw skeleton, full facial FACS rig,
 * fused mouth topology or photorealistic/art-approved character.
 */
public final class M36PerioralSkin {
    private M36PerioralSkin(){}

    // |x| center, source y, source z, radii, vertical displacement at open=1.
    // Gaussian domains overlap, so no rigid seams at the labial/chin boundary.
    private static final float[][] ZONES={
        {.020f,2.294f,.183f,.065f,.028f,.110f,.0036f},
        {.026f,2.250f,.183f,.075f,.029f,.110f,-.0042f},
        {.043f,2.207f,.138f,.115f,.063f,.125f,-.0076f}
    };

    public static ArtKit.Model deform(ArtKit.Model source,float openness){
        if(source==null||source.vertices==null||source.vertices.length%27!=0)
            throw new IllegalArgumentException("Missing connected facial triangles");
        if(!Float.isFinite(openness)||openness<0f||openness>1f)
            throw new IllegalArgumentException("Openness must be finite 0..1");
        if(openness==0f)return new ArtKit.Model(source.vertices.clone());
        float[] out=source.vertices.clone();
        for(int i=0;i<out.length;i+=9){
            final float x=source.vertices[i],y=source.vertices[i+1],
                        z=source.vertices[i+2];
            if(Math.abs(x)>.25f||y<2.115f||y>2.355f||z<.025f)
                continue;
            if(!M25SkinPolish.isBodySkin(source.vertices[i+6],
                 source.vertices[i+7],source.vertices[i+8]))continue;
            float shift=0f,gx=0f,gy=0f,gz=0f;
            for(float[] q:ZONES){
                float px=(Math.abs(x)-q[0])/q[3];
                float py=(y-q[1])/q[4],pz=(z-q[2])/q[5];
                float d=px*px+py*py+pz*pz;
                if(d>13f)continue;
                float amount=openness*q[6]*(float)Math.exp(-d);
                shift+=amount;
                gx+=amount*(-2f*px/q[3])*(x<0f?-1f:1f);
                gy+=amount*(-2f*py/q[4]);
                gz+=amount*(-2f*pz/q[5]);
            }
            if(Math.abs(shift)<1e-8f)continue;
            if(Math.abs(shift)>.013f)
                throw new IllegalArgumentException("Perioral movement exceeded bound");
            // y' = y + f(x,y,z), so inverse-transpose of I + e_y grad(f).
            float divisor=1f+gy;
            if(!Float.isFinite(divisor)||divisor<.75f)
                throw new IllegalArgumentException("Perioral foldover");
            float oldNy=source.vertices[i+4];
            float nx=source.vertices[i+3]-gx*oldNy/divisor;
            float ny=oldNy/divisor;
            float nz=source.vertices[i+5]-gz*oldNy/divisor;
            float length=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(!Float.isFinite(length)||length<1e-8f)
                throw new IllegalArgumentException("Perioral normal invalid");
            out[i+1]=y+shift;
            out[i+3]=nx/length;out[i+4]=ny/length;out[i+5]=nz/length;
        }
        return new ArtKit.Model(out);
    }
}
