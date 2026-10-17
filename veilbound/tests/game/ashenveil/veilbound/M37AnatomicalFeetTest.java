package game.ashenveil.veilbound;

/**
 * M37 acceptance is geometry-only. References: NCBI foot arch anatomy,
 * Cleveland Clinic deltoid landmarks. NOT an artistic realism verdict.
 */
public final class M37AnatomicalFeetTest {
    private M37AnatomicalFeetTest(){}
    private static void ok(boolean b,String why){
        if(!b)throw new AssertionError(why);
    }
    private static float shoulderEdge(ArtKit.Model m){
        float edge=0f;
        for(int i=0;i<m.vertices.length;i+=9){
            float x=Math.abs(m.vertices[i]),y=m.vertices[i+1];
            // Restrict to the deltoid/upper-humerus, not the fingers.
            if(y>1.68f&&y<1.98f&&x>.35f)
                edge=Math.max(edge,x);
        }
        return edge;
    }
    private static float[] toeFronts(ArtKit.Model m,boolean right){
        float[] front={-9f,-9f,-9f,-9f,-9f};
        for(int i=0;i<m.vertices.length;i+=9){
            float x=m.vertices[i],y=m.vertices[i+1],z=m.vertices[i+2];
            if((right?x<0:x>0)||y<-.06f||y>.22f)continue;
            float absX=Math.abs(x);
            for(int toe=0;toe<5;toe++){
                float tx=.133f+toe*.042f;
                if(Math.abs(absX-tx)<.016f)
                    front[toe]=Math.max(front[toe],z);
            }
        }
        return front;
    }
    private static void one(boolean lite){
        ArtKit.Model baseline=HumanAnatomy.buildM36Candidate(lite,0f);
        ArtKit.Model newMesh=HumanAnatomy.buildM37Candidate(lite,0f);
        ok(newMesh.triangleCount>12000,"Lost connected anatomical body");
        ok(Math.abs(newMesh.triangleCount-baseline.triangleCount)<10000,
           "M37 unexpectedly replaced most of the human");
        float prev=shoulderEdge(baseline),current=shoulderEdge(newMesh);
        ok(prev>0f&&current>0f&&current<prev,
            "Shoulder silhouette did not move inward "+prev+" vs "+current);
        ok(prev-current<.06f,
            "Over-narrowed deltoid breadth");
        int protectedPoints=0,footSkin=0;
        float lowest=100f;
        for(int i=0;i<newMesh.vertices.length;i+=9){
            float[] v=newMesh.vertices;
            for(int k=0;k<9;k++)
                ok(Float.isFinite(v[i+k]),"Nonfinite anatomical vertex");
            float nn=v[i+3]*v[i+3]+v[i+4]*v[i+4]+v[i+5]*v[i+5];
            ok(Math.abs(nn-1f)<.13f,"Surface normal unnormalized");
            lowest=Math.min(lowest,v[i+1]);
            if(v[i+1]<.45f&&M25SkinPolish.isBodySkin(v[i+6],v[i+7],v[i+8]))
                footSkin++;
            if(v[i+6]<.29f&&v[i+7]<.29f&&v[i+8]<.29f)
                protectedPoints++;
        }
        ok(lowest>-.13f&&lowest<.065f,
            "Toe/heel grounding corrupted "+lowest);
        ok(footSkin>90&&protectedPoints>200,
            "Lost foot surface or original hair and clothing");
        for(boolean right:new boolean[]{false,true}){
            float[] tips=toeFronts(newMesh,right);
            for(int i=0;i<5;i++)
                ok(tips[i]>.32f,"Toe "+i+" not geometrically represented");
            ok(tips[0]>tips[4]+.012f,
               "Hallux/little toe must not end at same plane");
        }
        ArtKit.Model opened=HumanAnatomy.buildM37Candidate(lite,1f);
        ok(opened.triangleCount==newMesh.triangleCount,
           "M37 lips altered foot topology");
        ArtKit.Model raised=M32ShoulderRig.pose(newMesh,
            M32ShoulderRig.T_POSE,HumanAnatomy.M37_SHOULDER_SPAN);
        ok(raised.triangleCount==newMesh.triangleCount,
           "M37 shoulder rotation replaced feet or fingers");
        // Pose should never pull feet with an arm rotation.
        int footMoved=0,garmentsMoved=0;
        for(int i=0;i<newMesh.vertices.length;i+=9){
            float[] a=newMesh.vertices,b=raised.vertices;
            float d=Math.abs(a[i]-b[i])+Math.abs(a[i+1]-b[i+1])+
                    Math.abs(a[i+2]-b[i+2]);
            if(a[i+1]<.39f&&d>1e-5f)footMoved++;
            if(a[i+6]<.29f&&a[i+7]<.28f&&a[i+8]<.28f&&a[i+1]<1.68f&&d>1e-5f)
                garmentsMoved++;
        }
        ok(footMoved==0&&garmentsMoved==0,
           "M37 arm weights leaked into feet or original shorts");
        System.out.println("M37_ANATOMY_REFERENCE_PASS lite="+lite+
            " shoulder_before="+prev+" shoulder_after="+current+
            " foot_vertices="+footSkin+" triangles="+newMesh.triangleCount+
            " manual_visual_approval=false");
    }
    public static void main(String[] args){
        one(true);one(false);
        boolean bad=false;
        try{HumanAnatomy.buildM37Candidate(true,Float.NaN);}
        catch(IllegalArgumentException valid){bad=true;}
        ok(bad,"Reject nonfinite mouth input");
    }
}
