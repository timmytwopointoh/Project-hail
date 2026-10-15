package game.ashenveil.veilbound;

/**
 * Production-facing procedural texture baker, original deterministic artwork.
 * Two 512x512 RGBA atlases: albedo microstructure and tangent micro-normal /
 * roughness / occlusion. No download or internet connection is required.
 *
 * Material cells (2x2 atlas):
 *   lower-left: carved limestone, upper-left: hammered steel
 *   lower-right: woven ash cloth, upper-right: distressed leather
 *
 * This is a lightweight PBR-inspired surface atlas, NOT authored UV-mapped
 * photogrammetry. A physically based BRDF and UV-authored PBR textures remain
 * separate future art work.
 */
public final class SurfaceAtlas {
    public static final int SIZE=512;
    public static final int TILE=SIZE/2;
    public static final int CHANNELS=4;
    public static final int STONE=0,STEEL=1,CLOTH=2,LEATHER=3;
    public static final class Pair {
        public final byte[] albedo,normalRoughness;
        Pair(byte[] a,byte[] n){albedo=a;normalRoughness=n;}
    }
    private SurfaceAtlas(){}
    private static int hash(int x,int y,int seed){
        int v=x*0x9E3779B9^y*0x85EBCA6B^seed*0xC2B2AE35;
        v^=v>>>16;v*=0x7FEB352D;v^=v>>>15;v*=0x846CA68B;v^=v>>>16;
        return v;
    }
    private static float rand(int x,int y,int seed){
        return ((hash(x,y,seed)>>>8)&0xffffff)/16777215f;
    }
    private static float smooth(float x){return x*x*(3f-2f*x);}
    private static float value(float u,float v,int period,int seed){
        float px=u*period,py=v*period;
        int x=(int)Math.floor(px),y=(int)Math.floor(py);
        float sx=smooth(px-x),sy=smooth(py-y);
        int x0=((x%period)+period)%period,x1=(x0+1)%period;
        int y0=((y%period)+period)%period,y1=(y0+1)%period;
        float aa=rand(x0,y0,seed),bb=rand(x1,y0,seed);
        float cc=rand(x0,y1,seed),dd=rand(x1,y1,seed);
        return (aa+(bb-aa)*sx)*(1-sy)+(cc+(dd-cc)*sx)*sy;
    }
    private static float clamp(float x){return Math.max(0f,Math.min(1f,x));}
    private static int channel(float x){return Math.round(clamp(x)*255);}
    private static void pixel(byte[] b,int i,float r,float g,float bl,float a){
        b[i]=(byte)channel(r);b[i+1]=(byte)channel(g);
        b[i+2]=(byte)channel(bl);b[i+3]=(byte)channel(a);
    }
    private static float height(int type,float u,float v){
        float coarse=value(u,v,7,101+type*7);
        float medium=value(u,v,24,211+type*13);
        float fine=value(u,v,81,317+type*17);
        float h=.48f+(coarse-.5f)*.30f+(medium-.5f)*.21f+(fine-.5f)*.13f;
        switch(type){
            case STONE:{
                float mortarX=(float)Math.abs(Math.sin(u*22.0*Math.PI));
                float mortarY=(float)Math.abs(Math.sin(v*16.0*Math.PI+
                                  Math.floor(u*11f)*1.57f));
                float seam=Math.min(mortarX,mortarY);
                h-=.21f*(1f-smooth(clamp(seam*4f)));
                float fracture=(float)Math.sin((u*6.3+v*8.1+
                               coarse*2.0)*Math.PI*2f);
                h-=.08f*clamp((fracture-.83f)*6f);
                break;
            }
            case STEEL:{
                float striation=(float)Math.sin(v*368.0+u*31.0+
                                coarse*1.8);
                h+=.027f*striation;
                float dent=value(u,v,46,411);
                h+=.065f*(dent-.5f);
                break;
            }
            case CLOTH:{
                float warp=(float)Math.sin(u*TILE*.66f*Math.PI);
                float weft=(float)Math.sin(v*TILE*.77f*Math.PI);
                h+=.055f*warp+.050f*weft+.021f*warp*weft;
                h+=.032f*(fine-.5f);
                break;
            }
            default:{
                float crease=(float)Math.sin((u*14.3f+v*8.1f+
                              coarse*2.4f)*Math.PI);
                h+=.075f*crease+.05f*(medium-.5f);
                float pebble=value(u,v,56,617);
                h+=.044f*(pebble-.5f);
            }
        }
        return clamp(h);
    }
    /**
     * Texture data intentionally not compressed in memory, but Android's
     * packaging compresses the generated code. GPU stores 2 x 1 MiB RGBA.
     */
    public static Pair bake(){
        byte[] albedo=new byte[SIZE*SIZE*CHANNELS];
        byte[] surface=new byte[SIZE*SIZE*CHANNELS];
        for(int y=0;y<SIZE;y++){
            for(int x=0;x<SIZE;x++){
                int type=(x>=TILE?1:0)+(y>=TILE?2:0);
                // Map arrangement: 0=stone,1=steel,2=cloth,3=leather.
                int material=type==0?STONE:type==1?STEEL:type==2?CLOTH:LEATHER;
                float u=((x%TILE)+.5f)/TILE,v=((y%TILE)+.5f)/TILE;
                float h=height(material,u,v);
                float du=height(material,(u+1f/TILE)%1f,v)-
                         height(material,(u-1f/TILE+1f)%1f,v);
                float dv=height(material,u,(v+1f/TILE)%1f)-
                         height(material,u,(v-1f/TILE+1f)%1f);
                float rx=-du*3.1f,ry=-dv*3.1f;
                float norm=(float)Math.sqrt(rx*rx+ry*ry+1);
                float nx=.5f+.5f*rx/norm,ny=.5f+.5f*ry/norm;
                float grain=value(u,v,41,137+material*7);
                float rough,ao,albedoBase;
                if(material==STONE){
                    rough=.80f+.11f*(grain-.5f);
                    albedoBase=.61f+(h-.50f)*.48f;
                }else if(material==STEEL){
                    rough=.23f+.23f*(grain-.5f)+.14f*(1-h);
                    albedoBase=.68f+(h-.5f)*.25f;
                }else if(material==CLOTH){
                    rough=.91f-.07f*grain;
                    albedoBase=.59f+(h-.5f)*.33f;
                }else{
                    rough=.72f+.14f*(grain-.5f);
                    albedoBase=.56f+(h-.5f)*.38f;
                }
                ao=clamp(.65f+.39f*h);
                int offset=(y*SIZE+x)*CHANNELS;
                pixel(surface,offset,nx,ny,rough,ao);
                pixel(albedo,offset,albedoBase,
                      albedoBase*(material==STONE?1.0f:material==STEEL?1.06f:
                                  material==CLOTH?.87f:.79f),
                      albedoBase*(material==STEEL?1.16f:material==STONE?.96f:
                                  material==CLOTH?.91f:.68f),1);
            }
        }
        return new Pair(albedo,surface);
    }
}
