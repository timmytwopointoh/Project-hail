package game.ashenveil.veilbound;

/** A bounded, review-only geometry/regression gate for M24 VEILFORGE. */
public final class M24FullBodyTest {
    private M24FullBodyTest(){}
    private static void ok(boolean valid,String reason){
        if(!valid)throw new AssertionError(reason);
    }
    private static void inspect(ArtKit.Model m,boolean lite){
        ok(m!=null&&m.triangleCount>(lite?9000:22000),
           "M24 whole-body mesh too low resolution");
        ok(m.triangleCount<250000,"M24 exceeds source triangle budget");
        float minY=99,maxY=-99,minX=99,maxX=-99;
        int torso=0,head=0,legs=0,feet=0,arms=0;
        for(int i=0;i<m.vertices.length;i+=9){
            float[] v=m.vertices;
            float x=v[i],y=v[i+1],z=v[i+2];
            float n=(float)Math.sqrt(v[i+3]*v[i+3]+v[i+4]*v[i+4]+v[i+5]*v[i+5]);
            ok(Float.isFinite(n)&&Math.abs(n-1f)<.06f,"Invalid vertex normal");
            minY=Math.min(y,minY);maxY=Math.max(y,maxY);
            minX=Math.min(x,minX);maxX=Math.max(x,maxX);
            if(y>1.2f&&y<1.95f&&Math.abs(x)<.36f)torso++;
            if(y>2.14f&&y<2.64f)head++;
            if(y>.25f&&y<.91f&&Math.abs(x)<.4f)legs++;
            if(y<.18f&&z>.13f)feet++;
            if(y>.88f&&y<1.78f&&Math.abs(x)>.38f)arms++;
        }
        ok(maxY-minY>2.50f&&maxY-minY<2.85f,"Human height outside expected range");
        ok(maxX-minX>.90f&&maxX-minX<1.8f,"Limb silhouette outside expected range");
        ok(torso>50&&head>50&&legs>50&&feet>50&&arms>50,
           "Missing one or more major modeled body regions");
        HumanSkeleton rig=HumanSkeleton.bind(m);
        ok(rig.first.length==m.vertices.length/9,
           "Cannot bind full-body candidate to human rig");
        float[] angles=new float[HumanSkeleton.JOINTS];
        angles[6]=.22f;angles[12]=-.18f;angles[14]=.12f;
        float[] posed=rig.pose(angles);
        ok(posed.length==m.vertices.length,"Deformation vertex count changed");
        for(float x:posed)ok(Float.isFinite(x),"Nonfinite rigged vertex");
        System.out.println("M24_BODY_GEOMETRY_PASS lite="+lite+
            " tris="+m.triangleCount+" torso="+torso+
            " head="+head+" arms="+arms+" legs="+legs+" feet="+feet);
    }
    public static void main(String[] args){
        ArtKit.Model baseline=HumanAnatomy.build(false);
        ArtKit.Model refined=HumanAnatomy.buildM24Candidate(false);
        ArtKit.Model mobile=HumanAnatomy.buildM24Candidate(true);
        inspect(refined,false);inspect(mobile,true);
        ok(baseline.triangleCount!=refined.triangleCount,
           "M24 must actually sculpt new continuous geometry");
        ok(mobile.triangleCount<refined.triangleCount,
           "Mobile level of detail must be less detailed");
        ok(HumanHandSculpt.FINGERS_PER_HAND==4&&HumanHandSculpt.THUMBS_PER_HAND==1,
           "Exactly four fingers plus an opposable thumb on each hand");
        ok(refined.vertices.length%27==0,"Triangle stream damaged");
        ok("IMPORTED OBJ".equals(ModelStudio.ITEMS[ModelStudio.ITEMS.length-1]),
           "Existing OBJ importer must remain available");
        System.out.println("VEILBOUND_M24_FULL_BODY_PASS unarmored_only manual_review_required");
    }
}
