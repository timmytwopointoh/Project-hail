package game.ashenveil.veilbound;

import java.util.Arrays;

/**
 * M28 original face sculpt test: anatomical eye openings with two visibly
 * curved eyelid ribbons, bounded iris/pupil, naturally arched brows,
 * nasal alae and a narrow central lip seam. Head skin is recessed in
 * M28SkinContinuity; all pieces remain provisional real triangle meshes.
 * The original M25 face is preserved for exact before/after review.
 */
public final class M28FaceSculpt {
    private M28FaceSculpt(){}
    public static final float EYE_Y=2.422f, EYE_X=.077f;
    private static final float[] SCLERA={.72f,.626f,.568f};
    private static final float[] IRIS={.263f,.214f,.172f};
    private static final float[] PUPIL={.112f,.099f,.094f};
    private static final float[] LID={.672f,.423f,.337f};
    private static final float[] LID_EDGE={.495f,.320f,.275f};
    private static final float[] BROW={.629f,.401f,.321f};
    private static final float[] NOSTRIL={.480f,.304f,.251f};
    private static final float[] LIPS={.640f,.405f,.357f};
    private static final float[] MOUTH={.376f,.234f,.217f};
    private static final float[] FACE_NORMAL={0f,0f,1f};

    private static final class MeshWriter {
        float[] buffer=new float[4096];int size;
        void vertex(float[] p,float[] n,float[] col){
            if(size+9>buffer.length)buffer=Arrays.copyOf(buffer,buffer.length*2);
            for(float f:p)buffer[size++]=f;
            for(float f:n)buffer[size++]=f;
            for(float f:col)buffer[size++]=f;
        }
        void tri(float[] p,float[] q,float[] r,
                 float[] np,float[] nq,float[] nr,float[] color){
            float ax=q[0]-p[0],ay=q[1]-p[1],az=q[2]-p[2];
            float bx=r[0]-p[0],by=r[1]-p[1],bz=r[2]-p[2];
            float cx=ay*bz-az*by,cy=az*bx-ax*bz,cz=ax*by-ay*bx;
            if(cx*cx+cy*cy+cz*cz<1.e-15f)return;
            if(cz<0){float[] tmp=q;q=r;r=tmp;
                     tmp=nq;nq=nr;nr=tmp;}
            vertex(p,np,color);vertex(q,nq,color);vertex(r,nr,color);
        }
        ArtKit.Model finish(){return new ArtKit.Model(Arrays.copyOf(buffer,size));}
    }
    private static float[] point(float x,float y,float z){
        return new float[]{x,y,z};
    }
    private static float[] eyePoint(float centerX,float centerY,float frontZ,
                                    float rx,float ry,float depth,float t,float theta){
        float xx=(float)Math.cos(theta)*t;
        float yy=(float)Math.sin(theta)*t;
        return point(centerX+rx*xx,centerY+ry*yy,frontZ-depth*t*t);
    }
    private static float[] eyeNormal(float rx,float ry,float depth,float t,float theta){
        float xx=(float)Math.cos(theta)*t;
        float yy=(float)Math.sin(theta)*t;
        float gx=2f*depth*xx/rx,gy=2f*depth*yy/ry;
        float n=(float)Math.sqrt(gx*gx+gy*gy+1f);
        return point(gx/n,gy/n,1f/n);
    }
    private static void lens(MeshWriter w,float centerX,float centerY,float frontZ,
                             float radiusX,float radiusY,float depth,
                             float[] color,int sides){
        for(int ring=0;ring<3;ring++){
            float a=(float)ring/3f,b=(float)(ring+1)/3f;
            for(int i=0;i<sides;i++){
                float t0=(float)(2*Math.PI*i/sides),
                      t1=(float)(2*Math.PI*(i+1)/sides);
                float[] p=eyePoint(centerX,centerY,frontZ,radiusX,radiusY,depth,a,t0);
                float[] q=eyePoint(centerX,centerY,frontZ,radiusX,radiusY,depth,b,t0);
                float[] r=eyePoint(centerX,centerY,frontZ,radiusX,radiusY,depth,b,t1);
                float[] s=eyePoint(centerX,centerY,frontZ,radiusX,radiusY,depth,a,t1);
                float[] pn=eyeNormal(radiusX,radiusY,depth,a,t0);
                float[] qn=eyeNormal(radiusX,radiusY,depth,b,t0);
                float[] rn=eyeNormal(radiusX,radiusY,depth,b,t1);
                float[] sn=eyeNormal(radiusX,radiusY,depth,a,t1);
                w.tri(p,q,r,pn,qn,rn,color);
                if(ring>0)w.tri(p,r,s,pn,rn,sn,color);
            }
        }
    }
    /**
     * Connected upper/lower eyelid bands that follow the eye's ellipse.
     * Inner edge meets the sclera, outer edge dies under connected facial
     * skin. No horizontal black-dash brows or dangling floating plates.
     */
    private static void eyelid(MeshWriter w,float centerX,boolean upper,int segments){
        float begin=upper?0f:(float)Math.PI;
        for(int i=0;i<segments;i++){
            float a=begin+(float)Math.PI*i/segments;
            float b=begin+(float)Math.PI*(i+1)/segments;
            float[] innerA=lidPoint(centerX,a,false,upper);
            float[] outerA=lidPoint(centerX,a,true,upper);
            float[] innerB=lidPoint(centerX,b,false,upper);
            float[] outerB=lidPoint(centerX,b,true,upper);
            w.tri(innerA,outerA,outerB,FACE_NORMAL,FACE_NORMAL,FACE_NORMAL,LID);
            w.tri(innerA,outerB,innerB,FACE_NORMAL,FACE_NORMAL,FACE_NORMAL,LID);
            // A narrow pigmented inner crease hints at lid thickness rather
            // than surrounding the eye with a harsh black circle.
            float[] creaseA=lidCrease(centerX,a);
            float[] creaseB=lidCrease(centerX,b);
            w.tri(innerA,creaseA,creaseB,FACE_NORMAL,FACE_NORMAL,FACE_NORMAL,LID_EDGE);
            w.tri(innerA,creaseB,innerB,FACE_NORMAL,FACE_NORMAL,FACE_NORMAL,LID_EDGE);
        }
    }
    private static float[] lidPoint(float centerX,float theta,boolean outer,boolean upper){
        float sn=(float)Math.sin(theta),cs=(float)Math.cos(theta);
        float rx=outer?.041f:.0310f;
        float ry=outer?(upper?.025f:.022f):.0139f;
        float z=outer?.1815f:.1960f;
        return point(centerX+rx*cs,EYE_Y+ry*sn,z+.0012f*cs*cs);
    }
    private static float[] lidCrease(float centerX,float theta){
        return point(centerX+.0292f*(float)Math.cos(theta),
                     EYE_Y+.0130f*(float)Math.sin(theta),.1985f);
    }
    private static void brow(MeshWriter w,float x,int segments){
        for(int i=0;i<segments;i++){
            float t0=-1f+2f*i/segments,t1=-1f+2f*(i+1)/segments;
            float[] a=browPoint(x,t0,false),b=browPoint(x,t0,true);
            float[] c=browPoint(x,t1,true),d=browPoint(x,t1,false);
            w.tri(a,b,c,FACE_NORMAL,FACE_NORMAL,FACE_NORMAL,BROW);
            w.tri(a,c,d,FACE_NORMAL,FACE_NORMAL,FACE_NORMAL,BROW);
        }
    }
    private static float[] browPoint(float x,float t,boolean lower){
        float y=EYE_Y+.041f+.0050f*(1f-t*t)-.0020f*t;
        float width=(.0018f+.0010f*(1f-t*t))*(lower?-1f:1f);
        // The brow mark now lies just under the connected orbital ridge.
        // Avoid a detached slab visibly sticking out in profile.
        return point(x+t*.0390f,y+width,.1585f+.0020f*(1f-t*t));
    }
    private static void lips(MeshWriter w,int sections){
        for(int layer=0;layer<3;layer++){
            float[] color=layer==1?MOUTH:LIPS;
            for(int i=0;i<sections;i++){
                float a=-1f+2f*i/sections,b=-1f+2f*(i+1)/sections;
                float[] p=lipPoint(a,layer,true),q=lipPoint(a,layer,false);
                float[] r=lipPoint(b,layer,false),s=lipPoint(b,layer,true);
                w.tri(p,q,r,FACE_NORMAL,FACE_NORMAL,FACE_NORMAL,color);
                w.tri(p,r,s,FACE_NORMAL,FACE_NORMAL,FACE_NORMAL,color);
            }
        }
    }
    private static float[] lipPoint(float t,int layer,boolean outer){
        float centerY=layer==0?2.278f:(layer==1?2.273f:2.266f);
        float halfHeight=outer?(layer==1?.0009f:.0034f):.00025f;
        float y=centerY+(outer?(layer==0?halfHeight:-halfHeight):0)
                        +.0027f*(1-t*t);
        float z=.210f+.0040f*(1f-t*t)+(layer==1?.0012f:0f);
        return point(.043f*t,y,z);
    }
    public static ArtKit.Model build(boolean lite){
        return build(lite,true); // preserve exact M28-M33 mouth baseline
    }
    /**
     * M35 can reuse the original M28 eyes and brows without its old
     * three-flat-strip mouth. False is opt-in only for the M35 replacement.
     */
    public static ArtKit.Model build(boolean lite,boolean includeLegacyLips){
        MeshWriter w=new MeshWriter();
        int sides=lite?16:28;
        for(int side:new int[]{-1,1}){
            float x=side*EYE_X;
            lens(w,x,EYE_Y,.2030f,.0293f,.0132f,.0100f,SCLERA,sides);
            // Cornea/iris do not extend outside sclera; both remain inspectable.
            lens(w,x-side*.0025f,EYE_Y,.208f,.0080f,.0089f,.0030f,IRIS,sides);
            lens(w,x-side*.0025f,EYE_Y,.211f,.0037f,.0046f,.0015f,PUPIL,sides);
            eyelid(w,x,true,sides/2);
            eyelid(w,x,false,sides/2);
            brow(w,x,Math.max(8,sides/2));
            // Alae nostrils with subtle underside shade: not black freckles.
            lens(w,side*.026f,2.301f,.217f,.0048f,.0022f,.0018f,NOSTRIL,12);
        }
        if(includeLegacyLips)lips(w,Math.max(12,sides));
        return w.finish();
    }
}
