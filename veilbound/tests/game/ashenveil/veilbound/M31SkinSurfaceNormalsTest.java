package game.ashenveil.veilbound;

/**
 * Validate actual normalized smoothed skin normals, exact unchanged positions,
 * colors, triangle count and preserved garments/eyes on both game LODs.
 */
public final class M31SkinSurfaceNormalsTest {
    private M31SkinSurfaceNormalsTest(){}
    private static void ok(boolean condition,String message) {
        if(!condition)throw new AssertionError(message);
    }
    private static void check(boolean lite){
        ArtKit.Model m28=HumanAnatomy.buildM28Candidate(lite);
        ArtKit.Model m31=HumanAnatomy.buildM31Candidate(lite);
        ok(m28.triangleCount==m31.triangleCount,"Normal sculpt changed topology");
        int smoothed=0,skin=0,protectedVerts=0;
        for(int i=0;i<m31.vertices.length;i+=9) {
            float[] old=m28.vertices,newv=m31.vertices;
            for(int j=0;j<3;j++){
                ok(old[i+j]==newv[i+j],"Smoother altered source geometry");
                ok(old[i+j+6]==newv[i+j+6],"Smoother altered material color");
            }
            float norm=newv[i+3]*newv[i+3]+newv[i+4]*newv[i+4]+
                       newv[i+5]*newv[i+5];
            ok(Float.isFinite(norm)&&Math.abs(norm-1f)<.12f,
               "Skin source-normal continuity not unit length");
            boolean isSkin=M25SkinPolish.isBodySkin(
                old[i+6],old[i+7],old[i+8]);
            float delta=Math.abs(old[i+3]-newv[i+3])+
                        Math.abs(old[i+4]-newv[i+4])+
                        Math.abs(old[i+5]-newv[i+5]);
            if(isSkin){
                skin++;
                if(delta>.00001f)smoothed++;
            }else{
                protectedVerts++;
                ok(delta<.000001f,
                   "Eye pigment, hair or original shorts got blurred");
            }
        }
        ok(skin>5000&&protectedVerts>100,
           "Skin/garments not represented in source model");
        ok(smoothed>100,
           "The smoothing algorithm did not operate on real skin vertices");
        ArtKit.Model posed=M30ReferenceRig.pose(m31,M30ReferenceRig.T_POSE);
        ok(posed.triangleCount==m31.triangleCount,
           "Skin improvement broke the corrected T-pose rig");
        System.out.println("VEILFORGE_M31_SKIN_NORMAL_CONTINUITY_PASS "+
            "lite="+lite+" source_vertices="+m31.vertices.length/9+
            " skin_verts="+skin+" modified_normals="+smoothed+
            " protected_other_materials="+protectedVerts+
            " target_reference_likeness_approved=false");
    }
    public static void main(String[] args){
        check(true);check(false);
    }
}
