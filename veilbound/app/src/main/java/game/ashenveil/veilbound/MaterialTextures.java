package game.ashenveil.veilbound;

/**
 * Small reproducible runtime texture atlas.
 *
 * Tiled stone/soil micro-detail built once, then sampled in the OpenGL shader.
 * This avoids storing expensive high-resolution assets in the APK and keeps the
 * GL draw budget constant while making surfaces more materially distinct.
 * This is a lightweight pre-PBR art solution, not photorealistic scanning.
 */
public final class MaterialTextures {
    public static final int SIZE=128;
    private MaterialTextures(){}

    private static int hash(int x,int y,int seed){
        int a=x*0x5bd1e995 ^ y*0x27d4eb2f ^ seed*0x165667b1;
        a^=a>>>15;a*=0x85ebca6b;a^=a>>>13;a*=0xc2b2ae35;a^=a>>>16;
        return a & 0x7fffffff;
    }
    private static float rand(int x,int y,int period,int seed){
        x=((x%period)+period)%period;
        y=((y%period)+period)%period;
        return hash(x,y,seed)/2147483647f;
    }
    private static float noise(float x,float y,int period,int seed){
        int xx=(int)Math.floor(x), yy=(int)Math.floor(y);
        float tx=x-xx,ty=y-yy;
        tx=tx*tx*(3-2*tx);ty=ty*ty*(3-2*ty);
        float a=rand(xx,yy,period,seed);
        float b=rand(xx+1,yy,period,seed);
        float c=rand(xx,yy+1,period,seed);
        float d=rand(xx+1,yy+1,period,seed);
        float u=a+(b-a)*tx;
        float v=c+(d-c)*tx;
        return u+(v-u)*ty;
    }
    private static float clamp(float v){return Math.max(0,Math.min(1,v));}
    private static int channel(float v){return Math.max(0,Math.min(255,Math.round(v*255)));}
    /** Exact RGBA8888 128 x 128 image, deterministic across all Android GPUs. */
    public static byte[] stoneRgba(){
        byte[] out=new byte[SIZE*SIZE*4];
        final int period=8;
        for(int y=0;y<SIZE;y++){
            for(int x=0;x<SIZE;x++){
                float a=noise(x/32f,y/32f,4,73);
                float b=noise(x/16f,y/16f,8,73);
                float c=noise(x/8f,y/8f,16,73);
                float d=noise(x/4f,y/4f,32,73);
                // Very small tiled Voronoi cracks: edges of nearby grains.
                float px=x/16f,py=y/16f;
                int ix=(int)Math.floor(px),iy=(int)Math.floor(py);
                float best=100,second=100;
                for(int j=-1;j<=1;j++)for(int i=-1;i<=1;i++){
                    int tx=ix+i,ty=iy+j;
                    float fx=tx+.19f+.65f*rand(tx,ty,period,43);
                    float fy=ty+.17f+.67f*rand(tx,ty,period,91);
                    float dx=fx-px,dy=fy-py;
                    float dist=dx*dx+dy*dy;
                    if(dist<best){second=best;best=dist;}
                    else if(dist<second)second=dist;
                }
                float crack=clamp((float)(Math.sqrt(second)-Math.sqrt(best))/.15f);
                float variation=(a-.5f)*.33f+(b-.5f)*.23f+
                                (c-.5f)*.15f+(d-.5f)*.09f;
                float grain=clamp(.63f+variation);
                grain*=.69f+.31f*crack;
                // Mineral grey with slight warmth and dispersed moss.
                float moss=clamp((noise(x/24f,y/24f,6,133)-.58f)*2.8f);
                float rr=grain*.99f-moss*.19f;
                float gg=grain*1.01f+moss*.07f;
                float bb=grain*1.04f-moss*.17f;
                int p=(y*SIZE+x)*4;
                out[p]=(byte)channel(rr);
                out[p+1]=(byte)channel(gg);
                out[p+2]=(byte)channel(bb);
                out[p+3]=(byte)255;
            }
        }
        return out;
    }
}
