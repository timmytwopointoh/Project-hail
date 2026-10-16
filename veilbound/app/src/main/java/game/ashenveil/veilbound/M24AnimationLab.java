package game.ashenveil.veilbound;

/**
 * VEILFORGE testing-ground ONLY rig/deformation stress loop.
 * Samples eight distinct, actual vertex-deformed human poses. This is not
 * a claim of motion-captured gait, production animation or finished weights.
 * No changes to existing knight's original playable CharacterRig.
 */
public final class M24AnimationLab {
    public static final int FRAMES=8;
    private M24AnimationLab(){}
    private static float smooth(float v){
        v=Math.max(0f,Math.min(1f,v));
        return v*v*(3f-2f*v);
    }
    public static ArtKit.Model frame(ArtKit.Model source,HumanSkeleton rig,int frame){
        if(source==null||rig==null||frame<0||frame>=FRAMES)
            throw new IllegalArgumentException("Invalid deforming source or frame");
        float time=frame*(float)(Math.PI*2.0/FRAMES);
        float swing=(float)Math.sin(time);
        float recover=(float)Math.cos(time);
        float[] jointAngles=new float[HumanSkeleton.JOINTS];
        jointAngles[6]=.34f+.21f*swing;
        jointAngles[9]=-.29f+.16f*swing;
        jointAngles[12]=.22f*swing;
        jointAngles[14]=-.22f*swing;
        float[] result=rig.pose(jointAngles);
        for(int i=0;i<source.vertices.length;i+=9){
            float x=source.vertices[i],y=source.vertices[i+1];
            float tx=result[i],ty=result[i+1];
            int side=x<0f?-1:1;
            float armWeight=smooth((Math.abs(x)-.34f)/.13f)*
                            (1f-smooth((y-1.68f)/.39f))*
                            smooth((y-.71f)/.18f);
            // Turn around the actual retargeted deltoid, revealing
            // silhouettes the old X-only hinge stress test could not.
            float shoulderX=side*.445f,shoulderY=M24BodyRetarget.y(shoulderX,1.82f);
            float a=side*(.48f+.27f*swing);
            float c=(float)Math.cos(a),s=(float)Math.sin(a);
            float dx=tx-shoulderX,dy=ty-shoulderY;
            float ox=shoulderX+dx*c-dy*s,oy=shoulderY+dx*s+dy*c;
            tx+=(ox-tx)*armWeight;
            ty+=(oy-ty)*armWeight;
            float legWeight=smooth((Math.abs(x)-.075f)/.075f)*
                            (1f-smooth((Math.abs(x)-.35f)/.06f))*
                            (1f-smooth((y-1.14f)/.30f));
            float hipX=side*.208f,hipY=M24BodyRetarget.y(hipX,1.055f);
            float l=side*(.06f+.13f*recover);
            c=(float)Math.cos(l);s=(float)Math.sin(l);
            dx=tx-hipX;dy=ty-hipY;
            ox=hipX+dx*c-dy*s;oy=hipY+dx*s+dy*c;
            result[i]=tx+(ox-tx)*legWeight;
            result[i+1]=ty+(oy-ty)*legWeight;
        }
        // Posed normals must not remain in bind-pose orientation. The
        // triangle-stream representation permits deterministic face normals
        // for inspection; smooth skinned tangents await later retopology.
        for(int i=0;i<result.length;i+=27){
            float ax=result[i],ay=result[i+1],az=result[i+2];
            float ux=result[i+9]-ax,uy=result[i+10]-ay,uz=result[i+11]-az;
            float vx=result[i+18]-ax,vy=result[i+19]-ay,vz=result[i+20]-az;
            float nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
            float length=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(!Float.isFinite(length)||length<1.e-7f)continue;
            nx/=length;ny/=length;nz/=length;
            for(int k=0;k<3;k++){
                int idx=i+k*9;
                result[idx+3]=nx;result[idx+4]=ny;result[idx+5]=nz;
            }
        }
        return new ArtKit.Model(result);
    }
}
