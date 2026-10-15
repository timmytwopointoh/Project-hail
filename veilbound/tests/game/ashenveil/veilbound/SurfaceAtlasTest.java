package game.ashenveil.veilbound;

/** Verify deterministic texture arrays and genuine material distinctions. */
public final class SurfaceAtlasTest {
    private static void check(boolean x,String message){if(!x)throw new AssertionError(message);}
    public static void main(String[] args){
        SurfaceAtlas.Pair a=SurfaceAtlas.bake();
        SurfaceAtlas.Pair b=SurfaceAtlas.bake();
        int expected=SurfaceAtlas.SIZE*SurfaceAtlas.SIZE*4;
        check(a.albedo.length==expected&&a.normalRoughness.length==expected,"RGBA size");
        for(int k=0;k<expected;k+=277){
            check(a.albedo[k]==b.albedo[k],"Baking not deterministic");
            check(a.normalRoughness[k]==b.normalRoughness[k],"Normal atlas not reproducible");
        }
        int[] variability=new int[4];
        int[] minR=new int[]{255,255,255,255},maxR=new int[4];
        for(int material=0;material<4;material++){
            int bx=material%2*SurfaceAtlas.TILE;
            int by=material/2*SurfaceAtlas.TILE;
            for(int y=3;y<SurfaceAtlas.TILE;y+=9){
                for(int x=3;x<SurfaceAtlas.TILE;x+=9){
                    int ix=((by+y)*SurfaceAtlas.SIZE+bx+x)*4;
                    int red=a.albedo[ix]&255;
                    minR[material]=Math.min(minR[material],red);
                    maxR[material]=Math.max(maxR[material],red);
                    int rough=a.normalRoughness[ix+2]&255;
                    check(rough>5&&rough<251,"Bad roughness");
                }
            }
            variability[material]=maxR[material]-minR[material];
            check(variability[material]>9,"Texture lacks detail type="+material);
        }
        int metalIx=(SurfaceAtlas.TILE/2*SurfaceAtlas.SIZE+
                     (SurfaceAtlas.TILE+SurfaceAtlas.TILE/2))*4;
        int fabricIx=((SurfaceAtlas.TILE+SurfaceAtlas.TILE/2)*SurfaceAtlas.SIZE+
                     SurfaceAtlas.TILE/2)*4;
        int metalRough=a.normalRoughness[metalIx+2]&255;
        int fabricRough=a.normalRoughness[fabricIx+2]&255;
        check(fabricRough>metalRough+90,"Steel must be glossier than woven cloth");
        System.out.println("VEILBOUND_SURFACE_ATLAS_PASS size="+expected+
                           " roughness_gap="+(fabricRough-metalRough)+
                           " detail_range="+java.util.Arrays.toString(variability));
    }
}
