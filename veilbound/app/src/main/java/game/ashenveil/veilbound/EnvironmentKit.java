package game.ashenveil.veilbound;

import java.util.Arrays;

/**
 * Original sculptural world props, authored in the same 9-float triangle format
 * as the high-detail character Atelier. Deterministic and Android independent.
 * No proprietary engine or downloaded textures are required.
 */
public final class EnvironmentKit {
    private EnvironmentKit(){}
    private static final float PI=(float)Math.PI;
    private static float[] v(float x,float y,float z){return new float[]{x,y,z};}
    private static final class Sculpt {
        private float[] data=new float[4096];
        private int size=0;
        private void vertex(float[] p,float nx,float ny,float nz,float r,float g,float b){
            if(size+9>data.length)data=Arrays.copyOf(data,data.length*2);
            data[size++]=p[0];data[size++]=p[1];data[size++]=p[2];
            data[size++]=nx;data[size++]=ny;data[size++]=nz;
            data[size++]=r;data[size++]=g;data[size++]=b;
        }
        void tri(float[] a,float[] b,float[] c,float red,float green,float blue){
            float ux=b[0]-a[0],uy=b[1]-a[1],uz=b[2]-a[2];
            float vx=c[0]-a[0],vy=c[1]-a[1],vz=c[2]-a[2];
            float nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
            float length=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(length<.0000001f)return;
            vertex(a,nx/length,ny/length,nz/length,red,green,blue);
            vertex(b,nx/length,ny/length,nz/length,red,green,blue);
            vertex(c,nx/length,ny/length,nz/length,red,green,blue);
        }
        void quad(float[] a,float[] b,float[] c,float[] d,float r,float g,float blue){
            tri(a,b,c,r,g,blue);tri(a,c,d,r,g,blue);
        }
        void rod(float x0,float y0,float z0,float x1,float y1,float z1,
                 float r0,float r1,int sides,float r,float g,float blue){
            // Frame around arbitrary direction to create a tapering round forging.
            float dx=x1-x0,dy=y1-y0,dz=z1-z0;
            float length=(float)Math.sqrt(dx*dx+dy*dy+dz*dz);
            if(length<.0001f)return;
            dx/=length;dy/=length;dz/=length;
            float ux=dz,uy=0,uz=-dx;
            float un=(float)Math.sqrt(ux*ux+uz*uz);
            if(un<.0001f){ux=1;uz=0;un=1;}
            ux/=un;uz/=un;
            float vx=dy*uz-dz*uy,vy=dz*ux-dx*uz,vz=dx*uy-dy*ux;
            for(int i=0;i<sides;i++){
                float a=2f*PI*i/sides,b=2f*PI*(i+1)/sides;
                float ca=(float)Math.cos(a),sa=(float)Math.sin(a);
                float cb=(float)Math.cos(b),sb=(float)Math.sin(b);
                float[] p=v(x0+r0*(ux*ca+vx*sa),y0+r0*(uy*ca+vy*sa),z0+r0*(uz*ca+vz*sa));
                float[] q=v(x0+r0*(ux*cb+vx*sb),y0+r0*(uy*cb+vy*sb),z0+r0*(uz*cb+vz*sb));
                float[] c=v(x1+r1*(ux*cb+vx*sb),y1+r1*(uy*cb+vy*sb),z1+r1*(uz*cb+vz*sb));
                float[] d=v(x1+r1*(ux*ca+vx*sa),y1+r1*(uy*ca+vy*sa),z1+r1*(uz*ca+vz*sa));
                float shade=.87f+.13f*(float)Math.cos(a*2f);
                quad(p,d,c,q,r*shade,g*shade,blue*shade);
            }
        }
        void box(float x,float y,float z,float sx,float sy,float sz,float r,float g,float b){
            float x0=x-sx*.5f,x1=x+sx*.5f,y0=y-sy*.5f,y1=y+sy*.5f,z0=z-sz*.5f,z1=z+sz*.5f;
            float[] a=v(x0,y0,z0),bb=v(x1,y0,z0),c=v(x1,y0,z1),d=v(x0,y0,z1);
            float[] e=v(x0,y1,z0),f=v(x1,y1,z0),h=v(x1,y1,z1),i=v(x0,y1,z1);
            quad(d,c,h,i,r*1.04f,g*1.04f,b*1.04f);
            quad(bb,a,e,f,r*.83f,g*.83f,b*.83f);
            quad(a,d,i,e,r*.90f,g*.90f,b*.90f);
            quad(c,bb,f,h,r*.95f,g*.95f,b*.95f);
            quad(e,i,h,f,r*1.13f,g*1.13f,b*1.13f);
            quad(a,bb,c,d,r*.60f,g*.60f,b*.60f);
        }
        ArtKit.Model done(){return new ArtKit.Model(Arrays.copyOf(data,size));}
    }
    private static float grain(int index,int seed){
        int value=(index*1103515245+seed*1597334677)>>>8;
        return (value&4095)/4095f;
    }

    /** Asymmetric chipped, bevel-edged slab with sediment layer and 3D fractures. */
    public static ArtKit.Model flagstone(){
        Sculpt s=new Sculpt();
        final int n=13;
        float[] wx=new float[n],wz=new float[n],ix=new float[n],iz=new float[n];
        for(int i=0;i<n;i++){
            float a=2*PI*i/n;
            float rad=1f+(grain(i,77)-.5f)*.17f;
            wx[i]=rad*(float)Math.cos(a);
            wz[i]=rad*(float)Math.sin(a)*.79f;
            ix[i]=wx[i]*(.77f+.045f*grain(i,41));
            iz[i]=wz[i]*(.77f+.045f*grain(i,99));
        }
        for(int i=0;i<n;i++){
            int next=(i+1)%n;
            float top=.15f+.024f*grain(i,63);
            float ntop=.15f+.024f*grain(next,63);
            float[] center=v(0,.17f,0);
            float red=.45f+.07f*grain(i,8),green=red*.96f,blue=red*.91f;
            // Interleaved, multi-faced chipped surface with a raised interior ridge.
            s.tri(center,v(ix[next],ntop+.025f,iz[next]),v(ix[i],top+.025f,iz[i]),red,green,blue);
            s.quad(v(ix[i],top+.025f,iz[i]),v(ix[next],ntop+.025f,iz[next]),
                  v(wx[next],ntop-.025f,wz[next]),v(wx[i],top-.025f,wz[i]),
                  red*.91f,green*.93f,blue*.94f);
            s.quad(v(wx[i],top-.025f,wz[i]),v(wx[next],ntop-.025f,wz[next]),
                  v(wx[next]*.94f,-.095f,wz[next]*.94f),
                  v(wx[i]*.94f,-.095f,wz[i]*.94f),
                  red*.67f,green*.68f,blue*.69f);
            // Fine fissures sunk into the stone instead of painted black lines.
            if(i%3==0){
                float a=i*2f*PI/n;
                float[] p=v(ix[i]*.24f,.181f,iz[i]*.24f);
                float[] q=v(ix[i]*.78f,.180f,iz[i]*.78f);
                float x=(float)Math.cos(a+1.2f)*.014f,z=(float)Math.sin(a+1.2f)*.014f;
                s.quad(p,q,v(q[0]+x,.181f,q[2]+z),
                       v(p[0]+x,.182f,p[2]+z),.19f,.22f,.22f);
            }
        }
        return s.done();
    }
    /** Carved funeral headstone: pointed arc, bonded courses, inner recess, chips. */
    public static ArtKit.Model cenotaph(){
        Sculpt s=new Sculpt();
        s.box(0,.13f,0,1.15f,.26f,.78f,.32f,.34f,.34f);
        s.box(0,.42f,0,.85f,.48f,.45f,.38f,.40f,.42f);
        s.box(0,1.18f,0,.71f,1.23f,.36f,.46f,.48f,.46f);
        for(int side=-1;side<=1;side+=2){
            s.rod(side*.29f,1.50f,0,side*.09f,2.10f,0,.09f,.028f,8,.51f,.54f,.51f);
            s.box(side*.38f,.96f,0,.12f,1.55f,.49f,.30f,.34f,.35f);
        }
        s.rod(0,1.62f,0,0,2.22f,0,.30f,.015f,10,.45f,.47f,.44f);
        s.box(0,1.15f,.211f,.36f,.56f,.035f,.17f,.23f,.24f);
        s.box(0,1.14f,.244f,.065f,.47f,.041f,.54f,.51f,.35f);
        s.box(0,1.14f,.259f,.26f,.06f,.040f,.54f,.51f,.35f);
        for(int k=0;k<6;k++){
            float x=(k%3-1)*.25f,z=.18f+(k%2)*.024f;
            s.rod(x,.28f+(k/3)*.22f,z,x+.09f,.21f+(k/3)*.23f,z+.02f,
                  .010f,.005f,4,.17f,.24f,.22f);
        }
        return s.done();
    }
    /** Iron reliquary: legible negative space and bent, tapered blacksmith work. */
    public static ArtKit.Model reliquary(){
        Sculpt s=new Sculpt();
        s.box(0,.18f,0,1.23f,.32f,1.10f,.26f,.28f,.29f);
        s.box(0,2.25f,0,1.27f,.24f,1.08f,.39f,.38f,.32f);
        for(int side=-1;side<=1;side+=2){
            for(int front=-1;front<=1;front+=2){
                s.rod(side*.48f,.28f,front*.43f,side*.46f,2.23f,front*.43f,
                      .105f,.089f,9,.33f,.35f,.36f);
                s.rod(0,1.08f,front*.37f,side*.46f,1.75f,front*.37f,
                      .046f,.028f,7,.44f,.42f,.34f);
            }
            s.rod(side*.45f,1.25f,-.42f,side*.45f,1.25f,.42f,
                .055f,.055f,7,.39f,.38f,.33f);
        }
        for(int k=0;k<9;k++){
            float a=(float)(2*PI*k/9);
            float x=(float)Math.sin(a)*.41f,z=(float)Math.cos(a)*.38f;
            s.rod(x,2.30f,z,x*.84f,2.75f,z*.84f,.055f,.006f,6,.49f,.42f,.32f);
        }
        s.rod(0,.42f,0,0,2.13f,0,.14f,.13f,10,.52f,.38f,.28f);
        return s.done();
    }
    /** Gnarled root fan with asymmetrical forks and taper on a shared rock. */
    public static ArtKit.Model rootFan(){
        Sculpt s=new Sculpt();
        for(int k=0;k<8;k++){
            float a=(float)(2*PI*k/8),turn=a+.4f*(grain(k,71)-.5f);
            float len=.75f+grain(k,91)*1.12f;
            float x=(float)Math.cos(turn),z=(float)Math.sin(turn);
            s.rod(0,.37f,0,x*len*.62f,.13f,z*len*.62f,
                  .16f,.08f,8,.23f,.19f,.16f);
            s.rod(x*len*.62f,.13f,z*len*.62f,x*len,-.018f,z*len,
                  .08f,.012f,7,.27f,.22f,.19f);
            s.rod(x*len*.35f,.21f,z*len*.35f,
                  x*len*.75f,.07f,z*len*.75f+.29f,
                  .045f,.006f,6,.30f,.24f,.19f);
        }
        s.rod(0,.01f,0,0,1.30f,.12f,.29f,.155f,12,.25f,.22f,.18f);
        for(int i=0;i<5;i++){
            float a=(float)(PI*.4f+i*2*PI/5f);
            s.rod(0,.90f,.10f,(float)Math.cos(a)*.58f,1.80f,
                  (float)Math.sin(a)*.5f,.10f,.014f,8,.28f,.23f,.19f);
        }
        return s.done();
    }
}
