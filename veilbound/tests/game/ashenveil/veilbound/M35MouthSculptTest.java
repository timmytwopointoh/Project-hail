package game.ashenveil.veilbound;

/** Structural gates for actual lips, mouth cavity and unchanged human. */
public final class M35MouthSculptTest {
    private M35MouthSculptTest(){}
    private static void ok(boolean yes,String why){
        if(!yes)throw new AssertionError(why);
    }
    private static float[] oralGap(ArtKit.Model mesh){
        float low=100f,high=-100f;int n=0;
        float[] data=mesh.vertices;
        for(int i=0;i<data.length;i+=9){
            float x=data[i];
            float r=data[i+6],g=data[i+7],b=data[i+8];
            if(Math.abs(x)>.005f||
               Math.abs(r-.329f)>.00001f||
               Math.abs(g-.184f)>.00001f||
               Math.abs(b-.185f)>.00001f)continue;
            low=Math.min(low,data[i+1]);high=Math.max(high,data[i+1]);n++;
        }
        ok(n>=6,"No real pigmented mouth cavity triangles near centerline");
        return new float[]{low,high,n};
    }
    private static void inspect(boolean lite) {
        ArtKit.Model old=HumanAnatomy.buildM32Candidate(lite);
        ArtKit.Model neutral=HumanAnatomy.buildM35Candidate(lite,false);
        ArtKit.Model opened=HumanAnatomy.buildM35Candidate(lite,true);
        ArtKit.Model source=M28FaceSculpt.build(lite);
        ArtKit.Model withoutOldMouth=M28FaceSculpt.build(lite,false);
        ArtKit.Model mouth=M35MouthSculpt.build(lite,0f);
        ArtKit.Model parted=M35MouthSculpt.build(lite,1f);
        ok(source.triangleCount>withoutOldMouth.triangleCount,
           "Original mouth was not preserved for historical comparison");
        ok(mouth.triangleCount>=600,
           "New upper/lower lip mesh is not a genuine volumetric sculpt");
        ok(parted.triangleCount==mouth.triangleCount,
           "Parted-lip test changed topology; rig cannot reuse mesh");
        ok(neutral.triangleCount==opened.triangleCount,
           "Actual human open-mouth pose changed topology");
        ok(Math.abs(neutral.triangleCount-old.triangleCount)<3200,
           "M35 unexpectedly replaced the skull/body/hands");
        float[] closed=oralGap(mouth),open=oralGap(parted);
        ok(open[1]-open[0]>(closed[1]-closed[0])+.008f,
           "Opening pose did not reveal an actual enlarged mouth");
        float[] closedData=mouth.vertices,openedData=parted.vertices;
        int skin=0,upper=0,lower=0,different=0;
        float minX=10,maxX=-10;
        for(int i=0;i<closedData.length;i+=9){
            float x=closedData[i],y=closedData[i+1],z=closedData[i+2];
            minX=Math.min(minX,x);maxX=Math.max(maxX,x);
            for(int j=0;j<9;j++)
                ok(Float.isFinite(closedData[i+j]),"NaN in real lip geometry");
            float nx=closedData[i+3],ny=closedData[i+4],nz=closedData[i+5];
            ok(Math.abs(nx*nx+ny*ny+nz*nz-1f)<.12f,
               "Lip surface has non-unit normals");
            if(y>M35MouthSculpt.MOUTH_Y+.002f)upper++;
            if(y<M35MouthSculpt.MOUTH_Y-.002f)lower++;
            if(Math.abs(closedData[i+1]-openedData[i+1])>.0004f)different++;
            if(M25SkinPolish.isBodySkin(closedData[i+6],
                  closedData[i+7],closedData[i+8]))skin++;
        }
        ok(minX<-.049f&&maxX>.049f,"Mouth lacks two natural corners");
        ok(upper>150&&lower>150&&different>150,
           "Upper/lower lip form or opening articulation missing");
        // Confirm entire body, 5 digits each hand and baseline material survive.
        int oldHair=0,newHair=0;
        for(int i=0;i<neutral.vertices.length;i+=9){
            float[] a=neutral.vertices;
            for(int j=0;j<9;j++)ok(Float.isFinite(a[i+j]),
                                   "Whole-body mouth caused corrupt geometry");
            float len=a[i+3]*a[i+3]+a[i+4]*a[i+4]+a[i+5]*a[i+5];
            ok(Math.abs(len-1f)<.12f,"Whole-body facial normal corrupted");
            if(a[i+6]<.29f&&a[i+7]<.29f&&a[i+8]<.29f)newHair++;
        }
        for(int i=0;i<old.vertices.length;i+=9){
            float[] a=old.vertices;
            if(a[i+6]<.29f&&a[i+7]<.29f&&a[i+8]<.29f)oldHair++;
        }
        ok(newHair==oldHair,
           "M35 changed hair or dark clothing in untouched source");
        ok(HumanHandSculpt.FINGERS_PER_HAND==4&&
           HumanHandSculpt.THUMBS_PER_HAND==1,
           "Must retain 4 fingers and opposed thumb on both hands");
        ArtKit.Model raised=M32ShoulderRig.pose(neutral,M32ShoulderRig.T_POSE);
        ok(raised.triangleCount==neutral.triangleCount,
           "New mouth unexpectedly interfered with correct T-pose rig");
        System.out.println("VEILFORGE_M35_REAL_ADULT_MOUTH_PASS lite="+lite+
            " neutral_body_triangles="+neutral.triangleCount+
            " mouth_triangles="+mouth.triangleCount+
            " open_gap_mm_proportional="+(open[1]-open[0])+
            " closed_gap="+(closed[1]-closed[0])+
            " preserved_dark_material_vertices="+newHair+
            " visual_approval=false");
    }
    public static void main(String[] args){inspect(true);inspect(false);}
}
