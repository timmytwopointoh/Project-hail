package game.ashenveil.veilbound;
import java.util.HashMap;
import java.util.HashSet;

/**
 * M20: no more stacked cylinder/sphere "skin" for the main unarmored body.
 * Quantized shared positions detect disconnected anatomical islands.
 */
public final class ContinuousHumanTest {
    private static void ok(boolean b,String s){if(!b)throw new AssertionError(s);}
    private static int root(int[] parent,int x){
        while(parent[x]!=x){parent[x]=parent[parent[x]];x=parent[x];}
        return x;
    }
    private static void union(int[] parent,int a,int b){
        parent[root(parent,a)]=root(parent,b);
    }
    private static long q(float x,float y,float z){
        long a=Math.round((x+2f)*10000f),
             b=Math.round((y+2f)*10000f),
             c=Math.round((z+2f)*10000f);
        return (a<<42)|(b<<21)|c;
    }
    public static void main(String[] args){
        for(boolean lite:new boolean[]{false,true}){
            ArtKit.Model mesh=HumanAnatomy.build(lite);
            int vertexCount=mesh.vertices.length/9;
            ok(mesh.triangleCount>(lite?2400:8500),"Mesh surface too low resolution");
            int[] parent=new int[vertexCount];
            HashMap<Long,Integer> lookup=new HashMap<>();
            float minY=99,maxY=-99,minX=99,maxX=-99;
            int skin=0,hair=0,shorts=0;
            for(int v=0;v<vertexCount;v++){
                parent[v]=v;
                int i=v*9;float[] a=mesh.vertices;
                float x=a[i],y=a[i+1],z=a[i+2];
                minY=Math.min(y,minY);maxY=Math.max(y,maxY);
                minX=Math.min(x,minX);maxX=Math.max(x,maxX);
                float norm=(float)Math.sqrt(a[i+3]*a[i+3]+a[i+4]*a[i+4]+a[i+5]*a[i+5]);
                ok(Float.isFinite(norm)&&Math.abs(norm-1f)<.04f,
                   "Implicit human missing real smoothed anatomical normal");
                if(a[i+6]>.5f&&a[i+7]>.25f)skin++;
                if(a[i+6]<.17f&&y>2.53f)hair++;
                if(a[i+6]>.19f&&a[i+6]<.23f&&y<1.20f&&y>.85f)shorts++;
                Long key=q(x,y,z);
                Integer first=lookup.putIfAbsent(key,v);
                if(first!=null)union(parent,first,v);
            }
            for(int v=0;v<vertexCount;v+=3){
                union(parent,v,v+1);union(parent,v,v+2);
            }
            HashSet<Integer> components=new HashSet<>();
            for(int v=0;v<vertexCount;v++)components.add(root(parent,v));
            ok(components.size()<=2,
               "Disconnected limb or standalone body part: "+components.size());
            ok(maxY-minY>2.53f&&maxY-minY<2.80f,
                "Human height no longer anatomically proportioned");
            ok(maxX-minX>.91f&&maxX-minX<1.80f,
                "Shoulder silhouette outside accepted reference proportion");
            ok(skin>1000&&shorts>50&&hair>30,
               "Missing coherent skin, hair or modest shorts material regions");
            ok(HumanSkeleton.bind(mesh).first.length==vertexCount,
                "Continuous human not accepted by the existing M18 rig");
            System.out.println("VEILBOUND_M20_FUSED_HUMAN_PASS mobile="+lite+
                " triangles="+mesh.triangleCount+" components="+components.size()+
                " shared_points="+lookup.size()+" hair="+hair+" shorts="+shorts);
        }
    }
}
