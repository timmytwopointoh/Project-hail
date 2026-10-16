package game.ashenveil.veilbound;

import java.util.ArrayList;

/**
 * M23 unarmored hands modeled with the existing ShapeEngine smooth-loft tools.
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
        new ShapeEngine.Palette(.716f,.447f,.337f);
    // Anatomical order from little through index.
    public static final float[] TIPS={.629f,.595f,.578f,.608f};
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
            float t=(float)Math.pow((float)i/(rings-1),1.35);
            float y=tip+(base-tip)*t;
            // Round the fleshy fingertip over roughly 8% of finger length.
            float pad=(float)Math.sin(Math.PI*.5f*Math.min(1f,t/.085f));
            // TIP -> DIP -> PIP -> MCP: taper and shallow knuckle swelling.
            float width=(.018f+.007f*t)
                *(.06f+.94f*pad)
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
            float t=(float)Math.pow((float)i/(rings-1),1.35);
            float y=.731f+(.862f-.731f)*t;
            float tipRound=(float)Math.sin(Math.PI*.5f*Math.min(1f,t/.125f));
            float width=(.026f+.009f*t)*(.055f+.945f*tipRound);
            width*=1f+.08f*bump(t,.43f,.12f);
            // CMC opposition and IP bend visible in 3/4; never a fifth ray.
            float x=center+side*(.183f-.104f*t-.012f*smooth(t));
            float z=.178f-.070f*t+.010f*(float)Math.sin(Math.PI*t);
            rows[i]=new ShapeEngine.Ring(x,y,z,width,width*.93f,0f,.001f);
        }
        return rows;
    }
    /**
     * A shallow nail BED is painted directly onto the distal dorsal surface,
     * not attached as a floating bevel plate. Genuine finger/knuckle shapes
     * remain geometric; nail coloring is subtle vertex material variation.
     */
    private static ArtKit.Model nailBed(ArtKit.Model surface,float cx,
                                        float fromY,float toY,float halfWidth){
        float[] stream=surface.vertices.clone();
        for(int i=0;i<stream.length;i+=9){
            float x=stream[i],y=stream[i+1],front=stream[i+5];
            float u=Math.abs(x-cx)/halfWidth;
            float v=(y-fromY)/(toY-fromY);
            float edge=smooth((1f-u)*3.5f)*
                       smooth(Math.min(v,1f-v)*7.0f);
            float dorsal=smooth((front-.46f)/.35f);
            float mask=edge*dorsal*.65f;
            stream[i+6]=SKIN.r+(NAIL.r-SKIN.r)*mask;
            stream[i+7]=SKIN.g+(NAIL.g-SKIN.g)*mask;
            stream[i+8]=SKIN.b+(NAIL.b-SKIN.b)*mask;
        }
        return new ArtKit.Model(stream);
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
            pair[side<0?1:2]=ShapeEngine.loftSmoothCapped(palm,lite?16:32,SKIN);
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
                int anatomical=side>0?f:3-f;
                float tip=TIPS[anatomical];
                // Nail shape follows the curved geometry; zero extra islands.
                models.add(nailBed(ShapeEngine.loftSmoothCapped(rows,sides,SKIN),
                    rows[0].cx,tip+.014f,tip+.050f,.017f));
            }
            ShapeEngine.Ring[] rows=thumb(side,rings,shoulderSpan);
            models.add(nailBed(ShapeEngine.loftSmoothCapped(rows,sides,SKIN),
                rows[1].cx,.744f,.786f,.024f));
        }
        return ShapeEngine.combine(models.toArray(new ArtKit.Model[0]));
    }
}
