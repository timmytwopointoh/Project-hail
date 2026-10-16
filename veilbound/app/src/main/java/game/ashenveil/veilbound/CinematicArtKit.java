package game.ashenveil.veilbound;

import java.util.Arrays;

/**
 * VEILBOUND hero-mesh atelier: authored procedural surface forms with smooth
 * sculpted silhouettes. Everything is native vertex geometry; no WebView.
 *
 * Underlying M0.7 hands retain their individually plated fingers. New outer
 * forms hide primitive cylinders: shaped cuirasses, laminated pauldrons,
 * engraved visors, double-sided folded mantles, fluted greaves, embossed
 * sigils, scalloped weapon guards and ornate Ash Knight crown pieces.
 *
 * All procedural tessellation happens ONCE when the workshop loads. Animated
 * gameplay continues using its original lower-cost Level of Detail.
 */
public final class CinematicArtKit {
    private CinematicArtKit(){}
    private static final float PI=(float)Math.PI,TAU=2f*PI;
    private static float[] v(float x,float y,float z){return new float[]{x,y,z};}
    private static float clamp(float x,float a,float b){return Math.max(a,Math.min(b,x));}

    private static final class Form {
        private float[] verts; private int count;
        Form(float[] base){
            verts=Arrays.copyOf(base,Math.max(base.length+131072,131072));
            count=base.length;
        }
        void vertex(float[] p,float[] normal,float r,float g,float b){
            if(count+9>verts.length)verts=Arrays.copyOf(verts,verts.length*2);
            verts[count++]=p[0];verts[count++]=p[1];verts[count++]=p[2];
            verts[count++]=normal[0];verts[count++]=normal[1];verts[count++]=normal[2];
            verts[count++]=r;verts[count++]=g;verts[count++]=b;
        }
        private float[] normal(float[] a,float[] b,float[] c){
            float ux=b[0]-a[0],uy=b[1]-a[1],uz=b[2]-a[2];
            float vx=c[0]-a[0],vy=c[1]-a[1],vz=c[2]-a[2];
            float nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
            float l=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(l<.0000001f)return v(0,1,0);
            return v(nx/l,ny/l,nz/l);
        }
        void tri(float[] a,float[] b,float[] c,float r,float g,float blue){
            float[] n=normal(a,b,c);
            vertex(a,n,r,g,blue);vertex(b,n,r,g,blue);vertex(c,n,r,g,blue);
        }
        void quad(float[] a,float[] b,float[] c,float[] d,float r,float g,float blue){
            tri(a,b,c,r,g,blue);tri(a,c,d,r,g,blue);
        }
        void smoothTri(float[] a,float[] b,float[] c,
                       float[] an,float[] bn,float[] cn,float r,float g,float blue){
            vertex(a,an,r,g,blue);vertex(b,bn,r,g,blue);vertex(c,cn,r,g,blue);
        }
        void smoothQuad(float[] a,float[] b,float[] c,float[] d,
                        float[] na,float[] nb,float[] nc,float[] nd,
                        float r,float g,float blue){
            smoothTri(a,b,c,na,nb,nc,r,g,blue);
            smoothTri(a,c,d,na,nc,nd,r,g,blue);
        }
        float[] ellipse(float theta,float phi,float x,float y,float z,
                        float rx,float ry,float rz){
            return v(x+rx*(float)Math.cos(phi)*(float)Math.cos(theta),
                     y+ry*(float)Math.sin(phi),
                     z+rz*(float)Math.cos(phi)*(float)Math.sin(theta));
        }
        float[] ellipseNormal(float theta,float phi,float rx,float ry,float rz){
            float nx=(float)Math.cos(phi)*(float)Math.cos(theta)/rx;
            float ny=(float)Math.sin(phi)/ry;
            float nz=(float)Math.cos(phi)*(float)Math.sin(theta)/rz;
            float l=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            return v(nx/l,ny/l,nz/l);
        }
        void ellipsoid(float x,float y,float z,float rx,float ry,float rz,
                       int longitude,int latitude,float r,float g,float b){
            for(int row=0;row<latitude;row++){
                float phi0=-PI/2f+PI*row/latitude;
                float phi1=-PI/2f+PI*(row+1)/latitude;
                for(int col=0;col<longitude;col++){
                    float th0=TAU*col/longitude,th1=TAU*(col+1)/longitude;
                    float[] a=ellipse(th0,phi0,x,y,z,rx,ry,rz);
                    float[] bb=ellipse(th0,phi1,x,y,z,rx,ry,rz);
                    float[] c=ellipse(th1,phi1,x,y,z,rx,ry,rz);
                    float[] d=ellipse(th1,phi0,x,y,z,rx,ry,rz);
                    float[] an=ellipseNormal(th0,phi0,rx,ry,rz);
                    float[] bn=ellipseNormal(th0,phi1,rx,ry,rz);
                    float[] cn=ellipseNormal(th1,phi1,rx,ry,rz);
                    float[] dn=ellipseNormal(th1,phi0,rx,ry,rz);
                    float shade=.93f+.07f*(float)Math.sin(col*.77f+row*.21f);
                    smoothQuad(a,bb,c,d,an,bn,cn,dn,r*shade,g*shade,b*shade);
                }
            }
        }
        /** Curved plate whose width/center shift changes down the body. */
        void torsoLoft(float centerX,float centerZ,float bottom,float height,
                       float[] rx,float[] rz,int longitude,
                       float r,float g,float blue){
            int rows=rx.length-1;
            for(int j=0;j<rows;j++){
                float y0=bottom+height*j/rows,y1=bottom+height*(j+1)/rows;
                for(int i=0;i<longitude;i++){
                    float a=TAU*i/longitude,bb=TAU*(i+1)/longitude;
                    float[] p=v(centerX+rx[j]*(float)Math.cos(a),y0,
                                centerZ+rz[j]*(float)Math.sin(a));
                    float[] q=v(centerX+rx[j+1]*(float)Math.cos(a),y1,
                                centerZ+rz[j+1]*(float)Math.sin(a));
                    float[] ss=v(centerX+rx[j+1]*(float)Math.cos(bb),y1,
                                 centerZ+rz[j+1]*(float)Math.sin(bb));
                    float[] t=v(centerX+rx[j]*(float)Math.cos(bb),y0,
                                centerZ+rz[j]*(float)Math.sin(bb));
                    float[] n1=v((float)Math.cos(a),.03f,(float)Math.sin(a));
                    float[] n2=v((float)Math.cos(bb),.03f,(float)Math.sin(bb));
                    float c=.95f+.05f*(float)Math.sin(a*3);
                    smoothQuad(p,q,ss,t,n1,n1,n2,n2,r*c,g*c,blue*c);
                }
            }
        }
        /** Raised engraved line, segmented into smooth 10-sided tubes. */
        void engraving(float[] path,float radius,float r,float g,float b){
            int points=path.length/3;
            for(int i=0;i<points-1;i++){
                int a=i*3,j=(i+1)*3;
                rod(path[a],path[a+1],path[a+2],path[j],path[j+1],path[j+2],
                    radius,8,r,g,b);
            }
        }
        void rod(float ax,float ay,float az,float bx,float by,float bz,
                 float radius,int sides,float r,float g,float blue){
            float dx=bx-ax,dy=by-ay,dz=bz-az;
            float norm=(float)Math.sqrt(dx*dx+dy*dy+dz*dz);
            if(norm<.00001f)return;
            dx/=norm;dy/=norm;dz/=norm;
            float ux=dz,uy=0f,uz=-dx;
            float ln=(float)Math.hypot(ux,uz);
            if(ln<.01f){ux=1;uz=0;}else{ux/=ln;uz/=ln;}
            float vx=dy*uz-dz*uy,vy=dz*ux-dx*uz,vz=dx*uy-dy*ux;
            for(int i=0;i<sides;i++){
                float a=TAU*i/sides,ang=TAU*(i+1)/sides;
                float ca=(float)Math.cos(a),sa=(float)Math.sin(a);
                float cb=(float)Math.cos(ang),sb=(float)Math.sin(ang);
                float[] p=v(ax+radius*(ux*ca+vx*sa),ay+radius*(uy*ca+vy*sa),
                            az+radius*(uz*ca+vz*sa));
                float[] q=v(bx+radius*(ux*ca+vx*sa),by+radius*(uy*ca+vy*sa),
                            bz+radius*(uz*ca+vz*sa));
                float[] rr=v(bx+radius*(ux*cb+vx*sb),by+radius*(uy*cb+vy*sb),
                             bz+radius*(uz*cb+vz*sb));
                float[] t=v(ax+radius*(ux*cb+vx*sb),ay+radius*(uy*cb+vy*sb),
                            az+radius*(uz*cb+vz*sb));
                quad(p,q,rr,t,r,g,blue);
            }
        }
        /** A 30x16 pleated textile with double-sided geometry. */
        void mantle(float width,float top,float bottom,float back,
                    float red,float green,float blue){
            int columns=32,rows=19;
            for(int i=0;i<columns;i++){
                float u0=i/(float)columns,u1=(i+1f)/columns;
                for(int j=0;j<rows;j++){
                    float t0=j/(float)rows,t1=(j+1f)/rows;
                    float[] a=clothPoint(u0,t0,width,top,bottom,back);
                    float[] b=clothPoint(u1,t0,width,top,bottom,back);
                    float[] c=clothPoint(u1,t1,width,top,bottom,back);
                    float[] d=clothPoint(u0,t1,width,top,bottom,back);
                    float shade=.84f+.18f*(float)Math.cos(u0*TAU*7f);
                    quad(a,b,c,d,red*shade,green*shade,blue*shade);
                    quad(d,c,b,a,red*.62f,green*.67f,blue*.72f);
                }
            }
            for(int edge=0;edge<=1;edge++){
                float[] line=new float[(rows+1)*3];
                for(int j=0;j<=rows;j++){
                    float[] p=clothPoint(edge,j/(float)rows,width,top,bottom,back);
                    System.arraycopy(p,0,line,j*3,3);
                }
                engraving(line,.015f,.73f,.55f,.34f);
            }
        }
        float[] clothPoint(float u,float t,float width,float top,float bottom,float back){
            float arc=(float)Math.sin(u*TAU*6.5f);
            float x=(u-.5f)*width*(1f+.35f*t);
            float y=top-(top-bottom)*t+
                    t*t*.09f*(float)Math.sin(u*TAU*8);
            float z=back-.19f*t-.13f*(float)Math.sin(u*TAU*6)*t-
                    .06f*(float)Math.cos(u*TAU*14)*t;
            return v(x,y,z+.04f*arc*t);
        }
        ArtKit.Model result(){return new ArtKit.Model(Arrays.copyOf(verts,count));}
    }
    private static void bellwardenSculpt(Form f){
        // A tapered, fluted cuirass overlays the temporary conical torso.
        f.torsoLoft(0,-.01f,.81f,1.12f,
            new float[]{.29f,.35f,.42f,.52f,.54f,.47f,.40f},
            new float[]{.30f,.36f,.39f,.43f,.43f,.34f,.30f},32,
            .52f,.64f,.70f);
        f.ellipsoid(0,1.50f,.25f,.45f,.38f,.29f,32,15,.63f,.75f,.80f);
        // Laminated asymmetric shoulder armor, with gold ridge filigree.
        for(int side=-1;side<=1;side+=2){
            float x=side*.73f;
            f.ellipsoid(x,1.80f,-.025f,.55f,.31f,.49f,30,14,
                        .45f,.57f,.66f);
            f.ellipsoid(x,1.89f,-.005f,.47f,.20f,.48f,30,11,
                        .57f,.66f,.70f);
            f.ellipsoid(x,1.99f,.00f,.37f,.14f,.38f,28,9,
                        .62f,.70f,.71f);
            f.rod(x-side*.41f,1.83f,.28f,x,2.08f,.22f,
                  .043f,9,.85f,.68f,.39f);
            f.rod(x,2.08f,.22f,x+side*.42f,1.84f,.10f,
                  .043f,9,.82f,.63f,.38f);
            // Sculpted shin shells: separate rounded knees, tapered ankles.
            f.ellipsoid(side*.26f,.53f,.17f,.23f,.43f,.27f,22,12,
                        .39f,.45f,.53f);
            f.ellipsoid(side*.26f,.75f,.29f,.23f,.17f,.23f,25,10,
                        .71f,.70f,.58f);
            f.rod(side*.38f,.22f,.30f,side*.37f,.71f,.36f,
                  .022f,9,.82f,.72f,.54f);
        }
        // Historically inspired armet with a low brow and curved snout visor.
        f.ellipsoid(0,2.31f,.0f,.42f,.47f,.39f,40,20,.46f,.59f,.66f);
        f.ellipsoid(0,2.56f,.07f,.405f,.17f,.39f,40,12,.76f,.72f,.57f);
        f.ellipsoid(0,2.23f,.33f,.33f,.18f,.11f,32,10,.10f,.13f,.19f);
        // Thin angular orbital bar and gold central fluting.
        f.rod(-.36f,2.30f,.37f,.36f,2.30f,.37f,.033f,9,.87f,.75f,.52f);
        f.rod(0,2.78f,.10f,0,2.18f,.43f,.047f,11,.82f,.68f,.44f);
        for(int k=0;k<11;k++){
            float a=-PI*.87f+k*PI*.174f;
            float x=.38f*(float)Math.cos(a),z=.36f*(float)Math.sin(a);
            f.ellipsoid(x,2.65f,z,.032f,.046f,.032f,10,6,.80f,.72f,.51f);
        }
        // Folded velvet mantle, gold piping and darker embroidered lining.
        f.mantle(1.29f,1.97f,.14f,-.53f,.18f,.23f,.38f);
        // Circlet / reliquary bell emblem on breastplate.
        float[] chest=new float[3*33];
        for(int i=0;i<=32;i++){
            float a=TAU*i/32f;
            chest[i*3]=.15f*(float)Math.sin(a);
            chest[i*3+1]=1.46f+.19f*(float)Math.cos(a);
            chest[i*3+2]=.535f;
        }
        f.engraving(chest,.024f,.88f,.71f,.45f);
        f.rod(0,1.41f,.55f,0,1.28f,.55f,.034f,10,.90f,.71f,.44f);
        f.ellipsoid(0,1.26f,.58f,.07f,.06f,.045f,14,8,.91f,.77f,.51f);
        // M11 player-only upgrade: overlapping forged collar, mail neck,
        // bevelled fan tassets and scale-by-scale surface break-up.
        // Distinct contours survive the distant third-person camera.
        for(int side=-1;side<=1;side+=2){
            // Layered burnished throat plate and forged torc collar.
            f.ellipsoid(side*.23f,1.97f,.14f,.28f,.12f,.31f,22,9,
                        .29f,.35f,.41f);
            f.rod(side*.17f,2.035f,.40f,side*.48f,1.97f,.25f,
                  .025f,9,.77f,.68f,.49f);
            // Interlocking breastplate side ribs / riveted underlay.
            for(int rib=0;rib<5;rib++){
                float yy=1.24f+rib*.123f;
                float xx=side*(.34f+rib*.022f);
                f.ellipsoid(xx,yy,.31f,.135f,.061f,.10f,15,7,
                            .32f+rib*.018f,.39f+rib*.012f,.46f+rib*.01f);
                f.ellipsoid(xx+side*.073f,yy,.391f,.016f,.015f,.019f,
                            10,5,.79f,.67f,.48f);
            }
            // Overlapping hip flaps cascade toward the upper thighs.
            for(int t=0;t<4;t++){
                float tx=side*(.40f+t*.09f);
                f.ellipsoid(tx,.84f-t*.095f,.15f,.135f,.19f,.103f,
                            18,11,.29f+t*.025f,.36f+t*.027f,.41f+t*.029f);
                f.rod(tx-side*.068f,.72f-t*.095f,.225f,
                      tx+side*.065f,.72f-t*.095f,.22f,
                      .017f,8,.70f,.60f,.40f);
            }
            // Anatomically rounded sabaton and floating knee trim.
            f.ellipsoid(side*.26f,.16f,.40f,.25f,.13f,.43f,27,13,
                        .36f,.42f,.46f);
            for(int ring=0;ring<4;ring++){
                float zz=.53f+ring*.066f;
                f.ellipsoid(side*.26f,.19f,zz,.24f-ring*.022f,.045f,.09f,
                            20,7,.43f,.49f,.54f);
            }
            f.ellipsoid(side*.26f,.73f,.34f,.285f,.17f,.26f,26,12,
                        .65f,.65f,.59f);
            f.rod(side*.12f,.75f,.49f,side*.41f,.75f,.48f,
                  .018f,8,.83f,.71f,.47f);
            // Raised pauldron ridge and amber plated rivet heads.
            float shoulder=side*.76f;
            for(int plate=0;plate<4;plate++){
                f.ellipsoid(shoulder+side*.14f,1.92f-plate*.105f,
                            -.045f+plate*.05f,.47f-plate*.025f,.085f,.40f,
                            24,10,.35f+plate*.055f,.45f+plate*.05f,
                            .52f+plate*.04f);
                f.ellipsoid(shoulder+side*.37f,1.91f-plate*.103f,.23f,
                            .027f,.027f,.030f,11,7,.82f,.69f,.46f);
            }
        }
        // Ventilated visor slits and raised bronze brow create believable
        // negative space rather than a smooth featureless helmet sphere.
        for(int slit=0;slit<7;slit++){
            float sx=(slit-3f)*.085f;
            float y=2.24f+(slit%2)*.014f;
            f.rod(sx,y,.437f,sx,y+.087f,.425f,.016f,8,.10f,.13f,.16f);
            f.ellipsoid(sx,2.34f,.419f,.026f,.022f,.029f,
                        11,6,.78f,.68f,.47f);
        }
        // Angular cheek guards and raised center seam carry the silhouette
        // into gameplay without increasing global lighting costs.
        f.rod(-.37f,2.35f,.23f,-.25f,2.11f,.36f,.046f,12,
              .49f,.57f,.61f);
        f.rod(.37f,2.35f,.23f,.25f,2.11f,.36f,.046f,12,
              .49f,.57f,.61f);
        f.rod(0,2.80f,.06f,0,2.95f,-.05f,.055f,11,
              .76f,.65f,.46f);
        // Scalloped leather lamellar scales over hips.
        for(int side=-1;side<=1;side+=2){
            for(int i=0;i<7;i++){
                float a=side*(.18f+i*.105f);
                float x=.36f*(float)Math.sin(a*2.1f),z=.29f*(float)Math.cos(a*2f);
                f.ellipsoid(side*x,.75f+i*.009f,z,
                    .085f,.22f,.071f,12,8,.46f,.48f,.53f);
            }
        }
    }
    private static void ashKnightSculpt(Form f){
        f.torsoLoft(0,-.08f,1.03f,1.72f,
            new float[]{.48f,.60f,.69f,.77f,.86f,.85f,.66f},
            new float[]{.52f,.60f,.65f,.70f,.73f,.62f,.45f},36,
            .36f,.37f,.42f);
        f.ellipsoid(0,2.36f,.33f,.75f,.57f,.54f,40,17,.41f,.43f,.48f);
        // Distinct silhouette: sweeping spiked pauldrons, broken ivory ridges.
        for(int side=-1;side<=1;side+=2){
            float x=side*1.09f;
            f.ellipsoid(x,2.62f,0,.79f,.42f,.74f,38,17,.39f,.43f,.47f);
            f.ellipsoid(x,2.82f,-.03f,.68f,.30f,.62f,34,13,.50f,.47f,.46f);
            for(int prong=0;prong<5;prong++){
                float xx=x+side*(prong*.13f-.22f);
                float h=prong%2==0?.71f:.50f;
                f.rod(xx,2.82f,.11f,xx+side*.24f,3.05f+h,.04f,
                      .07f,10,.70f,.56f,.44f);
            }
            f.ellipsoid(side*.43f,.96f,.25f,.35f,.52f,.41f,24,14,
                        .42f,.43f,.47f);
            f.rod(side*.65f,.34f,.30f,side*.58f,1.18f,.42f,
                  .036f,10,.72f,.55f,.44f);
        }
        f.ellipsoid(0,3.26f,0,.55f,.62f,.49f,42,20,.30f,.34f,.40f);
        f.ellipsoid(0,3.43f,.40f,.46f,.20f,.16f,30,12,.12f,.07f,.09f);
        f.rod(-.49f,3.48f,.43f,.49f,3.48f,.43f,
              .051f,11,.83f,.51f,.34f);
        // Thorn crown roots wrap all the way around the armet.
        for(int i=0;i<18;i++){
            float a=i*TAU/18f;
            float x=.52f*(float)Math.cos(a),z=.50f*(float)Math.sin(a);
            f.rod(x,3.60f,z,x*1.17f,3.95f+(i%3)*.22f,z*1.21f,
                  .055f,9,.68f,.54f,.44f);
        }
        f.mantle(2.0f,3.02f,.13f,-.80f,.28f,.12f,.16f);
        float[] serpent=new float[3*49];
        for(int i=0;i<=48;i++){
            float t=i/48f;
            serpent[i*3]=.24f*(float)Math.sin(t*PI*4.);
            serpent[i*3+1]=1.54f+t*.93f;
            serpent[i*3+2]=.74f+.08f*(float)Math.sin(t*PI);
        }
        f.engraving(serpent,.046f,.90f,.37f,.23f);
        for(int i=0;i<8;i++){
            float a=TAU*i/8f;
            f.ellipsoid(.40f*(float)Math.cos(a),2.35f+.28f*(float)Math.sin(a),
                    .62f,.055f,.068f,.039f,12,7,.90f,.69f,.46f);
        }
    }
    private static void hushedSculpt(Form f){
        f.ellipsoid(0,2.24f,.01f,.29f,.41f,.32f,26,16,.47f,.49f,.45f);
        f.ellipsoid(0,2.20f,.30f,.23f,.12f,.08f,20,8,.06f,.07f,.08f);
        for(int side=-1;side<=1;side+=2){
            f.ellipsoid(side*.51f,1.75f,.0f,.35f,.23f,.33f,22,10,
                        .48f,.48f,.42f);
            for(int rib=0;rib<6;rib++){
                float y=1.16f+rib*.14f;
                f.rod(side*.06f,y,.29f,side*.36f,y+.045f,.15f,
                      .045f,9,.69f,.65f,.54f);
            }
        }
        f.mantle(.91f,1.97f,.16f,-.43f,.15f,.19f,.22f);
    }
    private static void bladeSculpt(Form f,boolean great){
        float width=great?.37f:.15f;
        float length=great?2.12f:1.25f;
        float yStart=great?.39f:.30f;
        int sections=26;
        for(int i=0;i<sections;i++){
            float t=i/(float)sections,t1=(i+1f)/sections;
            float w0=width*(1f-.76f*t*t);
            float w1=width*(1f-.76f*t1*t1);
            float y0=yStart+length*t,y1=yStart+length*t1;
            float raised=great?.15f:.08f;
            float[] bl=v(-w0,y0,0),bm=v(0,y0,raised),br=v(w0,y0,0);
            float[] tl=v(-w1,y1,0),tm=v(0,y1,raised),tr=v(w1,y1,0);
            f.quad(bl,tl,tm,bm,.77f,.84f,.90f);
            f.quad(bm,tm,tr,br,.54f,.63f,.70f);
            f.quad(br,tr,v(0,y1,-raised),v(0,y0,-raised),
                   .62f,.69f,.73f);
            f.quad(v(0,y0,-raised),v(0,y1,-raised),tl,bl,
                   .47f,.57f,.66f);
        }
        float hilt=great?.22f:.10f;
        for(int side=-1;side<=1;side+=2){
            float[] wing=new float[3*21];
            for(int k=0;k<=20;k++){
                float t=k/20f;
                wing[k*3]=side*t*(great?.99f:.47f);
                wing[k*3+1]=hilt+.14f*(float)Math.sin(t*PI);
                wing[k*3+2]=-.01f+(float)Math.sin(t*PI)*.07f;
            }
            f.engraving(wing,.06f,.86f,.64f,.43f);
        }
    }
    public static ArtKit.Model bellwarden(){
        Form f=new Form(DetailArtKit.bellwarden().vertices);
        bellwardenSculpt(f);return f.result();
    }
    public static ArtKit.Model hushed(){
        Form f=new Form(DetailArtKit.hushed().vertices);
        hushedSculpt(f);return f.result();
    }
    public static ArtKit.Model ashKnight(){
        Form f=new Form(DetailArtKit.ashKnight().vertices);
        ashKnightSculpt(f);return f.result();
    }
    public static ArtKit.Model sword(){
        Form f=new Form(DetailArtKit.sword().vertices);
        bladeSculpt(f,false);return f.result();
    }
    public static ArtKit.Model greatsword(){
        Form f=new Form(DetailArtKit.greatsword().vertices);
        bladeSculpt(f,true);return f.result();
    }
}
