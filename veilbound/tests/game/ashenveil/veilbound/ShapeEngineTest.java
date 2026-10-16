package game.ashenveil.veilbound;

/** Reject circular dummy props, invalid profiles and lost triangle paint. */
public final class ShapeEngineTest {
    private static void check(boolean b,String text){if(!b)throw new AssertionError(text);}
    public static void main(String[] args){
        ShapeEngine.Palette steel=new ShapeEngine.Palette(.4f,.6f,.7f);
        ArtKit.Model profile=ShapeEngine.loft(new ShapeEngine.Ring[]{
            new ShapeEngine.Ring(0,.1f,0,.17f,.21f,0,.03f),
            new ShapeEngine.Ring(.1f,.4f,0,.36f,.19f,.1f,.12f),
            new ShapeEngine.Ring(.04f,.8f,.04f,.20f,.30f,.2f,.015f)
        },20,steel);
        check(profile.triangleCount==80,"Profile ring loft triangle count wrong");
        float largestZ=-999,smallestZ=999;
        for(int i=0;i<profile.vertices.length;i+=9){
            float[] a=profile.vertices;
            float n=(float)Math.sqrt(a[i+3]*a[i+3]+a[i+4]*a[i+4]+a[i+5]*a[i+5]);
            check(Float.isFinite(n)&&Math.abs(n-1)<.02f,"Invalid normals");
            largestZ=Math.max(largestZ,a[i+2]);smallestZ=Math.min(smallestZ,a[i+2]);
        }
        check(largestZ-smallestZ>.45f,"Forged profile lost 3D front-back depth");
        ArtKit.Model beveled=ShapeEngine.bevelPlate(
            new float[]{-.3f,.2f,.3f,.2f,.4f,.5f,0,.72f,-.4f,.5f},
            .28f,.10f,.04f,steel,new ShapeEngine.Palette(.8f,.6f,.3f));
        check(beveled.triangleCount>=15,"Plate must have edges and raised crest");
        ArtKit.Model forged=ShapeEngine.bellwardenForgedPlates(false);
        ArtKit.Model lite=ShapeEngine.bellwardenForgedPlates(true);
        check(forged.triangleCount>450&&forged.triangleCount>lite.triangleCount,
            "Complex forged armor and mobile tessellation budget missing");
        ArtKit.Model complete=CinematicArtKit.bellwarden();
        check(complete.triangleCount>forged.triangleCount+1000,
            "Forged profiles are not assembled into the actual Bellwarden");
        boolean caught=false;
        try{ShapeEngine.loft(new ShapeEngine.Ring[]{
            new ShapeEngine.Ring(0,.2f,0,.2f,.2f,0,0),
            new ShapeEngine.Ring(0,.1f,0,.2f,.2f,0,0)},18,steel);
        }catch(IllegalArgumentException ex){caught=true;}
        check(caught,"Reversed loft must be rejected");
        System.out.println("VEILBOUND_SHAPE_ENGINE_PASS shaped_lofts beveled_plates normal_unit true_geometry");
    }
}