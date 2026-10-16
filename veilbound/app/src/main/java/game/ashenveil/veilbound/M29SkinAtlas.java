package game.ashenveil.veilbound;

/**
 * M29 source-defined epidermis micro-detail for the unarmored study mesh.
 * Generates one deterministic, periodic RGBA tile: R/G represent subtle
 * tangent-space height slopes, B roughness, A low-amplitude color variation.
 *
 * The geometry still lacks final facial retopology and authored UV islands,
 * so this is a mobile material experiment, NOT captured human skin or
 * photorealistic texture. Original knight/armor and hair remain untouched.
 */
public final class M29SkinAtlas {
    private M29SkinAtlas(){}
    public static final int SIZE=128;
    public static final int CHANNELS=4;

    private static double wave(double x,double y){
        double n=2*Math.PI/SIZE;
        return .54*Math.sin(n*(11*x+4*y)+.61)*
                    Math.cos(n*(7*y-3*x)-.28)+
               .28*Math.sin(n*(23*x-13*y)+1.22)*
                    Math.sin(n*(19*y+8*x)+.37)+
               .18*Math.cos(n*(37*x+19*y)+.92)*
                    Math.cos(n*(29*y-17*x)-.81);
    }
    private static int byteOf(double v){
        return Math.max(0,Math.min(255,(int)Math.round(v)));
    }
    public static byte[] bake(){
        byte[] bytes=new byte[SIZE*SIZE*CHANNELS];
        for(int y=0;y<SIZE;y++)for(int x=0;x<SIZE;x++){
            // A signed periodic height derivative with a bounded normal slope.
            double h=wave(x,y);
            double dx=(wave(x+1,y)-wave(x-1,y))*.5;
            double dy=(wave(x,y+1)-wave(x,y-1))*.5;
            double magnitude=Math.sqrt(dx*dx+dy*dy+1.0);
            int p=(y*SIZE+x)*CHANNELS;
            bytes[p]=(byte)byteOf(127.5-80*dx/magnitude);
            bytes[p+1]=(byte)byteOf(127.5-80*dy/magnitude);
            // Roughness is realistically high on matte epidermis, with a
            // narrow spatial range rather than glitter or plastic sheen.
            bytes[p+2]=(byte)byteOf(196+13*h);
            bytes[p+3]=(byte)byteOf(127+11*h);
        }
        return bytes;
    }
}
