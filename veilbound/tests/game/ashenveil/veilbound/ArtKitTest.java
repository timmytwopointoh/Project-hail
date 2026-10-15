package game.ashenveil.veilbound;

/**
 * Native-asset preflight. Runs on GitHub before Gradle/Android emulator.
 * The art kit has no Android imports so geometry can be checked with javac.
 */
public final class ArtKitTest {
    static void check(boolean yes,String reason){if(!yes)throw new AssertionError(reason);}
    private static int validate(String name,ArtKit.Model model,float minHeight){
        check(model.triangleCount>=25,name+" must not be a placeholder cube");
        check(model.triangleCount<=1800,name+" exceeds mobile mesh triangle budget");
        float minY=Float.MAX_VALUE,maxY=-Float.MAX_VALUE;
        float minX=Float.MAX_VALUE,maxX=-Float.MAX_VALUE;
        for(int i=0;i<model.vertices.length;i+=9){
            float x=model.vertices[i],y=model.vertices[i+1];
            minX=Math.min(minX,x);maxX=Math.max(maxX,x);
            minY=Math.min(minY,y);maxY=Math.max(maxY,y);
            float nx=model.vertices[i+3],ny=model.vertices[i+4],nz=model.vertices[i+5];
            float len=nx*nx+ny*ny+nz*nz;
            check(len>.90f&&len<1.10f,name+" has invalid surface normal");
            for(int j=6;j<9;j++){
                float c=model.vertices[i+j];
                check(c>=0&&c<=1.4,name+" has invalid vertex color");
            }
        }
        check(maxY-minY>minHeight,name+" silhouette is too short");
        check(maxX-minX>.3f,name+" silhouette is too narrow");
        System.out.println("ARTKIT_OK "+name+" triangles="+model.triangleCount+
            " height="+(maxY-minY)+" width="+(maxX-minX));
        return model.triangleCount;
    }
    public static void main(String[] args){
        int total=0;
        total+=validate("Bellwarden",ArtKit.bellwarden(),2.4f);
        total+=validate("Hushed",ArtKit.hushed(),2.1f);
        total+=validate("Ash Knight",ArtKit.ashKnight(),3.5f);
        total+=validate("Sword",ArtKit.sword(),2f);
        total+=validate("Greatsword",ArtKit.greatsword(),2.8f);
        total+=validate("Lantern",ArtKit.lantern(),1.0f);
        check(total<6500,"Scene actor mesh budgets exceeded");
        check(ArtKit.ashKnight().triangleCount>ArtKit.hushed().triangleCount,
            "Boss should have more sculpted detail than minion");
        System.out.println("VEILBOUND_ART_PIPELINE_PASS "+total+" base triangles");
    }
}
