package game.ashenveil.veilbound;

import java.util.Arrays;

/**
 * Real controllable 3D surface construction, NOT sphere/box duplication.
 * Cross-section lofting supports per-ring taper, translation, twist, front
 * keel, asymmetric profiles and explicit shape ridges. Bevel panels add
 * edged raised plates. Output is immutable triangle/normals/painted RGB.
 *
 * Profiles can be authored by separate offline workers and evaluated through
 * this same deterministic Android-free kernel. No source-code evaluation.
 */
public final class ShapeEngine {
    private ShapeEngine(){}
    public static final class Ring {
        public final float cx,y,cz,rx,rz,twist,keel;
        public Ring(float cx,float y,float cz,float rx,float rz,
                    float twist,float keel){
            if(!finite(cx,y,cz,rx,rz,twist,keel)||rx<=0||rz<=0)
                throw new IllegalArgumentException("Invalid sculpture cross section");
            this.cx=cx;this.y=y;this.cz=cz;this.rx=rx;this.rz=rz;
            this.twist=twist;this.keel=keel;
        }
    }
    public static final class Palette {
        public final float r,g,b;
        public Palette(float r,float g,float b){
            if(!finite(r,g,b)||r<0||g<0||b<0||r>1.4f||g>1.4f||b>1.4f)
                throw new IllegalArgumentException("Invalid sculpture palette");
            this.r=r;this.g=g;this.b=b;
        }
    }
    private static boolean finite(float... values){
        for(float v:values)if(Float.isNaN(v)||Float.isInfinite(v))return false;
        return true;
    }
    private static float[] point(Ring ring,int side,int sides,float offset){
        float angle=(float)(Math.PI*2*side/sides)+ring.twist;
        float x=(float)Math.cos(angle),z=(float)Math.sin(angle);
        // Deliberate front ridge: not an elliptical orbit or round bead.
        float front=Math.max(0f,z),ridge=front*front*front;
        float r=1f+.035f*(float)Math.cos(angle*4);
        return new float[]{ring.cx+ring.rx*x*r,ring.y+offset,
                           ring.cz+ring.rz*z*r+ring.keel*ridge};
    }
    private static final class Forge {
        float[] data=new float[16384];int count=0;
        private void vertex(float[] p,float nx,float ny,float nz,Palette tint){
            if(count+9>data.length)data=Arrays.copyOf(data,data.length*2);
            data[count++]=p[0];data[count++]=p[1];data[count++]=p[2];
            data[count++]=nx;data[count++]=ny;data[count++]=nz;
            data[count++]=tint.r;data[count++]=tint.g;data[count++]=tint.b;
        }
        void triangle(float[] a,float[] b,float[] c,Palette tint){
            float ux=b[0]-a[0],uy=b[1]-a[1],uz=b[2]-a[2];
            float vx=c[0]-a[0],vy=c[1]-a[1],vz=c[2]-a[2];
            float nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
            float length=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(length<1e-7f)return;
            vertex(a,nx/length,ny/length,nz/length,tint);
            vertex(b,nx/length,ny/length,nz/length,tint);
            vertex(c,nx/length,ny/length,nz/length,tint);
        }
        void quad(float[] a,float[] b,float[] c,float[] d,Palette t){
            triangle(a,b,c,t);triangle(a,c,d,t);
        }
        ArtKit.Model finish(){return new ArtKit.Model(Arrays.copyOf(data,count));}
    }
    /**
     * Forge a shaped surface from ordered cross sections bottom to top.
     * Triangles follow continuous taper and overlap ridge detail, not spheres.
     */
    public static ArtKit.Model loft(Ring[] rings,int sides,Palette tint){
        if(rings==null||rings.length<2||rings.length>64||sides<8||sides>64)
            throw new IllegalArgumentException("Loft budget/profile invalid");
        Forge f=new Forge();
        for(int row=0;row<rings.length-1;row++){
            Ring a=rings[row],b=rings[row+1];
            if(b.y<=a.y+1e-4f)throw new IllegalArgumentException("Loft rings not ordered");
            for(int k=0;k<sides;k++){
                float[] p=point(a,k,sides,0),q=point(b,k,sides,0);
                float[] r=point(b,k+1,sides,0),t=point(a,k+1,sides,0);
                f.quad(p,q,r,t,tint);
            }
        }
        return f.finish();
    }
    /**
     * Forged plate with FOUR purposeful surfaces: base flange, 45-degree
     * dressed edge, inset bevel and a BROAD low-relief face. A uniform
     * peaked triangle fan made these look like artificial pyramids; this
     * actual inset surface reads as worked steel with hard, narrow edge glints.
     * Convex hand-authored outlines, mobile-safe fixed triangle budget.
     */
    public static ArtKit.Model bevelPlate(float[] xy,float backZ,float height,
                                           float thickness,Palette face,Palette edge){
        if(xy==null||xy.length<6||xy.length>48||xy.length%2!=0||
           !finite(backZ,height,thickness)||thickness<=0||height<=0)
            throw new IllegalArgumentException("Plate polygon invalid");
        int n=xy.length/2;
        float cx=0,cy=0;
        for(int i=0;i<n;i++){cx+=xy[i*2];cy+=xy[i*2+1];}
        cx/=n;cy/=n;
        Forge f=new Forge();
        // Nearly-flat center is deliberately 70% of the silhouette. The
        // narrow successive bevel widths break up highlights naturally.
        final float topZ=backZ+thickness+height;
        float[] center={cx,cy,topZ+.001f};
        for(int i=0;i<n;i++){
            int j=(i+1)%n;
            float ax=xy[i*2],ay=xy[i*2+1];
            float bx=xy[j*2],by=xy[j*2+1];
            float[] backA={ax,ay,backZ},backB={bx,by,backZ};
            float[] outerA={ax,ay,backZ+thickness};
            float[] outerB={bx,by,backZ+thickness};
            float[] flangeA={cx+(ax-cx)*.95f,cy+(ay-cy)*.95f,
                              backZ+thickness+height*.33f};
            float[] flangeB={cx+(bx-cx)*.95f,cy+(by-cy)*.95f,
                              backZ+thickness+height*.33f};
            float[] innerA={cx+(ax-cx)*.82f,cy+(ay-cy)*.82f,topZ};
            float[] innerB={cx+(bx-cx)*.82f,cy+(by-cy)*.82f,topZ};
            f.quad(backA,backB,outerB,outerA,edge);
            f.quad(outerA,outerB,flangeB,flangeA,edge);
            f.quad(flangeA,flangeB,innerB,innerA,face);
            f.triangle(center,innerA,innerB,face);
        }
        return f.finish();
    }
    /** Merge only finite fully normalized triangle streams (GL ES2 budget). */
    public static ArtKit.Model combine(ArtKit.Model... models){
        if(models==null||models.length==0)throw new IllegalArgumentException("No models");
        int length=0;
        for(ArtKit.Model m:models){
            if(m==null||m.vertices.length%27!=0)throw new IllegalArgumentException("Broken mesh");
            length=Math.addExact(length,m.vertices.length);
            if(length>9*3*250000)throw new IllegalArgumentException("GPU triangle budget");
        }
        float[] out=new float[length];int p=0;
        for(ArtKit.Model m:models){
            System.arraycopy(m.vertices,0,out,p,m.vertices.length);p+=m.vertices.length;
        }
        return new ArtKit.Model(out);
    }
    private static Ring ring(float x,float y,float z,float rx,float rz,float keel){
        return new Ring(x,y,z,rx,rz,0,keel);
    }
    /**
     * Bellwarden player-only: six authored plates using profile lofts, five
     * bevelled ornamental panels, shoulder transition angles and a peaked
     * breastplate. The joints stay individually classifiable by CharacterRig.
     */
    public static ArtKit.Model bellwardenForgedPlates(boolean mobile){
        int n=mobile?12:24;
        Palette steel=new Palette(.46f,.54f,.61f);
        Palette cold=new Palette(.32f,.41f,.47f);
        Palette trim=new Palette(.77f,.66f,.46f);
        ArtKit.Model breast=loft(new Ring[]{
            ring(0f,1.13f,.075f,.27f,.24f,.055f),
            ring(0f,1.28f,.105f,.35f,.29f,.085f),
            ring(0f,1.47f,.085f,.41f,.31f,.12f),
            ring(0f,1.68f,.07f,.43f,.31f,.12f),
            ring(0f,1.83f,.055f,.37f,.26f,.07f),
            ring(0f,1.94f,.03f,.29f,.22f,.01f)
        },n,steel);
        ArtKit.Model[] m=new ArtKit.Model[12];m[0]=breast;
        for(int side=-1;side<=1;side+=2){
            int id=side<0?1:2;
            // Armored shoulder changes radius at each hand-specified ring.
            float x=side*.69f;
            m[id]=loft(new Ring[]{
                ring(x,1.55f,-.035f,.17f,.18f,.01f),
                ring(x,1.67f,-.035f,.26f,.26f,.02f),
                ring(x,1.82f,-.06f,.33f,.32f,.045f),
                ring(x,1.98f,-.075f,.29f,.27f,.04f),
                ring(x,2.09f,-.09f,.13f,.14f,.01f)
            },n,cold);
            m[id+2]=loft(new Ring[]{
                ring(side*.28f,.20f,.12f,.15f,.14f,.02f),
                ring(side*.28f,.33f,.125f,.17f,.18f,.03f),
                ring(side*.28f,.56f,.15f,.18f,.19f,.04f),
                ring(side*.28f,.70f,.18f,.20f,.21f,.05f),
                ring(side*.28f,.78f,.18f,.15f,.18f,.02f)
            },n,cold);
        }
        // A tapered raised chest glyph, two split breast wings, and shin plates.
        m[5]=bevelPlate(new float[]{-.27f,1.67f,-.18f,1.76f,-.03f,1.74f,
            -.02f,1.40f,-.22f,1.27f,-.32f,1.48f},.405f,.035f,.026f,steel,trim);
        m[6]=bevelPlate(new float[]{.03f,1.74f,.18f,1.76f,.27f,1.67f,
            .32f,1.48f,.22f,1.27f,.02f,1.40f},.405f,.035f,.026f,steel,trim);
        m[7]=bevelPlate(new float[]{-.37f,.66f,-.15f,.70f,-.15f,.33f,
            -.28f,.17f,-.41f,.30f},.33f,.023f,.018f,steel,cold);
        m[8]=bevelPlate(new float[]{.15f,.70f,.37f,.66f,.41f,.30f,
            .28f,.17f,.15f,.33f},.33f,.023f,.018f,steel,cold);
        m[9]=bevelPlate(new float[]{-.11f,2.46f,-.08f,2.60f,0f,2.76f,
            .08f,2.60f,.11f,2.46f,0f,2.35f},.25f,.024f,.014f,steel,trim);
        m[10]=bevelPlate(new float[]{-.13f,1.89f,-.04f,1.95f,0f,1.90f,
            .04f,1.95f,.13f,1.89f,0f,1.80f},.44f,.021f,.014f,trim,cold);
        m[11]=bevelPlate(new float[]{-.06f,1.56f,0f,1.64f,.06f,1.56f,
            .04f,1.48f,0f,1.42f,-.04f,1.48f},.50f,.021f,.014f,trim,cold);
        return combine(m);
    }
}
