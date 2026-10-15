package game.ashenveil.veilbound;

import java.io.IOException;
import java.io.StringReader;

/** Portable importer tests; run without Android or an emulator. */
public final class ObjMeshLoaderTest {
    static void check(boolean c,String why){if(!c)throw new AssertionError(why);}
    public static void main(String[] args)throws Exception{
        String quad=
            "# A hand-authored OBJ quad, vertex colors and per-corner normals\n"+
            "v 0 0 0 1 .5 .2\n"+
            "v 2 0 0 .3 .7 1\n"+
            "v 2 1 0 .5 .6 .7\n"+
            "v 0 1 0 1 .8 .3\n"+
            "vn 0 0 1\n"+
            "f -4//1 -3//1 -2//1 -1//1\n";
        ArtKit.Model m=ObjMeshLoader.load(new StringReader(quad));
        check(m.triangleCount==2,"Quad should triangulate to 2 faces");
        check(m.vertices.length==54,"Interleaved asset stride must be 9 floats");
        float loX=100,hiX=-100,loY=100,hiY=-100;
        for(int i=0;i<m.vertices.length;i+=9){
            loX=Math.min(loX,m.vertices[i]);hiX=Math.max(hiX,m.vertices[i]);
            loY=Math.min(loY,m.vertices[i+1]);hiY=Math.max(hiY,m.vertices[i+1]);
            check(Math.abs(m.vertices[i+5]-1f)<.01f,"Imported normal must remain normalized");
            check(m.vertices[i+6]>=0&&m.vertices[i+6]<=1.4f,"Vertex RGB must remain valid");
        }
        check(Math.abs((hiX-loX)-3.3f)<.01f,"OBJ should be scaled to 3.3-world-unit range");
        check(Math.abs(loY)<.001f,"Imported mesh must stand on ground plane");
        String multi="v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\nv -1 .5 0\nf 1 2 3 4 5\n";
        check(ObjMeshLoader.load(new StringReader(multi)).triangleCount==3,
              "N-gons must triangulate as a fan");
        try{
            ObjMeshLoader.load(new StringReader("v 0 0 0\nf 9 8 7\n"));
            throw new AssertionError("Invalid OBJ indices must not be accepted");
        }catch(IOException expected){}
        System.out.println("VEILBOUND_OBJ_IMPORT_PASS streamed triangulation, colors, normals, negative indices, scale and validation");
    }
}
