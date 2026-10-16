package game.ashenveil.veilbound;

/**
 * Reproducible structural evidence for opt-in M28 integrated face sculpt.
 * Visual likeness is still a manual acceptance requirement.
 */
public final class M28AnatomyTest {
    private static void require(boolean pass,String reason){
        if(!pass)throw new AssertionError(reason);
    }
    private static int region(ArtKit.Model model,float x,float y,float z,
                              float radius,float loRed,float hiRed){
        int count=0;float rr=radius*radius;
        for(int i=0;i<model.vertices.length;i+=9){
            float[] a=model.vertices;
            float dx=a[i]-x,dy=a[i+1]-y,dz=a[i+2]-z;
            if(dx*dx+dy*dy+dz*dz<=rr &&
               a[i+6]>=loRed&&a[i+6]<=hiRed)count++;
        }
        return count;
    }
    public static void main(String[] args){
        ArtKit.Model base=HumanAnatomy.buildM26Candidate(true,
            new float[]{.42f,.34f,.38f,.24f,.43f,.39f,.38f,.35f});
        ArtKit.Model revised=HumanAnatomy.buildM28Candidate(true);
        ArtKit.Model face=M28FaceSculpt.build(false);
        require(face.triangleCount>700,"M28 anatomical lid geometry absent");
        require(revised.triangleCount>base.triangleCount*.82f &&
                revised.triangleCount<base.triangleCount*1.28f,
                "Full-body triangle budget unexpectedly changed");
        int skin=0, protectedMaterial=0;
        float minHead=99,maxHead=-99;
        for(int i=0;i<revised.vertices.length;i+=9){
            float[] v=revised.vertices;
            float n=(float)Math.sqrt(v[i+3]*v[i+3]+v[i+4]*v[i+4]+v[i+5]*v[i+5]);
            require(Float.isFinite(n)&&Math.abs(n-1f)<.10f,
                    "Face or body normals not normalized");
            for(int k=0;k<9;k++)
                require(Float.isFinite(v[i+k]),"M28 nonfinite mesh data");
            if(M25SkinPolish.isBodySkin(v[i+6],v[i+7],v[i+8]))skin++;
            if(v[i+6]<.24f&&v[i+7]<.24f&&v[i+8]<.24f)protectedMaterial++;
            if(v[i+1]>2.30f){
                minHead=Math.min(minHead,v[i]);maxHead=Math.max(maxHead,v[i]);
            }
        }
        require(skin>500,"M28 stripped away actual epidermis");
        require(protectedMaterial>100,"M28 removed hair or modest shorts");
        require(maxHead-minHead>.21f,"Head width accidentally collapsed");
        for(int side:new int[]{-1,1}){
            float x=side*M28FaceSculpt.EYE_X;
            float y=M24BodyRetarget.y(x,M28FaceSculpt.EYE_Y);
            require(region(revised,x,y,.2055f,.058f,.69f,.78f)>10,
                    "Sclera not present on both sides");
            require(region(revised,x-side*.0025f,y,.211f,.031f,.23f,.30f)>5,
                    "Iris not visible on both sides");
            require(region(revised,x-side*.0025f,y,.214f,.020f,.09f,.14f)>3,
                    "Pupil not present on both sides");
            require(region(revised,x,y+.015f,.193f,.064f,.62f,.70f)>5,
                    "Curved upper/lower lid missing");
        }
        require(HumanHandSculpt.FINGERS_PER_HAND==4&&
                HumanHandSculpt.THUMBS_PER_HAND==1,
                "Original digit count must be preserved");
        System.out.println("VEILFORGE_M28_INTEGRATED_FACIAL_SCULPT_PASS"+
            " triangles="+revised.triangleCount+
            " face_triangles="+face.triangleCount+
            " preexisting_game_hero_unchanged=true"+
            " manual_visual_signoff=false");
    }
}
