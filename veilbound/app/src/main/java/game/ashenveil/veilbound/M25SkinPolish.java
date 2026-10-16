package game.ashenveil.veilbound;

/**
 * Low-frequency, bounded flesh-tone variation over actual model vertex colors.
 * The proprietary armor atlas, knight and the original hair/shorts polygons
 * are intentionally left untouched. This is a prototype skin work-over, not
 * a photographically scanned pore texture or a manually unwrapped UV map.
 */
public final class M25SkinPolish {
    private M25SkinPolish(){}
    private static float clamp(float x,float low,float high){
        return Math.max(low,Math.min(high,x));
    }
    private static float smooth(float x){
        x=clamp(x,0f,1f);return x*x*(3f-2f*x);
    }
    /** Pure classification tied to M20's known, separate skin palette. */
    public static boolean isBodySkin(float r,float g,float b){
        return Math.abs(r-.68f)<.081f&&
               Math.abs(g-.425f)<.059f&&
               Math.abs(b-.315f)<.054f;
    }
    public static ArtKit.Model apply(ArtKit.Model source){
        if(source==null)throw new IllegalArgumentException("Human skin source missing");
        float[] v=source.vertices.clone();
        for(int i=0;i<v.length;i+=9){
            float r=v[i+6],g=v[i+7],b=v[i+8];
            if(!isBodySkin(r,g,b))continue;
            float x=v[i],y=v[i+1],z=v[i+2];
            // Broad continuous tonal variation (not random speckle).
            float mottling=(float)(Math.sin(x*11.2f+y*4.3f+z*6.8f)*
                                  Math.sin(x*6.1f-y*7.9f+z*3.4f));
            float variation=1f+.026f*mottling+
                .012f*(float)Math.sin(x*25.2f+y*7.1f+z*9.7f);
            float face=smooth((y-2.26f)/.12f);
            float cheek=(float)Math.exp(-Math.pow((Math.abs(x)-.115f)/.062f,2)
                                          -Math.pow((y-2.49f)/.085f,2));
            float jointTone=smooth((Math.abs(x)-.42f)/.18f)*
                            (1f-smooth((y-1.30f)/.53f))*.014f;
            // Face subtly warmer, cheeks slightly more red, wrists less flat.
            v[i+6]=clamp(r*variation*(1f+.026f*face+.024f*cheek),
                         0f,1f);
            v[i+7]=clamp(g*variation*(1f-.010f*face-.017f*cheek-jointTone),
                         0f,1f);
            v[i+8]=clamp(b*variation*(1f-.018f*face-.014f*cheek),
                         0f,1f);
        }
        return new ArtKit.Model(v);
    }
}
