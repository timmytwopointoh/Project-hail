package game.ashenveil.veilbound;

public final class MaterialTexturesTest {
    private static void check(boolean value,String message) {
        if(!value)throw new AssertionError(message);
    }
    public static void main(String[] args) {
        byte[] rgba=MaterialTextures.stoneRgba();
        int size=MaterialTextures.SIZE;
        check(rgba.length==size*size*4,"Correct RGBA texture size");
        long checksum=0;
        int low=255,high=0;
        long edge=0;
        for(int i=0;i<rgba.length;i+=4){
            int r=rgba[i]&255,g=rgba[i+1]&255,b=rgba[i+2]&255;
            int a=rgba[i+3]&255;
            check(a==255,"Opaque stone texture; no depth sorting required");
            check(r>=0&&g>=0&&b>=0,"Colors in valid unsigned-byte range");
            low=Math.min(low,r);high=Math.max(high,r);
            checksum+=(long)(r+g+b)*(i/4+1);
        }
        for(int y=0;y<size;y++) {
            int first=(y*size)*4, last=(y*size+size-1)*4;
            for(int j=0;j<3;j++)
                edge+=Math.abs((rgba[first+j]&255)-(rgba[last+j]&255));
        }
        check(high-low>30,"Stone textures need enough tonal detail");
        check(edge/(size*3)<75,"Texture seam has excessive discontinuity");
        check(checksum>100000L,"Texture must contain actual data");
        System.out.println("VEILBOUND_MATERIAL_QA_PASS dimensions="+size+
            " contrast="+(high-low)+" wrap_error="+(edge/(size*3))+
            " checksum="+checksum);
    }
}
