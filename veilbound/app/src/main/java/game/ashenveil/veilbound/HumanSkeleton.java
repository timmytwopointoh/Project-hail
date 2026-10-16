package game.ashenveil.veilbound;

/**
 * Original lightweight linear-blend skinning foundation. A continuous body
 * topology is the M18 modeling TARGET; current M17 multi-loft geometry is a
 * provisional input, not falsely claimed to be a connected anatomical mesh.
 * Every vertex receives normalized weights to a 15-joint humanoid skeleton.
 *
 * CPU reference deformation is deliberately independent of Android/GL so
 * worker tests can validate weighting before any shader integration.
 */
public final class HumanSkeleton {
    public static final String[] BONES={
        "pelvis","spine","chest","neck","head",
        "left_shoulder","left_elbow","left_wrist",
        "right_shoulder","right_elbow","right_wrist",
        "left_hip","left_knee","right_hip","right_knee"
    };
    public static final int JOINTS=BONES.length;
    public final float[][] bind=new float[JOINTS][3];
    public final int[] first,second;
    public final float[] secondWeight;
    public final float[] bindVertices;

    private HumanSkeleton(ArtKit.Model model){
        float[][] pts={
            {0,1.06f,0},{0,1.42f,0},{0,1.76f,0},{0,2.07f,0},{0,2.43f,0},
            {-.56f,1.88f,0},{-.56f,1.38f,0},{-.56f,.85f,0},
            {.56f,1.88f,0},{.56f,1.38f,0},{.56f,.85f,0},
            {-.205f,1.09f,0},{-.205f,.69f,0},
            {.205f,1.09f,0},{.205f,.69f,0}
        };
        for(int i=0;i<JOINTS;i++)System.arraycopy(pts[i],0,bind[i],0,3);
        bindVertices=model.vertices.clone();
        int count=bindVertices.length/9;
        first=new int[count];second=new int[count];secondWeight=new float[count];
        for(int v=0;v<count;v++){
            float x=bindVertices[v*9],y=bindVertices[v*9+1];
            int[] chain;
            if(y>2.08f)chain=new int[]{3,4};
            else if(y>1.96f&&Math.abs(x)<.28f)chain=new int[]{2,3};
            else if(Math.abs(x)>.40f&&y>.51f){
                chain=x<0?new int[]{5,6,7}:new int[]{8,9,10};
            }else if(y<1.18f&&Math.abs(x)>.07f){
                chain=x<0?new int[]{11,12}:new int[]{13,14};
            }else chain=y>1.64f?new int[]{1,2}:new int[]{0,1};
            int best=chain[0],next=chain[0];
            float bd=Float.MAX_VALUE,nd=Float.MAX_VALUE;
            for(int id:chain){
                float dy=y-bind[id][1],dx=x-bind[id][0];
                float d=dy*dy+dx*dx*.45f;
                if(d<bd){next=best;nd=bd;best=id;bd=d;}
                else if(d<nd){next=id;nd=d;}
            }
            first[v]=best;second[v]=next;
            float total=bd+nd;
            secondWeight[v]=best==next||total<1e-7f?0f:
                Math.max(0f,Math.min(.5f,bd/total));
        }
    }
    public static HumanSkeleton bind(ArtKit.Model mesh){
        if(mesh==null)throw new IllegalArgumentException("Human mesh missing");
        return new HumanSkeleton(mesh);
    }
    /**
     * Reference LBS for animated vertex positioning. Joint angles are radians,
     * measured about local X, so a test can verify blended knees and elbows.
     * Not yet active in production game animation or GPU skinning.
     */
    public float[] pose(float[] angles){
        if(angles==null||angles.length!=JOINTS)
            throw new IllegalArgumentException("Humanoid bone angle count");
        float[] out=bindVertices.clone();
        for(int v=0;v<first.length;v++){
            int a=first[v],b=second[v];float w=secondWeight[v];
            float x=bindVertices[v*9],y=bindVertices[v*9+1],z=bindVertices[v*9+2];
            float[] p=rot(x,y,z,a,angles[a]);
            float[] q=rot(x,y,z,b,angles[b]);
            out[v*9]=(1-w)*p[0]+w*q[0];
            out[v*9+1]=(1-w)*p[1]+w*q[1];
            out[v*9+2]=(1-w)*p[2]+w*q[2];
        }
        return out;
    }
    private float[] rot(float x,float y,float z,int i,float a){
        float dy=y-bind[i][1],dz=z-bind[i][2];
        float c=(float)Math.cos(a),s=(float)Math.sin(a);
        return new float[]{x,bind[i][1]+c*dy-s*dz,
                           bind[i][2]+s*dy+c*dz};
    }
}
