package game.veilforge.probe;

import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.content.res.AssetManager;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.opengl.Matrix;
import android.opengl.GLUtils;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
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
            renderer.disableNormal=intent.getBooleanExtra("flat",false);
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
        FloatBuffer vertices,normals,colors,texcoords,tangents,bitangents;
        int count,albedo,metalRough,normalMap,aoMap;
        float metalFactor,roughFactor;
        Geometry(float[] p,float[] n,float[] c,float[] uv,
                 float[] tangent,float[] bitangent,
                 int tex,int mr,int normal,int ao,float metallic,float roughness) {
            count=p.length/3;
            vertices=buffer(p);normals=buffer(n);colors=buffer(c);texcoords=buffer(uv);
            tangents=buffer(tangent);bitangents=buffer(bitangent);
            albedo=tex;metalRough=mr;normalMap=normal;aoMap=ao;
            metalFactor=metallic;roughFactor=roughness;
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
        volatile boolean disableNormal=false;
        volatile boolean loaded=false;
        int program,aPos,aNormal,aColor,aUv,aTangent,aBitangent,uMvp,uModel;
        int uBaseTexture,uMrTexture,uNormalTexture,uAOTexture;
        int uUseAlbedo,uUseMr,uUseNormal,uUseAO,uMetallic,uRoughness;
        final HashMap<Integer,Integer> imageTextures=new HashMap<>();
        int texAlbedoCount=0,texMrCount=0,texNormalCount=0,texAOCount=0;
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
            "attribute vec3 aPos; attribute vec3 aNormal; attribute vec4 aColor; attribute vec2 aUv;\n"+
            "attribute vec3 aTangent; attribute vec3 aBitangent;\n"+
            "uniform mat4 uMvp; uniform mat4 uModel;\n"+
            "varying vec4 vColor; varying vec3 vNormal; varying vec2 vUv;\n"+
            "varying vec3 vTangent; varying vec3 vBitangent;\n"+
            "void main(){ gl_Position=uMvp*vec4(aPos,1.0); "+
            "vNormal=mat3(uModel)*aNormal; vTangent=mat3(uModel)*aTangent; "+
            "vBitangent=mat3(uModel)*aBitangent; vColor=aColor; vUv=aUv; }\n";
        // Android test shader samples real baked tangent-space normals + AO.
        // Direct lighting is still an approximation, NOT a calibrated PBR BRDF.
        static final String FRAG=
            "precision mediump float; varying vec4 vColor; varying vec3 vNormal; varying vec2 vUv;\n"+
            "varying vec3 vTangent; varying vec3 vBitangent;\n"+
            "uniform sampler2D uBaseTexture; uniform sampler2D uMrTexture;\n"+
            "uniform sampler2D uNormalTexture; uniform sampler2D uAOTexture;\n"+
            "uniform float uUseAlbedo; uniform float uUseMr; uniform float uUseNormal; uniform float uUseAO;\n"+
            "uniform float uMetallic; uniform float uRoughness;\n"+
            "void main(){vec3 original=normalize(vNormal);"+
            "vec3 sampled=texture2D(uNormalTexture,vUv).rgb*2.0-1.0;"+
            "vec3 mapped=normalize(sampled.x*normalize(vTangent)+sampled.y*normalize(vBitangent)+sampled.z*original);"+
            "vec3 n=normalize(mix(original,mapped,uUseNormal));"+
            "float ao=mix(1.0,texture2D(uAOTexture,vUv).r,uUseAO);"+
            "vec3 light=normalize(vec3(0.4,0.8,0.5));"+
            "float diffuse=max(dot(n,light),0.0);"+
            "vec3 albedo=vColor.rgb*mix(vec3(1.0),texture2D(uBaseTexture,vUv).rgb,uUseAlbedo);"+
            "vec3 rm=texture2D(uMrTexture,vUv).rgb;"+
            "float rough=clamp(mix(uRoughness,rm.g*uRoughness,uUseMr),0.05,1.0);"+
            "float metal=clamp(mix(uMetallic,rm.b*uMetallic,uUseMr),0.0,1.0);"+
            "vec3 halfdir=normalize(light+vec3(0.0,0.0,1.0));"+
            "float spec=pow(max(dot(n,halfdir),0.0),mix(70.0,7.0,rough));"+
            "vec3 lit=albedo*(0.22+0.78*diffuse)*(1.0-0.15*metal)*ao;"+
            "vec3 reflectance=mix(vec3(0.045),albedo,metal);"+
            "gl_FragColor=vec4(lit+reflectance*spec*0.8,1.0);}\n";
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
            aUv=GLES20.glGetAttribLocation(program,"aUv");
            aTangent=GLES20.glGetAttribLocation(program,"aTangent");
            aBitangent=GLES20.glGetAttribLocation(program,"aBitangent");
            uMvp=GLES20.glGetUniformLocation(program,"uMvp");
            uModel=GLES20.glGetUniformLocation(program,"uModel");
            uBaseTexture=GLES20.glGetUniformLocation(program,"uBaseTexture");
            uMrTexture=GLES20.glGetUniformLocation(program,"uMrTexture");
            uNormalTexture=GLES20.glGetUniformLocation(program,"uNormalTexture");
            uAOTexture=GLES20.glGetUniformLocation(program,"uAOTexture");
            uUseNormal=GLES20.glGetUniformLocation(program,"uUseNormal");
            uUseAO=GLES20.glGetUniformLocation(program,"uUseAO");
            uUseAlbedo=GLES20.glGetUniformLocation(program,"uUseAlbedo");
            uUseMr=GLES20.glGetUniformLocation(program,"uUseMr");
            uMetallic=GLES20.glGetUniformLocation(program,"uMetallic");
            uRoughness=GLES20.glGetUniformLocation(program,"uRoughness");
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
        int texture(int index,JSONObject doc)throws Exception{
            Integer cached=imageTextures.get(index);
            if(cached!=null)return cached;
            JSONObject tex=doc.getJSONArray("textures").getJSONObject(index);
            JSONObject image=doc.getJSONArray("images").getJSONObject(tex.getInt("source"));
            String uri=image.getString("uri");
            if(!uri.startsWith("textures/")||uri.contains("..")||!uri.endsWith(".png"))
                throw new Exception("Unsafe/non-PNG material texture "+uri);
            byte[] raw=read("scene/"+uri);
            if(raw.length<100||raw.length>1500000)throw new Exception("Invalid material PNG byte length");
            BitmapFactory.Options opts=new BitmapFactory.Options();
            opts.inScaled=false;
            Bitmap bitmap=BitmapFactory.decodeByteArray(raw,0,raw.length,opts);
            if(bitmap==null)throw new Exception("Unreadable material PNG "+uri);
            if(bitmap.getWidth()>512||bitmap.getHeight()>512||
               bitmap.getWidth()<16||bitmap.getHeight()<16)
                throw new Exception("Material dimensions exceed probe limits");
            int[] id=new int[1];GLES20.glGenTextures(1,id,0);
            if(id[0]==0)throw new Exception("GPU texture allocation failed");
            GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,id[0]);
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MIN_FILTER,GLES20.GL_LINEAR);
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MAG_FILTER,GLES20.GL_LINEAR);
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_WRAP_S,GLES20.GL_REPEAT);
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_WRAP_T,GLES20.GL_REPEAT);
            GLUtils.texImage2D(GLES20.GL_TEXTURE_2D,0,bitmap,0);
            bitmap.recycle();
            int err=GLES20.glGetError();
            if(err!=GLES20.GL_NO_ERROR)throw new Exception("Material GL upload error "+err);
            imageTextures.put(index,id[0]);
            return id[0];
        }
        void load()throws Exception{
            Log.i(TAG,"KAIYU_M8_LOAD_BEGIN before_json_parse");
            // GLSurfaceView may create a new EGL context for every test-view
            // Activity restart. Never append old glTF meshes repeatedly:
            // this previously inflated 7 models into >200 in emulator QA.
            loaded=false;
            models.clear();
            instances.clear();
            imageTextures.clear();
            texAlbedoCount=0;texMrCount=0;texNormalCount=0;texAOCount=0;
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
                if(j%10==0)Log.i(TAG,"KAIYU_M8_LOAD_PROGRESS mesh="+j+"/"+meshes.length());
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
                    float[] uvs=attr.has("TEXCOORD_0")?floats(attr.getInt("TEXCOORD_0"),doc,binary):null;
                    int[] idx=indices(prim.getInt("indices"),doc,binary);
                    int colorStride=c==null?0:c.length/(p.length/3);
                    if(p.length%3!=0||n.length!=p.length||
                       (c!=null&&c.length!=(p.length/3)*colorStride)||
                       (c!=null&&colorStride!=3&&colorStride!=4)||
                       (uvs!=null&&uvs.length!=(p.length/3)*2))
                        throw new Exception("Invalid vertex stream");
                    JSONObject pbr=gltfMaterials.getJSONObject(prim.getInt("material"))
                            .getJSONObject("pbrMetallicRoughness");
                    JSONArray base=pbr.getJSONArray("baseColorFactor");
                    int albedo=0,mr=0;
                    if(pbr.has("baseColorTexture")){
                        if(uvs==null)throw new Exception("Textured mesh missing UVs");
                        albedo=texture(pbr.getJSONObject("baseColorTexture").getInt("index"),doc);
                        texAlbedoCount++;
                    }
                    if(pbr.has("metallicRoughnessTexture")){
                        if(uvs==null)throw new Exception("Metallic-roughness mesh missing UVs");
                        mr=texture(pbr.getJSONObject("metallicRoughnessTexture").getInt("index"),doc);
                        texMrCount++;
                    }
                    JSONObject mat=gltfMaterials.getJSONObject(prim.getInt("material"));
                    int normalMap=0,aoMap=0;
                    if(mat.has("normalTexture")){
                        if(uvs==null)throw new Exception("Normal-mapped mesh must have UVs");
                        normalMap=texture(mat.getJSONObject("normalTexture").getInt("index"),doc);
                        texNormalCount++;
                    }
                    if(mat.has("occlusionTexture")){
                        if(uvs==null)throw new Exception("AO-mapped mesh must have UVs");
                        aoMap=texture(mat.getJSONObject("occlusionTexture").getInt("index"),doc);
                        texAOCount++;
                    }
                    float[] xyz=new float[idx.length*3],normal=new float[idx.length*3],
                            color=new float[idx.length*4],texcoord=new float[idx.length*2];
                    for(int k=0;k<idx.length;k++){
                        int v=idx[k];
                        if(v>=p.length/3)throw new Exception("Bad vertex index");
                        for(int t=0;t<3;t++){
                            float point=p[v*3+t],norm=n[v*3+t];
                            if(!Float.isFinite(point)||!Float.isFinite(norm))throw new Exception("Nonfinite vertex");
                            xyz[k*3+t]=point;normal[k*3+t]=norm;
                        }
                        if(uvs!=null){
                            for(int t=0;t<2;t++){
                                float uv=uvs[v*2+t];
                                if(!Float.isFinite(uv))throw new Exception("Nonfinite texture coordinates");
                                texcoord[k*2+t]=uv;
                            }
                        }
                        float[] bounds={xyz[k*3],xyz[k*3+1],xyz[k*3+2]};
                        mesh.expand(bounds);
                        for(int t=0;t<4;t++){
                            float tint=(float)base.getDouble(t);
                            color[k*4+t]=tint*(c==null||t>=colorStride?1f:c[v*colorStride+t]);
                        }
                    }
                    // Expanded triangles: derive a correctly signed tangent/
                    // bitangent basis from the same UV edges used by the baker.
                    float[] tangent=new float[xyz.length],bitangent=new float[xyz.length];
                    for(int k=0;k<idx.length;k+=3){
                        int a=k*3,b=(k+1)*3,d=(k+2)*3;
                        float px=xyz[b]-xyz[a],py=xyz[b+1]-xyz[a+1],pz=xyz[b+2]-xyz[a+2];
                        float qx=xyz[d]-xyz[a],qy=xyz[d+1]-xyz[a+1],qz=xyz[d+2]-xyz[a+2];
                        int ta=k*2,tb=(k+1)*2,td=(k+2)*2;
                        float du1=texcoord[tb]-texcoord[ta],dv1=texcoord[tb+1]-texcoord[ta+1];
                        float du2=texcoord[td]-texcoord[ta],dv2=texcoord[td+1]-texcoord[ta+1];
                        float det=du1*dv2-du2*dv1;
                        for(int corner=0;corner<3;corner++){
                            int o=(k+corner)*3;
                            float nx=normal[o],ny=normal[o+1],nz=normal[o+2];
                            float tx,ty,tz;
                            if(Math.abs(det)>1e-9f){
                                tx=(px*dv2-qx*dv1)/det;
                                ty=(py*dv2-qy*dv1)/det;
                                tz=(pz*dv2-qz*dv1)/det;
                            }else{
                                tx=Math.abs(nx)<.85f?1f:0f;ty=Math.abs(nx)<.85f?0f:1f;tz=0;
                            }
                            float projected=tx*nx+ty*ny+tz*nz;
                            tx-=nx*projected;ty-=ny*projected;tz-=nz*projected;
                            float mag=(float)Math.sqrt(tx*tx+ty*ty+tz*tz);
                            if(mag<1e-7f)throw new Exception("Degenerate tangent basis");
                            tx/=mag;ty/=mag;tz/=mag;
                            float sign=det>=0?1f:-1f;
                            tangent[o]=tx;tangent[o+1]=ty;tangent[o+2]=tz;
                            bitangent[o]=(ny*tz-nz*ty)*sign;
                            bitangent[o+1]=(nz*tx-nx*tz)*sign;
                            bitangent[o+2]=(nx*ty-ny*tx)*sign;
                        }
                    }
                    mesh.shapes.add(new Geometry(xyz,normal,color,texcoord,tangent,bitangent,
                        albedo,mr,normalMap,aoMap,
                        (float)pbr.optDouble("metallicFactor",1.0),
                        (float)pbr.optDouble("roughnessFactor",1.0)));
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
            Log.i(TAG,"MATERIAL_MAPS_LOADED basecolor="+texAlbedoCount+
                    " metallic_roughness="+texMrCount+" unique_gpu_textures="+imageTextures.size());
            Log.i(TAG,"M30_NORMAL_MAPS_LOADED normal="+texNormalCount+
                    " ao="+texAOCount+" tangent_basis=derived");
        }
        @Override public void onSurfaceCreated(javax.microedition.khronos.opengles.GL10 unused,
                                                javax.microedition.khronos.egl.EGLConfig config){
            Log.i(TAG,"KAIYU_M8_SURFACE_CREATED_BEGIN");
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
                    geom.vertices.position(0);geom.normals.position(0);
                    geom.colors.position(0);geom.texcoords.position(0);
                    geom.tangents.position(0);geom.bitangents.position(0);
                    GLES20.glActiveTexture(GLES20.GL_TEXTURE0);
                    GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,geom.albedo);
                    GLES20.glUniform1i(uBaseTexture,0);
                    GLES20.glUniform1f(uUseAlbedo,geom.albedo==0?0f:1f);
                    GLES20.glActiveTexture(GLES20.GL_TEXTURE1);
                    GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,geom.metalRough);
                    GLES20.glUniform1i(uMrTexture,1);
                    GLES20.glUniform1f(uUseMr,geom.metalRough==0?0f:1f);
                    GLES20.glUniform1f(uMetallic,geom.metalFactor);
                    GLES20.glUniform1f(uRoughness,geom.roughFactor);
                    GLES20.glActiveTexture(GLES20.GL_TEXTURE2);
                    GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,geom.normalMap);
                    GLES20.glUniform1i(uNormalTexture,2);
                    GLES20.glUniform1f(uUseNormal,geom.normalMap==0||disableNormal?0f:1f);
                    GLES20.glActiveTexture(GLES20.GL_TEXTURE3);
                    GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,geom.aoMap);
                    GLES20.glUniform1i(uAOTexture,3);
                    GLES20.glUniform1f(uUseAO,geom.aoMap==0?0f:1f);
                    GLES20.glEnableVertexAttribArray(aUv);
                    GLES20.glEnableVertexAttribArray(aTangent);
                    GLES20.glEnableVertexAttribArray(aBitangent);
                    GLES20.glVertexAttribPointer(aTangent,3,GLES20.GL_FLOAT,false,0,geom.tangents);
                    GLES20.glVertexAttribPointer(aBitangent,3,GLES20.GL_FLOAT,false,0,geom.bitangents);
                    GLES20.glVertexAttribPointer(aUv,2,GLES20.GL_FLOAT,false,0,geom.texcoords);
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
            if("vq_m30_patch".equals(filter))
                Log.i(TAG,"M30_NORMAL_MAP_DRAW asset="+filter+" active_normal="+
                    (texNormalCount>0&&!disableNormal)+" triangles="+drawn);
            Log.i(TAG,"FRAME_OK asset="+filter+" instances="+visible+" triangles="+drawn+
                    " yaw="+yaw+" pitch="+pitch+" size="+width+"x"+height);
        }
    }
}
