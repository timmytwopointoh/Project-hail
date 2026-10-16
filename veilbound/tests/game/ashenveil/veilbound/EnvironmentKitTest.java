package game.ashenveil.veilbound;

/** Repeatable geometry checks for production scene meshes and the studio. */
public final class EnvironmentKitTest {
    private static void check(boolean pass,String message){
        if(!pass)throw new AssertionError(message);
    }
    private static void inspect(String label,ArtKit.Model mesh,int minimumTriangles,float maxHeight){
        check(mesh.triangleCount>=minimumTriangles,label+" lacks sculpted facets");
        float maxY=-1000f,minY=1000f,maxX=-1000f,minX=1000f;
        for(int i=0;i<mesh.vertices.length;i+=9){
            float x=mesh.vertices[i],y=mesh.vertices[i+1];
            float nx=mesh.vertices[i+3],ny=mesh.vertices[i+4],nz=mesh.vertices[i+5];
            maxY=Math.max(y,maxY);minY=Math.min(y,minY);
            maxX=Math.max(x,maxX);minX=Math.min(x,minX);
            float n=nx*nx+ny*ny+nz*nz;
            check(Float.isFinite(n)&&n>.80f&&n<1.20f,label+" bad triangle normal");
            for(int k=6;k<9;k++)
                check(mesh.vertices[i+k]>=0&&mesh.vertices[i+k]<=1.4f,
                    label+" invalid painted material");
        }
        check(maxX-minX>.40f,label+" asset flattened");
        check(maxY-minY>.18f&&maxY<maxHeight,label+" unrealistic scale");
        System.out.println("ENVIRONMENT_ASSET_PASS "+label+" tris="+mesh.triangleCount);
    }
    public static void main(String[] args){
        inspect("CHIPPED_FLAGSTONE",EnvironmentKit.flagstone(),68,.5f);
        inspect("CENOTAPH",EnvironmentKit.cenotaph(),100,3.1f);
        inspect("RELIQUARY",EnvironmentKit.reliquary(),150,3.1f);
        inspect("ROOT_FAN",EnvironmentKit.rootFan(),200,2.8f);
        ModelStudio s=new ModelStudio();
        check(ModelStudio.ITEMS.length>=12,"New world props not registered in atelier");
        for(int i=0;i<7;i++)s.nextItem(1);
        check(s.snapshot().item==7,"Flagstone must appear in the atelier");
        for(int i=7;i<=10;i++){
            check(ModelStudio.ITEMS[s.snapshot().item].length()>4,
                 "Every prop needs a named asset slot");
            s.nextItem(1);
        }
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("HUMAN BASE"),
            "New anatomy study must follow the old world props");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M23 HAND"),
              "Hand sculpt must be inspectable after the full human preview");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M24 DEFORMATION"),
              "VEILFORGE deformation stress asset missing from testing grounds");
        s.nextItem(1);
        check(s.snapshot().item==ModelStudio.ITEMS.length-1 &&
              "IMPORTED OBJ".equals(ModelStudio.ITEMS[s.snapshot().item]),
            "Last slot must remain import OBJ");
        System.out.println("VEILBOUND_ENVIRONMENT_STUDIO_PASS four_3d_props");
    }
}
