package game.ashenveil.veilbound;

/** Thorough offline preflight of native inspection-grade high-density meshes. */
public final class DetailArtKitTest {
    private static void check(boolean value,String why){if(!value)throw new AssertionError(why);}
    private static void validate(String name,ArtKit.Model model,int minTriangles){
        check(model.triangleCount>=minTriangles,
              name+" missing sculpted geometric detail: "+model.triangleCount);
        float minX=Float.MAX_VALUE,maxX=-Float.MAX_VALUE;
        float minY=Float.MAX_VALUE,maxY=-Float.MAX_VALUE;
        int verts=model.vertices.length/9;
        for(int i=0;i<model.vertices.length;i+=9){
            float x=model.vertices[i],y=model.vertices[i+1];
            minX=Math.min(x,minX);maxX=Math.max(x,maxX);
            minY=Math.min(y,minY);maxY=Math.max(y,maxY);
            float nx=model.vertices[i+3],ny=model.vertices[i+4],nz=model.vertices[i+5];
            float len=nx*nx+ny*ny+nz*nz;
            check(len>.85f&&len<1.15f,name+" invalid face normal");
            for(int j=6;j<=8;j++)
                check(model.vertices[i+j]>=0&&model.vertices[i+j]<=1.40f,
                    name+" vertex palette value out of bounds");
        }
        check(minY>-10f&&maxY<12f,"Mesh unexpected local-space offset");
        check(maxX-minX>.22f,"Mesh collapsed on X");
        System.out.println("MODEL_ATELIER_MESH_PASS "+name+
            " triangles="+model.triangleCount+" vertices="+verts+
            " width="+(maxX-minX)+" height="+(maxY-minY));
    }
    public static void main(String[] args){
        ArtKit.Model hero=DetailArtKit.bellwarden();
        ArtKit.Model boss=DetailArtKit.ashKnight();
        ArtKit.Model revenant=DetailArtKit.hushed();
        validate("BELLWARDEN",hero,9000);
        validate("ASH_KNIGHT",boss,9000);
        validate("HUSHED",revenant,5000);
        validate("WARDEN_SWORD",DetailArtKit.sword(),500);
        validate("ASH_GREATSWORD",DetailArtKit.greatsword(),650);
        validate("EMBER_LANTERN",DetailArtKit.lantern(),400);
        check(hero.triangleCount>ArtKit.bellwarden().triangleCount*5,
            "Close-up hero did not receive distinct high detail mesh");
        check(boss.triangleCount>ArtKit.ashKnight().triangleCount*5,
            "Close-up boss requires genuinely improved geometric density");
        System.out.println("VEILBOUND_INSPECTION_GRADE_ASSETS_PASS "+
            "no arbitrary APK byte limit; gameplay LOD preserved");
    }
}
