package game.ashenveil.veilbound;

import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.opengl.Matrix;
import android.util.Log;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.Random;
import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

/** Native OpenGL ES 2.0 third-person renderer; no WebView or HTML. */
public final class ValeRenderer implements GLSurfaceView.Renderer {
    private static final String TAG="VEILBOUND_RENDER";
    private final WorldState state;
    private final float[] projection=new float[16],view=new float[16],vp=new float[16],
                          model=new float[16],mvp=new float[16];
    private int program,skyProgram,aPos,aNormal,aColor,uMvp,uModel,uTint,uEye,uGlow,uFog;
    private int skyPos,skyClock;
    private Mesh staticWorld,cube,octa,needle;
    private FloatBuffer skyVertices;
    private int screenWidth=1,screenHeight=1;
    private long previous=0;
    private float qualityClock=0,fps=60;
    private int frames=0;
    private float cx,cy,cz;
    private final float[] fogColor={.105f,.143f,.185f};

    public ValeRenderer(WorldState s){state=s;}
    public float currentFps(){return fps;}

    private static final String VERTEX=
        "uniform mat4 uMvp; uniform mat4 uModel; attribute vec3 aPos; "+
        "attribute vec3 aNormal; attribute vec3 aColor; "+
        "varying vec3 vNormal; varying vec3 vColor; varying vec3 vWorld; "+
        "void main(){ vec4 w=uModel*vec4(aPos,1.); vWorld=w.xyz; "+
        "vNormal=normalize(mat3(uModel)*aNormal); vColor=aColor; "+
        "gl_Position=uMvp*vec4(aPos,1.); }";
    private static final String FRAGMENT=
        "precision mediump float; varying vec3 vNormal; varying vec3 vColor; "+
        "varying vec3 vWorld; uniform vec3 uTint; uniform vec3 uEye; "+
        "uniform vec3 uFog; uniform float uGlow; "+
        "void main(){vec3 n=normalize(vNormal); "+
        "float sun=max(dot(n,normalize(vec3(-0.42,0.84,-0.31))),0.); "+
        "float rim=pow(1.-max(dot(n,normalize(uEye-vWorld)),0.),2.)*.11; "+
        "float ambient=.32+max(n.y,0.)*.11; "+
        "vec3 col=vColor*uTint*(ambient+sun*.70+rim); "+
        "col+=uGlow*vColor*uTint*.55; "+
        "float d=distance(uEye,vWorld); "+
        "float fog=clamp((d-15.)/78.,0.,.86); "+
        "fog=fog*fog*(3.-2.*fog); "+
        "gl_FragColor=vec4(mix(col,uFog,fog),1.);}";
    private static final String SKY_VERTEX=
        "attribute vec2 aPos; varying vec2 vUv; "+
        "void main(){vUv=aPos*.5+.5;gl_Position=vec4(aPos,1.,1.);}";
    private static final String SKY_FRAGMENT=
        "precision mediump float; varying vec2 vUv;uniform float uTime; "+
        "float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);} "+
        "void main(){float t=pow(vUv.y,1.18); "+
        "vec3 upper=vec3(.015,.028,.060);vec3 horizon=vec3(.19,.21,.23); "+
        "vec3 sky=mix(horizon,upper,smoothstep(.04,1.,t)); "+
        "vec2 moon=(vUv-vec2(.74,.78))*vec2(1.6,1.);"+
        "float md=length(moon);"+
        "sky+=vec3(.35,.42,.47)*smoothstep(.12,.104,md);"+
        "sky+=vec3(.09,.16,.19)*exp(-md*14.)*.55;"+
        "float star=step(.9985,h(floor(vUv*vec2(255.,125.))));"+
        "sky+=star*vec3(.28,.38,.43)*(smoothstep(.32,.87,vUv.y));"+
        "float cloud=sin(vUv.x*12.+uTime*.006)*sin(vUv.y*16.-uTime*.007);"+
        "sky+=vec3(.035,.055,.064)*cloud*cloud*smoothstep(.28,.05,vUv.y);"+
        "gl_FragColor=vec4(sky,1.);}";

    @Override public void onSurfaceCreated(GL10 ignored,EGLConfig config){
        GLES20.glClearColor(.07f,.09f,.13f,1);
        GLES20.glEnable(GLES20.GL_DEPTH_TEST);
        GLES20.glDepthFunc(GLES20.GL_LEQUAL);
        GLES20.glEnable(GLES20.GL_CULL_FACE);
        GLES20.glCullFace(GLES20.GL_BACK);
        program=link(VERTEX,FRAGMENT);
        skyProgram=link(SKY_VERTEX,SKY_FRAGMENT);
        aPos=GLES20.glGetAttribLocation(program,"aPos");
        aNormal=GLES20.glGetAttribLocation(program,"aNormal");
        aColor=GLES20.glGetAttribLocation(program,"aColor");
        uMvp=GLES20.glGetUniformLocation(program,"uMvp");
        uModel=GLES20.glGetUniformLocation(program,"uModel");
        uTint=GLES20.glGetUniformLocation(program,"uTint");
        uEye=GLES20.glGetUniformLocation(program,"uEye");
        uGlow=GLES20.glGetUniformLocation(program,"uGlow");
        uFog=GLES20.glGetUniformLocation(program,"uFog");
        skyPos=GLES20.glGetAttribLocation(skyProgram,"aPos");
        skyClock=GLES20.glGetUniformLocation(skyProgram,"uTime");
        skyVertices=allocate(new float[]{-1,-1,1,-1,-1,1,1,1});
        cube=makeCube();octa=makeOcta();needle=makeNeedle();
        staticWorld=buildWorld();
        previous=System.nanoTime();
        Log.i(TAG,"OpenGL ES active; static scene vertices="+staticWorld.count);
    }
    @Override public void onSurfaceChanged(GL10 ignored,int w,int h){
        screenWidth=Math.max(1,w);screenHeight=Math.max(1,h);
        GLES20.glViewport(0,0,screenWidth,screenHeight);
        Matrix.perspectiveM(projection,0,64f,(float)screenWidth/screenHeight,.12f,148f);
    }
    @Override public void onDrawFrame(GL10 ignored){
        long now=System.nanoTime();
        float dt=Math.max(.001f,Math.min((now-previous)*1e-9f,.044f));
        previous=now;
        state.update(dt);
        qualityClock+=dt;frames++;
        if(qualityClock>1.1f){fps=frames/qualityClock;frames=0;qualityClock=0;}
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT|GLES20.GL_DEPTH_BUFFER_BIT);
        renderSky();
        float yaw=state.cameraYaw;
        cx=state.x-(float)Math.sin(yaw)*8.4f;
        cy=terrain(state.x,state.z)+4.35f;
        cz=state.z-(float)Math.cos(yaw)*8.4f;
        Matrix.setLookAtM(view,0,cx,cy,cz,state.x,terrain(state.x,state.z)+1.3f,
                state.z+1.6f,0,1,0);
        Matrix.multiplyMM(vp,0,projection,0,view,0);
        GLES20.glUseProgram(program);
        GLES20.glUniform3f(uEye,cx,cy,cz);
        GLES20.glUniform3f(uFog,fogColor[0],fogColor[1],fogColor[2]);
        drawStatic();
        drawAnimatedObjects();
        if(state.hurtFlash>0){
            // Hurt feedback remains subtle; native HUD adds stronger warning.
        }
    }
    private void renderSky(){
        GLES20.glDisable(GLES20.GL_DEPTH_TEST);
        GLES20.glDepthMask(false);
        GLES20.glUseProgram(skyProgram);
        GLES20.glEnableVertexAttribArray(skyPos);
        skyVertices.position(0);
        GLES20.glVertexAttribPointer(skyPos,2,GLES20.GL_FLOAT,false,8,skyVertices);
        GLES20.glUniform1f(skyClock,state.time);
        GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP,0,4);
        GLES20.glDisableVertexAttribArray(skyPos);
        GLES20.glDepthMask(true);
        GLES20.glEnable(GLES20.GL_DEPTH_TEST);
    }
    private void drawStatic(){
        Matrix.setIdentityM(model,0);
        draw(staticWorld,model,1,1,1,0);
    }

    private static float terrain(float x,float z) {
        return .12f*(float)(Math.sin(x*.26)*Math.cos(z*.20))
              +.06f*(float)Math.sin(z*.12+x*.16);
    }
    private void drawAnimatedObjects(){
        float tm=state.time;
        // Ember shrine at the edge of the path: fire and pulsing runestone.
        drawCube(-4.4f,terrain(-4.4f,11)+.6f,11,1.5f,1.25f,1.5f,.43f,.47f,.48f,0,0);
        drawOcta(-4.4f,terrain(-4.4f,11)+1.45f+(.08f*(float)Math.sin(tm*3)),11,
                .36f,.72f,.36f,
                state.shrineLit?1f:.58f,state.shrineLit?.51f:.26f,.13f,2.2f,tm*20);
        for(int i=0;i<10;i++){
            float a=(float)(i*2.39996+tm*.57);
            float r=.35f+i*.065f;
            float fy=terrain(-4.4f,11)+.8f+((tm*.58f+i*.17f)%2.8f);
            drawOcta(-4.4f+(float)Math.sin(a)*r,fy,11+(float)Math.cos(a)*r,
                .025f,.065f,.025f,1f,.45f,.16f,2.8f,0);
        }
        // Relic runes and occasional blue motes invite exploration.
        drawOcta(6.1f,terrain(6.1f,19)+1.9f,19,.21f,.46f,.21f,.28f,.8f,1f,1.7f,tm*9);
        // Combatants are rendered as articulated primitive armor; replace with
        // rigged character assets at animation milestone M3.
        drawKnight(state.x,terrain(state.x,state.z),state.z,state.heading,
                false,false,tm,state.walkPhase,state.swing,state.dodge);
        for(WorldState.Foe foe:state.foes){
            if(!foe.alive||(foe.boss&&!state.bossTriggered))continue;
            float ang=(float)Math.atan2(state.x-foe.x,state.z-foe.z);
            drawKnight(foe.x,terrain(foe.x,foe.z),foe.z,ang,true,foe.boss,
                    tm,foe.phase,0,0);
            if(foe.windup>0){
                float t=foe.boss?foe.windup/.92f:foe.windup/.72f;
                float glow=.50f+(1-t)*1.7f;
                drawOcta(foe.x,terrain(foe.x,foe.z)+2.5f,foe.z,
                    foe.boss?.37f:.23f,foe.boss?.37f:.23f,foe.boss?.37f:.23f,
                    1f,.15f,.10f,glow,tm*44);
            }
            if(foe.boss){
                // Thorn-crown boss halo and greatsword silhouette.
                for(int i=0;i<6;i++){
                    float ang2=(float)(i*Math.PI/3+tm*.17);
                    drawOcta(foe.x+(float)Math.sin(ang2)*1.12f,
                        terrain(foe.x,foe.z)+3.6f,
                        foe.z+(float)Math.cos(ang2)*1.12f,
                        .15f,.45f,.15f,.55f,.67f,.75f,1.6f,tm*17);
                }
            }
        }
        // Gate light becomes accessible after the boss falls.
        if(!state.foes[3].alive){
            drawOcta(0,terrain(0,59)+4.5f,59,1.2f,2.3f,1.2f,.7f,.9f,1f,3,tm*13);
        }
    }
    private void drawKnight(float x,float y,float z,float yaw,boolean foe,
                            boolean boss,float tm,float walk,float swing,float dodge){
        float scale=boss?1.46f:1f;
        float c=foe?.38f:.61f;float g=foe?.35f:.53f;float b=foe?.39f:.48f;
        float bob= (float)Math.sin(walk*1.4)*.045f;
        float root=y+bob;
        // Feet and leggings
        drawPart(x,root+.40f*scale,z,-.31f,.42f,0,.36f,.85f,.44f,
                yaw,c*.51f,g*.52f,b*.57f,0);
        drawPart(x,root+.40f*scale,z,.31f,.42f,0,.36f,.85f,.44f,
                yaw,c*.51f,g*.52f,b*.57f,0);
        // Tattered cloak, armored torso and layered gorget.
        drawPart(x,root+1.25f*scale,z,0,0,-.24f,.99f,1.54f,.25f,
                yaw,foe?.12f:.08f,foe?.16f:.21f,foe?.19f:.30f,0);
        drawPart(x,root+1.35f*scale,z,0,0,0,.88f,.97f,.56f,
                yaw,c,g,b,0);
        drawPart(x,root+1.88f*scale,z,0,0,0,.95f,.20f,.72f,
                yaw,foe?.65f:.77f,foe?.36f:.66f,foe?.30f:.57f,.15f);
        // Head and winged helmet; visor darkness makes a readable silhouette.
        drawPart(x,root+2.25f*scale,z,0,0,0,.54f,.62f,.59f,
                yaw,c*.8f,g*.85f,b*.98f,0);
        drawPart(x,root+2.34f*scale,z,0,0,.31f,.41f,.18f,.08f,
                yaw,.035f,.045f,.055f,0);
        for(int side=-1;side<=1;side+=2){
            drawPart(x,root+2.63f*scale,z,side*.30f,0,0,.23f,.38f,.26f,
                    yaw,c*.65f,g*.75f,b*.90f,0);
        }
        float armSwing=(float)Math.sin(walk*1.4f)*.10f;
        drawPart(x,root+1.38f*scale,z,-.65f,armSwing,0,.38f,.90f,.39f,
                yaw,c*.78f,g*.78f,b*.83f,0);
        drawPart(x,root+1.38f*scale,z,.65f,-armSwing,0,.38f,.90f,.39f,
                yaw,c*.72f,g*.69f,b*.72f,0);
        // Sword is attached to right hand; rotation signals active swing.
        float slash=swing>0?(float)Math.sin((.57f-swing)/.57f*Math.PI)*.9f:0;
        drawPart(x,root+1.05f*scale+slash*.36f,z,.79f,0,.4f,.10f,.14f,.72f,
                yaw+.30f+slash, .23f,.19f,.13f,0);
        drawPart(x,root+1.66f*scale+slash*.42f,z,.79f,0,.40f,.15f,1.08f,.10f,
                yaw+.30f+slash,.65f,.76f,.80f,foe?.1f:.20f);
        if(dodge>0)drawOcta(x,root+.35f,z,.58f,.18f,.58f,.28f,.50f,.59f,.25f,tm*60);
    }
    private void drawPart(float x,float y,float z,float ox,float oy,float oz,
                          float sx,float sy,float sz,float yaw,
                          float r,float g,float b,float glow){
        Matrix.setIdentityM(model,0);Matrix.translateM(model,0,x,y,z);
        Matrix.rotateM(model,0,(float)Math.toDegrees(yaw),0,1,0);
        Matrix.translateM(model,0,ox,oy,oz);
        Matrix.scaleM(model,0,sx,sy,sz);
        draw(cube,model,r,g,b,glow);
    }
    private void drawCube(float x,float y,float z,float sx,float sy,float sz,
                          float r,float g,float b,float glow,float angle){
        Matrix.setIdentityM(model,0);Matrix.translateM(model,0,x,y,z);
        Matrix.rotateM(model,0,angle,0,1,0);
        Matrix.scaleM(model,0,sx,sy,sz);
        draw(cube,model,r,g,b,glow);
    }
    private void drawOcta(float x,float y,float z,float sx,float sy,float sz,
                          float r,float g,float b,float glow,float angle){
        Matrix.setIdentityM(model,0);Matrix.translateM(model,0,x,y,z);
        Matrix.rotateM(model,0,angle,0,1,0);
        Matrix.scaleM(model,0,sx,sy,sz);
        draw(octa,model,r,g,b,glow);
    }
    private void draw(Mesh mesh,float[] transformation,float red,float green,float blue,float glow){
        if(mesh==null)return;
        Matrix.multiplyMM(mvp,0,vp,0,transformation,0);
        GLES20.glUniformMatrix4fv(uMvp,1,false,mvp,0);
        GLES20.glUniformMatrix4fv(uModel,1,false,transformation,0);
        GLES20.glUniform3f(uTint,red,green,blue);
        GLES20.glUniform1f(uGlow,glow);
        mesh.data.position(0);GLES20.glEnableVertexAttribArray(aPos);
        GLES20.glVertexAttribPointer(aPos,3,GLES20.GL_FLOAT,false,36,mesh.data);
        mesh.data.position(3);GLES20.glEnableVertexAttribArray(aNormal);
        GLES20.glVertexAttribPointer(aNormal,3,GLES20.GL_FLOAT,false,36,mesh.data);
        mesh.data.position(6);GLES20.glEnableVertexAttribArray(aColor);
        GLES20.glVertexAttribPointer(aColor,3,GLES20.GL_FLOAT,false,36,mesh.data);
        GLES20.glDrawArrays(GLES20.GL_TRIANGLES,0,mesh.count);
        GLES20.glDisableVertexAttribArray(aPos);
        GLES20.glDisableVertexAttribArray(aNormal);
        GLES20.glDisableVertexAttribArray(aColor);
    }
    private static int shader(int type,String code){
        int id=GLES20.glCreateShader(type);
        GLES20.glShaderSource(id,code);GLES20.glCompileShader(id);
        int[] ok=new int[1];GLES20.glGetShaderiv(id,GLES20.GL_COMPILE_STATUS,ok,0);
        if(ok[0]==0)throw new IllegalStateException(GLES20.glGetShaderInfoLog(id));
        return id;
    }
    private static int link(String vertex,String fragment){
        int program=GLES20.glCreateProgram();
        GLES20.glAttachShader(program,shader(GLES20.GL_VERTEX_SHADER,vertex));
        GLES20.glAttachShader(program,shader(GLES20.GL_FRAGMENT_SHADER,fragment));
        GLES20.glLinkProgram(program);
        int[] ok=new int[1];GLES20.glGetProgramiv(program,GLES20.GL_LINK_STATUS,ok,0);
        if(ok[0]==0)throw new IllegalStateException(GLES20.glGetProgramInfoLog(program));
        return program;
    }
    private static FloatBuffer allocate(float[] v){
        FloatBuffer b=ByteBuffer.allocateDirect(v.length*4).order(ByteOrder.nativeOrder()).asFloatBuffer();
        b.put(v);b.position(0);return b;
    }
    private static final class Mesh {
        final FloatBuffer data;final int count;
        Mesh(float[] vertices){data=allocate(vertices);count=vertices.length/9;}
    }
    private static final class Builder {
        private float[] a=new float[4096];private int len=0;
        private void append(float x,float y,float z,float nx,float ny,float nz,
                            float r,float g,float b){
            if(len+9>a.length){float[] next=new float[a.length*2];System.arraycopy(a,0,next,0,len);a=next;}
            float[] f={x,y,z,nx,ny,nz,r,g,b};
            for(float c:f)a[len++]=c;
        }
        void tri(float[] p,float[] q,float[] r,float cr,float cg,float cb){
            float ux=q[0]-p[0],uy=q[1]-p[1],uz=q[2]-p[2];
            float vx=r[0]-p[0],vy=r[1]-p[1],vz=r[2]-p[2];
            float nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
            float norm=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(norm<.0001f)return;
            nx/=norm;ny/=norm;nz/=norm;
            append(p[0],p[1],p[2],nx,ny,nz,cr,cg,cb);
            append(q[0],q[1],q[2],nx,ny,nz,cr,cg,cb);
            append(r[0],r[1],r[2],nx,ny,nz,cr,cg,cb);
        }
        void quad(float[] p,float[] q,float[] r,float[] s,float cr,float cg,float cb){
            tri(p,q,r,cr,cg,cb);tri(p,r,s,cr,cg,cb);
        }
        void box(float x,float y,float z,float w,float h,float d,float red,float green,float blue){
            float l=x-w*.5f,r=x+w*.5f,b=y-h*.5f,t=y+h*.5f,n=z-d*.5f,f=z+d*.5f;
            // Visible exterior faces wound consistently counterclockwise.
            quad(v(l,b,f),v(r,b,f),v(r,t,f),v(l,t,f),red,green,blue);
            quad(v(r,b,n),v(l,b,n),v(l,t,n),v(r,t,n),red*.86f,green*.86f,blue*.86f);
            quad(v(l,b,n),v(l,b,f),v(l,t,f),v(l,t,n),red*.78f,green*.78f,blue*.78f);
            quad(v(r,b,f),v(r,b,n),v(r,t,n),v(r,t,f),red*.93f,green*.93f,blue*.93f);
            quad(v(l,t,f),v(r,t,f),v(r,t,n),v(l,t,n),red*1.12f,green*1.12f,blue*1.12f);
            quad(v(l,b,n),v(r,b,n),v(r,b,f),v(l,b,f),red*.60f,green*.60f,blue*.60f);
        }
        Mesh mesh(){float[] v=new float[len];System.arraycopy(a,0,v,0,len);return new Mesh(v);}
    }
    private static float[] v(float x,float y,float z){return new float[]{x,y,z};}
    private static Mesh makeCube(){Builder b=new Builder();b.box(0,0,0,1,1,1,1,1,1);return b.mesh();}
    private static Mesh makeOcta(){
        Builder b=new Builder();
        float[] top=v(0,.5f,0),bot=v(0,-.5f,0);
        float[][] eq={v(.5f,0,0),v(0,0,.5f),v(-.5f,0,0),v(0,0,-.5f)};
        for(int i=0;i<4;i++){int j=(i+1)%4;b.tri(top,eq[i],eq[j],1,1,1);b.tri(bot,eq[j],eq[i],.7f,.85f,.95f);}
        return b.mesh();
    }
    private static Mesh makeNeedle(){return makeOcta();}
    private Mesh buildWorld(){
        Builder b=new Builder();Random rng=new Random(7249);
        for(int ix=-22;ix<22;ix++){
            for(int iz=-14;iz<90;iz+=2){
                float x=ix,z=iz;
                float y=terrain(x,z)-.42f;
                float r=.27f+(rng.nextFloat()-.5f)*.055f;
                float g=.30f+(rng.nextFloat()-.5f)*.065f;
                float bb=.295f+(rng.nextFloat()-.5f)*.045f;
                float pathDist=Math.abs(x-(float)Math.sin(z*.10f)*1.4f);
                if(pathDist<3.2f){r=.34f;g=.32f;bb=.285f;}
                float dx=1,dz=2;
                b.quad(v(x,y,z),v(x+dx,terrain(x+dx,z)-.42f,z),
                       v(x+dx,terrain(x+dx,z+dz)-.42f,z+dz),
                       v(x,terrain(x,z+dz)-.42f,z+dz),r,g,bb);
            }
        }
        // Worn paving broken across the pilgrimage road, including deliberate gaps.
        for(int z=4;z<69;z+=3){
            for(int row=-2;row<=2;row++){
                float x=row*1.42f+.35f*(float)Math.sin(z*.23);
                if(rng.nextFloat()<.19f)continue;
                b.box(x,terrain(x,z)-.18f,z+.3f,1.22f,.22f,2.35f,
                    .47f+rng.nextFloat()*.07f,.45f,.45f);
            }
        }
        // Chapter landmark: the broken bell tower across the northern horizon.
        ruinTower(b,0,72,8.5f,17.5f,rng);
        ruinTower(b,-15,64,5.8f,11.3f,rng);
        ruinTower(b,16,66,5.8f,12.3f,rng);
        // Cathedral walls and arches mark successive story beats.
        for(int z: new int[]{22,40,47}){
            arch(b,0,z,8.5f,6.1f);
        }
        for(int z=20;z<59;z+=8){
            for(int s=-1;s<=1;s+=2){
                float x=s*13.5f;
                if(rng.nextFloat()<.25f)continue;
                b.box(x,2.1f,z,1.65f,4.9f,1.65f,.46f,.48f,.51f);
                b.box(x,4.9f,z,2f,.48f,2f,.55f,.56f,.57f);
                if(z%16==4){
                    b.box(x,6.1f,z,.9f,2.5f,.9f,.38f,.39f,.42f);
                }
            }
        }
        // A broken chapel to the left, chimney spires and exterior buttresses.
        b.box(-8,2.2f,9,4.1f,5.5f,8.8f,.47f,.47f,.47f);
        b.box(-8,5.2f,9,5f,.55f,9.3f,.38f,.39f,.42f);
        for(int s=-1;s<=1;s+=2){
            b.box(-8+s*2.3f,6.5f,6.8f,.76f,2.4f,.86f,.51f,.51f,.55f);
        }
        // Gravestones: silhouette clusters avoid blocking the playable track.
        for(int i=0;i<95;i++){
            float x=(rng.nextBoolean()?1:-1)*(5f+rng.nextFloat()*15f);
            float z=rng.nextFloat()*72;
            float ht=.6f+rng.nextFloat()*1.25f;
            b.box(x,terrain(x,z)+ht*.5f-.35f,z,.47f,ht,.19f,
                .37f+rng.nextFloat()*.12f,.42f,.46f);
            if(i%5==0)b.box(x,terrain(x,z)+ht*.72f-.35f,z,.91f,.21f,.27f,.44f,.46f,.47f);
        }
        // The withered grove: trunks, branch candelabra, and wind-torn leaves.
        for(int i=0;i<52;i++){
            float x=(rng.nextBoolean()?1:-1)*(7+rng.nextFloat()*15);
            float z=-3+rng.nextFloat()*79;
            float ht=2.7f+rng.nextFloat()*3.2f;
            float y=terrain(x,z)+ht*.5f-.28f;
            b.box(x,y,z,.25f,ht,.26f,.29f,.235f,.20f);
            b.box(x+.65f,y+ht*.28f,z,.10f,.14f,1.6f,.28f,.24f,.22f);
            b.box(x-.50f,y+ht*.16f,z,.95f,.14f,.11f,.26f,.22f,.19f);
        }
        // Foreground fragments of ruined defensive walls.
        for(int z=12;z<64;z+=10){
            float x=(z%20==12)?-17:18;
            b.box(x,1.8f,z,1.6f,4.3f,5.5f,.43f,.44f,.46f);
            for(int i=-2;i<=2;i++){
                if((i+z)%3!=0)b.box(x,4.25f,z+i,1.9f,1.0f,.85f,.43f,.44f,.47f);
            }
        }
        // Broad mountains at distance painted with coarse geometric silhouettes.
        for(int i=0;i<22;i++){
            float x=-95+i*9.2f;
            float height=11+(float)Math.abs(Math.sin(i*1.7))*26;
            float z=95+(i%3)*6;
            b.tri(v(x-9,-1,z),v(x,height,z),v(x+10,-1,z),
                  .23f,.27f,.32f);
        }
        return b.mesh();
    }
    private static void ruinTower(Builder b,float x,float z,float radius,float height,Random r){
        float stone=.46f;
        for(int lvl=0;lvl<5;lvl++){
            float y=(lvl+.5f)*height/5;
            float w=radius*(1-lvl*.047f);
            b.box(x,y,z,w,height/5+.02f,w,stone-lvl*.025f,.47f-lvl*.023f,.50f-lvl*.02f);
        }
        b.box(x,height+.2f,z,radius*1.2f,.7f,radius*1.2f,.35f,.38f,.42f);
        for(int s=-1;s<=1;s+=2)
            for(int k=-1;k<=1;k++){
                b.box(x+s*radius*.47f,height+.95f,z+k*radius*.48f,
                      1.3f,1.8f,1.1f,.45f,.48f,.52f);
            }
        b.box(x,height+2f,z,.9f,2.6f,.9f,.51f,.53f,.55f);
    }
    private static void arch(Builder b,float x,float z,float width,float height){
        float stone=.49f;
        for(int sign=-1;sign<=1;sign+=2){
            float px=x+sign*width*.5f;
            b.box(px,height*.47f,z,1.5f,height,1.8f,
                stone,.51f,.53f);
            b.box(px,height+.42f,z,2.2f,.76f,2.2f,.36f,.39f,.43f);
            for(int k=0;k<4;k++){
                b.box(px,height*1.0f+1.05f+k*.45f,z,
                    1.12f,.17f,1.10f,.46f,.49f,.50f);
            }
        }
        b.box(x,height+1.5f,z,width+1.9f,2.2f,1.9f,.42f,.43f,.46f);
        for(int i=-5;i<=5;i++){
            if((i+13)%4==0)continue;
            float px=x+i*(width/11f);
            b.box(px,height+2.87f,z,.59f,.75f,1.83f,.50f,.53f,.57f);
        }
    }
}