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
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M25 FACE"),
              "Face geometry close-up is not wired into the Atelier");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M26 SCULPT"),
              "M26 learned geometry cannot be inspected in testing grounds");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M28 ORBITAL"),
              "M28 connected facial anatomy reviewer was not registered");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M29 REFERENCE T-POSE"),
              "T-pose reference geometry not inspectable");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M29 REFERENCE 3/4"),
              "Relaxed reference pose geometry not inspectable");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M31 REALISM NEUTRAL"),
              "M31 realistic skin study missing from testing grounds");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M31 RIGGED T-POSE"),
              "M31 corrected T-pose not selectable");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M31 RIGGED RELAXED"),
              "M31 corrected relaxed pose not selectable");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M32 ANATOMY"),
              "M32 whole human skin sculpt missing from game test grounds");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M32 SHOULDER"),
              "M32 accurate shoulder T-pose missing");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M32 RELAXED"),
              "M32 relaxed anatomy reference missing");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M35 MOUTH NEUTRAL"),
              "Actual new anatomical mouth missing in testing grounds");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M35 MOUTH OPEN"),
              "Mouth articulation preview not selectable");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M35 MOUTH T-POSE"),
              "M35 attached mouth and T-pose inspection missing");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M36 FACE NEUTRAL"),
            "M36 neutral skin-scaffold candidate missing");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M36 FACE OPEN"),
            "M36 moving connected face skin not inspectable");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M36 FACE T-POSE"),
            "M36 anatomical T-pose model not inspectable");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M37 FEET AND SHOULDERS"),
            "M37 anatomy candidate not inspectable");
        s.nextItem(1);
        check(ModelStudio.ITEMS[s.snapshot().item].startsWith("M37 NARROW SHOULDER"),
            "M37 matched anatomical T-pose not inspectable");
        s.nextItem(1);
        check(s.snapshot().item==ModelStudio.ITEMS.length-1 &&
              "IMPORTED OBJ".equals(ModelStudio.ITEMS[s.snapshot().item]),
            "Last slot must remain import OBJ");
        System.out.println("VEILBOUND_ENVIRONMENT_STUDIO_PASS four_3d_props");
    }
}
