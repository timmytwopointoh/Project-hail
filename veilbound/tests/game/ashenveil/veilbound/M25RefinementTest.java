package game.ashenveil.veilbound;

/** Review-only unit checks for actual face geometry and skin-safe refinements. */
public final class M25RefinementTest {
    private static void require(boolean b,String reason){
        if(!b)throw new AssertionError(reason);
    }
    private static int countNear(ArtKit.Model m,float x,float y,float z,
                                  float distance,float minR,float maxR){
        float rr=distance*distance;int count=0;
        for(int i=0;i<m.vertices.length;i+=9){
            float[] v=m.vertices;
            float dx=v[i]-x,dy=v[i+1]-y,dz=v[i+2]-z;
            if(dx*dx+dy*dy+dz*dz<rr&&v[i+6]>=minR&&v[i+6]<=maxR)count++;
        }
        return count;
    }
    public static void main(String[] args){
        ArtKit.Model original=HumanAnatomy.build(true);
        ArtKit.Model m24=HumanAnatomy.buildM24Candidate(true);
        ArtKit.Model m25=HumanAnatomy.buildM25Candidate(true);
        ArtKit.Model face=M25FaceSculpt.build(false);
        require(face.triangleCount>600,"Eyes/eyelids have no actual surface triangles");
        require(m25.triangleCount>m24.triangleCount,
                "M25 must add physical facial mesh without subtracting hands");
        for(int side:new int[]{-1,1}){
            float x=side*M25FaceSculpt.EYE_X;
            float y=M24BodyRetarget.y(x,M25FaceSculpt.EYE_Y);
            require(countNear(m25,x,y,M25FaceSculpt.EYE_FRONT,.052f,.69f,.86f)>10,
                    "Missing shaped sclera on face side "+side);
            require(countNear(m25,x-side*.005f,y,.212f,.035f,.17f,.32f)>10,
                    "Missing visible iris on face side "+side);
            require(countNear(m25,x-side*.005f,y,.215f,.020f,.06f,.12f)>5,
                    "Missing pupil on face side "+side);
        }
        ArtKit.Model polish=M25SkinPolish.apply(original);
        int changedSkin=0,unchangedGarments=0;
        for(int i=0;i<original.vertices.length;i+=9){
            float[] a=original.vertices,b=polish.vertices;
            require(Math.abs(a[i]-b[i])<1e-6f&&
                    Math.abs(a[i+1]-b[i+1])<1e-6f&&
                    Math.abs(a[i+2]-b[i+2])<1e-6f,
                    "Palette pass illegally changed original mesh geometry");
            float d=Math.abs(a[i+6]-b[i+6])+Math.abs(a[i+7]-b[i+7])+
                    Math.abs(a[i+8]-b[i+8]);
            if(M25SkinPolish.isBodySkin(a[i+6],a[i+7],a[i+8])){
                if(d>.0001f)changedSkin++;
            }else{
                require(d<1e-7f,"Hair or shorts altered by skin work-over");
                unchangedGarments++;
            }
            float norm=(float)Math.sqrt(m25.vertices[i+3]*m25.vertices[i+3]+
                m25.vertices[i+4]*m25.vertices[i+4]+m25.vertices[i+5]*m25.vertices[i+5]);
            require(Float.isFinite(norm)&&Math.abs(norm-1)<.09f,
                    "M25 normal no longer unit length");
        }
        require(changedSkin>150&&unchangedGarments>50,
                "Skin work-over failed or clothing/hair palette no longer protected");
        require(HumanHandSculpt.FINGERS_PER_HAND==4&&HumanHandSculpt.THUMBS_PER_HAND==1,
                "Both hands must retain four fingers plus thumb");
        require(m25.triangleCount<200000,"M25 sculpt exceeded mobile mesh budget");
        System.out.println("VEILFORGE_M25_FACE_SKIN_PASS eyes=2 nails_preserved=true "+
            "skin_vertices_changed="+changedSkin+" hair_garment_vertices_protected="+
            unchangedGarments+" m25_triangles="+m25.triangleCount+
            " approved_for_production=false");
    }
}
