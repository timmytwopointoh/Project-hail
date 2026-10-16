package game.ashenveil.veilbound;

import java.util.Arrays;

/**
 * Five-bone rigid armor rig extracted from existing hand-authored mesh triangles.
 * Each segment keeps its normals and painted materials. The original merged
 * meshes remain untouched for Model Atelier inspection and imported OBJ work.
 * Cloth and helmet remain attached to the torso rather than stretching.
 */
public final class CharacterRig {
    private CharacterRig() {}
    public static final class Parts {
        public final ArtKit.Model torso, leftArm, rightArm, leftLeg, rightLeg, mantle;
        public final float shoulderX,shoulderY,hipX,hipY;
        Parts(ArtKit.Model[] models,float sx,float sy,float hx,float hy){
            torso=models[0];leftArm=models[1];rightArm=models[2];
            leftLeg=models[3];rightLeg=models[4];mantle=models[5];
            shoulderX=sx;shoulderY=sy;hipX=hx;hipY=hy;
        }
        public int vertices(){
            return (torso.vertices.length+leftArm.vertices.length+rightArm.vertices.length
                +leftLeg.vertices.length+rightLeg.vertices.length+
                (mantle==null?0:mantle.vertices.length))/9;
        }
    }
    private static final class Accumulator {
        float[] data=new float[1024];int used;
        void add(float[] source,int start,float px,float py,float pz){
            if(used+27>data.length)data=Arrays.copyOf(data,data.length*2);
            for(int i=0;i<27;i++)data[used+i]=source[start+i];
            for(int i=0;i<27;i+=9){
                data[used+i]-=px;data[used+i+1]-=py;data[used+i+2]-=pz;
            }
            used+=27;
        }
        ArtKit.Model finish(){return used==0?null:new ArtKit.Model(Arrays.copyOf(data,used));}
    }
    public static Parts split(ArtKit.Model model,boolean boss,boolean revenant){
        final float shoulderX=boss?1.05f:(revenant?.55f:.66f);
        final float shoulderY=boss?2.55f:(revenant?1.51f:1.56f);
        final float hipX=boss?.47f:(revenant?.22f:.25f);
        final float hipY=boss?1.08f:(revenant?.70f:.70f);
        final float armEdge=boss?.78f:(revenant?.40f:.49f);
        final float armBottom=boss?1.16f:(revenant?.89f:.90f);
        final float armTop=boss?3.34f:(revenant?2.06f:2.14f);
        final float legTop=boss?1.16f:(revenant?.82f:.77f);
        final float legEdge=boss?.26f:(revenant?.13f:.15f);
        Accumulator[] a=new Accumulator[6];
        for(int i=0;i<6;i++)a[i]=new Accumulator();
        float[] src=model.vertices;
        if(src.length%27!=0)throw new IllegalArgumentException("Non-triangular source");
        for(int i=0;i<src.length;i+=27){
            float x=(src[i]+src[i+9]+src[i+18])/3f;
            float y=(src[i+1]+src[i+10]+src[i+19])/3f;
            float z=(src[i+2]+src[i+11]+src[i+20])/3f;
            int part=0;float px=0,py=0,pz=0;
            float paintedRed=(src[i+6]+src[i+15]+src[i+24])/3f;
            if(!boss&&!revenant&&z<-.42f&&y>.12f&&y<2.05f
                    &&paintedRed<.38f){
                // Distinct cloth island with shoulder-level hinge, not welded
                // to the entire rigid torso. Enemy rigs remain unchanged.
                part=5;py=1.93f;pz=-.51f;
            }else if(z>-.34f&&y<legTop&&Math.abs(x)>legEdge){
                part=x<0?3:4;px=x<0?-hipX:hipX;py=hipY;
            }else if(z>-.34f&&y>armBottom&&y<armTop&&Math.abs(x)>armEdge){
                part=x<0?1:2;px=x<0?-shoulderX:shoulderX;py=shoulderY;
            }
            a[part].add(src,i,px,py,pz);
        }
        ArtKit.Model[] out=new ArtKit.Model[6];
        for(int i=0;i<6;i++)out[i]=a[i].finish();
        return new Parts(out,shoulderX,shoulderY,hipX,hipY);
    }
}
