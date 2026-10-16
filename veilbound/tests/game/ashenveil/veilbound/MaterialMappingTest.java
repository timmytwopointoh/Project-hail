package game.ashenveil.veilbound;

/** Verify stable original atlas coords can accompany production OBJ exports. */
public final class MaterialMappingTest {
    private static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    public static void main(String[] args){
        check(MaterialMapping.tile(.42f,.50f,.58f)==SurfaceAtlas.STEEL,
            "Forged steel not mapped to steel cell");
        check(MaterialMapping.tile(.20f,.19f,.27f)==SurfaceAtlas.CLOTH,
            "Mantle must have rough cloth texture, not metal");
        check(MaterialMapping.tile(.31f,.26f,.20f)==SurfaceAtlas.LEATHER,
            "Leather underarmor material classification wrong");
        for(ArtKit.Model mesh:new ArtKit.Model[]{
                BellwardenAnatomy.build(false),
                BellwardenAnatomy.build(true)}){
            float[] v=mesh.vertices;
            for(int i=0;i<v.length;i+=9){
                float[] uv=MaterialMapping.uv(v[i],v[i+1],v[i+2],
                    v[i+3],v[i+4],v[i+5],v[i+6],v[i+7],v[i+8]);
                check(uv[0]>=0f&&uv[0]<1f&&
                      uv[1]>=0f&&uv[1]<1f,
                      "Atlas UV outside the original texture");
                float[] identical=MaterialMapping.uv(v[i],v[i+1],v[i+2],
                    v[i+3],v[i+4],v[i+5],v[i+6],v[i+7],v[i+8]);
                check(uv[0]==identical[0]&&uv[1]==identical[1],
                    "Non-deterministic UV assignment");
            }
        }
        System.out.println("VEILBOUND_M16_MATERIAL_MAPPING_PASS steel_cloth_leather object_local");
    }
}
