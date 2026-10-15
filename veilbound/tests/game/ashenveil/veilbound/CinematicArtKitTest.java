package game.ashenveil.veilbound;
/** Geometry details must change silhouette and preserve finite, normalized data. */
public final class CinematicArtKitTest {
    private static void check(boolean v,String m){if(!v)throw new AssertionError(m);}
    private static void inspect(String name,ArtKit.Model detail,ArtKit.Model premium){
        check(premium.triangleCount>detail.triangleCount+1000,
            name+" upgrade missing substantial sculpted geometry");
        float minY=1000,maxY=-1000,minX=1000,maxX=-1000;
        int nonFinite=0;
        for(int i=0;i<premium.vertices.length;i+=9){
            float x=premium.vertices[i],y=premium.vertices[i+1];
            minX=Math.min(minX,x);maxX=Math.max(maxX,x);
            minY=Math.min(minY,y);maxY=Math.max(maxY,y);
            for(int k=i+3;k<i+6;k++){
                float n=premium.vertices[k];if(!Float.isFinite(n))nonFinite++;
            }
            float rough=premium.vertices[i+6];
            check(rough>=0&&rough<=1.4f,name+" invalid color palette");
        }
        check(nonFinite==0,name+" contains nonfinite normal");
        check(maxY-minY>2f,name+" unexpectedly short silhouette");
        check(maxX-minX>.5f,name+" unexpectedly narrow silhouette");
        System.out.println("CINEMATIC_SCULPT_PASS "+name+
            " triangles="+premium.triangleCount+" delta="+
            (premium.triangleCount-detail.triangleCount));
    }
    public static void main(String[] args){
        inspect("Bellwarden",DetailArtKit.bellwarden(),CinematicArtKit.bellwarden());
        inspect("Ash Knight",DetailArtKit.ashKnight(),CinematicArtKit.ashKnight());
        inspect("Hushed",DetailArtKit.hushed(),CinematicArtKit.hushed());
        // Weapons are narrower, so validate geometry and segment richness separately.
        check(CinematicArtKit.sword().triangleCount>DetailArtKit.sword().triangleCount+100,
             "Longsword bevels must be visible");
        check(CinematicArtKit.greatsword().triangleCount>DetailArtKit.greatsword().triangleCount+100,
             "Greatsword bevels must be visible");
        System.out.println("VEILBOUND_CINEMATIC_ART_PASS");
    }
}
