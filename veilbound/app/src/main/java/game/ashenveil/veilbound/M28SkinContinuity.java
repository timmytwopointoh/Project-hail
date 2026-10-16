package game.ashenveil.veilbound;

/**
 * VEILFORGE M28 surface-continuity lesson:
 * locally sculpt connected facial skin instead of gluing on oversized
 * eye/brow/nose capsules. Source geometry, clothing, hair and knight stay intact.
 * A bounded, smooth z-displacement is applied BEFORE M24 height retarget.
 * This is not retopology, UV skinning, or automatic aesthetic approval.
 */
public final class M28SkinContinuity {
    private M28SkinContinuity(){}
    private static final class Zone {
        final float ax,y,z,rx,ry,rz,amplitude;
        Zone(float ax,float y,float z,float rx,float ry,float rz,float a){
            this.ax=ax;this.y=y;this.z=z;
            this.rx=rx;this.ry=ry;this.rz=rz;this.amplitude=a;
        }
    }
    private static final Zone[] ZONES={
        // Symmetric actual skin recesses behind the orbital openings.
        new Zone(.077f,2.422f,.172f,.056f,.029f,.078f,-.014f),
        // Upper/lower lid support rises continuously from underlying cheek.
        new Zone(.077f,2.455f,.171f,.065f,.020f,.074f,.005f),
        new Zone(.077f,2.395f,.163f,.069f,.020f,.079f,.004f),
        // Nasal bridge and alae are part of the skin, never floating dots.
        new Zone(.011f,2.384f,.185f,.041f,.087f,.087f,.006f),
        // Cheek and jaw lose the excessive capsule-like frontal mass.
        new Zone(.126f,2.367f,.146f,.091f,.072f,.093f,-.007f),
        new Zone(.120f,2.285f,.117f,.111f,.077f,.092f,-.007f),
        // Small philtrum / upper lip transition, not painted lips.
        new Zone(.025f,2.291f,.178f,.044f,.019f,.069f,.003f)
    };
    public static ArtKit.Model refine(ArtKit.Model source){
        if(source==null||source.vertices.length%9!=0)
            throw new IllegalArgumentException("Malformed connected skin model");
        float[] v=source.vertices.clone();
        for(int i=0;i<v.length;i+=9){
            float x=v[i],y=v[i+1],z=v[i+2];
            if(y<2.205f||y>2.515f||z<.052f||Math.abs(x)>.285f)
                continue; // no hair, gameplay clothing or body parts
            if(!M25SkinPolish.isBodySkin(v[i+6],v[i+7],v[i+8]))
                continue;
            float dz=0f,gx=0f,gy=0f,gz=0f;
            for(Zone q:ZONES){
                float ax=Math.abs(x);
                float xx=(ax-q.ax)/q.rx;
                float yy=(y-q.y)/q.ry;
                float zz=(z-q.z)/q.rz;
                float w=(float)Math.exp(-(xx*xx+yy*yy+zz*zz));
                float shift=q.amplitude*w;
                dz+=shift;
                gx+=shift*(-2f*xx/q.rx)*(x<0?-1f:1f);
                gy+=shift*(-2f*yy/q.ry);
                gz+=shift*(-2f*zz/q.rz);
            }
            dz=Math.max(-.022f,Math.min(.022f,dz));
            v[i+2]=z+dz;
            // Inverse transpose of [1 0 0; 0 1 0; gx gy 1+gz].
            float jac=1+gz;
            if(jac<.70f||!Float.isFinite(jac))
                throw new IllegalArgumentException("M28 facial displacement folded over");
            float oldZ=v[i+5];
            float nx=v[i+3]-gx*oldZ/jac;
            float ny=v[i+4]-gy*oldZ/jac;
            float nz=oldZ/jac;
            float length=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(!Float.isFinite(length)||length<1.e-8f)
                throw new IllegalArgumentException("M28 invalid skin normal");
            v[i+3]=nx/length;v[i+4]=ny/length;v[i+5]=nz/length;
        }
        return new ArtKit.Model(v);
    }
}
