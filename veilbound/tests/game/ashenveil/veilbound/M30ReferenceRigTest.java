package game.ashenveil.veilbound;

/**
 * M30 actual vertex geometry, bind-weight and triangle strain safeguards.
 * This is a numerical quality threshold, not a photoreal likeness score.
 */
public final class M30ReferenceRigTest {
    private M30ReferenceRigTest(){}
    private static void ok(boolean yes,String why){
        if(!yes)throw new AssertionError(why);
    }
    private static double length(float[] a,int i,float[] b,int j){
        double x=a[i]-b[j],y=a[i+1]-b[j+1],z=a[i+2]-b[j+2];
        return Math.sqrt(x*x+y*y+z*z);
    }
    private static double strain(float[] original,float[] posed,int x,int y) {
        double before=length(original,x,original,y);
        double after=length(posed,x,posed,y);
        if(before<1e-7||after<1e-7)
            throw new AssertionError("Degenerate deformed triangle edge");
        return Math.max(before/after,after/before);
    }
    private static void inspect(String name,ArtKit.Model rest,ArtKit.Model pose,
                                boolean isTpose) {
        ok(rest.triangleCount==pose.triangleCount,"Changed topology: "+name);
        int stretched=0,extreme=0,garments=0,legLeaks=0,changed=0;
        double maxFactor=1.;
        float lowX=1000,highX=-1000;
        for(int i=0;i<rest.vertices.length;i+=9){
            float[] a=rest.vertices,b=pose.vertices;
            float nx=b[i+3],ny=b[i+4],nz=b[i+5];
            float normal=nx*nx+ny*ny+nz*nz;
            ok(Float.isFinite(normal)&&Math.abs(normal-1f)<.12f,
               "Invalid M30 reference pose normal");
            for(int k=0;k<9;k++)
                ok(Float.isFinite(b[i+k]),"Nonfinite skinned vertex");
            for(int k=6;k<9;k++)
                ok(a[i+k]==b[i+k],"Rig damaged original color/material");
            float ax=a[i],ay=a[i+1];
            double displacement=length(a,i,b,i);
            if(displacement>.0001)changed++;
            if(Math.abs(ax)<.405f&&ay>.95f&&ay<1.62f&&
               displacement>.065)legLeaks++;
            boolean shorts=a[i+6]<.29f&&a[i+7]<.28f&&
                            a[i+8]<.28f&&ay<1.68f;
            if(shorts){
                garments++;
                ok(displacement<.000005,"Shorts vertex rotated with the arm");
            }
            lowX=Math.min(lowX,b[i]);highX=Math.max(highX,b[i]);
        }
        for(int i=0;i<rest.vertices.length;i+=27){
            double d1=strain(rest.vertices,pose.vertices,i,i+9);
            double d2=strain(rest.vertices,pose.vertices,i+9,i+18);
            double d3=strain(rest.vertices,pose.vertices,i+18,i);
            double ratio=Math.max(d1,Math.max(d2,d3));
            maxFactor=Math.max(maxFactor,ratio);
            if(ratio>3.)stretched++;
            if(ratio>10.)extreme++;
        }
        ok(stretched<=250,"Unacceptable reference strain >3x: "+
           name+" faces="+stretched);
        ok(extreme<=15,"Unacceptable tearing strain >10x: "+
           name+" faces="+extreme);
        ok(legLeaks<=35,"Thigh is following upper arm: "+legLeaks);
        ok(garments>100&&changed>500,"Rig did not preserve clothing or move arms");
        if(isTpose)
            ok(lowX<-.95f&&highX>.95f,"T-pose arms not actually horizontal");
        else
            ok(highX<1.16f,"Relaxed reference incorrectly T-posed");
        System.out.println("VEILFORGE_M30_SKINNING_STRAIN_PASS "+name+
           " moved="+changed+" over_3x="+stretched+" over_10x="+extreme+
           " hip_leak="+legLeaks+" preserved_shorts="+garments+
           " max_edge_ratio="+maxFactor+" manual_art_review=false");
    }
    public static void main(String[] args){
        for(boolean lite:new boolean[]{false,true}){
            ArtKit.Model rest=HumanAnatomy.buildM28Candidate(lite);
            ArtKit.Model t=M30ReferenceRig.pose(rest,M30ReferenceRig.T_POSE);
            ArtKit.Model relaxed=M30ReferenceRig.pose(rest,M30ReferenceRig.RELAXED);
            inspect(lite?"lite-tpose":"full-tpose",rest,t,true);
            inspect(lite?"lite-relaxed":"full-relaxed",rest,relaxed,false);
        }
        ok(M30ReferenceRig.armWeight(.32f,1.16f,.67f,.41f,.32f)==0,
           "Thigh accidentally received arm weight");
        ok(M30ReferenceRig.armWeight(.56f,1.18f,.67f,.41f,.32f)>.97f,
           "Forearm did not receive mostly rigid shoulder weights");
        ok(M30ReferenceRig.armWeight(.56f,1.18f,.20f,.20f,.20f)==0,
           "Dark shorts affected");
        ok(HumanHandSculpt.FINGERS_PER_HAND==4&&
           HumanHandSculpt.THUMBS_PER_HAND==1,
           "Ten-finger original model contract damaged");
        System.out.println("VEILFORGE_M30_REFERENCE_RIG_PASS 4 actual mesh tests");
    }
}
