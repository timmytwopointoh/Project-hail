package game.ashenveil.veilbound;
import java.util.ArrayList;
/** Loader must actually prepare game assets and report completed stages. */
public final class BootAssetsTest {
    private static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
    public static void main(String[] args){
        final ArrayList<Integer> values=new ArrayList<>();
        final ArrayList<String> labels=new ArrayList<>();
        BootAssets a=BootAssets.prepare(new BootAssets.Progress(){
            @Override public void stage(int p,String s){values.add(p);labels.add(s);}
        });
        check(values.size()>=7,"Loading uses too few genuine prep stages");
        for(int i=1;i<values.size();i++)
            check(values.get(i)>values.get(i-1),"Loading progress must be monotonic");
        check(values.get(0)<10&&values.get(values.size()-1)>=80,"Loading split is incorrect");
        check(a.hero.triangleCount>a.heroLite.triangleCount,"High and low LOD confused");
        check(a.heroRig.vertices()==a.hero.vertices.length/9,
            "Pre-rigged playable model lost source triangles");
        check(a.heroRig.helmet!=null&&a.heroRig.mantle!=null,
            "Preloaded helmet or cape joints missing");
        check(a.flagstone.triangleCount>0&&a.cenotaph.triangleCount>0&&
              a.reliquary.triangleCount>0&&a.roots.triangleCount>0,
              "Environment assets must actually be prepared during splash");
        check(a.stoneRgba.length==MaterialTextures.SIZE*MaterialTextures.SIZE*4,
            "Surface micro-detail not baked");
        check(a.atlas.albedo.length==SurfaceAtlas.SIZE*SurfaceAtlas.SIZE*4&&
              a.atlas.normalRoughness.length==a.atlas.albedo.length,
              "PBR-inspired atlases not baked");
        System.out.println("VEILBOUND_BOOT_ASSETS_PASS actual_preload stages="+values.size());
    }
}