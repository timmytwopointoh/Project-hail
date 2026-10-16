package game.ashenveil.veilbound;

/**
 * VEILFORGE M26: bounded, differentiable anatomical sculpt lessons applied to
 * real M25 mesh coordinates. These eight revision controls are review-only.
 * The baseline M25, armored Bellwarden, and basic hair remain unchanged.
 *
 * The field is a smooth displacement with an analytic inverse-transpose
 * normal transform. This avoids pasting disconnected face plates or
 * creating hard-edged lump seams. It is NOT retopology or AI vision.
 */
public final class M26SculptDials {
    private M26SculptDials(){}
    public static final String[] NAMES={
        "eye_recession","upper_lid_transition","cheek_plane","nose_bridge",
        "jaw_transition","shoulder_flow","chest_flow","ankle_transition"
    };
    public static final int COUNT=NAMES.length;
    private static final class Zone {
        final float ax,y,z,rx,ry,rz,depth;
        Zone(float ax,float y,float z,float rx,float ry,float rz,float depth){
            this.ax=ax;this.y=y;this.z=z;this.rx=rx;this.ry=ry;
            this.rz=rz;this.depth=depth;
        }
    }
    // Actual M24-retargeted M25 coordinates. No armature, clothing or hair
    // coordinates are inferred from an unseen screenshot.
    private static final Zone[] ZONES={
        new Zone(.077f,2.528f,.204f,.052f,.039f,.064f,-.010f),
        new Zone(.077f,2.555f,.191f,.064f,.030f,.063f,-.006f),
        new Zone(.120f,2.488f,.154f,.078f,.086f,.092f,-.009f),
        new Zone(.018f,2.451f,.208f,.066f,.099f,.084f,.006f),
        new Zone(.113f,2.378f,.115f,.107f,.101f,.097f,-.010f),
        new Zone(.449f,1.950f,.082f,.126f,.182f,.124f,-.008f),
        new Zone(.180f,1.843f,.161f,.164f,.154f,.148f,-.007f),
        new Zone(.219f,.235f,.051f,.082f,.155f,.134f,.007f)
    };
    private static float clamp(float x,float lo,float hi){
        return Math.max(lo,Math.min(hi,x));
    }
    public static void validate(float[] dials){
        if(dials==null||dials.length!=COUNT)
            throw new IllegalArgumentException("Eight VEILFORGE sculpt dials required");
        for(float dial:dials)
            if(!Float.isFinite(dial)||dial<0f||dial>1f)
                throw new IllegalArgumentException("Sculpt dial outside [0,1]");
    }
    public static float[] parse(String csv){
        String[] parts=csv.split(",",-1);
        if(parts.length!=COUNT)throw new IllegalArgumentException("Expected eight M26 dials");
        float[] d=new float[COUNT];
        for(int i=0;i<COUNT;i++)d[i]=Float.parseFloat(parts[i]);
        validate(d);return d;
    }
    public static ArtKit.Model apply(ArtKit.Model source,float[] dials){
        validate(dials);
        if(source==null)throw new IllegalArgumentException("No geometry to sculpt");
        float[] v=source.vertices.clone();
        for(int i=0;i<v.length;i+=9){
            float x=v[i],y=v[i+1],z=v[i+2];
            float r=v[i+6],g=v[i+7],b=v[i+8];
            // Only the front of facial skin, including colored eye geometry,
            // and confirmed body-skin points can move. Base hair and garment
            // vertex colors are protected unconditionally.
            boolean coloredFace=y>2.29f&&y<2.60f&&z>.115f&&Math.abs(x)<.275f
                    &&r>.20f&&g>.13f;
            if(!M25SkinPolish.isBodySkin(r,g,b)&&!coloredFace)continue;
            if(y>.0f&&y<1.47f&&Math.abs(x)<.4f&&z<-.11f)
                continue; // no changes to back of modest shorts
            float dz=0f,dxz=0f,dyz=0f,dzz=0f;
            for(int j=0;j<COUNT;j++){
                if(dials[j]==0f)continue;
                Zone q=ZONES[j];
                float ax=Math.abs(x),px=(ax-q.ax)/q.rx;
                float py=(y-q.y)/q.ry,pz=(z-q.z)/q.rz;
                float field=(float)Math.exp(-(px*px+py*py+pz*pz));
                float a=q.depth*dials[j]*field;
                dz+=a;
                dxz+=a*(-2f*px/q.rx)*(x<0f?-1f:1f);
                dyz+=a*(-2f*py/q.ry);
                dzz+=a*(-2f*pz/q.rz);
            }
            dz=clamp(dz,-.027f,.027f);
            v[i+2]=z+dz;
            // Normal of z' = z + displacement(x,y,z).
            float scale=1f+dzz;
            if(scale<.75f)throw new IllegalArgumentException("Deformed face Jacobian");
            float nx=v[i+3]-dxz*v[i+5]/scale;
            float ny=v[i+4]-dyz*v[i+5]/scale;
            float nz=v[i+5]/scale;
            float length=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(!Float.isFinite(length)||length<1.e-7f)
                throw new IllegalArgumentException("Non-finite sculpt normal");
            v[i+3]=nx/length;v[i+4]=ny/length;v[i+5]=nz/length;
        }
        return new ArtKit.Model(v);
    }
}
