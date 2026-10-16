package game.ashenveil.veilbound;

import java.util.Arrays;

/**
 * VEILFORGE/VQ M35: a real three-dimensional adult male mouth study.
 *
 * The former M28 prototype rendered three nearly-flat colored lip stripes.
 * M35 replaces them ONLY in an opt-in human candidate with symmetric,
 * anatomically tapered upper/lower vermilion volumes, Cupid's bow, mouth
 * corners, an actual recessed dark oral opening, philtrum/chin skin support,
 * and a second partly-open pose for a future speech/expression rig.
 *
 * Neither the legacy M28 face nor the original armored knight is mutated.
 * The generated mouth is review topology and is not yet a fused skinned
 * production face with deformation-ready concentric mouth loops.
 */
public final class M35MouthSculpt {
    private M35MouthSculpt(){}

    public static final float MOUTH_Y=2.2715f;
    public static final float HALF_WIDTH=.0505f;

    // Low-amplitude source-skin shifts: lip mound, philtrum, lower contour,
    // with a real depression where the teeth/oral opening would sit.
    private static final float[][] SUPPORT={
        // |x|, y, z, radiusX, radiusY, radiusZ, deltaZ
        {.017f,2.283f,.197f,.052f,.021f,.085f,.0040f},
        {.017f,2.259f,.197f,.055f,.022f,.085f,.0045f},
        {.014f,2.273f,.211f,.049f,.007f,.070f,-.0050f},
        {.010f,2.301f,.189f,.021f,.012f,.065f,.0026f},
        {.019f,2.237f,.175f,.054f,.026f,.085f,-.0015f}
    };
    private static final float[] UPPER_COLOR={.668f,.421f,.372f};
    private static final float[] LOWER_COLOR={.655f,.407f,.361f};
    private static final float[] ORAL_SHADOW={.329f,.184f,.185f};

    public static ArtKit.Model sculptConnectedSkin(ArtKit.Model source){
        if(source==null||source.vertices==null||
           source.vertices.length%27!=0)
            throw new IllegalArgumentException("Invalid continuous facial source");
        float[] data=source.vertices.clone();
        for(int i=0;i<data.length;i+=9){
            float x=data[i],y=data[i+1],z=data[i+2];
            if(Math.abs(x)>.093f||y<2.220f||y>2.318f||z<.09f)
                continue;
            if(!M25SkinPolish.isBodySkin(data[i+6],data[i+7],data[i+8]))
                continue;
            float dz=0,gx=0,gy=0,gz=0;
            for(float[] q:SUPPORT){
                float ax=(Math.abs(x)-q[0])/q[3];
                float yy=(y-q[1])/q[4];
                float zz=(z-q[2])/q[5];
                float dist=ax*ax+yy*yy+zz*zz;
                if(dist>13f)continue;
                float movement=q[6]*(float)Math.exp(-dist);
                dz+=movement;
                gx+=movement*(-2f*ax/q[3])*(x<0?-1f:1f);
                gy+=movement*(-2f*yy/q[4]);
                gz+=movement*(-2f*zz/q[5]);
            }
            if(Math.abs(dz)<1e-8f)continue;
            if(Math.abs(dz)>.015f)
                throw new IllegalStateException("M35 mouth skin shift out of bounds");
            float divisor=1f+gz;
            if(!Float.isFinite(divisor)||divisor<.72f)
                throw new IllegalStateException("M35 facial skin foldover");
            float oldZ=data[i+5];
            float nx=data[i+3]-gx*oldZ/divisor;
            float ny=data[i+4]-gy*oldZ/divisor;
            float nz=oldZ/divisor;
            float norm=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(!Float.isFinite(norm)||norm<1e-7f)
                throw new IllegalStateException("Invalid mouth skin normal");
            data[i+2]=z+dz;
            data[i+3]=nx/norm;data[i+4]=ny/norm;data[i+5]=nz/norm;
        }
        return new ArtKit.Model(data);
    }

    private static final class Writer{
        private float[] data=new float[16384];
        private int count=0;
        void add(float[] point,float[] normal,float[] color){
            if(count+9>data.length)data=Arrays.copyOf(data,data.length*2);
            for(float v:point)data[count++]=v;
            for(float v:normal)data[count++]=v;
            for(float v:color)data[count++]=v;
        }
        void quad(float[] a,float[] b,float[] c,float[] d,
                  float[] an,float[] bn,float[] cn,float[] dn,float[] pigment){
            triangle(a,b,c,an,bn,cn,pigment);
            triangle(a,c,d,an,cn,dn,pigment);
        }
        private void triangle(float[] a,float[] b,float[] c,
                              float[] an,float[] bn,float[] cn,float[] color){
            float abx=b[0]-a[0],aby=b[1]-a[1],abz=b[2]-a[2];
            float acx=c[0]-a[0],acy=c[1]-a[1],acz=c[2]-a[2];
            float z=abx*acy-aby*acx;
            if(Math.abs(z)<1e-12f && 
               Math.abs(aby*acz-abz*acy)<1e-12f &&
               Math.abs(abz*acx-abx*acz)<1e-12f)return;
            if(z<0){float[] t=b;b=c;c=t;t=bn;bn=cn;cn=t;}
            add(a,an,color);add(b,bn,color);add(c,cn,color);
        }
        ArtKit.Model finish(){
            return new ArtKit.Model(Arrays.copyOf(data,count));
        }
    }
    private static float saturate(float x){return Math.max(0f,Math.min(1f,x));}
    private static float falloff(float t){
        return (float)Math.pow(Math.max(0f,1f-t*t),.75);
    }
    private static float cupid(float t){
        float ax=Math.abs(t);
        float lobe=(float)Math.exp(-Math.pow((ax-.32f)/.18f,2));
        float middle=(float)Math.exp(-Math.pow(ax/.16f,2));
        return .0030f*lobe-.0012f*middle;
    }
    private static float gap(float t,float openness){
        float shape=falloff(t);
        return (.0017f+.0095f*openness)*shape;
    }
    private static float[] lip(float t,float r,boolean upper,float openness){
        float f=falloff(t);
        float edge=1f-f;
        float center=MOUTH_Y-.0015f*edge;
        float gapWidth=gap(t,openness);
        float lineY=center+(upper?gapWidth/2f:-gapWidth/2f);
        float topY=center+.0162f*f+cupid(t)*f;
        float bottomY=center-.0144f*f;
        float outsideY=upper?topY:bottomY;
        // r=0 is the concealed outer rim merging into head skin;
        // r=1 is the inner vermilion rim bordering the real oral slit.
        float y=outsideY*(1f-r)+lineY*r;
        float pillow=(float)Math.sin(Math.PI*saturate(r));
        float mouthZ=.2165f+.0052f*f;
        float skinZ=.2010f+.004f*f;
        float z=skinZ*(1f-r)+mouthZ*r+.0055f*f*pillow;
        return new float[]{t*HALF_WIDTH,y,z};
    }
    private static float[] normal(float t,float r,boolean upper,float openness){
        float eps=.0005f;
        float[] lo=lip(Math.max(-1f,t-eps),r,upper,openness);
        float[] hi=lip(Math.min(1f,t+eps),r,upper,openness);
        float[] a=lip(t,Math.max(0,r-eps),upper,openness);
        float[] b=lip(t,Math.min(1,r+eps),upper,openness);
        float ux=hi[0]-lo[0],uy=hi[1]-lo[1],uz=hi[2]-lo[2];
        float vx=b[0]-a[0],vy=b[1]-a[1],vz=b[2]-a[2];
        float nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
        if(nz<0){nx=-nx;ny=-ny;nz=-nz;}
        float n=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
        if(n<1e-10f)return new float[]{0f,0f,1f};
        return new float[]{nx/n,ny/n,nz/n};
    }
    private static float[] cavity(float t,boolean upper,float openness){
        float c=MOUTH_Y-.0015f*(1f-falloff(t));
        float h=gap(t,openness)/2f;
        float z=.2173f+.0031f*falloff(t);
        return new float[]{t*HALF_WIDTH,
                c+(upper?h:-h),z};
    }
    /**
     * @param opening 0 closed neutral expression; 1 modestly parted lips.
     * Neither expression changes the skull, eyes, ten digits or historic
     * knight. This produces REAL triangles, not a painted mouth.
     */
    public static ArtKit.Model build(boolean lite,float opening){
        if(!Float.isFinite(opening)||opening<0f||opening>1f)
            throw new IllegalArgumentException("Mouth opening must be 0..1");
        Writer w=new Writer();
        int segments=lite?30:50;
        int rings=lite?5:7;
        for(boolean upper:new boolean[]{true,false}){
            float[] skin=upper?UPPER_COLOR:LOWER_COLOR;
            for(int j=0;j<segments;j++){
                float t0=-1f+2f*j/segments;
                float t1=-1f+2f*(j+1)/segments;
                for(int k=0;k<rings;k++){
                    float r0=(float)k/rings,r1=(float)(k+1)/rings;
                    w.quad(lip(t0,r0,upper,opening),
                           lip(t1,r0,upper,opening),
                           lip(t1,r1,upper,opening),
                           lip(t0,r1,upper,opening),
                           normal(t0,r0,upper,opening),
                           normal(t1,r0,upper,opening),
                           normal(t1,r1,upper,opening),
                           normal(t0,r1,upper,opening),skin);
                }
            }
        }
        // A real recessed oral opening between the two lip rim loops.
        // The exterior stays dark in neutral pose and visibly parts during
        // the 'mouth open' pose. Mouth interior is deliberately shallow:
        // no claim yet of full teeth, tongue or skeletal jaw retargeting.
        for(int j=0;j<segments;j++){
            float t0=-1f+2f*j/segments,t1=-1f+2f*(j+1)/segments;
            float[] n={0f,0f,1f};
            w.quad(cavity(t0,true,opening),cavity(t1,true,opening),
                   cavity(t1,false,opening),cavity(t0,false,opening),
                   n,n,n,n,ORAL_SHADOW);
        }
        return w.finish();
    }
}
