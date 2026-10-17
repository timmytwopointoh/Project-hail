package game.ashenveil.veilbound;

/** M36: expression really changes local connected facial vertices. */
public final class M36PerioralSkinTest {
    private M36PerioralSkinTest(){}
    private static void ok(boolean valid,String message){
        if(!valid)throw new AssertionError(message);
    }
    private static void inspect(boolean lite){
        ArtKit.Model source=M35MouthSculpt.sculptConnectedSkin(
            M28SkinContinuity.refine(
                ContinuousHuman.buildM25WithoutDigits(
                    lite,ContinuousHuman.BASE)));
        float[] copy=source.vertices.clone();
        ArtKit.Model zero=M36PerioralSkin.deform(source,0f);
        ArtKit.Model opened=M36PerioralSkin.deform(source,1f);
        ok(zero.triangleCount==source.triangleCount &&
           opened.triangleCount==source.triangleCount,
           "Expression changed connected skin topology");
        int moved=0,preserved=0,lowerMoved=0;float largest=0f;
        for(int i=0;i<copy.length;i+=9){
            float[] data=opened.vertices;
            float dy=data[i+1]-copy[i+1];
            largest=Math.max(largest,Math.abs(dy));
            for(int k=0;k<9;k++){
                ok(Float.isFinite(data[i+k]),"Invalid M36 value");
                ok(copy[i+k]==source.vertices[i+k],"Mutated source mesh");
                ok(copy[i+k]==zero.vertices[i+k],"Neutral not backward compatible");
            }
            boolean skin=M25SkinPolish.isBodySkin(copy[i+6],copy[i+7],copy[i+8]);
            if(!skin){
                preserved++;
                ok(Math.abs(dy)<1e-8f,"Changed iris/hair/nails/shorts");
            }
            if(Math.abs(dy)>.00002f){
                moved++;
                ok(Math.abs(copy[i])<.25f&&copy[i+1]>2.11f&&
                   copy[i+1]<2.36f,
                   "Jaw expression leaked into unrelated body");
                if(copy[i+1]<2.25f&&dy<0)lowerMoved++;
            }
            float nn=data[i+3]*data[i+3]+data[i+4]*data[i+4]+
                     data[i+5]*data[i+5];
            ok(Math.abs(nn-1f)<.12f,"M36 normal not unit length");
        }
        ok(preserved>100&&moved>10&&lowerMoved>3,
           "Expression failed to move underlying lower-face skin "+moved);
        ok(largest>.0007f&&largest<.013f,
           "Face expression has implausible displacement "+largest);
        ArtKit.Model prev=HumanAnatomy.buildM35Candidate(lite,false);
        ArtKit.Model neutral=HumanAnatomy.buildM36Candidate(lite,0f);
        ArtKit.Model parted=HumanAnatomy.buildM36Candidate(lite,1f);
        ok(neutral.triangleCount==prev.triangleCount &&
           parted.triangleCount==prev.triangleCount,
           "M36 replaced head, fingers or body");
        int changed=0;
        for(int i=0;i<prev.vertices.length;i+=9){
            for(int k=0;k<9;k++){
                ok(Float.isFinite(parted.vertices[i+k]),
                   "Bad composed M36 mouth/skin geometry");
                ok(prev.vertices[i+k]==neutral.vertices[i+k],
                   "Neutral face no longer matches exact M35 model");
            }
            if(Math.abs(parted.vertices[i+1]-neutral.vertices[i+1])>.0003f)
                changed++;
        }
        ok(changed>150,"Parted lips/skin failed to articulate");
        ArtKit.Model tpose=M32ShoulderRig.pose(neutral,M32ShoulderRig.T_POSE);
        ok(tpose.triangleCount==neutral.triangleCount,
           "M36 removed shoulder rig or ten digits");
        System.out.println("VEILFORGE_M36_PERIORAL_SKIN_PASS lite="+lite+
            " sourceMoved="+moved+" chinMoved="+lowerMoved+
            " largest="+largest+" expressionVertices="+changed+
            " artistApproval=false");
    }
    public static void main(String[] args){
        inspect(true);inspect(false);
        boolean rejected=false;
        try{
            M36PerioralSkin.deform(
                new ArtKit.Model(new float[0]),Float.NaN);
        }catch(IllegalArgumentException expected){rejected=true;}
        ok(rejected,"NaN expression should be rejected");
    }
}
