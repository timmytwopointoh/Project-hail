package game.ashenveil.veilbound;

import java.util.ArrayList;

/**
 * M23 unarmored hands modeled with the existing ShapeEngine loft/bevel tools.
 * Local coordinates MATCH ContinuousHuman and its skin palette. Four fingers
 * and one thumb per hand are independent geometric digits, not painted lines.
 *
 * Palm and wrist remain part of ContinuousHuman's implicit mesh. Proximal
 * phalanges extend inside that palm so disconnected fingertip geometry does
 * not float beside the body. These preview meshes are not yet finger-skinned.
 */
public final class HumanHandSculpt {
    private HumanHandSculpt(){}
    private static final ShapeEngine.Palette SKIN=
        new ShapeEngine.Palette(.68f,.425f,.315f);
    private static final ShapeEngine.Palette NAIL=
        new ShapeEngine.Palette(.745f,.475f,.360f);
    // Anatomical order from little through index.
    public static final float[] TIPS={.576f,.517f,.493f,.538f};
    public static final int FINGERS_PER_HAND=4, THUMBS_PER_HAND=1;

    private static float smooth(float x){
        x=Math.max(0f,Math.min(1f,x));
        return x*x*(3f-2f*x);
    }
    private static float bump(float t,float at,float radius){
        float v=(t-at)/radius;
        return (float)Math.exp(-v*v*2.6f);
    }
    private static ShapeEngine.Ring[] finger(int side,int f,int rings,float shoulderSpan){
        // Reverse which finger reaches each x coordinate on the left, so
        // each index finger stays nearest its own opposable thumb.
        int anatomical=side>0?f:3-f;
        float center=side*.554f*shoulderSpan,fx=center+(f-1.5f)*.067f;
        float tip=TIPS[anatomical],base=.832f;
        ShapeEngine.Ring[] rows=new ShapeEngine.Ring[rings];
        for(int i=0;i<rings;i++){
            float t=(float)i/(rings-1);
            float y=tip+(base-tip)*t;
            float pad=smooth(t/.105f);
            // TIP -> DIP -> PIP -> MCP: taper and shallow knuckle swelling.
            float width=(.018f+.007f*t)
                *(.22f+.78f*pad)
                *(1f+.065f*bump(t,.34f,.085f)+.095f*bump(t,.67f,.11f));
            float sideLean=side*.004f*(1f-t);
            float x=fx+sideLean+(f-1.5f)*.0018f*(1f-t);
            float z=.095f+.024f*(1f-t)+.004f*(float)Math.sin(Math.PI*t);
            rows[i]=new ShapeEngine.Ring(x,y,z,width,width*1.09f,0f,.0008f);
        }
        return rows;
    }
    private static ShapeEngine.Ring[] thumb(int side,int rings,float shoulderSpan){
        ShapeEngine.Ring[] rows=new ShapeEngine.Ring[rings];
        float center=side*.554f*shoulderSpan;
        for(int i=0;i<rings;i++){
            float t=(float)i/(rings-1);
            float y=.689f+(.862f-.689f)*t;
            float width=(.026f+.009f*t)*(.18f+.82f*smooth(t/.13f));
            width*=1f+.08f*bump(t,.43f,.12f);
            // CMC opposition and IP bend visible in 3/4; never a fifth ray.
            float x=center+side*(.183f-.104f*t-.012f*smooth(t));
            float z=.178f-.070f*t+.010f*(float)Math.sin(Math.PI*t);
            rows[i]=new ShapeEngine.Ring(x,y,z,width,width*.93f,0f,.001f);
        }
        return rows;
    }
    private static ArtKit.Model nail(float cx,float tip,float z,float width,
                                     boolean thumb,int side){
        float y0=tip+(thumb?.020f:.014f),y1=tip+(thumb?.054f:.050f);
        float w=width*(thumb?1.0f:.89f);
        // Deliberately narrow, rounded-looking low-relief nail bed.
        float[] polygon={
            cx-w*.72f,y0, cx+w*.72f,y0,
            cx+w,y0+.010f, cx+w*.87f,y1-.005f,
            cx,y1, cx-w*.87f,y1-.005f, cx-w,y0+.010f
        };
        return ShapeEngine.bevelPlate(polygon,z,.0007f,.0006f,NAIL,SKIN);
    }
    /**
     * Complete standalone HAND ASSET for the Atelier and OBJ interchange:
     * independent shaped palm/wrist lofts, plus all ten detailed digits.
     * The attached-human variant intentionally uses the existing implicit
     * palms instead, so it does not duplicate visible palm surfaces.
     */
    public static ArtKit.Model buildStandalone(boolean lite,float shoulderSpan){
        if(!Float.isFinite(shoulderSpan)||shoulderSpan<.83f||shoulderSpan>1.17f)
            throw new IllegalArgumentException("Shoulder span out of range");
        ArtKit.Model[] pair=new ArtKit.Model[3];
        pair[0]=build(lite,shoulderSpan);
        for(int side:new int[]{-1,1}){
            float x=side*.554f*shoulderSpan;
            ShapeEngine.Ring[] palm={
                new ShapeEngine.Ring(x,.735f,.080f,.073f,.055f,0,0),
                new ShapeEngine.Ring(x,.755f,.078f,.099f,.070f,0,0),
                new ShapeEngine.Ring(x,.815f,.070f,.108f,.078f,0,0),
                new ShapeEngine.Ring(x,.860f,.062f,.110f,.081f,0,0),
                new ShapeEngine.Ring(x,.907f,.057f,.101f,.077f,0,0),
                new ShapeEngine.Ring(x,.956f,.052f,.090f,.071f,0,0),
                new ShapeEngine.Ring(x,1.025f,.047f,.098f,.079f,0,0)
            };
            pair[side<0?1:2]=ShapeEngine.loft(palm,lite?16:32,SKIN);
        }
        return ShapeEngine.combine(pair);
    }
    public static ArtKit.Model buildStandalone(boolean lite){
        return buildStandalone(lite,1f);
    }
    /** Actual model returned to both Android Atelier and offline OBJ exporter. */
    public static ArtKit.Model build(boolean lite){return build(lite,1f);}
    public static ArtKit.Model build(boolean lite,float shoulderSpan){
        if(!Float.isFinite(shoulderSpan)||shoulderSpan<.83f||shoulderSpan>1.17f)
            throw new IllegalArgumentException("Shoulder span out of supported range");
        int sides=lite?12:24,rings=lite?11:21;
        ArrayList<ArtKit.Model> models=new ArrayList<>(30);
        for(int side:new int[]{-1,1}){
            for(int f=0;f<4;f++){
                ShapeEngine.Ring[] rows=finger(side,f,rings,shoulderSpan);
                models.add(ShapeEngine.loft(rows,sides,SKIN));
                int anatomical=side>0?f:3-f;
                float cx=side*.554f*shoulderSpan+(f-1.5f)*.067f+side*.003f+
                         (f-1.5f)*.00135f;
                // Dorsal nail rests on modeled soft tissue, no floating ivory.
                models.add(nail(cx,TIPS[anatomical],.137f,.016f,false,side));
            }
            ShapeEngine.Ring[] rows=thumb(side,rings,shoulderSpan);
            models.add(ShapeEngine.loft(rows,sides,SKIN));
            models.add(nail(side*(.554f*shoulderSpan+.177f),.689f,.203f,.020f,true,side));
        }
        return ShapeEngine.combine(models.toArray(new ArtKit.Model[0]));
    }
}
