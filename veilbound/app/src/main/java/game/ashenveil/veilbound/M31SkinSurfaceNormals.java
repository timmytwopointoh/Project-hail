package game.ashenveil.veilbound;

import java.util.HashMap;

/**
 * VEILFORGE M31 — source-preserving skin normal continuity.
 *
 * The native human is stored as a non-indexed triangle stream and old face
 * normals exposed every triangle in flat studio light. This worker computes
 * seam-conscious, angle-safe shared normals for *skin only*, preserving
 * 100% of original vertex positions, triangle indices and vertex colors.
 *
 * UV seams, opposite-facing surfaces, hard garment boundaries and eye
 * materials are never averaged together. The source remains separately
 * exportable. This is lighting refinement, NOT facial retopology or
 * photorealistic skin photography.
 */
public final class M31SkinSurfaceNormals {
    private M31SkinSurfaceNormals(){}

    private static final class Norm {
        float x,y,z;
        int n;
        void add(float a,float b,float c){
            x+=a;y+=b;z+=c;n++;
        }
    }
    private static float clamp(float a,float lo,float hi){
        return Math.max(lo,Math.min(hi,a));
    }
    private static long key(float x,float y,float z,
                            float nx,float ny,float nz) {
        // 16-bit coordinates are ample for the retargeted ±3-unit human.
        int xx=Math.round(x*10000f)+32768;
        int yy=Math.round(y*10000f)+32768;
        int zz=Math.round(z*10000f)+32768;
        if((xx|yy|zz)<0||xx>65535||yy>65535||zz>65535)
            throw new IllegalArgumentException("Skin coordinate out of range");
        // Octant prevents unrelated interpenetrating SDF patches from
        // averaging their normals and giving inverted or wax-like skin.
        int oct=(nx<0?4:0)|(ny<0?2:0)|(nz<0?1:0);
        return (((long)xx)<<35)|(((long)yy)<<19)|
               (((long)zz)<<3)|oct;
    }
    public static ArtKit.Model smooth(ArtKit.Model source) {
        if(source==null||source.vertices==null||
           source.vertices.length%27!=0)
            throw new IllegalArgumentException("Invalid human triangles");
        float[] base=source.vertices,refined=base.clone();
        HashMap<Long,Norm> normalMap=new HashMap<>();
        for(int i=0;i<base.length;i+=9){
            float r=base[i+6],g=base[i+7],b=base[i+8];
            if(!M25SkinPolish.isBodySkin(r,g,b))continue;
            long k=key(base[i],base[i+1],base[i+2],
                       base[i+3],base[i+4],base[i+5]);
            Norm group=normalMap.get(k);
            if(group==null){group=new Norm();normalMap.put(k,group);}
            group.add(base[i+3],base[i+4],base[i+5]);
        }
        for(int i=0;i<base.length;i+=9){
            if(!M25SkinPolish.isBodySkin(base[i+6],base[i+7],base[i+8]))
                continue;
            long k=key(base[i],base[i+1],base[i+2],
                       base[i+3],base[i+4],base[i+5]);
            Norm group=normalMap.get(k);
            if(group==null||group.n<2)continue;
            float m=(float)Math.sqrt(group.x*group.x+
                                      group.y*group.y+group.z*group.z);
            if(m<1e-6f||!Float.isFinite(m))continue;
            float sx=group.x/m,sy=group.y/m,sz=group.z/m;
            float d=base[i+3]*sx+base[i+4]*sy+base[i+5]*sz;
            if(d<.72f)continue; // keep edge and crease
            float blend=.82f*(float)Math.pow(clamp((d-.72f)/.28f,0f,1f),.35);
            float nx=(1f-blend)*base[i+3]+blend*sx;
            float ny=(1f-blend)*base[i+4]+blend*sy;
            float nz=(1f-blend)*base[i+5]+blend*sz;
            float len=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(!Float.isFinite(len)||len<1e-6f)
                throw new IllegalStateException("Skin normal collapsed");
            refined[i+3]=nx/len;refined[i+4]=ny/len;refined[i+5]=nz/len;
        }
        return new ArtKit.Model(refined);
    }
}
