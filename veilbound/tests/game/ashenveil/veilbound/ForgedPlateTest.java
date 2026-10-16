package game.ashenveil.veilbound;

/**
 * Reject swollen shoulders, faceted pyramid plates and detached fake fingers.
 * Tests the actual M15 modeling kernel without a GL driver.
 */
public final class ForgedPlateTest {
    static void require(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    public static void main(String[] args){
        ShapeEngine.Palette steel=new ShapeEngine.Palette(.56f,.62f,.67f);
        ShapeEngine.Palette edge=new ShapeEngine.Palette(.29f,.39f,.46f);
        ArtKit.Model panel=ShapeEngine.bevelPlate(
            new float[]{-.27f,0,.27f,0,.35f,.19f,0,.38f,-.35f,.19f},
            .34f,.05f,.024f,steel,edge);
        require(panel.triangleCount>=35,"Panel is a cheap triangle-fan pyramid, not a forged bevel");
        int faceVertices=0,flangeVertices=0;
        float top=.34f+.024f+.05f;
        for(int i=0;i<panel.vertices.length;i+=9){
            float[] v=panel.vertices;
            require(Float.isFinite(v[i+3])&&Float.isFinite(v[i+4])&&Float.isFinite(v[i+5]),
                    "Nonfinite forged-surface normal");
            if(Math.abs(v[i+2]-top)<.002f)faceVertices++;
            if(Math.abs(v[i+2]-.34f)<.002f)flangeVertices++;
        }
        require(faceVertices>22,"Forged panel has no broad raised steel surface");
        require(flangeVertices>0,"Forged panel lost physical thickness");
        ArtKit.Model pauldron=ShapeEngine.pauldronShell(new ShapeEngine.Ring[]{
            new ShapeEngine.Ring(.57f,1.67f,-.05f,.20f,.17f,0,.02f),
            new ShapeEngine.Ring(.57f,1.80f,-.06f,.25f,.21f,0,.04f),
            new ShapeEngine.Ring(.57f,1.93f,-.07f,.27f,.23f,0,.05f),
            new ShapeEngine.Ring(.57f,2.09f,-.07f,.13f,.12f,0,.01f)
        },26,steel,edge);
        require(pauldron.triangleCount>220,
                "Open layered shoulder was replaced with dummy primitives");
        float zmin=99f,zmax=-99f;
        for(int i=0;i<pauldron.vertices.length;i+=9){
            zmin=Math.min(zmin,pauldron.vertices[i+2]);
            zmax=Math.max(zmax,pauldron.vertices[i+2]);
        }
        require(zmin>-.10f&&zmax>.16f,
                "Shoulder plate needs genuinely open back and dished front");
        ArtKit.Model hero=BellwardenAnatomy.build(false);
        float maxX=-999,minX=999;int lowerGlove=0;
        for(int i=0;i<hero.vertices.length;i+=9){
            float x=hero.vertices[i],y=hero.vertices[i+1];
            maxX=Math.max(x,maxX);minX=Math.min(x,minX);
            if(Math.abs(x)>.50f&&y<.91f&&y>.69f)lowerGlove++;
        }
        require(maxX-minX<1.88f&&maxX-minX>1.58f,
                "Shoulders must have a convincing fitted human proportion");
        require(lowerGlove>100,"Anatomical hands must descend below the palm");
        CharacterRig.Parts r=CharacterRig.split(hero,false,false);
        require(r.leftArm.triangleCount>400&&r.rightArm.triangleCount>400,
                "Detailed fitted armor was severed from arm rig");
        require(r.leftArm.triangleCount+r.rightArm.triangleCount>
                r.leftLeg.triangleCount*.60f,
                "Long gauntlets misassigned to legs");
        System.out.println("VEILBOUND_M15_FORGED_PASS bevel_triangles="+
            panel.triangleCount+" shoulder_width="+(maxX-minX)+" glove_vertices="+lowerGlove);
    }
}
