package game.ashenveil.veilbound;

import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.Polygon;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.io.BufferedWriter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Locale;
import javax.imageio.ImageIO;

/**
 * Independent inspectable geometry variant; never modifies game source.
 * Exports M23 reviewed-candidate composite as OBJ and four real 3D software projections.
 * Camera labels are truthful; images render generated geometry, not AI art.
 */
public final class HumanVariantCLI {
    private static String studyLabel="M25";
    private static final String[] VIEWS={
        "front","side","back","three_quarter",
        "orbit_030","orbit_060","orbit_120","orbit_150","orbit_210",
        "orbit_225","orbit_240","orbit_270","orbit_300","orbit_330"
    };
    private static final int[] AZIMUTH={
        0,90,180,45,30,60,120,150,210,225,240,270,300,330
    };
    private static final class Face {
        final int[] px=new int[3],py=new int[3];
        final double depth;
        final Color color;
        Face(int[] x,int[] y,double d,Color c){
            System.arraycopy(x,0,px,0,3);
            System.arraycopy(y,0,py,0,3);
            depth=d;color=c;
        }
    }
    private static String f(float x){return String.format(Locale.US,"%.6f",x);}
    private static void obj(ArtKit.Model mesh,Path file) throws Exception{
        float[] v=mesh.vertices;
        try(BufferedWriter w=Files.newBufferedWriter(file,StandardCharsets.UTF_8)){
            w.write("# VEILBOUND "+studyLabel+
                    " face/surface whole-body candidate, review pending\n");
            for(int i=0;i<v.length;i+=9)
                w.write("v "+f(v[i])+" "+f(v[i+1])+" "+f(v[i+2])+" "+
                    f(v[i+6])+" "+f(v[i+7])+" "+f(v[i+8])+"\n");
            for(int i=0;i<v.length;i+=9)
                w.write("vn "+f(v[i+3])+" "+f(v[i+4])+" "+f(v[i+5])+"\n");
            for(int i=0;i<v.length;i+=9){
                float[] uv=MaterialMapping.uv(v[i],v[i+1],v[i+2],
                  v[i+3],v[i+4],v[i+5],v[i+6],v[i+7],v[i+8]);
                w.write("vt "+f(uv[0])+" "+f(uv[1])+"\n");
            }
            for(int i=0;i<mesh.triangleCount;i++){
                int a=i*3+1;
                w.write("f "+a+"/"+a+"/"+a+" "+(a+1)+"/"+(a+1)+"/"+(a+1)+
                        " "+(a+2)+"/"+(a+2)+"/"+(a+2)+"\n");
            }
        }
    }
    private static float[] camera(int view){
        double radians=Math.toRadians(AZIMUTH[view]);
        return new float[]{(float)Math.sin(radians),0f,(float)Math.cos(radians)};
    }
    private static void render(ArtKit.Model mesh,int view,Path file) throws Exception{
        int width=640,height=720;
        BufferedImage image=new BufferedImage(width,height,BufferedImage.TYPE_INT_RGB);
        Graphics2D g=image.createGraphics();
        g.setColor(new Color(215,216,218));g.fillRect(0,0,width,height);
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,RenderingHints.VALUE_ANTIALIAS_ON);
        float[] direction=camera(view),v=mesh.vertices;
        // Painter sort by camera depth; intended inspection preview, not a
        // replacement for actual Android screenshots and studio QA.
        ArrayList<Face> faces=new ArrayList<>(mesh.triangleCount);
        for(int i=0;i<v.length;i+=27){
            float nx=(v[i+3]+v[i+12]+v[i+21])/3f,
                  ny=(v[i+4]+v[i+13]+v[i+22])/3f,
                  nz=(v[i+5]+v[i+14]+v[i+23])/3f;
            float toward=nx*direction[0]+nz*direction[2];
            if(toward<-.02f)continue;
            int[] xx=new int[3],yy=new int[3];double depth=0;
            float r=0,gg=0,b=0;
            for(int k=0;k<3;k++){
                int j=i+k*9;
                float horizontal=v[j]*direction[2]-v[j+2]*direction[0];
                xx[k]=Math.round(width*.5f+horizontal*216f);
                yy[k]=Math.round(height-74-v[j+1]*216f);
                depth+=v[j]*direction[0]+v[j+2]*direction[2];
                r+=v[j+6];gg+=v[j+7];b+=v[j+8];
            }
            float light=Math.max(.44f,Math.min(1.14f,
               .72f+.22f*ny+.25f*toward));
            int red=Math.max(0,Math.min(255,Math.round(255f*r*light/3)));
            int green=Math.max(0,Math.min(255,Math.round(255f*gg*light/3)));
            int blue=Math.max(0,Math.min(255,Math.round(255f*b*light/3)));
            faces.add(new Face(xx,yy,depth/3,new Color(red,green,blue)));
        }
        faces.sort(Comparator.comparingDouble(a->a.depth));
        for(Face face:faces){
            g.setColor(face.color);
            g.fillPolygon(new Polygon(face.px,face.py,3));
        }
        g.setColor(new Color(45,50,55));
        g.drawString(VIEWS[view].toUpperCase(Locale.US)+"  |  ACTUAL 3D MESH",14,28);
        g.drawString(studyLabel+" FACE + SKIN - OFFLINE PREVIEW, NOT ANDROID",14,height-21);
        g.dispose();
        ImageIO.write(image,"png",file.toFile());
    }

    /** Cropped software projections of the REAL mesh. Never call these Android captures. */
    private static void renderHand(ArtKit.Model mesh,int view,int side,Path file)
            throws Exception{
        final int width=640,height=720;
        final float[] direction=camera(view);
        final float cx=side*.554f,cz=.115f,cy=1.235f,zoom=1160f;
        final float origin=cx*direction[2]-cz*direction[0];
        BufferedImage image=new BufferedImage(width,height,BufferedImage.TYPE_INT_RGB);
        Graphics2D g=image.createGraphics();
        g.setColor(new Color(215,216,218));
        g.fillRect(0,0,width,height);
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,
                           RenderingHints.VALUE_ANTIALIAS_ON);
        ArrayList<Face> faces=new ArrayList<>();
        float[] v=mesh.vertices;
        for(int i=0;i<v.length;i+=27){
            boolean inHand=true;
            for(int k=0;k<3;k++){
                int j=i+k*9;
                if(v[j+1]<.970f||v[j+1]>1.58f||
                   v[j]*side<.395f||v[j]*side>.795f){
                    inHand=false;break;
                }
            }
            if(!inHand)continue;
            float nx=(v[i+3]+v[i+12]+v[i+21])/3f;
            float ny=(v[i+4]+v[i+13]+v[i+22])/3f;
            float nz=(v[i+5]+v[i+14]+v[i+23])/3f;
            float toward=nx*direction[0]+nz*direction[2];
            if(toward<-.02f)continue;
            int[] xx=new int[3],yy=new int[3];
            double depth=0;
            float red=0,green=0,blue=0;
            for(int k=0;k<3;k++){
                int j=i+k*9;
                float horizontal=v[j]*direction[2]-v[j+2]*direction[0];
                xx[k]=Math.round(width*.5f+(horizontal-origin)*zoom);
                yy[k]=Math.round(height*.5f-(v[j+1]-cy)*zoom);
                depth+=v[j]*direction[0]+v[j+2]*direction[2];
                red+=v[j+6];green+=v[j+7];blue+=v[j+8];
            }
            float light=Math.max(.44f,Math.min(1.14f,
                .72f+.22f*ny+.25f*toward));
            faces.add(new Face(xx,yy,depth/3,
                new Color(Math.max(0,Math.min(255,Math.round(255f*red*light/3))),
                          Math.max(0,Math.min(255,Math.round(255f*green*light/3))),
                          Math.max(0,Math.min(255,Math.round(255f*blue*light/3))))));
        }
        faces.sort(Comparator.comparingDouble(a->a.depth));
        for(Face face:faces){
            g.setColor(face.color);
            g.fillPolygon(new Polygon(face.px,face.py,3));
        }
        g.setColor(new Color(45,50,55));
        g.drawString((side<0?"LEFT":"RIGHT")+" HAND / "+
                     VIEWS[view].toUpperCase(Locale.US),14,28);
        g.drawString("REAL MESH - OFFLINE CROPPED PROJECTION, NOT ANDROID",
                     14,height-21);
        g.dispose();
        ImageIO.write(image,"png",file.toFile());
    }

    /** Review-only head close-up of the M25 actual triangle stream. */
    private static void renderFace(ArtKit.Model mesh,int view,Path file)
            throws Exception{
        int width=640,height=720;
        BufferedImage image=new BufferedImage(width,height,BufferedImage.TYPE_INT_RGB);
        Graphics2D g=image.createGraphics();
        g.setColor(new Color(215,216,218));g.fillRect(0,0,width,height);
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,RenderingHints.VALUE_ANTIALIAS_ON);
        float[] direction=camera(view),v=mesh.vertices;
        float cy=M24BodyRetarget.y(0f,2.435f);
        float depthCenter=.015f;
        float origin=-depthCenter*direction[0];
        float zoom=1070f;
        ArrayList<Face> faces=new ArrayList<>();
        for(int i=0;i<v.length;i+=27){
            boolean inFace=true;
            for(int k=0;k<3;k++){
                int j=i+k*9;
                if(v[j+1]<2.30f||v[j+1]>2.81f||Math.abs(v[j])>.32f){
                    inFace=false;break;
                }
            }
            if(!inFace)continue;
            float nx=(v[i+3]+v[i+12]+v[i+21])/3f;
            float ny=(v[i+4]+v[i+13]+v[i+22])/3f;
            float nz=(v[i+5]+v[i+14]+v[i+23])/3f;
            float facing=nx*direction[0]+nz*direction[2];
            if(facing<-.02f)continue;
            int[] xx=new int[3],yy=new int[3];
            double depth=0;float red=0,green=0,blue=0;
            for(int k=0;k<3;k++){
                int j=i+k*9;
                float horizontal=v[j]*direction[2]-v[j+2]*direction[0];
                xx[k]=Math.round(width*.5f+(horizontal-origin)*zoom);
                yy[k]=Math.round(height*.53f-(v[j+1]-cy)*zoom);
                depth+=v[j]*direction[0]+v[j+2]*direction[2];
                red+=v[j+6];green+=v[j+7];blue+=v[j+8];
            }
            float light=Math.max(.48f,Math.min(1.13f,
                        .79f+.20f*ny+.22f*facing));
            faces.add(new Face(xx,yy,depth/3,new Color(
                Math.max(0,Math.min(255,Math.round(red/3f*light*255))),
                Math.max(0,Math.min(255,Math.round(green/3f*light*255))),
                Math.max(0,Math.min(255,Math.round(blue/3f*light*255))))));
        }
        faces.sort(Comparator.comparingDouble(face->face.depth));
        for(Face face:faces){g.setColor(face.color);
                             g.fillPolygon(new Polygon(face.px,face.py,3));}
        g.setColor(new Color(45,50,55));
        g.drawString(studyLabel+" FACE "+VIEWS[view].toUpperCase(Locale.US)+
                     " | REAL 3D MESH",14,28);
        g.drawString("OFFLINE CAMERA PROJECTION; NOT AN ANDROID SCREENSHOT",
                     14,height-21);
        g.dispose();
        ImageIO.write(image,"png",file.toFile());
    }
    public static void main(String[] args) throws Exception{
        if(args.length<2||args.length>4)
            throw new IllegalArgumentException(
                "args: <12 proportion controls> <output-folder> [8 sculpt dials] [--mesh-only]");
        boolean meshOnly="--mesh-only".equals(args[args.length-1]);
        boolean hasDials=args.length>=3&&!"--mesh-only".equals(args[2]);
        if(args.length==4&&(!hasDials||!meshOnly))
            throw new IllegalArgumentException("Unexpected M26 CLI options");
        float[] dials=hasDials?M26SculptDials.parse(args[2]):null;
        studyLabel=hasDials?"M26":"M25";
        String[] values=args[0].split(",");
        float[] p=new float[values.length];
        for(int i=0;i<values.length;i++)p[i]=Float.parseFloat(values[i]);
        ContinuousHuman.validate(p);
        Path dir=Path.of(args[1]);Files.createDirectories(dir);
        ArtKit.Model mesh=hasDials?
            HumanAnatomy.buildM26Candidate(false,p,dials):
            HumanAnatomy.buildM25Candidate(false,p);
        obj(mesh,dir.resolve("human_candidate.obj"));
        obj(HumanHandSculpt.buildStandalone(false,p[0]),dir.resolve("m23_sculpted_hands.obj"));
        if(!meshOnly){
            for(int view=0;view<VIEWS.length;view++)
                render(mesh,view,dir.resolve(VIEWS[view]+".png"));
            for(int side:new int[]{-1,1})
                for(int view:new int[]{0,1,3})
                    renderHand(mesh,view,side,dir.resolve(
                        (side<0?"left":"right")+"_hand_"+VIEWS[view]+".png"));
            for(int view:new int[]{0,1,3})
                renderFace(mesh,view,dir.resolve("face_"+VIEWS[view]+".png"));
        }
        StringBuilder views=new StringBuilder();
        for(String view:VIEWS){
            if(views.length()>0)views.append(',');
            views.append('"').append(view).append('"');
        }
        String json="{\"model\":\""+
            (hasDials?"m26_review_conditioned_sculpt_candidate":
                      "m25_refined_face_skin_candidate")+
            "\",\"triangles\":"+mesh.triangleCount+
            ",\"reviewed\":false,\"photo_realistic\":false,"+
            "\"offline_preview\":"+(!meshOnly)+
            ",\"sculpt_dials\":"+(hasDials?8:0)+
            ",\"hand_closeups_per_side\":"+(meshOnly?0:3)+
            ",\"camera_views\":["+(meshOnly?"":views.toString())+"]}";
        Files.writeString(dir.resolve("mesh_evidence.json"),json+"\n");
        System.out.println("VEILBOUND_HUMAN_VARIANT_PASS triangles="+mesh.triangleCount+
            " offline_camera_views="+VIEWS.length);
    }
}
