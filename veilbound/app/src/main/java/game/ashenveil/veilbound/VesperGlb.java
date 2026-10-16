package game.ashenveil.veilbound;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/**
 * Narrow, bounded glTF 2.0 GLB skinned-character importer.
 * Converts Vesper's real bind-pose mesh and animation channels into small
 * CPU-skinned frame sets compatible with the established GLES2 game renderer.
 * Does not claim a general-purpose glTF renderer or physical spring simulation.
 */
public final class VesperGlb {
    private VesperGlb() {}
    private static final int MAX_BYTES = 6_000_000;
    private static final int MAX_TRIANGLES = 80_000;
    private static final int MAX_JOINTS = 64;
    private static final int FRAMES = 8;
    public static final class Result {
        public final ArtKit.Model[] idle, walk, tPose, legUp, dance;
        public final boolean extraPoses;
        public final int joints, triangles;
        Result(ArtKit.Model[] i, ArtKit.Model[] w, ArtKit.Model[] t,
               ArtKit.Model[] l, ArtKit.Model[] d, boolean poses, int j, int triangles) {
            idle=i;walk=w;tPose=t;legUp=l;dance=d;extraPoses=poses;
            joints=j;this.triangles=triangles;
        }
    }
    private static final class Primitive {
        float[] position, normal, joints, weights, color;
        int[] triangles;
    }
    private static final class Track {
        int node;String path;float[] times,values;int width;
    }
    private static final class Clip {
        final ArrayList<Track> tracks=new ArrayList<>();
    }
    private static int u32(ByteBuffer b,int pos) throws IOException {
        if(pos<0 || pos>b.capacity()-4)throw new IOException("GLB header truncated");
        return b.getInt(pos);
    }
    private static byte[] bounded(InputStream stream)throws IOException {
        ByteArrayOutputStream out=new ByteArrayOutputStream();
        byte[] chunk=new byte[16384];int n,total=0;
        while((n=stream.read(chunk))!=-1) {
            total+=n;
            if(total>MAX_BYTES)throw new IOException("GLB exceeds 6 MB import limit");
            out.write(chunk,0,n);
        }
        return out.toByteArray();
    }
    private static final class Reader {
        final JSONObject doc;
        final ByteBuffer binary;
        final JSONArray accessors,views;
        Reader(JSONObject d,ByteBuffer b)throws JSONException {
            doc=d;binary=b;accessors=d.getJSONArray("accessors");
            views=d.getJSONArray("bufferViews");
        }
        float[] data(int id,int width)throws JSONException,IOException {
            JSONObject a=accessors.getJSONObject(id);
            if(a.optBoolean("normalized",false) || a.has("sparse"))
                throw new IOException("Unsupported normalized/sparse accessor");
            String typ=a.getString("type");
            if(!typ.equals(width==16?"MAT4":width==4?"VEC4":width==3?"VEC3":width==2?"VEC2":"SCALAR"))
                throw new IOException("Unexpected accessor width");
            int count=a.getInt("count"),component=a.getInt("componentType");
            if(count<1 || count>260000)throw new IOException("Accessor count exceeds limit");
            int bytes=component==5126 || component==5125?4:
                      component==5123?2:component==5121?1:0;
            if(bytes==0)throw new IOException("Unsupported accessor component type");
            JSONObject v=views.getJSONObject(a.getInt("bufferView"));
            if(v.getInt("buffer")!=0)throw new IOException("External GLB buffer rejected");
            int stride=v.optInt("byteStride",width*bytes);
            int offset=v.optInt("byteOffset",0)+a.optInt("byteOffset",0);
            int viewEnd=v.optInt("byteOffset",0)+v.getInt("byteLength");
            if(stride<width*bytes || offset<0 || viewEnd>binary.capacity() ||
                (long)offset+(long)(count-1)*stride+(long)width*bytes>viewEnd)
                throw new IOException("Accessor exceeds binary buffer");
            float[] result=new float[count*width];
            for(int i=0;i<count;i++)for(int k=0;k<width;k++) {
                int pos=offset+i*stride+k*bytes;
                float val=component==5126?binary.getFloat(pos):
                          component==5125?(float)(binary.getInt(pos)&0xffffffffL):
                          component==5123?(binary.getShort(pos)&65535):(binary.get(pos)&255);
                if(!Float.isFinite(val))throw new IOException("Nonfinite geometry/accessor");
                result[i*width+k]=val;
            }
            return result;
        }
    }
    private static float[] numbers(JSONArray a,int count)throws JSONException {
        float[] f=new float[count];
        for(int i=0;i<count;i++)f[i]=(float)a.getDouble(i);
        return f;
    }
    private static float[] ident() {
        float[] m=new float[16];m[0]=m[5]=m[10]=m[15]=1;return m;
    }
    private static float[] mult(float[] a,float[] b) {
        float[] c=new float[16];
        for(int col=0;col<4;col++)for(int row=0;row<4;row++)
            for(int k=0;k<4;k++)c[col*4+row]+=a[k*4+row]*b[col*4+k];
        return c;
    }
    private static float[] transform(float[] t,float[] q) {
        float x=q[0],y=q[1],z=q[2],w=q[3];
        float[] m=ident();
        m[0]=1-2*(y*y+z*z);m[1]=2*(x*y+w*z);m[2]=2*(x*z-w*y);
        m[4]=2*(x*y-w*z);m[5]=1-2*(x*x+z*z);m[6]=2*(y*z+w*x);
        m[8]=2*(x*z+w*y);m[9]=2*(y*z-w*x);m[10]=1-2*(x*x+y*y);
        m[12]=t[0];m[13]=t[1];m[14]=t[2];
        return m;
    }
    private static void normalize(float[] q){
        float s=0;for(float x:q)s+=x*x;
        if(s<1e-12f){q[0]=q[1]=q[2]=0;q[3]=1;return;}
        s=(float)Math.sqrt(s);for(int i=0;i<q.length;i++)q[i]/=s;
    }
    private static void animate(Track track,float time,float[][] t,float[][] q) {
        int last=track.times.length-1,at=0;
        while(at<last-1 && track.times[at+1]<time)at++;
        int other=Math.min(last,at+1);
        float gap=track.times[other]-track.times[at];
        float blend=gap<=0?0:Math.max(0,Math.min(1,(time-track.times[at])/gap));
        float[] out=new float[track.width];
        float dot=0;
        if(track.width==4)for(int k=0;k<4;k++)
            dot+=track.values[at*4+k]*track.values[other*4+k];
        for(int k=0;k<track.width;k++){
            float a=track.values[at*track.width+k],b=track.values[other*track.width+k];
            if(track.width==4 && dot<0)b=-b;
            out[k]=a+(b-a)*blend;
        }
        if(track.width==4){normalize(out);q[track.node]=out;}
        else t[track.node]=out;
    }
    private static ArtKit.Model pose(ArrayList<Primitive> primitives,
            float[][] rest,float[][] restRot,int[] parent,int[] jointNodes,
            float[][] inverse,Clip clip,float time,int triangleCount) {
        int nodes=rest.length;
        float[][] t=new float[nodes][],q=new float[nodes][];
        for(int i=0;i<nodes;i++){t[i]=rest[i].clone();q[i]=restRot[i].clone();}
        for(Track tr:clip.tracks)animate(tr,time,t,q);
        float[][] world=new float[nodes][];
        // glTF hierarchical joint nodes are parent-before-child in this model.
        for(int i=0;i<nodes;i++){
            float[] local=transform(t[i],q[i]);
            world[i]=parent[i]<0?local:mult(world[parent[i]],local);
        }
        float[][] palette=new float[jointNodes.length][];
        for(int i=0;i<palette.length;i++)
            palette[i]=mult(world[jointNodes[i]],inverse[i]);
        float[] result=new float[triangleCount*27];int cursor=0;
        for(Primitive p:primitives){
            float[] skinPos=new float[p.position.length],skinNormal=new float[p.normal.length];
            int nv=p.position.length/3;
            for(int i=0;i<nv;i++){
                int at=i*3,sk=i*4;
                float x=p.position[at],y=p.position[at+1],z=p.position[at+2];
                float nx=p.normal[at],ny=p.normal[at+1],nz=p.normal[at+2];
                float px=0,py=0,pz=0,sx=0,sy=0,sz=0;
                for(int k=0;k<4;k++){
                    float wt=p.weights[sk+k];if(wt<=0)continue;
                    int bone=(int)p.joints[sk+k];float[] m=palette[bone];
                    px+=wt*(m[0]*x+m[4]*y+m[8]*z+m[12]);
                    py+=wt*(m[1]*x+m[5]*y+m[9]*z+m[13]);
                    pz+=wt*(m[2]*x+m[6]*y+m[10]*z+m[14]);
                    sx+=wt*(m[0]*nx+m[4]*ny+m[8]*nz);
                    sy+=wt*(m[1]*nx+m[5]*ny+m[9]*nz);
                    sz+=wt*(m[2]*nx+m[6]*ny+m[10]*nz);
                }
                float nlen=(float)Math.sqrt(sx*sx+sy*sy+sz*sz);
                if(nlen>1e-8f){sx/=nlen;sy/=nlen;sz/=nlen;}
                skinPos[at]=px;skinPos[at+1]=py;skinPos[at+2]=pz;
                skinNormal[at]=sx;skinNormal[at+1]=sy;skinNormal[at+2]=sz;
            }
            for(int index:p.triangles){
                int at=index*3;
                for(int k=0;k<3;k++)result[cursor++]=skinPos[at+k];
                for(int k=0;k<3;k++)result[cursor++]=skinNormal[at+k];
                for(int k=0;k<3;k++)result[cursor++]=p.color[k];
            }
        }
        if(cursor!=result.length)throw new IllegalStateException("GLB frame vertex mismatch");
        return new ArtKit.Model(result);
    }
    public static Result load(InputStream input)throws IOException {
        byte[] file=bounded(input);
        ByteBuffer b=ByteBuffer.wrap(file).order(ByteOrder.LITTLE_ENDIAN);
        if(file.length<28 || u32(b,0)!=0x46546c67 || u32(b,4)!=2 || u32(b,8)!=file.length)
            throw new IOException("Not a GLB 2.0 file");
        int jsonSize=u32(b,12),jsonType=u32(b,16);
        if(jsonType!=0x4e4f534a || jsonSize<2 || jsonSize>file.length-28)
            throw new IOException("Invalid GLB JSON chunk");
        int binHeader=20+jsonSize,binSize=u32(b,binHeader),binType=u32(b,binHeader+4);
        if(binType!=0x004e4942 || binSize<1 || (long)binHeader+8+binSize>file.length)
            throw new IOException("Invalid GLB BIN chunk");
        ByteBuffer binary=ByteBuffer.wrap(file,binHeader+8,binSize).slice().order(ByteOrder.LITTLE_ENDIAN);
        try {
            JSONObject doc=new JSONObject(new String(file,20,jsonSize,StandardCharsets.UTF_8));
            Reader reader=new Reader(doc,binary);
            JSONArray meshes=doc.getJSONArray("meshes"),materials=doc.getJSONArray("materials"),
                      nodes=doc.getJSONArray("nodes"),skins=doc.getJSONArray("skins");
            if(meshes.length()!=1 || skins.length()!=1 || nodes.length()>96)
                throw new IOException("Vesper importer expects one skinned mesh");
            JSONObject skin=skins.getJSONObject(0);
            JSONArray joints=skin.getJSONArray("joints");
            if(joints.length()<2 || joints.length()>MAX_JOINTS)
                throw new IOException("Unsupported GLB joint count");
            int[] jointNodes=new int[joints.length()];
            for(int i=0;i<jointNodes.length;i++)jointNodes[i]=joints.getInt(i);
            float[] ibms=reader.data(skin.getInt("inverseBindMatrices"),16);
            if(ibms.length!=joints.length()*16)throw new IOException("Bad inverse bind matrices");
            float[][] inverse=new float[joints.length()][16];
            for(int i=0;i<inverse.length;i++)
                System.arraycopy(ibms,i*16,inverse[i],0,16);
            int[] parent=new int[nodes.length()];
            float[][] rest=new float[nodes.length()][3],rot=new float[nodes.length()][4];
            for(int i=0;i<nodes.length();i++)parent[i]=-1;
            for(int i=0;i<nodes.length();i++){
                JSONObject n=nodes.getJSONObject(i);
                rest[i]=n.has("translation")?numbers(n.getJSONArray("translation"),3):new float[3];
                rot[i]=n.has("rotation")?numbers(n.getJSONArray("rotation"),4):
                    new float[]{0,0,0,1};
                JSONArray children=n.optJSONArray("children");
                if(children!=null)for(int j=0;j<children.length();j++){
                    int child=children.getInt(j);
                    if(child<=i || child>=nodes.length())throw new IOException("Unsupported unordered joint tree");
                    parent[child]=i;
                }
            }
            JSONArray prims=meshes.getJSONObject(0).getJSONArray("primitives");
            if(prims.length()<1 || prims.length()>32)throw new IOException("Unsupported number of materials");
            ArrayList<Primitive> primitiveList=new ArrayList<>();int tris=0;
            for(int j=0;j<prims.length();j++){
                JSONObject prim=prims.getJSONObject(j),attr=prim.getJSONObject("attributes");
                if(prim.optInt("mode",4)!=4)throw new IOException("Only triangle primitives supported");
                Primitive p=new Primitive();
                p.position=reader.data(attr.getInt("POSITION"),3);
                p.normal=reader.data(attr.getInt("NORMAL"),3);
                p.joints=reader.data(attr.getInt("JOINTS_0"),4);
                p.weights=reader.data(attr.getInt("WEIGHTS_0"),4);
                int nv=p.position.length/3;
                if(p.normal.length!=nv*3 || p.joints.length!=nv*4 ||
                    p.weights.length!=nv*4)throw new IOException("Vertex attribute length mismatch");
                float[] ix=reader.data(prim.getInt("indices"),1);
                if(ix.length%3!=0 || ix.length==0)throw new IOException("Invalid triangle indices");
                tris+=ix.length/3;
                if(tris>MAX_TRIANGLES)throw new IOException("Mesh triangle budget exceeded");
                p.triangles=new int[ix.length];
                for(int i=0;i<ix.length;i++){
                    p.triangles[i]=(int)ix[i];
                    if(p.triangles[i]<0 || p.triangles[i]>=nv || p.triangles[i]!=ix[i])
                        throw new IOException("Mesh index outside bounds");
                }
                for(int i=0;i<nv*4;i+=4){
                    float sum=0;
                    for(int k=0;k<4;k++){
                        int bone=(int)p.joints[i+k];
                        if(bone<0 || bone>=jointNodes.length || bone!=p.joints[i+k] ||
                           p.weights[i+k]<0)throw new IOException("Invalid skin influence");
                        sum+=p.weights[i+k];
                    }
                    if(Math.abs(sum-1)>0.015f)throw new IOException("Unnormalized skin weights");
                }
                JSONObject m=materials.getJSONObject(prim.getInt("material"));
                JSONArray factor=m.getJSONObject("pbrMetallicRoughness").getJSONArray("baseColorFactor");
                p.color=numbers(factor,4);
                primitiveList.add(p);
            }
            JSONArray anims=doc.getJSONArray("animations");
            if(anims.length()<1)throw new IOException("No character animations");
            Clip idle=null,walk=null,tPose=null,legUp=null,dance=null;
            for(int i=0;i<anims.length();i++){
                JSONObject a=anims.getJSONObject(i);
                String name=a.optString("name","");
                if(!name.equals("Idle_Bouncy_Ears") && !name.equals("Walk_Springy")
                   && !name.equals("T_Pose_Review") && !name.equals("Cute_Leg_Up")
                   && !name.equals("Cute_Dance_Shuffle"))continue;
                Clip clip=new Clip();
                JSONArray samplers=a.getJSONArray("samplers"),channels=a.getJSONArray("channels");
                for(int j=0;j<channels.length();j++){
                    JSONObject ch=channels.getJSONObject(j),target=ch.getJSONObject("target");
                    String path=target.getString("path");
                    if(!path.equals("rotation") && !path.equals("translation"))continue;
                    JSONObject sampler=samplers.getJSONObject(ch.getInt("sampler"));
                    if(!sampler.optString("interpolation","LINEAR").equals("LINEAR"))
                        throw new IOException("Only linear animation supported");
                    Track tr=new Track();tr.path=path;tr.node=target.getInt("node");
                    if(tr.node<0 || tr.node>=nodes.length())throw new IOException("Invalid animation node");
                    tr.width=path.equals("rotation")?4:3;
                    tr.times=reader.data(sampler.getInt("input"),1);
                    tr.values=reader.data(sampler.getInt("output"),tr.width);
                    if(tr.times.length<2 || tr.values.length!=tr.times.length*tr.width)
                        throw new IOException("Invalid animation timeline");
                    clip.tracks.add(tr);
                }
                if(name.equals("Idle_Bouncy_Ears"))idle=clip;
                else if(name.equals("Walk_Springy"))walk=clip;
                else if(name.equals("T_Pose_Review"))tPose=clip;
                else if(name.equals("Cute_Leg_Up"))legUp=clip;
                else dance=clip;
            }
            if(idle==null || walk==null)throw new IOException("Vesper idle/walk clips missing");
            ArtKit.Model[] idleFrames=new ArtKit.Model[FRAMES],walkFrames=new ArtKit.Model[FRAMES];
            for(int i=0;i<FRAMES;i++){
                float t=i/(float)FRAMES;
                idleFrames[i]=pose(primitiveList,rest,rot,parent,jointNodes,inverse,idle,t,tris);
                walkFrames[i]=pose(primitiveList,rest,rot,parent,jointNodes,inverse,walk,t,tris);
            }
            // Optional review poses remain separate from gameplay's proven idle/walk.
            // Older 2-clip synthetic fixtures and V3 exports continue to import.
            boolean hasPoses=tPose!=null && legUp!=null && dance!=null;
            ArtKit.Model[] tFrames=new ArtKit.Model[1],legFrames=new ArtKit.Model[1],
                           danceFrames=new ArtKit.Model[6];
            tFrames[0]=pose(primitiveList,rest,rot,parent,jointNodes,inverse,
                            tPose!=null?tPose:idle,0.5f,tris);
            legFrames[0]=pose(primitiveList,rest,rot,parent,jointNodes,inverse,
                              legUp!=null?legUp:idle,0.5f,tris);
            for(int k=0;k<danceFrames.length;k++){
                float t=dance!=null?k*(2f/danceFrames.length):k/(float)danceFrames.length;
                danceFrames[k]=pose(primitiveList,rest,rot,parent,jointNodes,inverse,
                                    dance!=null?dance:idle,t,tris);
            }
            return new Result(idleFrames,walkFrames,tFrames,legFrames,danceFrames,
                              hasPoses,joints.length(),tris);
        }catch(JSONException error){
            throw new IOException("Malformed Vesper GLB JSON",error);
        }
    }
}
