package game.ashenveil.veilbound;

import java.awt.Color;
import java.awt.Font;
import java.awt.Graphics2D;
import java.awt.Polygon;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Locale;
import javax.imageio.ImageIO;

/**
 * VEILFORGE M1 standalone preview and source exporter.
 * Reuses VEILBOUND's actual M22 ContinuousHuman mesh, NOT a screenshot or an AI
 * generated replacement. 14 independent 3D projections. A fast CPU diagnostic
 * preview is NOT a physically-based render and is NOT an Android screenshot.
 */
public final class ForgeHumanCLI {
    private ForgeHumanCLI(){}
    private static final int W=720,H=780;
    private static final int VIEWS=14;
    private static class Triangle {
        int[] x=new int[3], y=new int[3];
        double depth;
        Color color;
    }
    private static String n(float f){return String.format(Locale.US,"%.6f",f);}
    private static float[] params(String[] args){
        if(args.length==1)return ContinuousHuman.BASE.clone();
        String[] values=args[1].split(",");
        if(values.length!=ContinuousHuman.CONTROLS)
            throw new IllegalArgumentException("Expected twelve comma-separated proportions");
        float[] p=new float[values.length];
        for(int i=0;i<p.length;i++)p[i]=Float.parseFloat(values[i]);
        ContinuousHuman.validate(p);
        return p;
    }
    private static void writeObj(ArtKit.Model mesh,Path out) throws Exception{
        float[] v=mesh.vertices;
        try(BufferedWriter w=Files.newBufferedWriter(out,StandardCharsets.UTF_8)){
            w.write("# VEILFORGE source, real original VEILBOUND M22 ContinuousHuman\n");
            w.write("# Non-indexed per-corner export; weld and retopologize before game promotion\n");
            for(int i=0;i<v.length;i+=9)
                w.write("v "+n(v[i])+" "+n(v[i+1])+" "+n(v[i+2])+" "+
                    n(v[i+6])+" "+n(v[i+7])+" "+n(v[i+8])+"\n");
            for(int i=0;i<v.length;i+=9)
                w.write("vn "+n(v[i+3])+" "+n(v[i+4])+" "+n(v[i+5])+"\n");
            for(int i=0;i<v.length;i+=9){
                float[] uv=MaterialMapping.uv(v[i],v[i+1],v[i+2],
                    v[i+3],v[i+4],v[i+5],v[i+6],v[i+7],v[i+8]);
                w.write("vt "+n(uv[0])+" "+n(uv[1])+"\n");
            }
            for(int i=0;i<mesh.triangleCount;i++){
                int v0=i*3+1;
                w.write("f "+v0+"/"+v0+"/"+v0+" "+
                    (v0+1)+"/"+(v0+1)+"/"+(v0+1)+" "+
                    (v0+2)+"/"+(v0+2)+"/"+(v0+2)+"\n");
            }
        }
    }
    private static int clamp(int v){return Math.max(0,Math.min(255,v));}
    private static BufferedImage render(ArtKit.Model mesh,int index) {
        double yaw=Math.toRadians(index<12?index*30:(index==12?45:225));
        double pitch=Math.toRadians(index<12?0:(index==12?40:-35));
        double sy=Math.sin(yaw),cy=Math.cos(yaw),sp=Math.sin(pitch),cp=Math.cos(pitch);
        // camera, orthonormal right and up (Y is the character's up axis).
        double[] camera={sy*cp,sp,cy*cp};
        double[] right={cy,0,-sy};
        double[] up={-sy*sp,cp,-cy*sp};
        BufferedImage img=new BufferedImage(W,H,BufferedImage.TYPE_INT_RGB);
        Graphics2D g=img.createGraphics();
        g.setColor(new Color(25,29,36));g.fillRect(0,0,W,H);
        g.setColor(new Color(47,53,62));
        for(int x=0;x<W;x+=60)g.drawLine(x,0,x,H);
        for(int y=0;y<H;y+=60)g.drawLine(0,y,W,y);
        ArrayList<Triangle> faces=new ArrayList<>(mesh.triangleCount);
        float[] v=mesh.vertices;
        for(int i=0;i<v.length;i+=27){
            double nx=0,ny=0,nz=0,red=0,green=0,blue=0;
            for(int k=0;k<3;k++){
                int j=i+k*9;
                nx+=v[j+3];ny+=v[j+4];nz+=v[j+5];
                red+=v[j+6];green+=v[j+7];blue+=v[j+8];
            }
            nx/=3;ny/=3;nz/=3;
            double toward=nx*camera[0]+ny*camera[1]+nz*camera[2];
            if(toward<-.02)continue;
            Triangle t=new Triangle();
            for(int k=0;k<3;k++){
                int j=i+k*9;
                double x=v[j],y=v[j+1]-1.36,z=v[j+2];
                t.x[k]=(int)Math.round(W*.5+205*(x*right[0]+z*right[2]));
                t.y[k]=(int)Math.round(H*.5-205*(x*up[0]+y*up[1]+z*up[2]));
                t.depth+=(x*camera[0]+y*camera[1]+z*camera[2])/3;
            }
            // Two diffuse inspection lights, no unearned PBR/photorealism claim.
            double key=Math.max(0,nx*.36+ny*.70+nz*.61);
            double fill=Math.max(0,-nx*.63+ny*.38-nz*.68);
            double light=Math.min(1.16,.30+.65*key+.26*fill+.22*Math.max(0,toward));
            t.color=new Color(clamp((int)(red/3*255*light)),
                clamp((int)(green/3*255*light)),clamp((int)(blue/3*255*light)));
            faces.add(t);
        }
        faces.sort(Comparator.comparingDouble(t->t.depth));
        for(Triangle t:faces){
            g.setColor(t.color);
            g.fillPolygon(new Polygon(t.x,t.y,3));
        }
        g.setColor(new Color(221,227,232));
        g.setFont(new Font("SansSerif",Font.BOLD,17));
        g.drawString(String.format(Locale.US,"VEILFORGE  |  ANGLE %02d / 14",index+1),22,34);
        g.setFont(new Font("SansSerif",Font.PLAIN,14));
        g.drawString(String.format(Locale.US,"Yaw %.0f\u00b0  Elevation %.0f\u00b0  |  SOURCE M22",Math.toDegrees(yaw),Math.toDegrees(pitch)),22,58);
        g.drawString("REAL 3D MESH | SOFTWARE INSPECTION | NOT PHOTOREAL",22,H-23);
        g.dispose();
        return img;
    }
    public static void main(String[] args)throws Exception{
        if(args.length<1||args.length>2)
            throw new IllegalArgumentException("Usage: <output directory> [12 comma-separated proportions]");
        float[] controls=params(args);
        Path dir=Path.of(args[0]).toAbsolutePath().normalize();
        Files.createDirectories(dir);
        ArtKit.Model human=ContinuousHuman.build(true,controls);
        writeObj(human,dir.resolve("human_source.obj"));
        BufferedImage sheet=new BufferedImage(4*260,4*305,BufferedImage.TYPE_INT_RGB);
        Graphics2D composite=sheet.createGraphics();
        composite.setColor(new Color(18,22,27));composite.fillRect(0,0,sheet.getWidth(),sheet.getHeight());
        composite.setRenderingHint(RenderingHints.KEY_INTERPOLATION,RenderingHints.VALUE_INTERPOLATION_BILINEAR);
        for(int index=0;index<VIEWS;index++){
            BufferedImage view=render(human,index);
            String name=String.format(Locale.US,"turntable_%02d.png",index);
            ImageIO.write(view,"png",dir.resolve(name).toFile());
            composite.drawImage(view,(index%4)*260,(index/4)*305,260,305,null);
        }
        composite.dispose();
        ImageIO.write(sheet,"png",dir.resolve("contact_sheet.png").toFile());
        Files.writeString(dir.resolve("forge_human.json"),
            "{\"engine\":\"VEILFORGE M1\",\"source\":\"ContinuousHuman M22\","+
            "\"triangles\":"+human.triangleCount+",\"angles\":14,"+
            "\"source_type\":\"original_real_3d_mesh\","+
            "\"software_preview_not_pbr\":true,\"photorealism_verified\":false,"+
            "\"ready_for_game\":false,\"review_required\":true}\n",StandardCharsets.UTF_8);
        System.out.println("VEILFORGE_HUMAN_PASS triangles="+human.triangleCount+
            " real_mesh_views=14 source_obj=true");
    }
}
