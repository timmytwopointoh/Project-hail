package game.ashenveil.veilbound;
public final class HumanSkeletonTest {
    private static void ok(boolean b,String s){if(!b)throw new AssertionError(s);}
    public static void main(String[] args){
        for(boolean lite:new boolean[]{false,true}){
            ArtKit.Model model=HumanAnatomy.build(lite);
            HumanSkeleton rig=HumanSkeleton.bind(model);
            int n=model.vertices.length/9;
            ok(rig.first.length==n&&rig.second.length==n,"Missing skin weights");
            int blends=0;
            for(int i=0;i<n;i++){
                ok(rig.first[i]>=0&&rig.first[i]<HumanSkeleton.JOINTS,"Invalid first joint");
                ok(rig.second[i]>=0&&rig.second[i]<HumanSkeleton.JOINTS,"Invalid second joint");
                ok(rig.secondWeight[i]>=0&&rig.secondWeight[i]<=.5f,"Invalid normalized weight");
                if(rig.secondWeight[i]>.02f)blends++;
            }
            ok(blends>n/6,"No joint blends near deformations");
            float[] zero=rig.pose(new float[HumanSkeleton.JOINTS]);
            for(int i=0;i<zero.length;i++)
                ok(Math.abs(zero[i]-model.vertices[i])<.00005f,
                   "Bind pose does not preserve original geometry");
            float[] angles=new float[HumanSkeleton.JOINTS];
            angles[6]=.60f;angles[9]=-.35f;
            angles[12]=.55f;angles[14]=.55f;
            float[] bent=rig.pose(angles);
            float diff=0;
            for(int i=0;i<n;i++){
                float dx=bent[i*9]-zero[i*9];
                float dy=bent[i*9+1]-zero[i*9+1];
                float dz=bent[i*9+2]-zero[i*9+2];
                ok(Float.isFinite(dx)&&Float.isFinite(dy)&&Float.isFinite(dz),
                   "Nonfinite weighted deformation");
                diff+=Math.abs(dx)+Math.abs(dy)+Math.abs(dz);
            }
            ok(diff>8f,"Elbow and knee animation has no measurable deformation");
            System.out.println("VEILBOUND_M18_SKIN_WEIGHTS_PASS triangles="+model.triangleCount+
                " blend_vertices="+blends+" motion="+diff);
        }
    }
}