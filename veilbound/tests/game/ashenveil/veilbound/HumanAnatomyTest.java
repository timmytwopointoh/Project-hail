package game.ashenveil.veilbound;
/** Human-only base must be real 3D, without repurposed armor art. */
public final class HumanAnatomyTest {
    private static void yes(boolean x,String m){if(!x)throw new AssertionError(m);}
    public static void main(String[] args){
        ArtKit.Model a=HumanAnatomy.build(false),b=HumanAnatomy.build(true);
        yes(a.triangleCount>2000,"Human model missing body anatomy");
        yes(b.triangleCount>900&&b.triangleCount<a.triangleCount,"Mobile human LOD invalid");
        int skin=0,shorts=0;float lo=99,hi=-99;
        for(int k=0;k<a.vertices.length;k+=9){
            float[] v=a.vertices;float y=v[k+1];
            lo=Math.min(lo,y);hi=Math.max(hi,y);
            float n=(float)Math.sqrt(v[k+3]*v[k+3]+v[k+4]*v[k+4]+v[k+5]*v[k+5]);
            yes(Float.isFinite(n)&&Math.abs(n-1)<.04f,"Invalid skin normals");
            if(v[k+6]>.5f&&v[k+7]>.25f)skin++;
            if(v[k+6]<.26f&&y<1.20f&&y>.85f)shorts++;
        }
        yes(hi-lo>2.55f&&hi-lo<3.0f,"Unrealistic human height");
        yes(skin>2000&&shorts>80,"Missing skin or modest shorts");
        yes(ModelStudio.ITEMS[ModelStudio.ITEMS.length-2].startsWith("HUMAN BASE"),
            "Human is not selectable as distinct Atelier viewer model");
        yes("IMPORTED OBJ".equals(ModelStudio.ITEMS[ModelStudio.ITEMS.length-1]),
            "Existing OBJ import was displaced");
        System.out.println("VEILBOUND_HUMAN_BASE_PASS tris="+a.triangleCount+
                           " mobile="+b.triangleCount+" skin="+skin);
    }
}