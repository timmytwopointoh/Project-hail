package game.ashenveil.veilbound;

/** Evidence that learned sculpt dials mutate real anatomy safely. */
public final class M26SculptLearningTest {
    private M26SculptLearningTest(){}
    private static void ok(boolean yes,String reason){
        if(!yes)throw new AssertionError(reason);
    }
    public static void main(String[] args){
        ArtKit.Model baseline=HumanAnatomy.buildM25Candidate(true);
        float[] none=new float[M26SculptDials.COUNT];
        ArtKit.Model unchanged=M26SculptDials.apply(baseline,none);
        ok(unchanged.triangleCount==baseline.triangleCount,
           "Zero-dial source topology changed");
        float[] dial={.68f,.58f,.58f,.40f,.56f,.55f,.55f,.55f};
        ArtKit.Model sculpt=HumanAnatomy.buildM26Candidate(true,dial);
        ok(sculpt.triangleCount==baseline.triangleCount,
           "M26 distorted source mesh triangle count");
        int changed=0,head=0,body=0,feet=0,garments=0;
        float maxChange=0f;
        for(int i=0;i<baseline.vertices.length;i+=9){
            float[] a=baseline.vertices,b=sculpt.vertices;
            ok(a[i]==unchanged.vertices[i]&&a[i+1]==unchanged.vertices[i+1]&&
               a[i+2]==unchanged.vertices[i+2],
               "Zero-dial lesson unexpectedly changes source geometry");
            float dx=a[i]-b[i],dy=a[i+1]-b[i+1],dz=a[i+2]-b[i+2];
            float shift=(float)Math.sqrt(dx*dx+dy*dy+dz*dz);
            ok(Float.isFinite(shift)&&shift<.029f,
               "Bounded sculpt exceeds displacement cap");
            maxChange=Math.max(maxChange,shift);
            if(shift>.000008f){
                changed++;
                if(a[i+1]>2.27f)head++;
                else if(a[i+1]>1.55f)body++;
                else if(a[i+1]<.46f)feet++;
            }
            for(int channel=6;channel<9;channel++)
                ok(a[i+channel]==b[i+channel],
                   "Sculpt changed skin/eye/hair material color");
            float normal=(float)Math.sqrt(
                b[i+3]*b[i+3]+b[i+4]*b[i+4]+b[i+5]*b[i+5]);
            ok(Float.isFinite(normal)&&Math.abs(normal-1f)<.09f,
               "Analytic normal invalid");
            if(!M25SkinPolish.isBodySkin(a[i+6],a[i+7],a[i+8])&&
               a[i+1]<2.25f){
                ok(shift<.000001f,"Shorts or non-skin prop was sculpted");
                garments++;
            }
        }
        ok(changed>100&&head>35&&body>35&&feet>5,
           "Sculpt lesson did not modify real targeted geometry");
        ok(garments>100,"Test did not sample preserved garment vertices");
        ok(HumanHandSculpt.FINGERS_PER_HAND==4&&
           HumanHandSculpt.THUMBS_PER_HAND==1,
           "Hands lost their precise 5-digit requirement");
        boolean rejected=false;
        try{M26SculptDials.parse("1,0,0,0,0,0,0,-.5");}
        catch(IllegalArgumentException ex){rejected=true;}
        ok(rejected,"Unsafe negative dial admitted");
        rejected=false;
        try{M26SculptDials.parse("1,0,0,0,0,0,0,NaN");}
        catch(IllegalArgumentException ex){rejected=true;}
        ok(rejected,"Nonfinite sculpt dial admitted");
        ok(maxChange>.001f,"No genuine vertex displacement");
        System.out.println("VEILFORGE_M26_SCULPT_LEARNING_PASS moved="+changed+
            " head="+head+" body="+body+" feet="+feet+
            " max="+maxChange+" manual_visual_review_required=true");
    }
}
