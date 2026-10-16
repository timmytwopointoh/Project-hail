package game.ashenveil.veilbound;

/**
 * M32 VQ anatomy gate: actual facial/shoulder/hand/foot vertex changes,
 * clothing and historical material isolation, corrected T-pose shoulder,
 * conservative source topology and deformed triangle strain.
 *
 * These tests enforce geometric safety; they do NOT certify artistic
 * perfection, photographic likeness, or production skin weights.
 */
public final class M32AnatomyPerfectionTest {
    private M32AnatomyPerfectionTest(){}
    private static void ok(boolean good,String reason){
        if(!good)throw new AssertionError(reason);
    }
    private static double length(float[] a,int i,float[] b,int j){
        double dx=a[i]-b[j],dy=a[i+1]-b[j+1],dz=a[i+2]-b[j+2];
        return Math.sqrt(dx*dx+dy*dy+dz*dz);
    }
    private static double stretch(float[] rest,float[] pose,int i,int j){
        double before=length(rest,i,rest,j);
        double after=length(pose,i,pose,j);
        if(before<1e-7||after<1e-7)
            throw new AssertionError("Triangle edge collapsed");
        return Math.max(before/after,after/before);
    }
    private static void one(boolean lite){
        ArtKit.Model previous=HumanAnatomy.buildM31Candidate(lite);
        ArtKit.Model candidate=HumanAnatomy.buildM32Candidate(lite);
        ok(previous.triangleCount==candidate.triangleCount,
           "New anatomy altered connectivity or removed fingers/toes");
        int[] changed=new int[4];
        int protectedPoints=0,garment=0;
        double maxMove=0;
        for(int i=0;i<previous.vertices.length;i+=9){
            float[] a=previous.vertices,b=candidate.vertices;
            for(int k=0;k<9;k++)ok(Float.isFinite(b[i+k]),
                                   "Nonfinite M32 mesh data");
            for(int k=6;k<9;k++)ok(a[i+k]==b[i+k],
                                   "Sculpt altered material, nail, iris or shorts");
            double displacement=length(a,i,b,i);
            maxMove=Math.max(maxMove,displacement);
            ok(displacement<.026,"Anatomical sculpt displacement exceeded safety cap");
            boolean skin=M25SkinPolish.isBodySkin(a[i+6],a[i+7],a[i+8]);
            if(!skin){
                protectedPoints++;
                ok(displacement<1e-6,
                   "Changed hair, iris, pupil, clothing or unapproved material");
            }
            float nx=b[i+3],ny=b[i+4],nz=b[i+5];
            float n=nx*nx+ny*ny+nz*nz;
            ok(Math.abs(n-1f)<.11f,"Recomputed skin normals are not unit length");
            if(displacement>.00004){
                float x=Math.abs(a[i]),y=a[i+1];
                if(y>2.27f)changed[0]++;       // face
                else if(y>1.65f)changed[1]++;  // shoulder & pectoral
                else if(x>.44f&&y>.90f)changed[2]++; // hand
                else if(y<.40f)changed[3]++;   // foot / toes
            }
            if(a[i+6]<.29f&&a[i+7]<.28f&&a[i+8]<.28f&&
               a[i+1]<1.68f)garment++;
        }
        for(int k=0;k<4;k++)ok(changed[k]>10,
            "Anatomical worker made no real local sculpt in region "+k+
            " count="+changed[k]);
        ok(protectedPoints>100&&garment>100,
           "Existing materials/historical clothing not represented");
        ArtKit.Model raised=M32ShoulderRig.pose(candidate,M32ShoulderRig.T_POSE);
        ArtKit.Model relaxed=M32ShoulderRig.pose(candidate,M32ShoulderRig.RELAXED);
        ok(raised.triangleCount==candidate.triangleCount,
           "Shoulder rig destroyed real original mesh");
        int extreme=0,strained=0,bodyLeak=0,shortsMoved=0;
        float minX=100,maxX=-100;
        for(int i=0;i<candidate.vertices.length;i+=9){
            float[] a=candidate.vertices,b=raised.vertices;
            double move=length(a,i,b,i);
            minX=Math.min(minX,b[i]);maxX=Math.max(maxX,b[i]);
            if(Math.abs(a[i])<.405f&&a[i+1]>.95f&&a[i+1]<1.62f&&
               move>.065)bodyLeak++;
            boolean shorts=a[i+6]<.29f&&a[i+7]<.28f&&
                           a[i+8]<.28f&&a[i+1]<1.68f;
            if(shorts&&move>1e-5)shortsMoved++;
        }
        for(int i=0;i<candidate.vertices.length;i+=27){
            double ratio=Math.max(stretch(candidate.vertices,raised.vertices,i,i+9),
                Math.max(stretch(candidate.vertices,raised.vertices,i+9,i+18),
                         stretch(candidate.vertices,raised.vertices,i+18,i)));
            if(ratio>3)strained++;
            if(ratio>10)extreme++;
        }
        ok(strained<=260&&extreme<=17,
            "T-pose produces dangerous shoulder/armpit strain "+strained+"/"+extreme);
        ok(bodyLeak<=40&&shortsMoved==0,
            "Armpit rig pulled thigh or shorts "+bodyLeak+"/"+shortsMoved);
        ok(minX<-.95f&&maxX>.95f,
            "Shoulder rig fails natural outstretched T-pose span");
        ok(relaxed.triangleCount==candidate.triangleCount,
            "Relaxed rig changed original anatomy topology");
        System.out.println("VEILFORGE_M32_ALL_ANATOMY_REGIONS_PASS lite="+lite+
            " face="+changed[0]+" clavicle="+changed[1]+
            " hands="+changed[2]+" feet="+changed[3]+
            " maxDisplacement="+maxMove+" over3x="+strained+
            " over10x="+extreme+" thighLeak="+bodyLeak+
            " manualReferenceArtApproved=false");
    }
    public static void main(String[] args){
        one(true);one(false);
        ok(HumanHandSculpt.FINGERS_PER_HAND==4&&
           HumanHandSculpt.THUMBS_PER_HAND==1,
           "Lost five separate anatomical digits per hand");
    }
}
