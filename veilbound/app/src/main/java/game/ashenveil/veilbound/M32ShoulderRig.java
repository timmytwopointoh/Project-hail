package game.ashenveil.veilbound;

/**
 * M32 reference-rig experiment: the torso is a stable reference, the
 * clavicle/scapula has a small controlled elevation, and the HUMERUS swings
 * about an anatomical shoulder pivot instead of bending at the armpit.
 *
 * This is CPU reference-pose geometry, not a claimed production bone rig.
 * The proven M30 forearm/garment weight gate is reused unchanged, preserving
 * the ten digits, original knight, and all older studio candidates.
 */
public final class M32ShoulderRig {
    public static final int T_POSE=0, RELAXED=1;
    private M32ShoulderRig(){}
    private static float smooth(float x){
        x=Math.max(0f,Math.min(1f,x));
        return x*x*(3f-2f*x);
    }
    private static float scapulaWeight(float ax,float y){
        // Low clavicle/scapula motion in upper chest, not a broad ribcage bend.
        float shoulderY=M24BodyRetarget.y(.445f,1.82f);
        float clavicleY=M24BodyRetarget.y(.310f,1.90f);
        float cx=smooth((ax-.275f)/.105f)*
                 (1f-smooth((ax-.520f)/.12f));
        float cy=smooth((y-shoulderY+.165f)/.125f)*
                 (1f-smooth((y-clavicleY+.015f)/.18f));
        return Math.max(0f,Math.min(1f,cx*cy));
    }
    public static ArtKit.Model pose(ArtKit.Model bind,int type){
        if(type!=T_POSE&&type!=RELAXED)
            throw new IllegalArgumentException("Unknown M32 pose");
        if(bind==null||bind.vertices==null||bind.vertices.length%27!=0)
            throw new IllegalArgumentException("Invalid source mesh");
        float[] v=bind.vertices.clone();
        for(int i=0;i<v.length;i+=9){
            float x=v[i],y=v[i+1],z=v[i+2];
            float nx=v[i+3],ny=v[i+4],nz=v[i+5];
            float side=x<0f?-1f:1f;
            float w=M30ReferenceRig.armWeight(x,y,v[i+6],v[i+7],v[i+8]);
            float clav=scapulaWeight(Math.abs(x),y);
            boolean garment=v[i+6]<.29f&&v[i+7]<.28f&&
                            v[i+8]<.28f&&y<1.68f;
            if(garment){w=0;clav=0;}
            if(w<=1e-6f&&clav<=1e-6f)continue;
            // A naturally raised T-pose has slight upward scapular rotation.
            float armAngle=type==T_POSE?1.435f:
                           side<0f?.25f:.39f;
            float clavicleLift=(type==T_POSE?.016f:.004f)*clav;
            float clavicleSlide=side*(type==T_POSE?.010f:.002f)*clav;
            float ax=side*.445f,ay=M24BodyRetarget.y(ax,1.82f);
            float radians=side*armAngle*w;
            float cs=(float)Math.cos(radians),sn=(float)Math.sin(radians);
            float dx=x-ax,dy=y-ay;
            float rotatedX=ax+cs*dx-sn*dy;
            float rotatedY=ay+sn*dx+cs*dy;
            v[i]=rotatedX+clavicleSlide;
            v[i+1]=rotatedY+clavicleLift;
            float rx=cs*nx-sn*ny,ry=sn*nx+cs*ny;
            float norm=(float)Math.sqrt(rx*rx+ry*ry+nz*nz);
            if(!Float.isFinite(norm)||norm<1e-8f)
                throw new IllegalArgumentException("Invalid shoulder-normal transformation");
            v[i+3]=rx/norm;v[i+4]=ry/norm;v[i+5]=nz/norm;
        }
        return new ArtKit.Model(v);
    }
}
