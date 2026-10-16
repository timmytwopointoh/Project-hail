package game.ashenveil.veilbound;

import java.util.Arrays;

/**
 * Subtle, original sculpted facial surface accents in the same local coordinates
 * as ContinuousHuman. Eyes are curved recessed-looking visible surfaces, not
 * textures pasted over a blank head. They remain preview geometry pending a
 * proper eyelid/eye rig and manual front/profile/three-quarter review.
 * Hair, baseline head and player character are not modified.
 */
public final class M25FaceSculpt {
    private M25FaceSculpt(){}
    public static final float EYE_X=.076f, EYE_Y=2.420f;
    public static final float EYE_FRONT=.207f;
    public static final int EYES=2;

    private static final float[] SCLERA={.76f,.655f,.588f};
    private static final float[] IRIS={.235f,.160f,.112f};
    private static final float[] PUPIL={.081f,.069f,.068f};
    private static final float[] LID={.575f,.337f,.266f};
    private static final float[] BROW={.405f,.264f,.212f};
    private static final float[] LIP={.595f,.337f,.310f};
    private static final float[] NOSTRIL={.34f,.215f,.177f};

    private static final class Writer {
        float[] values=new float[4096];
        int used;
        void vertex(float[] p,float[] n,float[] c){
            if(used+9>values.length)values=Arrays.copyOf(values,values.length*2);
            for(int i=0;i<3;i++)values[used++]=p[i];
            for(int i=0;i<3;i++)values[used++]=n[i];
            for(int i=0;i<3;i++)values[used++]=c[i];
        }
        void tri(float[] a,float[] b,float[] c,float[] na,float[] nb,float[] nc,float[] col){
            float ux=b[0]-a[0],uy=b[1]-a[1],uz=b[2]-a[2];
            float vx=c[0]-a[0],vy=c[1]-a[1],vz=c[2]-a[2];
            if((uy*vz-uz*vy)*(uy*vz-uz*vy)+
               (uz*vx-ux*vz)*(uz*vx-ux*vz)+
               (ux*vy-uy*vx)*(ux*vy-uy*vx)<1.e-15f)return;
            vertex(a,na,col);vertex(b,nb,col);vertex(c,nc,col);
        }
        ArtKit.Model finish(){return new ArtKit.Model(Arrays.copyOf(values,used));}
    }
    private static float[] point(float cx,float cy,float front,
                                 float rx,float ry,float depth,float t,float theta){
        float x=(float)Math.cos(theta)*t,y=(float)Math.sin(theta)*t;
        return new float[]{cx+rx*x,cy+ry*y,front-depth*t*t};
    }
    private static float[] norm(float rx,float ry,float depth,float t,float theta){
        float x=(float)Math.cos(theta)*t,y=(float)Math.sin(theta)*t;
        float nx=2*depth*x/rx,ny=2*depth*y/ry;
        float l=(float)Math.sqrt(nx*nx+ny*ny+1);
        return new float[]{nx/l,ny/l,1/l};
    }
    private static void lens(Writer w,float cx,float cy,float front,
                             float rx,float ry,float depth,float[] color,int sides){
        // 3 concentric soft curves. The rim slips under the fused face surface.
        int radial=3;
        for(int r=0;r<radial;r++){
            float t0=(float)r/radial,t1=(float)(r+1)/radial;
            for(int i=0;i<sides;i++){
                float a=(float)(2*Math.PI*i/sides);
                float b=(float)(2*Math.PI*(i+1)/sides);
                float[] p=point(cx,cy,front,rx,ry,depth,t0,a);
                float[] q=point(cx,cy,front,rx,ry,depth,t1,a);
                float[] rr=point(cx,cy,front,rx,ry,depth,t1,b);
                float[] ss=point(cx,cy,front,rx,ry,depth,t0,b);
                float[] pn=norm(rx,ry,depth,t0,a);
                float[] qn=norm(rx,ry,depth,t1,a);
                float[] rn=norm(rx,ry,depth,t1,b);
                float[] sn=norm(rx,ry,depth,t0,b);
                w.tri(p,q,rr,pn,qn,rn,color);
                if(r>0)w.tri(p,rr,ss,pn,rn,sn,color);
            }
        }
    }
    public static ArtKit.Model build(boolean lite){
        Writer w=new Writer();
        int sides=lite?12:24;
        for(int side:new int[]{-1,1}){
            float x=side*EYE_X;
            // Sclera is inset into the sculpted brow and cheek; its tinted
            // surface remains clearly distinct from a painted black dot.
            lens(w,x,EYE_Y,EYE_FRONT,.040f,.020f,.018f,SCLERA,sides);
            lens(w,x-side*.005f,EYE_Y,.211f,.013f,.0135f,.006f,IRIS,sides);
            lens(w,x-side*.005f,EYE_Y,.215f,.0062f,.0075f,.0025f,PUPIL,sides);
            // Upper eyelid hugs the ocular opening, brow sits higher.
            lens(w,x,EYE_Y+.020f,.192f,.043f,.0042f,.004f,LID,sides);
            lens(w,x,EYE_Y+.049f,.179f,.046f,.0055f,.004f,BROW,sides);
            // Small flared nostril shadows flank the fused nasal tip.
            lens(w,side*.029f,2.298f,.236f,.012f,.0045f,.003f,NOSTRIL,sides);
        }
        // Subtle curved upper/lower lip, retaining a neutral expression.
        lens(w,0,2.278f,.214f,.048f,.008f,.004f,LIP,sides);
        lens(w,0,2.264f,.211f,.043f,.009f,.004f,LIP,sides);
        return w.finish();
    }
}
