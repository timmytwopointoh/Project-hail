package game.ashenveil.veilbound;

import java.util.Arrays;

/**
 * Original procedural 3D hero, enemy and boss art-kit.
 *
 * Pure Java mesh generation, decoupled from Android/OpenGL. Each model is a
 * compact interleaved position/normal/albedo mesh (9 floats per vertex).
 * Immutable meshes are generated once on the GL thread. No allocations while
 * traversing the scene, no downloaded assets and no licensed third-party art.
 *
 * Design language: chipped silver, ash-plum tabards, aged brass, broken ivory,
 * oxblood corruption, cathedral blade silhouettes and embroidered ward sigils.
 */
public final class ArtKit {
    private ArtKit(){}
    public static final class Model {
        public final float[] vertices;
        public final int triangleCount;
        Model(float[] values) {
            vertices=values;
            triangleCount=values.length/27;
            if(vertices.length==0||vertices.length%27!=0)
                throw new IllegalArgumentException("Art mesh must contain complete triangles");
            for(float v:vertices)
                if(Float.isNaN(v)||Float.isInfinite(v))
                    throw new IllegalArgumentException("Invalid vertex coordinate");
        }
    }
    private static float[] v(float x,float y,float z){return new float[]{x,y,z};}
    private static final class Sculpt {
        float[] a=new float[4096];
        int size=0;
        void vertex(float[] p,float nx,float ny,float nz,float r,float g,float b){
            if(size+9>a.length)a=Arrays.copyOf(a,a.length*2);
            a[size++]=p[0];a[size++]=p[1];a[size++]=p[2];
            a[size++]=nx;a[size++]=ny;a[size++]=nz;
            a[size++]=r;a[size++]=g;a[size++]=b;
        }
        void tri(float[] p,float[] q,float[] r,float red,float green,float blue){
            float ux=q[0]-p[0],uy=q[1]-p[1],uz=q[2]-p[2];
            float vx=r[0]-p[0],vy=r[1]-p[1],vz=r[2]-p[2];
            float nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
            float length=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(length<.000001f)return;
            nx/=length;ny/=length;nz/=length;
            vertex(p,nx,ny,nz,red,green,blue);
            vertex(q,nx,ny,nz,red,green,blue);
            vertex(r,nx,ny,nz,red,green,blue);
        }
        void quad(float[] a,float[] b,float[] c,float[] d,float red,float green,float blue){
            tri(a,b,c,red,green,blue);tri(a,c,d,red,green,blue);
        }
        void box(float x,float y,float z,float w,float h,float d,float r,float g,float b){
            float l=x-w/2f,rr=x+w/2f,bottom=y-h/2f,top=y+h/2f;
            float n=z-d/2f,f=z+d/2f;
            quad(v(l,bottom,f),v(rr,bottom,f),v(rr,top,f),v(l,top,f),r,g,b);
            quad(v(rr,bottom,n),v(l,bottom,n),v(l,top,n),v(rr,top,n),r*.68f,g*.71f,b*.76f);
            quad(v(l,bottom,n),v(l,bottom,f),v(l,top,f),v(l,top,n),r*.80f,g*.81f,b*.86f);
            quad(v(rr,bottom,f),v(rr,bottom,n),v(rr,top,n),v(rr,top,f),r*.89f,g*.91f,b*.92f);
            quad(v(l,top,f),v(rr,top,f),v(rr,top,n),v(l,top,n),r*1.16f,g*1.16f,b*1.11f);
            quad(v(l,bottom,n),v(rr,bottom,n),v(rr,bottom,f),v(l,bottom,f),r*.61f,g*.62f,b*.65f);
        }
        void lathe(float x,float bottom,float z,float lowerRadius,float upperRadius,
                   float height,int sides,float red,float green,float blue){
            for(int i=0;i<sides;i++){
                float a=(float)(2*Math.PI*i/sides),b=(float)(2*Math.PI*(i+1)/sides);
                float ca=(float)Math.cos(a),sa=(float)Math.sin(a);
                float cb=(float)Math.cos(b),sb=(float)Math.sin(b);
                float shade=.89f+.11f*(float)Math.sin(i*1.27f+1);
                quad(v(x+lowerRadius*ca,bottom,z+lowerRadius*sa),
                    v(x+upperRadius*ca,bottom+height,z+upperRadius*sa),
                    v(x+upperRadius*cb,bottom+height,z+upperRadius*sb),
                    v(x+lowerRadius*cb,bottom,z+lowerRadius*sb),
                    red*shade,green*shade,blue*shade);
            }
        }
        void spike(float x,float baseY,float z,float radius,float height,
                   int sides,float r,float g,float b){
            for(int i=0;i<sides;i++){
                float a=(float)(2*Math.PI*i/sides),angle=(float)(2*Math.PI*(i+1)/sides);
                tri(v(x+radius*(float)Math.cos(a),baseY,z+radius*(float)Math.sin(a)),
                    v(x,baseY+height,z),
                    v(x+radius*(float)Math.cos(angle),baseY,z+radius*(float)Math.sin(angle)),
                    r*(.85f+i*.035f),g*(.84f+i*.035f),b*(.82f+i*.038f));
            }
        }
        void bone(float x,float z,float bottom,float top,float width,float rr,float gg,float bb){
            // Distinctively angled armor rib/bone with tapered outer edges.
            float slope=width*.2f;
            quad(v(x-width,bottom,z-.13f),v(x+width,bottom,z-.11f),
                v(x+width+slope,top,z-.08f),v(x-width+slope,top,z-.09f),rr,gg,bb);
        }
        void disc(float x,float y,float z,float radius,float depth,float r,float g,float b){
            lathe(x,y-depth/2f,z,radius,radius*.88f,depth,10,r,g,b);
        }
        void tatteredCape(float width,float bottom,float top,float backZ,
                          float red,float green,float blue){
            // Nine vertical strips with asymmetric hems. Double faces, faded piping.
            for(int i=0;i<9;i++){
                float left=(i/9f-.5f)*width;
                float right=((i+1)/9f-.5f)*width;
                float tw=.08f*(float)Math.sin(i*1.7f);
                float hem=bottom+.17f*(float)(.5+.5*Math.sin(i*2.3f));
                float edgeZ=backZ-.37f+tw;
                quad(v(left,top,backZ+.16f),v(right,top,backZ+.16f),
                    v(right*1.43f,hem,edgeZ),v(left*1.43f,hem-.03f,edgeZ),
                    red*(.92f+i*.018f),green*(.91f+i*.015f),blue*(.89f+i*.02f));
                quad(v(left*1.43f,hem-.03f,edgeZ-.012f),v(right*1.43f,hem,edgeZ-.012f),
                    v(right,top,backZ+.13f),v(left,top,backZ+.13f),
                    red*.69f,green*.71f,blue*.76f);
                if(i%2==0){
                    quad(v(left*1.44f,hem+.10f,edgeZ-.019f),
                         v(left*1.44f+.022f,hem+.10f,edgeZ-.019f),
                         v(left+.025f,top-.08f,backZ+.10f),
                         v(left,top-.08f,backZ+.10f),
                         .49f,.42f,.27f);
                }
            }
        }
        Model done(){return new Model(Arrays.copyOf(a,size));}
    }
    public static Model bellwarden(){
        Sculpt b=new Sculpt();
        // Layered scale mail beneath an iconic long, ash-plum mantle.
        b.tatteredCape(1.23f,.12f,2.04f,-.45f,.20f,.25f,.31f);
        b.lathe(0,.69f,0,.38f,.51f,1.05f,10,.44f,.53f,.59f);
        b.lathe(0,.67f,0,.41f,.36f,.25f,10,.24f,.24f,.27f);
        b.lathe(0,1.31f,0,.51f,.42f,.51f,10,.56f,.62f,.67f);
        b.lathe(0,1.73f,0,.40f,.38f,.14f,10,.68f,.61f,.47f);
        // Velvet tabard with a gold bell-shaped insignia on FRONT (+Z).
        b.box(0,.98f,.40f,.49f,1.05f,.11f,.20f,.20f,.35f);
        b.spike(0,.77f,.48f,.21f,.39f,5,.75f,.64f,.39f);
        b.box(0,.84f,.52f,.42f,.055f,.09f,.80f,.70f,.48f);
        b.lathe(0,.60f,.07f,.44f,.44f,.16f,10,.66f,.53f,.35f);
        // Bellwarden's signature helmet with an overhanging brow and carved visor.
        b.lathe(0,2.02f,.015f,.31f,.34f,.59f,12,.58f,.69f,.75f);
        b.lathe(0,2.54f,.015f,.36f,.23f,.20f,12,.74f,.75f,.70f);
        b.spike(0,2.62f,.00f,.24f,.30f,7,.80f,.72f,.50f);
        b.box(0,2.25f,.32f,.51f,.09f,.15f,.20f,.25f,.33f);
        b.box(0,2.34f,.34f,.39f,.038f,.06f,.74f,.72f,.49f);
        // Back of helm and collar remain readable to the chase camera.
        b.lathe(0,1.87f,-.07f,.47f,.42f,.22f,11,.54f,.64f,.68f);
        for(int sign=-1;sign<=1;sign+=2){
            float x=sign*.66f;
            b.lathe(x,1.42f,0,.37f,.51f,.52f,9,.48f,.60f,.67f);
            b.spike(x,1.91f,-.05f,.32f,.37f,5,.74f,.70f,.53f);
            b.lathe(x,1.08f,.04f,.20f,.23f,.62f,8,.33f,.41f,.47f);
            b.box(x,.82f,.07f,.34f,.30f,.44f,.76f,.72f,.50f);
            // Angled skirt armor plates, mail-lined boots, knee caps.
            b.bone(sign*.25f,.26f,.28f,.73f,.15f,.63f,.65f,.68f);
            b.lathe(sign*.25f,.12f,0,.22f,.17f,.74f,8,.28f,.32f,.39f);
            b.box(sign*.25f,.13f,.24f,.32f,.20f,.51f,.44f,.50f,.57f);
            b.disc(sign*.25f,.71f,.30f,.23f,.12f,.73f,.70f,.57f);
        }
        // Diagonal heraldic plates across the back of the mantle.
        b.tri(v(-.28f,1.70f,-.61f),v(.28f,1.70f,-.61f),
              v(0,1.02f,-.83f),.77f,.74f,.55f);
        b.tri(v(-.12f,1.58f,-.65f),v(.12f,1.58f,-.65f),
              v(0,1.26f,-.75f),.16f,.28f,.36f);
        return b.done();
    }
    public static Model hushed(){
        Sculpt b=new Sculpt();
        b.tatteredCape(.90f,.24f,1.92f,-.35f,.18f,.22f,.23f);
        // Hollow lanky revenant; one broken shoulder and exposed chest cage.
        b.lathe(0,.77f,0,.22f,.39f,1.06f,8,.24f,.26f,.28f);
        b.lathe(0,1.71f,0,.32f,.23f,.27f,8,.68f,.67f,.59f);
        b.lathe(0,2.08f,0,.25f,.30f,.50f,9,.37f,.41f,.39f);
        b.spike(0,2.56f,-.02f,.33f,.27f,7,.59f,.60f,.58f);
        b.box(0,2.32f,.28f,.48f,.12f,.11f,.63f,.29f,.23f);
        b.box(0,2.13f,.28f,.27f,.13f,.09f,.14f,.16f,.20f);
        for(int i=0;i<5;i++){
            float y=1.36f+i*.13f;
            b.bone(0,.29f,y,y+.038f,.34f*(1-i*.11f),.73f,.68f,.56f);
        }
        for(int sign=-1;sign<=1;sign+=2){
            b.lathe(sign*.55f,1.13f,0,.16f,.22f,.81f,7,.52f,.51f,.48f);
            b.lathe(sign*.22f,.14f,0,.13f,.19f,.89f,7,.24f,.27f,.29f);
            b.box(sign*.23f,.65f,.19f,.28f,.22f,.30f,.56f,.55f,.46f);
            if(sign==-1){
                b.lathe(-.59f,1.74f,-.03f,.32f,.38f,.22f,8,.49f,.49f,.45f);
                b.spike(-.66f,1.93f,-.03f,.21f,.30f,5,.58f,.56f,.47f);
            }
        }
        // A split ribcage protects a hostile red ash heart.
        b.spike(0,1.24f,.32f,.18f,.33f,7,.79f,.18f,.11f);
        return b.done();
    }
    public static Model ashKnight(){
        Sculpt b=new Sculpt();
        b.tatteredCape(2.25f,.12f,3.05f,-.70f,.24f,.17f,.19f);
        b.lathe(0,.92f,0,.63f,.81f,1.50f,12,.33f,.32f,.35f);
        b.lathe(0,2.24f,0,.83f,.69f,.62f,12,.30f,.37f,.43f);
        b.lathe(0,2.70f,0,.66f,.48f,.28f,12,.68f,.47f,.35f);
        b.lathe(0,2.95f,0,.42f,.48f,.68f,12,.28f,.31f,.39f);
        b.box(0,3.20f,.45f,.66f,.15f,.14f,.85f,.19f,.12f);
        b.lathe(0,3.60f,0,.56f,.50f,.21f,12,.69f,.55f,.43f);
        b.spike(0,3.74f,0,.47f,.68f,10,.68f,.62f,.50f);
        // A thorn-crown encircles the helmet: reads from every camera orbit.
        for(int k=0;k<9;k++){
            float a=(float)(2*Math.PI*k/9);
            b.spike((float)Math.sin(a)*.53f,3.65f,(float)Math.cos(a)*.53f,
                    .15f,.37f+(k%3)*.12f,5,.67f,.52f,.43f);
        }
        for(int sign=-1;sign<=1;sign+=2){
            float x=sign*1.05f;
            b.lathe(x,2.51f,0,.53f,.72f,.65f,10,.40f,.39f,.43f);
            b.spike(x,3.12f,0,.44f,.77f,6,.61f,.45f,.37f);
            b.lathe(x,1.55f,.02f,.26f,.36f,.95f,8,.30f,.34f,.38f);
            b.box(x,1.14f,.16f,.51f,.38f,.63f,.64f,.50f,.40f);
            b.lathe(sign*.47f,.11f,0,.36f,.29f,1.16f,9,.26f,.30f,.34f);
            b.lathe(sign*.47f,1.03f,0,.31f,.42f,.25f,9,.69f,.52f,.40f);
            b.box(sign*.47f,.16f,.28f,.63f,.31f,.72f,.34f,.35f,.37f);
        }
        // Gothic raised crest / scarlet reliquary core.
        b.box(0,2.03f,.64f,.75f,.99f,.18f,.55f,.16f,.17f);
        b.spike(0,1.72f,.75f,.35f,.74f,7,.99f,.25f,.16f);
        b.box(0,2.71f,-.70f,1.0f,.18f,.18f,.80f,.55f,.33f);
        b.box(0,2.08f,-.78f,.22f,1.27f,.14f,.73f,.55f,.37f);
        return b.done();
    }
    public static Model sword(){
        Sculpt b=new Sculpt();
        // Local origin = grip: vertical long-sword in the +Z facing hand.
        b.lathe(0,-.21f,0,.06f,.065f,.50f,7,.25f,.19f,.14f);
        b.box(0,.10f,0,.55f,.11f,.15f,.86f,.69f,.40f);
        b.lathe(0,.13f,0,.14f,.11f,.14f,8,.67f,.56f,.39f);
        b.box(0,.81f,0,.20f,1.31f,.085f,.68f,.78f,.84f);
        b.spike(0,1.46f,0,.18f,.62f,5,.83f,.91f,.96f);
        b.box(0,1.11f,.067f,.055f,.36f,.024f,.93f,.94f,.87f);
        return b.done();
    }
    public static Model greatsword(){
        Sculpt b=new Sculpt();
        b.lathe(0,-.34f,0,.12f,.14f,.79f,8,.26f,.22f,.22f);
        b.box(0,.19f,0,1.28f,.18f,.27f,.62f,.48f,.34f);
        b.box(0,1.19f,0,.45f,1.85f,.19f,.44f,.53f,.61f);
        b.spike(0,2.12f,0,.37f,.90f,7,.69f,.74f,.77f);
        b.box(0,1.22f,.13f,.08f,1.7f,.03f,.81f,.65f,.48f);
        for(int sign=-1;sign<=1;sign+=2)
            b.spike(sign*.60f,.16f,0,.16f,.53f,5,.53f,.43f,.39f);
        return b.done();
    }
    public static Model lantern(){
        Sculpt b=new Sculpt();
        b.lathe(0,0,0,.15f,.23f,.53f,8,.31f,.34f,.32f);
        b.lathe(0,.53f,0,.26f,.25f,.10f,8,.71f,.56f,.36f);
        b.lathe(0,.64f,0,.21f,.19f,.38f,8,.88f,.53f,.23f);
        b.spike(0,1.02f,0,.23f,.44f,8,.65f,.63f,.50f);
        return b.done();
    }
}
