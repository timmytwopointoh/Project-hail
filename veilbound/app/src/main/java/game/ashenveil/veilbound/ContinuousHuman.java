package game.ashenveil.veilbound;

import java.util.ArrayList;
import java.util.Arrays;

/**
 * Continuous implicit human skin surface for the original unarmored prototype.
 * Unlike M17's separate concentric ring cylinders, these volumes are joined
 * with smooth union BEFORE isosurface extraction. The resulting surface has
 * true smooth vertex normals and one fused body shape, suitable as the
 * foundation for anatomical retopology and weighted skeletal refinement.
 *
 * This is not photogrammetry, scanning, or finished photorealism.
 * Array indices expose bounded proportion dials to isolated optimizer workers.
 */
public final class ContinuousHuman {
    private ContinuousHuman(){}
    public static final int CONTROLS=12;
    public static final String[] NAMES={"shoulder_span","deltoid","waist",
        "ribcage","pelvis","quadriceps","cranium","jaw","calves",
        "nose","forearms","feet"};
    public static final float[] BASE={
        1f,1f,1f,1f,1f,1f,1f,1f,1f,1f,1f,1f};
    private static final float[] SKIN={.68f,.425f,.315f};
    private static final float[] SHADE={.55f,.335f,.245f};
    private static final float[] HAIR={.15f,.118f,.108f};
    private static final float[] SHORTS={.205f,.200f,.195f};
    private static final class Blob{
        final float x,y,z,tx,ty,tz,rx,ry,rz;
        Blob(float x,float y,float z,float rx,float ry,float rz){
            this(x,y,z,x,y,z,rx,ry,rz);
        }
        Blob(float x,float y,float z,float tx,float ty,float tz,
             float rx,float ry,float rz){
            this.x=x;this.y=y;this.z=z;
            this.tx=tx;this.ty=ty;this.tz=tz;
            this.rx=rx;this.ry=ry;this.rz=rz;
        }
        float distance(float px,float py,float pz){
            float ax=tx-x,ay=ty-y,az=tz-z;
            float length=ax*ax+ay*ay+az*az;
            float t=length<1e-9f?0f:
                    ((px-x)*ax+(py-y)*ay+(pz-z)*az)/length;
            t=Math.max(0f,Math.min(1f,t));
            float a=(px-x-ax*t)/rx,b=(py-y-ay*t)/ry,
                  c=(pz-z-az*t)/rz;
            return ((float)Math.sqrt(a*a+b*b+c*c)-1f)
                   *Math.min(rx,Math.min(ry,rz));
        }
    }
    private static final class Field{
        final ArrayList<Blob> shapes=new ArrayList<>();
        void add(float x,float y,float z,float rx,float ry,float rz){
            shapes.add(new Blob(x,y,z,rx,ry,rz));
        }
        void bone(float x0,float y0,float z0,float x1,float y1,float z1,
                  float radiusX,float radiusZ,int divisions){
            // ONE continuous analytic elliptical capsule rather than
            // spaced disconnected rings/blobs (particularly fingertips).
            // This is both watertight and cheaper than dozens of SDF bulbs.
            shapes.add(new Blob(x0,y0,z0,x1,y1,z1,
                                radiusX,radiusX*1.10f,radiusZ));
        }
        float sample(float x,float y,float z){
            float d=99f;
            for(Blob b:shapes){
                // Protect the air gaps between fingertips: global
                // .025 smoothing blended adjacent .04-wide digits into a
                // mitten. Keep soft transitions at elbow/shoulder/palm.
                float k=(y<.765f&&y>.46f&&Math.abs(x)>.40f)
                    ?.0035f:.025f;
                float v=b.distance(x,y,z);
                if(d==99f){d=v;continue;}
                // Smooth minimum applied in signed-distance space. Fuses
                // adjacent soft tissue instead of leaving mesh seam cracks.
                float h=Math.max(k-Math.abs(d-v),0f)/k;
                d=Math.min(d,v)-h*h*k*.25f;
            }
            return d;
        }
    }
    public static void validate(float[] g){
        if(g==null||g.length!=CONTROLS)
            throw new IllegalArgumentException("Expected 12 human proportions");
        for(float v:g)if(!Float.isFinite(v)||v<.83f||v>1.17f)
            throw new IllegalArgumentException("Human proportion outside reviewed range");
    }
    private static Field anatomy(float[] g){return anatomy(g,true,false);}
    private static Field anatomy(float[] g,boolean includeDigits){
        return anatomy(g,includeDigits,false);
    }
    private static Field anatomy(float[] g,boolean includeDigits,boolean m24){

        Field f=new Field();
        // Pelvis, abdomen and sternum each transition by overlapping
        // anatomical soft tissue instead of visible intersecting rings.
        f.add(0,1.095f,-.01f,.294f*g[4],.229f,.206f);
        f.add(0,1.34f,-.005f,.276f*g[2],.303f,.198f);
        f.add(0,1.69f,-.008f,.355f*g[3],.329f,.247f);
        f.add(0,1.87f,-.012f,.357f*g[3],.17f,.211f);
        f.add(0,1.985f,0,.145f,.15f,.122f);
        // A gentle realistic asymmetric pair of pectoral bulges.
        for(int side:new int[]{-1,1}){
            f.add(side*.174f,1.715f,.136f,.174f*g[3],.117f,.134f);
            f.add(side*.285f,1.785f,-.008f,.139f,.126f,.135f);
        }
        // Neck tendon and single skull volume, then chin, cheekbones, ears,
        // nasal bridge and lip mass all fused into the original skin surface.
        f.add(0,2.075f,0,.106f,.185f,.106f);
        f.add(0,2.392f,.014f,.177f*g[6],.234f,.167f);
        f.add(0,2.260f,.062f,.132f*g[7],.108f,.126f);
        f.add(0,2.506f,-.022f,.164f*g[6],.129f,.153f);
        f.add(0,2.347f,.177f,.044f*g[9],.095f,.065f*g[9]);
        f.add(0,2.259f,.171f,.064f,.021f,.036f);
        for(int side:new int[]{-1,1}){
            f.add(side*.122f,2.376f,.11f,.073f,.075f,.074f);
            f.add(side*.177f*g[6],2.393f,-.015f,.038f,.066f,.038f);
            // Clavicle joins shoulder before deltoid. No floating arm barrel.
            float sx=side*.445f*g[0];
            f.add(side*.325f,1.90f,-.002f,.156f,.109f,.146f);
            f.add(sx,1.82f,0,.161f*g[1],.187f,.163f);
            f.bone(sx,1.755f,-.005f,side*.536f*g[0],1.398f,.004f,
                   .128f*g[1],.123f*g[1],3);
            f.add(side*.543f*g[0],1.389f,.009f,.112f,.130f,.110f);
            f.bone(side*.543f*g[0],1.371f,.01f,
                   side*.554f*g[0],.998f,.041f,
                   .094f*g[10],.087f*g[10],3);
            f.add(side*.554f*g[0],.878f,.052f,.108f,.141f,.076f);
            // Four visibly separated tapering fingers and ONE opposable
            // thumb: exactly five digits per hand. Individual fingertip
            // lengths follow little/ring/middle/index proportions; the webbing
            // stays fused into the palm but tips do NOT join one another.
            if(includeDigits){
            final float[] tips={.576f,.517f,.493f,.538f}; // little, ring, middle, index
            float handCenter=side*.554f*g[0];
            for(int finger=0;finger<4;finger++){
                // The thumb is lateral on BOTH hands. Reverse anatomical
                // finger order on the left; otherwise its little finger
                // incorrectly sits beside the thumb.
                int anatomicalFinger=side>0?finger:3-finger;
                float spread=(finger-1.5f)*.067f;
                float fx=handCenter+spread;
                float tipY=tips[anatomicalFinger];
                // Three articulated anatomical sections per finger, with
                // decreasing girth and a shallow natural forward curl.
                // Preserve open air between tips and the existing hand SDF
                // probes at y=.614: detail must not recreate a mitten.
                // Subtle joint flexion sculpted into real capsules.
                float middleY=.708f, distalY=.627f;
                float middleZ=.096f, distalZ=.108f, tipZ=.119f;
                float midX=fx+side*.002f, tipX=fx+side*.004f;
                f.bone(fx,.795f,.087f,midX,middleY,middleZ,
                       .024f,.025f,2);
                f.bone(midX,middleY,middleZ,midX,distalY,distalZ,
                       .021f,.022f,2);
                f.bone(midX,distalY,distalZ,tipX,tipY,tipZ,
                       .018f,.019f,2);
                // Rounded fingertips and tapered knuckles, fused per digit.
                f.add(fx,.790f,.078f,.027f,.034f,.026f);
                f.add(midX,middleY,middleZ,.023f,.022f,.022f);
                f.add(midX,distalY,distalZ,.020f,.018f,.020f);
                f.add(tipX,tipY,tipZ,.018f,.019f,.019f);
            }
            // Opposable thumb has a separate angled metacarpal and phalanx.
            // Its base joins the palm, while its tip bends away from the
            // nearest index finger rather than becoming a fifth straight ray.
            f.bone(handCenter+side*.073f,.852f,.102f,
                   handCenter+side*.122f,.768f,.119f,
                   .032f,.031f,2);
            // A distinct thumb phalanx bend improves the side silhouette.
            f.bone(handCenter+side*.122f,.768f,.119f,
                   handCenter+side*.158f,.725f,.148f,
                   .028f,.028f,2);
            f.bone(handCenter+side*.158f,.725f,.148f,
                   handCenter+side*.183f,.689f,.170f,
                   .024f,.025f,2);
            f.add(handCenter+side*.183f,.689f,.170f,
                  .024f,.025f,.026f);
            } // End legacy SDF digits. Sculpted ones use HumanHandSculpt.
            // Joined pelvis/thigh/hips to calf, ankle and broad human foot.
            float hx=side*.207f*g[4];
            f.add(hx,1.045f,-.018f,.175f*g[5],.204f,.159f);
            f.bone(hx,1.025f,-.006f,side*.216f,.697f,.021f,
                   .161f*g[5],.162f*g[5],3);
            f.add(side*.216f,.656f,.035f,.116f,.123f,.128f);
            f.bone(side*.215f,.614f,-.01f,
                   side*.218f,.248f,.018f,.112f*g[8],.116f*g[8],4);
            f.add(side*.218f,.153f,.039f,.083f,.144f,.09f);
            f.add(side*.217f,.086f,.193f,.129f*g[11],.078f,.250f*g[11]);
            // Individual toes are fused to the front of each foot.
            for(int toe=0;toe<5;toe++){
                float tx=side*.217f+side*(toe-2)*.042f;
                f.add(tx,.048f,.377f-.012f*toe,
                      .025f,.032f,.067f);
            }
        }
        if(m24)refineWholeBody(f,g);
        return f;
    }
    /**
     * An opt-in, *real geometry* full-body study. Modest overlapping soft
     * tissue masses are sculpted in the same continuous signed distance
     * field as the body, not drawn as disconnected ornament or skin textures.
     * Hair and all historical baseline geometry remain unchanged.
     * Future retopology, texture painting and joint-weight review still needed.
     */
    private static void refineWholeBody(Field f,float[] g){
        // Thoracic / abdominal form: serratus, upper oblique and erector
        // spinae soften the formerly featureless barrel-shaped torso.
        for(int side:new int[]{-1,1}){
            f.add(side*.268f,1.630f,.092f,.092f*g[3],.134f,.085f);
            f.add(side*.224f,1.430f,.106f,.080f*g[2],.164f,.092f);
            f.add(side*.157f,1.563f,-.173f,.095f,.198f,.082f);
            f.add(side*.193f,1.292f,-.158f,.114f,.170f,.102f);
            // Gluteus-to-pelvis transition and upper thigh muscle sweep.
            f.add(side*.196f*g[4],.976f,-.140f,.154f,.155f,.115f);
            f.add(side*.206f,.836f,.085f,.129f*g[5],.174f,.132f);
            f.add(side*.192f,.752f,-.095f,.118f*g[5],.160f,.114f);
            // Patella and upper calf heads blend into the actual leg mesh.
            f.add(side*.216f,.650f,.128f,.082f,.073f,.055f);
            f.add(side*.251f,.461f,-.064f,.076f*g[8],.134f,.093f);
            f.add(side*.180f,.422f,-.077f,.066f*g[8],.131f,.086f);
            // Achilles and heel-to-midfoot volumes for proper side profile.
            f.add(side*.218f,.148f,-.062f,.074f,.086f,.090f);
            f.add(side*.213f,.079f,.300f,.119f*g[11],.059f,.156f*g[11]);
            // Deltoid transition, biceps, triceps and brachioradialis.
            float x=side*.445f*g[0];
            f.add(x,1.735f,.107f,.120f*g[1],.146f,.103f);
            f.add(side*.513f*g[0],1.567f,.088f,.088f*g[1],.151f,.078f);
            f.add(side*.515f*g[0],1.532f,-.084f,.099f*g[1],.165f,.088f);
            f.add(side*.557f*g[0],1.240f,.085f,.080f*g[10],.158f,.068f);
            f.add(side*.548f*g[0],1.196f,-.059f,.082f*g[10],.169f,.075f);
            // Upper cheekbone, jaw musculature and brow: modest volumes,
            // deliberately no artificial bead eyes, no hair modification.
            f.add(side*.097f,2.410f,.138f,.068f,.044f,.052f);
            f.add(side*.121f,2.308f,.103f,.067f*g[7],.075f,.066f);
            f.add(side*.081f,2.474f,.130f,.057f,.035f,.036f);
            f.add(side*.040f,2.275f,.179f,.035f,.023f,.031f);
        }
        f.add(0,1.461f,.184f,.114f,.153f,.039f); // subtle rectus contour
        f.add(0,1.840f,-.183f,.128f,.118f,.083f); // scapular bridge
        f.add(0,2.280f,.190f,.061f,.018f,.027f); // lower-lip soft tissue
    }
    /**
     * Pure distance-field probes for anatomical acceptance. Four fingertip
     * columns must be occupied, three web gaps open, and the thumb distinct.
     * Negative field is flesh; positive field is actual open air.
     */
    static float[] digitSeparationProbe(int side){
        if(side!=1&&side!=-1)throw new IllegalArgumentException("Hand side");
        Field f=anatomy(BASE);
        float center=side*.554f;
        float[] samples=new float[9];
        for(int finger=0;finger<4;finger++)
            samples[finger]=f.sample(center+(finger-1.5f)*.067f,.614f,.097f);
        for(int gap=0;gap<3;gap++)
            samples[4+gap]=f.sample(center+(gap-1f)*.067f,.614f,.097f);
        samples[7]=f.sample(center+side*.183f,.690f,.151f);
        samples[8]=f.sample(center+side*.150f,.685f,.150f);
        return samples;
    }
    private static int idx(int x,int y,int z,int nx,int ny){
        return (z*ny+y)*nx+x;
    }
    private static float node(float[] data,int x,int y,int z,int nx,int ny){
        return data[idx(x,y,z,nx,ny)];
    }
    private static final int[][] TETS={
        {0,5,1,6},{0,1,2,6},{0,2,3,6},
        {0,3,7,6},{0,7,4,6},{0,4,5,6}
    };
    private static final int[][] CORNERS={
        {0,0,0},{1,0,0},{1,1,0},{0,1,0},
        {0,0,1},{1,0,1},{1,1,1},{0,1,1}
    };
    private static final class Out {
        float[] stream=new float[8192];int n;
        void write(float[] p,float[] rgb){
            if(n+9>stream.length)stream=Arrays.copyOf(stream,stream.length*2);
            for(int i=0;i<6;i++)stream[n++]=p[i];
            for(int i=0;i<3;i++)stream[n++]=rgb[i];
        }
        void triangle(float[] a,float[] b,float[] c){
            float ux=b[0]-a[0],uy=b[1]-a[1],uz=b[2]-a[2];
            float vx=c[0]-a[0],vy=c[1]-a[1],vz=c[2]-a[2];
            float cx=uy*vz-uz*vy,cy=uz*vx-ux*vz,cz=ux*vy-uy*vx;
            float dx=(a[3]+b[3]+c[3])/3,dy=(a[4]+b[4]+c[4])/3,
                  dz=(a[5]+b[5]+c[5])/3;
            if(cx*cx+cy*cy+cz*cz<1.e-12f)return;
            if(cx*dx+cy*dy+cz*dz<0){float[] swap=b;b=c;c=swap;}
            write(a,paint(a));write(b,paint(b));write(c,paint(c));
        }
        ArtKit.Model finish(){return new ArtKit.Model(Arrays.copyOf(stream,n));}
    }
    private static float[] paint(float[] p){
        float x=p[0],y=p[1],z=p[2];
        if(y>.89f&&y<1.18f&&Math.abs(x)<.398f)
            return SHORTS;
        if(y>2.568f+.018f*(float)Math.sin(x*39f+z*25f)
            ||(y>2.515f&&z<-.09f&&Math.abs(x)<.18f))
            return HAIR;
        float subtle=.985f+.015f*(float)Math.sin(x*31f+y*47f+z*25f);
        float shade=y<.22f?.95f:1f;
        if(z<-.1f&&y<1.8f)shade*=.96f;
        return new float[]{Math.min(1f,SKIN[0]*subtle*shade),
                           SKIN[1]*subtle*shade,SKIN[2]*subtle*shade};
    }
    private static float[] intersection(int a,int b,float[][] pos,
                                        float[][] grad,float[] signed){
        float va=signed[a],vb=signed[b];
        float t=va/(va-vb);
        t=Math.max(0f,Math.min(1f,t));
        float[] p=new float[6];
        for(int i=0;i<3;i++){
            p[i]=pos[a][i]+t*(pos[b][i]-pos[a][i]);
            p[i+3]=grad[a][i]+t*(grad[b][i]-grad[a][i]);
        }
        float n=(float)Math.sqrt(p[3]*p[3]+p[4]*p[4]+p[5]*p[5]);
        if(n<1.e-6f)n=1;
        p[3]/=n;p[4]/=n;p[5]/=n;
        return p;
    }
    private static void tet(int[] corners,float[][] pos,float[][] grad,
                            float[] signed,Out out){
        int[] in=new int[4],outside=new int[4];int ni=0,no=0;
        for(int k:corners)if(signed[k]<0)in[ni++]=k;else outside[no++]=k;
        if(ni==0||ni==4)return;
        if(ni==1){
            out.triangle(intersection(in[0],outside[0],pos,grad,signed),
                intersection(in[0],outside[1],pos,grad,signed),
                intersection(in[0],outside[2],pos,grad,signed));
        }else if(ni==3){
            out.triangle(intersection(outside[0],in[0],pos,grad,signed),
                intersection(outside[0],in[1],pos,grad,signed),
                intersection(outside[0],in[2],pos,grad,signed));
        }else{
            float[] a=intersection(in[0],outside[0],pos,grad,signed);
            float[] b=intersection(in[0],outside[1],pos,grad,signed);
            float[] c=intersection(in[1],outside[0],pos,grad,signed);
            float[] d=intersection(in[1],outside[1],pos,grad,signed);
            out.triangle(a,b,c);out.triangle(b,d,c);
        }
    }
    public static ArtKit.Model build(boolean lite){return build(lite,BASE);}
    public static ArtKit.Model build(boolean lite,float[] controls){
        return build(lite,controls,true);
    }
    /** Palm/wrist mesh without the M21 cylinders; M23 loft digits attach here. */
    static ArtKit.Model buildWithoutDigits(boolean lite){
        return buildWithoutDigits(lite,BASE);
    }
    static ArtKit.Model buildWithoutDigits(boolean lite,float[] controls){
        return build(lite,controls,false,false);
    }
    /** M24 study with sculpted torso, limbs, head, hips and feet. */
    static ArtKit.Model buildM24WithoutDigits(boolean lite,float[] controls){
        return build(lite,controls,false,true);
    }
    private static ArtKit.Model build(boolean lite,float[] controls,boolean includeDigits){
        return build(lite,controls,includeDigits,false);
    }
    private static ArtKit.Model build(boolean lite,float[] controls,
                                      boolean includeDigits,boolean refined){
        validate(controls);
        Field field=anatomy(controls,includeDigits,refined);
        float h=lite?.062f:.039f;
        float x0=-.88f,y0=-.08f,z0=-.48f;
        int nx=2+(int)Math.ceil(1.76f/h),ny=2+(int)Math.ceil(2.88f/h),
            nz=2+(int)Math.ceil(1.14f/h);
        float[] v=new float[nx*ny*nz];
        for(int z=0;z<nz;z++)for(int y=0;y<ny;y++)for(int x=0;x<nx;x++)
            v[idx(x,y,z,nx,ny)]=field.sample(x0+x*h,y0+y*h,z0+z*h);
        Out out=new Out();
        float[][] pos=new float[8][3],grad=new float[8][3];
        float[] signed=new float[8];
        for(int z=1;z<nz-2;z++)for(int y=1;y<ny-2;y++)for(int x=1;x<nx-2;x++){
            boolean inside=false,outside=false;
            for(int k=0;k<8;k++){
                int[] c=CORNERS[k];int xx=x+c[0],yy=y+c[1],zz=z+c[2];
                signed[k]=node(v,xx,yy,zz,nx,ny);
                if(signed[k]<0)inside=true;else outside=true;
            }
            if(!inside||!outside)continue;
            for(int k=0;k<8;k++){
                int[] c=CORNERS[k];int xx=x+c[0],yy=y+c[1],zz=z+c[2];
                pos[k][0]=x0+xx*h;pos[k][1]=y0+yy*h;pos[k][2]=z0+zz*h;
                grad[k][0]=node(v,xx+1,yy,zz,nx,ny)-
                           node(v,xx-1,yy,zz,nx,ny);
                grad[k][1]=node(v,xx,yy+1,zz,nx,ny)-
                           node(v,xx,yy-1,zz,nx,ny);
                grad[k][2]=node(v,xx,yy,zz+1,nx,ny)-
                           node(v,xx,yy,zz-1,nx,ny);
            }
            for(int[] t:TETS)tet(t,pos,grad,signed,out);
        }
        return out.finish();
    }
}
