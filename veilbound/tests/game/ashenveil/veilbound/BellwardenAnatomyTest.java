package game.ashenveil.veilbound;

/**
 * M14: validates a complete shaped human silhouette. Fail if a future
 * 'model worker' silently replaces anatomy with a few primitive spheres.
 */
public final class BellwardenAnatomyTest {
    private static void check(boolean condition,String reason){
        if(!condition)throw new AssertionError(reason);
    }
    private static final class Summary{
        float maxX=-999,minX=999,maxY=-999,minY=999,maxZ=-999,minZ=999;
        int faceCount;
    }
    private static Summary inspect(ArtKit.Model model){
        Summary bounds=new Summary();
        for(int i=0;i<model.vertices.length;i+=9){
            float[] v=model.vertices;
            float x=v[i],y=v[i+1],z=v[i+2];
            bounds.maxX=Math.max(bounds.maxX,x);bounds.minX=Math.min(bounds.minX,x);
            bounds.maxY=Math.max(bounds.maxY,y);bounds.minY=Math.min(bounds.minY,y);
            bounds.maxZ=Math.max(bounds.maxZ,z);bounds.minZ=Math.min(bounds.minZ,z);
            float n=(float)Math.sqrt(v[i+3]*v[i+3]+v[i+4]*v[i+4]+v[i+5]*v[i+5]);
            check(Float.isFinite(n)&&Math.abs(n-1f)<.04f,
                  "Non-unit normals in authored anatomical armor");
        }
        bounds.faceCount=model.triangleCount;
        return bounds;
    }
    public static void main(String[] args){
        ArtKit.Model full=BellwardenAnatomy.build(false);
        ArtKit.Model mobile=BellwardenAnatomy.build(true);
        Summary b=inspect(full),low=inspect(mobile);
        check(full.triangleCount>mobile.triangleCount*1.8f,
              "High detail must contain authored higher resolution surfaces");
        check(mobile.triangleCount>3000,
              "Mobile sculpt lost anatomical detail");
        check(full.triangleCount>9000,
              "Full anatomy insufficient for the promised character");
        check(b.maxY-b.minY>2.65f,
              "Missing entire body height");
        check(b.maxX-b.minX>1.68f && b.maxX-b.minX<2.65f,
              "Human body shoulders no longer proportionate");
        check(b.maxZ-b.minZ>.7f,
              "Boots, cape and chest are not fully volumetric");
        check(Math.abs(b.maxY-low.maxY)<.18f&&Math.abs(b.minY-low.minY)<.18f,
              "LOD alters human height");
        CharacterRig.Parts rig=CharacterRig.split(full,false,false);
        CharacterRig.Parts liteRig=CharacterRig.split(mobile,false,false);
        check(rig.vertices()==full.vertices.length/9 &&
              liteRig.vertices()==mobile.vertices.length/9,
              "Articulated mesh lost source triangles");
        check(rig.leftArm.triangleCount>400 && rig.rightArm.triangleCount>400,
              "Forged arms have not been assigned to shoulder joints");
        check(rig.leftLeg.triangleCount>350 && rig.rightLeg.triangleCount>350,
              "Thigh-to-boot armor has not been assigned to legs");
        check(rig.helmet!=null && rig.helmet.triangleCount>350 &&
              liteRig.helmet!=null && liteRig.helmet.triangleCount>120,
              "Independent gothic visor is missing");
        check(rig.mantle!=null && rig.mantle.triangleCount>2000 &&
              liteRig.mantle!=null && liteRig.mantle.triangleCount>100,
              "Draped two-sided mantle no longer animates independently");
        System.out.println("VEILBOUND_M14_ANATOMY_PASS detailed_triangles="+
              full.triangleCount+" mobile_triangles="+mobile.triangleCount+
              " cape_triangles="+rig.mantle.triangleCount+
              " arms="+rig.leftArm.triangleCount+"/"+rig.rightArm.triangleCount+
              " legs="+rig.leftLeg.triangleCount+"/"+rig.rightLeg.triangleCount);
    }
}
