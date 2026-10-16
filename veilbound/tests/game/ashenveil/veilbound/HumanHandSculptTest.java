package game.ashenveil.veilbound;

import java.io.StringReader;
import java.util.Locale;

/**
 * M23 asset-gate: real hand surface, left/right digit landmarks, and OBJ
 * interchange using the game's existing importer. Human review is separate.
 */
public final class HumanHandSculptTest {
    private static void check(boolean ok,String msg){if(!ok)throw new AssertionError(msg);}
    private static boolean near(ArtKit.Model mesh,float x,float y,float z,float r){
        float rr=r*r;
        float[] p=mesh.vertices;
        for(int i=0;i<p.length;i+=9){
            float dx=p[i]-x,dy=p[i+1]-y,dz=p[i+2]-z;
            if(dx*dx+dy*dy+dz*dz<rr)return true;
        }
        return false;
    }
    private static String obj(ArtKit.Model model){
        StringBuilder b=new StringBuilder(model.vertices.length*9);
        float[] v=model.vertices;
        for(int i=0;i<v.length;i+=9)
            b.append("v ").append(v[i]).append(' ').append(v[i+1]).append(' ')
                .append(v[i+2]).append(' ').append(v[i+6]).append(' ')
                .append(v[i+7]).append(' ').append(v[i+8]).append('\n');
        for(int i=0;i<v.length/9;i+=3)
            b.append("f ").append(i+1).append(' ').append(i+2).append(' ')
                .append(i+3).append('\n');
        return b.toString();
    }
    public static void main(String[] args)throws Exception{
        ArtKit.Model full=HumanHandSculpt.build(false);
        ArtKit.Model lite=HumanHandSculpt.build(true);
        check(full.triangleCount>8000,"High detail fingers not sculpted");
        check(lite.triangleCount>2000&&lite.triangleCount<full.triangleCount,
              "Hand LOD budget is wrong");
        check(HumanHandSculpt.FINGERS_PER_HAND==4&&
              HumanHandSculpt.THUMBS_PER_HAND==1,"Exactly five digits per hand");
        for(int side:new int[]{-1,1}){
            for(int f=0;f<4;f++){
                int anatomical=side>0?f:3-f;
                float tip=HumanHandSculpt.TIPS[anatomical];
                float x=side*.554f+(f-1.5f)*.067f+side*.004f+
                        (f-1.5f)*.0018f;
                check(near(full,x,tip+.018f,.12f,.035f),
                    "Missing independently sculpted finger "+f+" side "+side);
            }
            check(near(full,side*(.554f+.180f),.710f,.175f,.065f),
                  "Missing angled opposable thumb side "+side);
        }
        for(int i=0;i<full.vertices.length;i+=9){
            float[] p=full.vertices;
            float len=(float)Math.sqrt(p[i+3]*p[i+3]+p[i+4]*p[i+4]+p[i+5]*p[i+5]);
            check(Float.isFinite(len)&&Math.abs(len-1)<.05f,
                  "Non-unit sculpt normal");
        }
        // Export the ACTUAL modeled triangle stream then reimport through
        // the same OBJ loader invoked from the Android file chooser.
        ArtKit.Model imported=ObjMeshLoader.load(new StringReader(obj(lite)));
        check(imported.triangleCount==lite.triangleCount,
              "Sculpted asset did not survive OBJ to Android mesh interchange");
        ArtKit.Model attached=HumanAnatomy.buildWithSculptedHands(true);
        check(attached.triangleCount>lite.triangleCount,
              "Modeled hand assets not integrated into the unarmored human");
        check(HumanAnatomy.build(true).triangleCount!=attached.triangleCount,
              "M20 baseline should remain independently selectable in source");
        System.out.println("VEILBOUND_M23_HAND_SCULPT_PASS ultra="+full.triangleCount+
            " lite="+lite.triangleCount+" obj="+imported.triangleCount+
            " attached="+attached.triangleCount+" ten_distinct_digits");
    }
}
