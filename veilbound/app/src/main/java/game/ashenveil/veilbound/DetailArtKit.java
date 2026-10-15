package game.ashenveil.veilbound;

import java.util.Arrays;

/**
 * Inspection-grade sculpted detail overlays. Meshes are tessellated once,
 * lazily when opening the Model Atelier, never every render frame.
 *
 * The original gameplay mesh remains in ArtKit so a weaker Android GPU can
 * keep its frame rate. Geometry budget deliberately is NOT an APK size limit.
 *
 * Every individual gauntlet has thousands of facets: curved palm surfaces,
 * segmented fingers, thumb roots, nail plates, cuff rings, knuckle caps,
 * filigree and rivets. The same builder is reused on bosses, not copied meshes.
 */
public final class DetailArtKit {
    private DetailArtKit(){}
    private static final float TAU=(float)(2*Math.PI);

    private static final class Sculpt {
        private float[] data;
        private int used;
        Sculpt(float[] base){
            data=Arrays.copyOf(base,Math.max(32768,base.length+4096));
            used=base.length;
        }
        void vertex(float[] p,float nx,float ny,float nz,
                    float r,float g,float b){
            if(used+9>data.length)data=Arrays.copyOf(data,data.length*2);
            data[used++]=p[0];data[used++]=p[1];data[used++]=p[2];
            data[used++]=nx;data[used++]=ny;data[used++]=nz;
            data[used++]=r;data[used++]=g;data[used++]=b;
        }
        void tri(float[] p,float[] q,float[] r,float red,float green,float blue){
            float ux=q[0]-p[0],uy=q[1]-p[1],uz=q[2]-p[2];
            float vx=r[0]-p[0],vy=r[1]-p[1],vz=r[2]-p[2];
            float nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
            float norm=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(norm<.0000005f)return;
            nx/=norm;ny/=norm;nz/=norm;
            vertex(p,nx,ny,nz,red,green,blue);
            vertex(q,nx,ny,nz,red,green,blue);
            vertex(r,nx,ny,nz,red,green,blue);
        }
        void quad(float[] a,float[] b,float[] c,float[] d,
                  float r,float g,float bl){
            tri(a,b,c,r,g,bl);tri(a,c,d,r,g,bl);
        }
        /**
         * Hand-modeled radial rings with subtly asymmetrical taper and bend.
         * ringCount controls longitudinal detail, sides the cross-section.
         * 24 x 18 rings = 864 hand-facing triangles per finger.
         */
        void tube(float ax,float ay,float az,
                  float bx,float by,float bz,
                  float thickness,int sides,int ringCount,
                  float r,float g,float blue,float asymmetry){
            float dx=bx-ax,dy=by-ay,dz=bz-az;
            float len=(float)Math.sqrt(dx*dx+dy*dy+dz*dz);
            if(len<.0001f)return;
            dx/=len;dy/=len;dz/=len;
            float ux=dz,uy=0,uz=-dx;
            float norm=(float)Math.hypot(ux,uz);
            if(norm<.001f){ux=1;uz=0;}
            else{ux/=norm;uz/=norm;}
            float vx=dy*uz-dz*uy,vy=dz*ux-dx*uz,vz=dx*uy-dy*ux;
            float[] lastRing=new float[sides*3];
            for(int row=0;row<=ringCount;row++){
                float t=(float)row/ringCount;
                float[] ring=new float[sides*3];
                float curve=(float)Math.sin(t*Math.PI)*asymmetry;
                float width=thickness*(1f-.24f*t);
                // Knuckles curve over joints instead of displaying cylinders.
                width*=1f+.11f*(float)Math.sin(t*TAU*2.7f);
                for(int k=0;k<sides;k++){
                    float a=TAU*k/sides;
                    float ca=(float)Math.cos(a),sa=(float)Math.sin(a);
                    float ridge=1f+.035f*(float)Math.sin(k*2.7+t*22.);
                    ring[3*k]=ax+(bx-ax)*t+curve*uz+
                        width*ridge*(ux*ca+vx*sa);
                    ring[3*k+1]=ay+(by-ay)*t+
                        width*ridge*(uy*ca+vy*sa);
                    ring[3*k+2]=az+(bz-az)*t+curve*.16f+
                        width*ridge*(uz*ca+vz*sa);
                }
                if(row>0){
                    float shade=1f+.025f*(float)Math.cos(t*TAU*3f);
                    for(int k=0;k<sides;k++){
                        int next=(k+1)%sides;
                        float[] p=point(lastRing,k),q=point(lastRing,next);
                        float[] a=point(ring,next),b=point(ring,k);
                        quad(p,b,a,q,r*shade,g*shade,blue*shade);
                    }
                }
                lastRing=ring;
            }
        }
        void band(float x,float y,float z,float radius,float height,
                  int sides,float r,float g,float b){
            tube(x,y-height*.5f,z,x,y+height*.5f,z,
                 radius,sides,3,r,g,b,.008f);
        }
        void orb(float x,float y,float z,float radius,
                 float r,float g,float b){
            // A jewel/rivet with two sculpted rings and pointed poles.
            int faces=10;
            float[] north=v(x,y+radius,z),south=v(x,y-radius,z);
            for(int k=0;k<faces;k++){
                float a=TAU*k/faces,bb=TAU*(k+1)/faces;
                float[] q=v(x+radius*(float)Math.cos(a),y,z+radius*(float)Math.sin(a));
                float[] rr=v(x+radius*(float)Math.cos(bb),y,z+radius*(float)Math.sin(bb));
                tri(north,q,rr,r,g,b);tri(south,rr,q,r*.72f,g*.72f,b*.73f);
            }
        }
        void stitchedTrim(float x,float y,float z,float width,float length,
                          float r,float g,float b){
            int n=Math.max(8,(int)(length*95));
            for(int k=0;k<n;k++){
                float yp=y+(k+.5f)/n*length;
                float xx=x+(float)Math.sin(k*2.4f)*.008f;
                float[] a=v(xx-width*.5f,yp-.005f,z);
                float[] p=v(xx+width*.5f,yp+.007f,z);
                float[] tip=v(xx+.02f,yp+.017f,z+.006f);
                tri(a,p,tip,r,g,b);
            }
        }
        ArtKit.Model model(){return new ArtKit.Model(Arrays.copyOf(data,used));}
        int triangles(){return used/27;}
    }
    private static float[] point(float[] ring,int k){
        return v(ring[k*3],ring[k*3+1],ring[k*3+2]);
    }
    private static float[] v(float x,float y,float z){return new float[]{x,y,z};}

    private static void gauntlet(Sculpt s,float side,float x,float shoulderY,
                                 float sc,float tint,float bronze){
        // Forged iron bracer, articulated wrist and anatomically distinct palm.
        float cx=side*x,z=.12f*sc;
        s.tube(cx,shoulderY,z,cx+side*.02f*sc,shoulderY-.63f*sc,z+.08f*sc,
               .205f*sc,24,25,.48f*tint,.56f*tint,.62f*tint,.018f*sc);
        for(int j=0;j<5;j++)
            s.band(cx,shoulderY-(.12f+j*.12f)*sc,z+.08f*sc,
                   (.218f-(j*.007f))*sc,.020f*sc,28,
                   .76f*bronze,.61f*bronze,.41f*bronze);
        float root=shoulderY-.66f*sc;
        s.tube(cx,root,z+.11f*sc,cx,root-.36f*sc,z+.18f*sc,
               .215f*sc,32,26,.58f*tint,.64f*tint,.69f*tint,.014f*sc);
        s.band(cx,root+.035f*sc,z+.13f*sc,.235f*sc,.075f*sc,32,
               .76f*bronze,.64f*bronze,.46f*bronze);
        // Four unequal digits, individually tapered: never a single mitten.
        float[] lengths={.33f,.46f,.43f,.34f};
        float[] gaps={-.17f,-.06f,.07f,.17f};
        for(int digit=0;digit<4;digit++){
            float fx=cx+side*gaps[digit]*sc;
            float y=root-.35f*sc;
            float len=lengths[digit]*sc;
            float fingerR=(digit==1||digit==2?.050f:.044f)*sc;
            s.tube(fx,y,z+.19f*sc,fx+side*.02f*sc,y-len,z+.23f*sc,
                   fingerR,24,18,.59f*tint,.65f*tint,.72f*tint,.012f*sc);
            for(int joint=0;joint<3;joint++){
                float jy=y-(joint+.65f)*len/3f;
                s.band(fx,jy,z+.21f*sc,fingerR*1.17f,.020f*sc,24,
                       .80f*bronze,.67f*bronze,.45f*bronze);
            }
            // Hard knuckle crest, inscribed steel fingernail and rivet.
            s.orb(fx,y-.030f*sc,z+.22f*sc,fingerR*1.28f,
                  .72f*tint,.77f*tint,.79f*tint);
            s.orb(fx+side*.008f*sc,y-len*.91f,z+.252f*sc,
                  fingerR*.74f,.87f,.81f,.65f);
        }
        float thumbX=cx+side*.22f*sc,thumbY=root-.21f*sc;
        s.tube(thumbX,thumbY,z+.18f*sc,
               thumbX+side*.21f*sc,thumbY-.19f*sc,z+.28f*sc,
               .070f*sc,24,17,.57f*tint,.65f*tint,.69f*tint,.035f*sc);
        s.band(thumbX+side*.16f*sc,thumbY-.15f*sc,z+.25f*sc,
               .066f*sc,.037f*sc,24,.78f*bronze,.58f*bronze,.39f*bronze);
        // Etched gauntlet trim and embossed micro-rivets.
        for(int k=0;k<14;k++){
            float y=root+.12f*sc+k*.023f*sc;
            s.orb(cx+side*(.205f+(k%3)*.005f)*sc,y,z+.14f*sc,
                  .009f*sc,.93f,.81f,.55f);
        }
    }
    public static ArtKit.Model bellwarden(){
        Sculpt s=new Sculpt(ArtKit.bellwarden().vertices);
        gauntlet(s,-1,.66f,1.45f,1f,1f,1f);
        gauntlet(s,1,.66f,1.45f,1f,1f,1f);
        // Embossed brass buckles and asymmetric engraved armor studs.
        for(int i=0;i<64;i++){
            float a=TAU*i/64f;
            float y=1.49f+.32f*(float)Math.sin(a);
            float x=.45f*(float)Math.cos(a);
            s.orb(x,y,.31f,.018f,.76f,.70f,.46f);
        }
        for(int i=0;i<20;i++){
            float y=.73f+i*.042f;
            s.stitchedTrim(-.24f,y,.48f,.14f,.035f,.79f,.66f,.43f);
        }
        return s.model();
    }
    public static ArtKit.Model hushed(){
        Sculpt s=new Sculpt(ArtKit.hushed().vertices);
        // Broken chainmail and fleshless finger bones.
        gauntlet(s,-1,.55f,1.35f,.72f,.69f,.38f);
        gauntlet(s,1,.55f,1.35f,.72f,.71f,.39f);
        for(int i=0;i<85;i++){
            float a=TAU*i/17f;
            float ring=(i/17f);
            float x=(float)Math.cos(a)*(.32f-ring*.014f);
            float z=.29f+(float)Math.sin(a)*.025f;
            float y=1.20f+ring*.112f;
            s.orb(x,y,z,.022f,.49f,.41f,.39f);
        }
        return s.model();
    }
    public static ArtKit.Model ashKnight(){
        Sculpt s=new Sculpt(ArtKit.ashKnight().vertices);
        gauntlet(s,-1,1.05f,2.25f,1.29f,.73f,.86f);
        gauntlet(s,1,1.05f,2.25f,1.29f,.76f,.92f);
        // 96 forged breastplate bolts and scarlet enamel serpent scales.
        for(int row=0;row<12;row++){
            float y=1.48f+row*.111f;
            for(int k=0;k<12;k++){
                float x=(k-5.5f)*.092f;
                float z=.80f+.045f*(float)Math.cos(x*7f);
                s.orb(x,y,z,.024f,row%3==0?.80f:.49f,
                      row%3==0?.42f:.31f,row%3==0?.27f:.27f);
            }
        }
        for(int side=-1;side<=1;side+=2){
            for(int i=0;i<35;i++){
                float ang=TAU*i/35f;
                float x=side*(1.02f+.42f*(float)Math.cos(ang));
                float z=.23f*(float)Math.sin(ang);
                float y=2.63f+.22f*(float)Math.sin(ang);
                s.orb(x,y,z,.027f,.79f,.64f,.44f);
            }
        }
        return s.model();
    }
    public static ArtKit.Model sword(){
        Sculpt s=new Sculpt(ArtKit.sword().vertices);
        for(int i=0;i<120;i++){
            float y=.34f+i*.009f;
            float a=i*.61f;
            s.orb(.082f*(float)Math.sin(a),y,
                  .055f*(float)Math.cos(a),.012f,.84f,.77f,.59f);
        }
        return s.model();
    }
    public static ArtKit.Model greatsword(){
        Sculpt s=new Sculpt(ArtKit.greatsword().vertices);
        for(int i=0;i<180;i++){
            float y=.30f+i*.0121f;
            float x=.175f*(float)Math.sin(i*.17f);
            s.orb(x,y,.10f,.0115f,.85f,.62f,.40f);
        }
        return s.model();
    }
    public static ArtKit.Model lantern(){
        Sculpt s=new Sculpt(ArtKit.lantern().vertices);
        for(int i=0;i<12;i++){
            float a=i*TAU/12f;
            float x=(float)Math.cos(a)*.22f,z=(float)Math.sin(a)*.22f;
            s.tube(x,.59f,z,x*.85f,1.05f,z*.85f,.011f,10,8,
                   .81f,.63f,.39f,.011f);
            s.orb(x,.64f,z,.030f,.87f,.55f,.25f);
        }
        return s.model();
    }
}
