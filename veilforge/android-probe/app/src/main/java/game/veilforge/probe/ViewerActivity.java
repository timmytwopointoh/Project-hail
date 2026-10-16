package game.veilforge.probe;

import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.content.res.AssetManager;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.opengl.Matrix;
import android.util.Log;
import android.view.WindowManager;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.ArrayList;
import java.util.HashMap;
import org.json.JSONArray;
import org.json.JSONObject;

/** Isolated render-test harness. Not a game activity, and no game code is linked. */
public final class ViewerActivity extends Activity {
    static final String TAG="VEILFORGE_PROBE";
    private GLSurfaceView surface;
    private ModelRenderer renderer;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                             WindowManager.LayoutParams.FLAG_FULLSCREEN);
        surface=new GLSurfaceView(this);
        surface.setEGLContextClientVersion(2);
        renderer=new ModelRenderer(getAssets());
        surface.setRenderer(renderer);
        surface.setRenderMode(GLSurfaceView.RENDERMODE_WHEN_DIRTY);
        setContentView(surface);
        select(getIntent());
    }
    private void select(Intent intent) {
        if (renderer!=null && intent!=null) {
            renderer.asset=intent.getStringExtra("asset");
            if(renderer.asset==null) renderer.asset="scene";
            renderer.yaw=intent.getIntExtra("yaw",0);
            renderer.pitch=intent.getIntExtra("pitch",20);
            if(surface!=null) surface.requestRender();
            Log.i(TAG,"VIEW asset="+renderer.asset+" yaw="+renderer.yaw+" pitch="+renderer.pitch);
        }
    }
    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        select(intent);
    }
    @Override protected void onPause(){super.onPause();if(surface!=null)surface.onPause();}
    @Override protected void onResume(){super.onResume();if(surface!=null){surface.onResume();surface.requestRender();}}

    static final class Geometry {
        FloatBuffer vertices,normals,colors;
        int count;
        Geometry(float[] p,float[] n,float[] c) {
            count=p.length/3;
            vertices=buffer(p);normals=buffer(n);colors=buffer(c);
        }
        static FloatBuffer buffer(float[] a) {
            FloatBuffer out=ByteBuffer.allocateDirect(a.length*4).order(ByteOrder.nativeOrder()).asFloatBuffer();
            out.put(a).position(0);return out;
        }
    }
    static final class MeshData {
        String id;ArrayList<Geometry> shapes=new ArrayList<>();
        float[] min={Float.POSITIVE_INFINITY,Float.POSITIVE_INFINITY,Float.POSITIVE_INFINITY};
        float[] max={Float.NEGATIVE_INFINITY,Float.NEGATIVE_INFINITY,Float.NEGATIVE_INFINITY};
        void expand(float[] xyz){
            for(int k=0;k<3;k++){min[k]=Math.min(min[k],xyz[k]);max[k]=Math.max(max[k],xyz[k]);}
        }
    }
    static final class Instance {
        String id,asset;
        int mesh;float[] position={0,0,0};
        float[] rotation={0,0,0,1};float scale=1;
    }
    static final class ModelRenderer implements GLSurfaceView.Renderer {
        final AssetManager assets;
        final ArrayList<MeshData> models=new ArrayList<>();
        final ArrayList<Instance> instances=new ArrayList<>();
        volatile String asset="scene";
        volatile int yaw=0,pitch=20;
        volatile boolean loaded=false;
        int program,aPos,aNormal,aColor,uMvp,uModel;
        int width=1,height=1;
        final float[] projection=new float[16],view=new float[16],model=new float[16];
        final float[] pv=new float[16],mvp=new float[16];

        ModelRenderer(AssetManager assets){this.assets=assets;}
        byte[] read(String file)throws Exception{
            try(InputStream in=assets.open(file);ByteArrayOutputStream out=new ByteArrayOutputStream()) {
                byte[] buf=new byte[16384];int size;
                while((size=in.read(buf))>=0){if(size>0)out.write(buf,0,size);}
                return out.toByteArray();
            }
        }
        static float[] floatArray(JSONArray a,int len)throws Exception{
            float[] out=new float[len];
            for(int i=0;i<len;i++)out[i]=(float)a.getDouble(i);
            return out;
        }
        static int compile(int kind,String code) {
            int shader=GLES20.glCreateShader(kind);
            GLES20.glShaderSource(shader,code);
            GLES20.glCompileShader(shader);
            int[] status=new int[1];
            GLES20.glGetShaderiv(shader,GLES20.GL_COMPILE_STATUS,status,0);
            if(status[0]==0)throw new RuntimeException("Shader compilation failed: "+GLES20.glGetShaderInfoLog(shader));
            return shader;
        }
        static final String VERT=
            "attribute vec3 aPos; attribute vec3 aNormal; attribute vec4 aColor;\n"+
            "uniform mat4 uMvp; uniform mat4 uModel;\n"+
            "varying vec4 vColor; varying vec3 vNormal;\n"+
            "void main(){ gl_Position=uMvp*vec4(aPos,1.0); "+
            "vNormal=mat3(uModel)*aNormal; vColor=aColor; }\n";
        static final String FRAG=
            "precision mediump float; varying vec4 vColor; varying vec3 vNormal;\n"+
            "void main(){vec3 n=normalize(vNormal);"+
            "vec3 light=normalize(vec3(0.4,0.8,0.5));"+
            "float l=0.32+0.68*max(dot(n,light),0.0);"+
            "gl_FragColor=vec4(vColor.rgb*l,1.0);}\n";
        void setup(){
            int a=compile(GLES20.GL_VERTEX_SHADER,VERT),b=compile(GLES20.GL_FRAGMENT_SHADER,FRAG);
            program=GLES20.glCreateProgram();
            GLES20.glAttachShader(program,a);GLES20.glAttachShader(program,b);
            GLES20.glLinkProgram(program);
            int[] status=new int[1];GLES20.glGetProgramiv(program,GLES20.GL_LINK_STATUS,status,0);
            if(status[0]==0)throw new RuntimeException("Program link failed: "+GLES20.glGetProgramInfoLog(program));
            GLES20.glDeleteShader(a);GLES20.glDeleteShader(b);
            aPos=GLES20.glGetAttribLocation(program,"aPos");
            aNormal=GLES20.glGetAttribLocation(program,"aNormal");
            aColor=GLES20.glGetAttribLocation(program,"aColor");
            uMvp=GLES20.glGetUniformLocation(program,"uMvp");
            uModel=GLES20.glGetUniformLocation(program,"uModel");
        }
        // Reads glTF 2.0 accessor buffers, including indexed primitives, from ACTUAL packed scene.
        static int comps(String type)throws Exception{
            if("SCALAR".equals(type))return 1;
            if("VEC2".equals(type))return 2;
            if("VEC3".equals(type))return 3;
            if("VEC4".equals(type))return 4;
            throw new Exception("Unsupported accessor type "+type);
        }
        float[] floats(int accessor,JSONObject doc,byte[][] binaries)throws Exception{
            JSONArray acc=doc.getJSONArray("accessors");
            JSONArray views=doc.getJSONArray("bufferViews");
            JSONObject a=acc.getJSONObject(accessor);
            if(a.getInt("componentType")!=5126)throw new Exception("Float accessor expected");
            JSONObject bv=views.getJSONObject(a.getInt("bufferView"));
            byte[] bin=binaries[bv.getInt("buffer")];
            int dimensions=comps(a.getString("type")),count=a.getInt("count");
            int stride=bv.optInt("byteStride",dimensions*4);
            int offset=bv.optInt("byteOffset",0)+a.optInt("byteOffset",0);
            if(count<0||count>800000||offset<0||stride<dimensions*4||
               (long)offset+(long)Math.max(0,count-1)*stride+dimensions*4>bin.length)
                throw new Exception("Float accessor out of bounds");
            ByteBuffer bytes=ByteBuffer.wrap(bin).order(ByteOrder.LITTLE_ENDIAN);
            float[] out=new float[count*dimensions];
            for(int i=0;i<count;i++)for(int j=0;j<dimensions;j++)
                out[i*dimensions+j]=bytes.getFloat(offset+i*stride+j*4);
            return out;
        }
        int[] indices(int accessor,JSONObject doc,byte[][] binaries)throws Exception{
            JSONObject a=doc.getJSONArray("accessors").getJSONObject(accessor);
            if(!"SCALAR".equals(a.getString("type")))throw new Exception("Index accessor must be scalar");
            JSONObject view=doc.getJSONArray("bufferViews").getJSONObject(a.getInt("bufferView"));
            byte[] bin=binaries[view.getInt("buffer")];
            int component=a.getInt("componentType"),size=component==5125?4:component==5123?2:0;
            if(size==0)throw new Exception("Unsupported index type");
            int n=a.getInt("count"),stride=view.optInt("byteStride",size);
            int offset=view.optInt("byteOffset",0)+a.optInt("byteOffset",0);
            if(n<=0||n>2400000||n%3!=0||stride<size||offset<0||
                (long)offset+(long)(n-1)*stride+size>bin.length)
                throw new Exception("Indices out of bounds");
            ByteBuffer data=ByteBuffer.wrap(bin).order(ByteOrder.LITTLE_ENDIAN);
            int[] out=new int[n];
            for(int i=0;i<n;i++){
                int value=component==5125?data.getInt(offset+i*stride):data.getShort(offset+i*stride)&0xffff;
                if(value<0)throw new Exception("Index above signed range");
                out[i]=value;
            }
            return out;
        }
        void load()throws Exception{
            JSONObject doc=new JSONObject(new String(read("scene/ruin_courtyard_demo.gltf"),"UTF-8"));
            if(!"2.0".equals(doc.getJSONObject("asset").getString("version")))throw new Exception("Not glTF 2.0");
            JSONArray sources=doc.getJSONArray("buffers");
            byte[][] binary=new byte[sources.length()][];
            for(int i=0;i<binary.length;i++){
                JSONObject source=sources.getJSONObject(i);
                String name=source.getString("uri");
                if(!name.startsWith("buffers/")||name.contains(".."))throw new Exception("Unsafe glTF buffer");
                binary[i]=read("scene/"+name);
                if(binary[i].length!=source.getInt("byteLength"))throw new Exception("Buffer mismatch");
            }
            JSONArray gltfMaterials=doc.getJSONArray("materials");
            JSONArray meshes=doc.getJSONArray("meshes");
            for(int j=0;j<meshes.length();j++){
                JSONObject in=meshes.getJSONObject(j);
                MeshData mesh=new MeshData();
                mesh.id=in.getString("name");
                JSONArray shapes=in.getJSONArray("primitives");
                for(int s=0;s<shapes.length();s++){
                    JSONObject prim=shapes.getJSONObject(s),attr=prim.getJSONObject("attributes");
                    if(prim.optInt("mode",4)!=4)throw new Exception("Non-triangles");
                    float[] p=floats(attr.getInt("POSITION"),doc,binary);
                    float[] n=floats(attr.getInt("NORMAL"),doc,binary);
                    float[] c=attr.has("COLOR_0")?floats(attr.getInt("COLOR_0"),doc,binary):null;
                    int[] idx=indices(prim.getInt("indices"),doc,binary);
                    if(p.length%3!=0||n.length!=p.length||(c!=null&&c.length!=(p.length/3)*4))
                        throw new Exception("Invalid vertex stream");
                    JSONArray base=gltfMaterials.getJSONObject(prim.getInt("material"))
                            .getJSONObject("pbrMetallicRoughness").getJSONArray("baseColorFactor");
                    float[] xyz=new float[idx.length*3],normal=new float[idx.length*3],color=new float[idx.length*4];
                    for(int k=0;k<idx.length;k++){
                        int v=idx[k];
                        if(v>=p.length/3)throw new Exception("Bad vertex index");
                        for(int t=0;t<3;t++){
                            float point=p[v*3+t],norm=n[v*3+t];
                            if(!Float.isFinite(point)||!Float.isFinite(norm))throw new Exception("Nonfinite vertex");
                            xyz[k*3+t]=point;normal[k*3+t]=norm;
                        }
                        float[] bounds={xyz[k*3],xyz[k*3+1],xyz[k*3+2]};
                        mesh.expand(bounds);
                        for(int t=0;t<4;t++){
                            float tint=(float)base.getDouble(t);
                            color[k*4+t]=tint*(c==null?1f:c[v*4+t]);
                        }
                    }
                    mesh.shapes.add(new Geometry(xyz,normal,color));
                }
                models.add(mesh);
            }
            JSONArray sceneNodes=doc.getJSONArray("nodes");
            for(int i=0;i<sceneNodes.length();i++){
                JSONObject n=sceneNodes.getJSONObject(i);
                Instance row=new Instance();
                row.id=n.getString("name");row.mesh=n.getInt("mesh");
                row.position=floatArray(n.getJSONArray("translation"),3);
                row.rotation=floatArray(n.getJSONArray("rotation"),4);
                row.scale=(float)n.getJSONArray("scale").getDouble(0);
                row.asset=n.getJSONObject("extras").getString("asset_id");
                if(row.mesh<0||row.mesh>=models.size())throw new Exception("Bad scene mesh index");
                instances.add(row);
            }
            loaded=!models.isEmpty()&&!instances.isEmpty();
            int triangles=0;for(MeshData mesh:models)for(Geometry part:mesh.shapes)triangles+=part.count/3;
            Log.i(TAG,"GLTF_LOADED actual_scene=true models="+models.size()+
                    " nodes="+instances.size()+" source_triangles="+triangles);
        }
        @Override public void onSurfaceCreated(javax.microedition.khronos.opengles.GL10 unused,
                                                javax.microedition.khronos.egl.EGLConfig config){
            GLES20.glClearColor(.065f,.084f,.113f,1f);
            GLES20.glEnable(GLES20.GL_DEPTH_TEST);
            try{
                setup();load();
                Log.i(TAG,"GLES_READY renderer="+GLES20.glGetString(GLES20.GL_RENDERER));
            }catch(Exception ex){
                loaded=false;Log.e(TAG,"LOAD_FAIL",ex);
            }
        }
        @Override public void onSurfaceChanged(javax.microedition.khronos.opengles.GL10 unused,int w,int h){
            width=Math.max(1,w);height=Math.max(1,h);GLES20.glViewport(0,0,width,height);
        }
        @Override public void onDrawFrame(javax.microedition.khronos.opengles.GL10 unused){
            GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT|GLES20.GL_DEPTH_BUFFER_BIT);
            if(!loaded)return;
            String filter=asset==null?"scene":asset;
            float[] min={Float.POSITIVE_INFINITY,Float.POSITIVE_INFINITY,Float.POSITIVE_INFINITY};
            float[] max={Float.NEGATIVE_INFINITY,Float.NEGATIVE_INFINITY,Float.NEGATIVE_INFINITY};
            int selected=0;
            // Instance bounds are conservative under rotations.
            for(Instance item:instances){
                if(!"scene".equals(filter)&&!filter.equals(item.asset))continue;
                selected++;
                MeshData shape=models.get(item.mesh);
                // Use bounds around the mesh's own center rather than
                // the world origin; the old radius inflated tall trees,
                // making their 14 emulator camera views nearly identical.
                float[] local=new float[3],half=new float[3];
                for(int k=0;k<3;k++){
                    local[k]=(shape.min[k]+shape.max[k])*.5f;
                    half[k]=(shape.max[k]-shape.min[k])*.5f;
                }
                float localRadius=(float)Math.sqrt(half[0]*half[0]+
                    half[1]*half[1]+half[2]*half[2])*item.scale;
                float theta=(float)(2*Math.atan2(item.rotation[1],item.rotation[3]));
                float sn=(float)Math.sin(theta),cs=(float)Math.cos(theta);
                float[] center={item.position[0]+item.scale*(cs*local[0]+sn*local[2]),
                    item.position[1]+item.scale*local[1],
                    item.position[2]+item.scale*(-sn*local[0]+cs*local[2])};
                for(int k=0;k<3;k++){
                    min[k]=Math.min(min[k],center[k]-localRadius);
                    max[k]=Math.max(max[k],center[k]+localRadius);
                }
            }
            if(selected==0){Log.e(TAG,"ASSET_NOT_FOUND "+filter);return;}
            float[] mid=new float[3];float radius=.1f;
            for(int k=0;k<3;k++){
                mid[k]=(min[k]+max[k])*.5f;
                radius=Math.max(radius,(max[k]-min[k])*.5f);
            }
            float yawRad=(float)Math.toRadians(yaw), pitchRad=(float)Math.toRadians(Math.max(-70,Math.min(70,pitch)));
            float eyeRadius=Math.max(3.0f,radius*2.35f+1.2f);
            float ex=mid[0]+eyeRadius*(float)(Math.sin(yawRad)*Math.cos(pitchRad));
            float ey=mid[1]+eyeRadius*(float)Math.sin(pitchRad);
            float ez=mid[2]+eyeRadius*(float)(Math.cos(yawRad)*Math.cos(pitchRad));
            Matrix.setLookAtM(view,0,ex,ey,ez,mid[0],mid[1],mid[2],0,1,0);
            float ratio=(float)width/height;
            Matrix.frustumM(projection,0,-ratio,ratio,-1,1,2,Math.max(150,eyeRadius*6));
            Matrix.multiplyMM(pv,0,projection,0,view,0);
            GLES20.glUseProgram(program);
            int visible=0,drawn=0;
            for(Instance item:instances){
                if(!"scene".equals(filter)&&!filter.equals(item.asset))continue;
                Matrix.setIdentityM(model,0);
                Matrix.translateM(model,0,item.position[0],item.position[1],item.position[2]);
                // glTF quaternion for yaw-only transform.
                Matrix.rotateM(model,0,(float)Math.toDegrees(2*Math.atan2(item.rotation[1],item.rotation[3])),0,1,0);
                Matrix.scaleM(model,0,item.scale,item.scale,item.scale);
                Matrix.multiplyMM(mvp,0,pv,0,model,0);
                GLES20.glUniformMatrix4fv(uMvp,1,false,mvp,0);
                GLES20.glUniformMatrix4fv(uModel,1,false,model,0);
                for(Geometry geom:models.get(item.mesh).shapes){
                    geom.vertices.position(0);geom.normals.position(0);geom.colors.position(0);
                    GLES20.glEnableVertexAttribArray(aPos);
                    GLES20.glEnableVertexAttribArray(aNormal);
                    GLES20.glEnableVertexAttribArray(aColor);
                    GLES20.glVertexAttribPointer(aPos,3,GLES20.GL_FLOAT,false,0,geom.vertices);
                    GLES20.glVertexAttribPointer(aNormal,3,GLES20.GL_FLOAT,false,0,geom.normals);
                    GLES20.glVertexAttribPointer(aColor,4,GLES20.GL_FLOAT,false,0,geom.colors);
                    GLES20.glDrawArrays(GLES20.GL_TRIANGLES,0,geom.count);
                    drawn+=geom.count/3;
                }
                visible++;
            }
            GLES20.glFinish();int err=GLES20.glGetError();
            if(err!=GLES20.GL_NO_ERROR){Log.e(TAG,"GL_ERROR "+err);return;}
            Log.i(TAG,"FRAME_OK asset="+filter+" instances="+visible+" triangles="+drawn+
                    " yaw="+yaw+" pitch="+pitch+" size="+width+"x"+height);
        }
    }
}
