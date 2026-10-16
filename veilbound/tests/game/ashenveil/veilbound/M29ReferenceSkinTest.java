package game.ashenveil.veilbound;

/** Reference-pose and source skin map tests; no unverified photoreal claims. */
public final class M29ReferenceSkinTest {
    private M29ReferenceSkinTest(){}
    private static void check(boolean b,String message){
        if(!b)throw new AssertionError(message);
    }
    private static float[] bounds(ArtKit.Model mesh){
        float minX=1000,maxX=-1000,minY=1000,maxY=-1000;
        for(int i=0;i<mesh.vertices.length;i+=9){
            float[] a=mesh.vertices;float x=a[i],y=a[i+1];
            minX=Math.min(minX,x);maxX=Math.max(maxX,x);
            minY=Math.min(minY,y);maxY=Math.max(maxY,y);
        }
        return new float[]{minX,maxX,minY,maxY};
    }
    private static void inspect(ArtKit.Model base,ArtKit.Model pose){
        check(base.triangleCount==pose.triangleCount,"Pose changed mesh topology");
        for(int i=0;i<base.vertices.length;i+=9){
            float[] v=base.vertices,a=pose.vertices;
            for(int j=0;j<9;j++)
                check(Float.isFinite(a[i+j]),"Invalid posed vertex");
            for(int j=6;j<9;j++)
                check(a[i+j]==v[i+j],"Pose changed PBR source color");
            float nx=a[i+3],ny=a[i+4],nz=a[i+5];
            check(Math.abs(nx*nx+ny*ny+nz*nz-1f)<.10f,
                  "Pose has non-unit deformed normal");
        }
    }
    public static void main(String[] args){
        byte[] texture=M29SkinAtlas.bake();
        byte[] repeat=M29SkinAtlas.bake();
        check(texture.length==M29SkinAtlas.SIZE*M29SkinAtlas.SIZE*4,
              "Atlas RGBA format unsupported by GLES2");
        int minR=255,maxR=0,minRough=255,maxRough=0;
        for(int i=0;i<texture.length;i++){
            check(texture[i]==repeat[i],"Atlas not deterministic");
            if(i%4==0){
                int c=texture[i]&255;
                minR=Math.min(minR,c);maxR=Math.max(maxR,c);
            }
            if(i%4==2){
                int c=texture[i]&255;
                minRough=Math.min(minRough,c);
                maxRough=Math.max(maxRough,c);
                check(c>=165&&c<=222,"Skin roughness outside safe source budget");
            }
        }
        check(maxR-minR>5&&maxRough-minRough>6,
              "Skin map flat or lacks real bump/roughness detail");
        ArtKit.Model model=HumanAnatomy.buildM28Candidate(true);
        ArtKit.Model tPose=M29ReferencePose.build(model,M29ReferencePose.T_POSE);
        ArtKit.Model relaxed=M29ReferencePose.build(model,
            M29ReferencePose.THREE_QUARTER_RELAXED);
        inspect(model,tPose);inspect(model,relaxed);
        float[] sourceBounds=bounds(model),tBounds=bounds(tPose);
        check(tBounds[1]-tBounds[0]>sourceBounds[1]-sourceBounds[0]+.22f,
              "Actual T-pose arms do not extend more horizontally");
        check(tBounds[1]>.83f&&tBounds[0]<-.83f,
              "Both arms must extend outward in source 3D");
        int lifted=0,altered=0;
        for(int i=0;i<model.vertices.length;i+=9){
            float x=model.vertices[i],y=model.vertices[i+1];
            float dx=Math.abs(tPose.vertices[i]-x),
                  dy=Math.abs(tPose.vertices[i+1]-y);
            if(dx+dy>.07f)altered++;
            if(Math.abs(tPose.vertices[i])>.79f&&tPose.vertices[i+1]>1.55f)
                lifted++;
        }
        check(lifted>60&&altered>90,"Reference pose did not articulate both arms");
        float[] relaxedBounds=bounds(relaxed);
        check(relaxedBounds[1]-relaxedBounds[0]<tBounds[1]-tBounds[0],
              "Relaxed reference must be distinct from strict T-pose");
        check(HumanHandSculpt.FINGERS_PER_HAND==4&&
              HumanHandSculpt.THUMBS_PER_HAND==1,
              "Five-digit hand references must be preserved");
        check("IMPORTED OBJ".equals(
             ModelStudio.ITEMS[ModelStudio.ITEMS.length-1]),
             "Existing model import slot has moved");
        System.out.println("VEILFORGE_M29_REFERENCE_AND_SKIN_PASS "+
            "skin_bytes="+texture.length+" tpose_lifted="+lifted+
            " moved="+altered+" textures_not_photo_scanned=true "+
            "manual_art_approval=false");
    }
}
