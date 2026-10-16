package game.ashenveil.veilbound;

import java.awt.image.BufferedImage;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.io.BufferedWriter;
import javax.imageio.ImageIO;
import java.util.Locale;

/**
 * Six isolated production engine modes, one per VEILBOUND manager team.
 * Native Java mesh kernel is shared; process files and resource budgets are
 * fully separate per GitHub runner. Does not execute AI-authored commands.
 *
 * This production CLI runs on desktop JDK only, NOT in Android's APK.
 */
public final class TeamEngineCLI {
    private TeamEngineCLI(){}
    private static String n(float f){return String.format(Locale.US,"%.5f",f);}
    private static void obj(ArtKit.Model mesh,Path file) throws Exception{
        if(mesh.triangleCount>250000)throw new IllegalArgumentException("Mesh triangle budget");
        try(BufferedWriter out=Files.newBufferedWriter(file,StandardCharsets.UTF_8)){
            out.write("# VEILBOUND original shaped geometry\n");
            float[] v=mesh.vertices;
            for(int i=0;i<v.length;i+=9)
                out.write("v "+n(v[i])+" "+n(v[i+1])+" "+n(v[i+2])+" "+
                    n(v[i+6])+" "+n(v[i+7])+" "+n(v[i+8])+"\n");
            for(int i=0;i<v.length;i+=9)
                out.write("vn "+n(v[i+3])+" "+n(v[i+4])+" "+n(v[i+5])+"\n");
            for(int k=0;k<mesh.triangleCount;k++){
                int a=k*3+1;out.write("f "+a+"//"+a+" "+(a+1)+"//"+
                                (a+1)+" "+(a+2)+"//"+(a+2)+"\n");
            }
        }
    }
    private static void png(byte[] bytes,Path file) throws Exception{
        BufferedImage image=new BufferedImage(SurfaceAtlas.SIZE,SurfaceAtlas.SIZE,
                                              BufferedImage.TYPE_INT_ARGB);
        for(int y=0;y<SurfaceAtlas.SIZE;y++)for(int x=0;x<SurfaceAtlas.SIZE;x++){
            int i=(y*SurfaceAtlas.SIZE+x)*4;
            int color=((bytes[i+3]&255)<<24)|((bytes[i]&255)<<16)|
                      ((bytes[i+1]&255)<<8)|(bytes[i+2]&255);
            image.setRGB(x,y,color);
        }
        if(!ImageIO.write(image,"png",file.toFile()))
            throw new IllegalStateException("Local PNG encoder unavailable");
    }
    private static void csvAnimation(Path file)throws Exception{
        try(BufferedWriter out=Files.newBufferedWriter(file,StandardCharsets.UTF_8)){
            out.write("frame,time,bob,hip_shift,root_pitch,root_yaw,left_leg,right_leg,left_toe,right_toe,helmet_yaw,helmet_pitch,cape_pitch,cape_yaw\n");
            HeroPose.Frame pose=new HeroPose.Frame();
            for(int i=0;i<180;i++){
                float time=i/60f,phase=time*5.4f;
                float attack=(i>=83&&i<121)?CombatMotion.DURATION*(1f-(i-83)/38f):0f;
                HeroPose.sample(pose,time,phase,.82f,.28f,attack,0f,0f);
                out.write(i+","+n(time)+","+n(pose.bob)+","+n(pose.hipShift)+","+
                          n(pose.rootPitch)+","+n(pose.rootYaw)+","+
                          n(pose.leftLegPitch)+","+n(pose.rightLegPitch)+","+
                          n(pose.leftFootLift)+","+n(pose.rightFootLift)+","+
                          n(pose.helmetYaw)+","+n(pose.helmetPitch)+","+
                          n(pose.mantlePitch)+","+n(pose.mantleYaw)+"\n");
            }
        }
    }
    private static void csvCombat(Path file)throws Exception{
        try(BufferedWriter out=Files.newBufferedWriter(file,StandardCharsets.UTF_8)){
            out.write("step,phase,blade_bearing_rad,blade_pitch_deg,active\n");
            for(int i=0;i<=90;i++){
                float phase=i/90f;
                out.write(i+","+n(phase)+","+n(CombatMotion.bladeBearing(phase))+
                          ","+n(CombatMotion.bladePitch(phase))+","+
                          (phase>=CombatMotion.ACTIVE_START&&phase<=CombatMotion.ACTIVE_END?"1":"0")+"\n");
            }
        }
    }
    public static void main(String[] args) throws Exception{
        if(args.length!=2)throw new IllegalArgumentException("Usage: <role> <output folder>");
        String role=args[0];
        if(!role.matches("models|animation|materials|world|combat|studio"))
            throw new IllegalArgumentException("Unknown manager-owned production engine");
        Path dir=Path.of(args[1]).toAbsolutePath().normalize();
        Files.createDirectories(dir);
        long t=System.nanoTime();
        int triangles=0;
        switch(role){
            case "models":
                ArtKit.Model forged=BellwardenAnatomy.build(false);
                obj(forged,dir.resolve("bellwarden_full_anatomy.obj"));
                triangles=forged.triangleCount;
                break;
            case "world":
                ArtKit.Model tomb=EnvironmentKit.cenotaph();
                obj(tomb,dir.resolve("carved_cenotaph.obj"));
                triangles=tomb.triangleCount;
                break;
            case "studio":
                ArtKit.Model studio=CinematicArtKit.bellwardenLite();
                obj(studio,dir.resolve("bellwarden_studio_preview.obj"));
                triangles=studio.triangleCount;
                break;
            case "animation":
                csvAnimation(dir.resolve("hero_pose_180_frames.csv"));
                break;
            case "materials":
                SurfaceAtlas.Pair atlas=SurfaceAtlas.bake();
                png(atlas.albedo,dir.resolve("material_albedo.png"));
                png(atlas.normalRoughness,dir.resolve("material_normal_roughness.png"));
                break;
            default:
                csvCombat(dir.resolve("combat_swing_phases.csv"));
        }
        long ms=(System.nanoTime()-t)/1000000L;
        String report="{\"team\":\""+role+"\",\"engine\":\"isolated-java-production\","+
            "\"status\":\"passed\",\"triangles\":"+triangles+
            ",\"elapsed_ms\":"+ms+",\"requires_review\":true}\n";
        Files.writeString(dir.resolve("engine_report.json"),report);
        System.out.println("VEILBOUND_TEAM_ENGINE_PASS role="+role+
                           " triangles="+triangles+" elapsed_ms="+ms);
    }
}
