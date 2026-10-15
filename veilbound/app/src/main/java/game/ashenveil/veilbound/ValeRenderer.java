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
    private int program,skyProgram,aPos,aNormal,aColor,uMvp,uModel,uTint,uEye,uGlow,uFog,uSurface,uStudioMode,uStudioMaterial,uStudioLight;
    private int skyPos,skyClock,detailTexture,uDetail;
    private Mesh staticWorld,studioWorld,studioChapel,cube,octa,wardenModel,hushedModel,bossModel,swordModel,greatswordModel,lanternModel;
    private Mesh studioWarden,studioHushed,studioBoss,studioSword,studioGreatsword,studioLantern;
    private FloatBuffer skyVertices;
    private int screenWidth=1,screenHeight=1;
    private long previous=0;
    private float qualityClock=0,fps=60;
    private int frames=0;
    private int drawCalls=0;
    private int lastGlError=GLES20.GL_NO_ERROR;
    private float cx,cy,cz;
    private final float[] fogColor={.125f,.159f,.189f};

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
        "uniform vec3 uFog; uniform float uGlow; uniform float uSurface; "+
        "uniform sampler2D uDetail; uniform float uStudioMode; "+
        "uniform float uStudioMaterial; uniform vec3 uStudioLight; "+
        "float grit(vec3 p){return fract(sin(dot(p,vec3(19.17,71.31,43.89)))*43758.5453);} "+
        "void main(){vec3 n=normalize(vNormal); "+
        "float sun=max(dot(n,normalize(vec3(-.45,.79,-.28))),0.); "+
        "float fill=max(dot(n,normalize(vec3(.72,.32,.29))),0.); "+
        "float wear=mix(1.,.84+.21*grit(floor(vWorld*5.5)),uSurface); "+
        "if(uSurface>.5){vec3 an=abs(n);vec2 uv=an.y>.65?vWorld.xz*.28:"+
        "(an.x>an.z?vWorld.zy*.28:vWorld.xy*.28);"+
        "float detail=texture2D(uDetail,uv).r;"+
        "wear*=.55+detail*1.15;} "+
        "float seam=step(.966,fract(vWorld.y*2.5)); "+
        "wear*=1.-uSurface*seam*.13; "+
        "float rim=pow(1.-max(dot(n,normalize(uEye-vWorld)),0.),2.)*.18; "+
        "vec3 warmth=vec3(1.12,.91,.70)*sun*.72; "+
        "vec3 cold=vec3(.46,.65,.88)*fill*.18; "+
        "vec3 col=vColor*uTint*wear*(vec3(.27,.32,.37)+warmth+cold+rim); "+
        "col+=uGlow*vColor*uTint*.65; "+
        "vec3 ember=vWorld-vec3(-4.4,1.4,11.);"+
        "float emberGlow=1./(1.+dot(ember,ember)*.23);"+
        "col+=vec3(.85,.28,.08)*emberGlow*.90; "+
        "float d=distance(uEye,vWorld); "+
        "float fog=clamp((d-13.)/67.,0.,.87); "+
        "fog+=clamp((2.-vWorld.y)*.045,0.,.13)*clamp(d/27.,0.,1.);"+
        "fog=clamp(fog,0.,.90); "+
        "fog=fog*fog*(3.-2.*fog); "+
        "if(uStudioMode>.5){"+
        "float key=max(dot(n,normalize(uStudioLight)),0.);"+
        "float bounce=max(dot(n,normalize(vec3(.3,.35,-.7))),0.);"+
        "vec3 tint=vec3(.15,.16,.18)+key*vec3(.90,.83,.73)+bounce*vec3(.16,.24,.32);"+
        "col=vColor*uTint*tint + uGlow*vColor*.30;"+
        "if(uStudioMaterial>.5&&uStudioMaterial<1.5)col=vColor*uTint;"+
        "if(uStudioMaterial>1.5&&uStudioMaterial<2.5)col=vec3(.012,.015,.025);"+
        "if(uStudioMaterial>2.5)col=n*.5+.5;"+
        "gl_FragColor=vec4(col,1.);return;}"+
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
        uSurface=GLES20.glGetUniformLocation(program,"uSurface");
        uDetail=GLES20.glGetUniformLocation(program,"uDetail");
        uStudioMode=GLES20.glGetUniformLocation(program,"uStudioMode");
        uStudioMaterial=GLES20.glGetUniformLocation(program,"uStudioMaterial");
        uStudioLight=GLES20.glGetUniformLocation(program,"uStudioLight");
        skyPos=GLES20.glGetAttribLocation(skyProgram,"aPos");
        skyClock=GLES20.glGetUniformLocation(skyProgram,"uTime");
        skyVertices=allocate(new float[]{-1,-1,1,-1,-1,1,1,1});
        initDetailTexture();
        cube=makeCube();octa=makeOcta();
        wardenModel=new Mesh(ArtKit.bellwarden().vertices);
        hushedModel=new Mesh(ArtKit.hushed().vertices);
        bossModel=new Mesh(ArtKit.ashKnight().vertices);
        swordModel=new Mesh(ArtKit.sword().vertices);
        greatswordModel=new Mesh(ArtKit.greatsword().vertices);
        lanternModel=new Mesh(ArtKit.lantern().vertices);
        staticWorld=buildWorld();
        studioWorld=buildStudioStage();
        studioChapel=buildStudioChapel();
        previous=System.nanoTime();
        Log.i(TAG,"OpenGL ES active; static scene vertices="+staticWorld.count+
              " actor_verts="+(wardenModel.count+hushedModel.count+bossModel.count)+
              " mesh_tris="+(wardenModel.count+hushedModel.count+bossModel.count)/3);
    }
    @Override public void onSurfaceChanged(GL10 ignored,int w,int h){
        screenWidth=Math.max(1,w);screenHeight=Math.max(1,h);
        GLES20.glViewport(0,0,screenWidth,screenHeight);
        Matrix.perspectiveM(projection,0,64f,(float)screenWidth/screenHeight,.12f,148f);
    }
    @Override public void onDrawFrame(GL10 ignored){
        long now=System.nanoTime();
        float actualDt=Math.max(.0001f,Math.min((now-previous)*1e-9f,.25f));
        float dt=Math.max(.001f,Math.min(actualDt,.044f));
        previous=now;
        state.update(dt);
        qualityClock+=actualDt;frames++;
        drawCalls=0;
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT|GLES20.GL_DEPTH_BUFFER_BIT);
        renderSky();
        if("lab".equals(state.snapshot().mode)){
            renderStudio();
            sampleFrameQuality();
            return;
        }
        float yaw=state.cameraYaw;
        cx=state.x-(float)Math.sin(yaw)*8.4f;
        cy=terrain(state.x,state.z)+4.35f;
        cz=state.z-(float)Math.cos(yaw)*8.4f;
        Matrix.setLookAtM(view,0,cx,cy,cz,state.x,terrain(state.x,state.z)+1.3f,
                state.z+1.6f,0,1,0);
        Matrix.multiplyMM(vp,0,projection,0,view,0);
        GLES20.glUseProgram(program);
        GLES20.glActiveTexture(GLES20.GL_TEXTURE0);
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,detailTexture);
        GLES20.glUniform1i(uDetail,0);
        GLES20.glUniform3f(uEye,cx,cy,cz);
        GLES20.glUniform1f(uStudioMode,0f);
        GLES20.glUniform1f(uStudioMaterial,0f);
        GLES20.glUniform3f(uStudioLight,-.40f,.83f,-.3f);
        GLES20.glUniform3f(uFog,fogColor[0],fogColor[1],fogColor[2]);
        drawStatic();
        drawAnimatedObjects();
        sampleFrameQuality();
    }
    private void sampleFrameQuality(){
        // Throttled diagnostics feed automated visual QA without per-frame
        // logcat overhead or lying about FPS when simulation clamps dt.
        if(qualityClock>1.35f){
            fps=frames/qualityClock;
            frames=0;qualityClock=0;
            lastGlError=GLES20.glGetError();
            Log.i(TAG,"FRAME_QA fps="+String.format(java.util.Locale.US,"%.1f",fps)+
                  " draws="+drawCalls+" static_vertices="+staticWorld.count+
                  " gl_error="+lastGlError);
        }
    }
    /**
     * Isolated model inspection stage with independent camera and materials.
     * Switching here does not simulate combat or alter the RPG world.
     */
    private void initStudioHighDetail(){
        if(studioWarden!=null)return;
        long start=System.nanoTime();
        studioWarden=new Mesh(DetailArtKit.bellwarden().vertices);
        studioHushed=new Mesh(DetailArtKit.hushed().vertices);
        studioBoss=new Mesh(DetailArtKit.ashKnight().vertices);
        studioSword=new Mesh(DetailArtKit.sword().vertices);
        studioGreatsword=new Mesh(DetailArtKit.greatsword().vertices);
        studioLantern=new Mesh(DetailArtKit.lantern().vertices);
        int triangles=(studioWarden.count+studioHushed.count+studioBoss.count+
                       studioSword.count+studioGreatsword.count+studioLantern.count)/3;
        long timeMs=(System.nanoTime()-start)/1000000L;
        Log.i("VEILBOUND_STUDIO","DETAIL_MESH_READY triangles="+triangles+
              " bellwarden_vertices="+studioWarden.count+
              " ash_knight_vertices="+studioBoss.count+" time_ms="+timeMs);
    }
    private void renderStudio(){
        initStudioHighDetail();
        ModelStudio.Snapshot m=state.studio.snapshot();
        float pitch=m.pitch,yaw=m.yaw;
        float horizontal=m.zoom*(float)Math.cos(pitch);
        float targetY=(m.item==2?2.0f:(m.item==3||m.item==4?1.3f:1.50f))+m.panY;
        float targetX=m.panX;
        cx=targetX+(float)Math.sin(yaw)*horizontal;
        cy=targetY+(float)Math.sin(pitch)*m.zoom;
        cz=(float)Math.cos(yaw)*horizontal;
        Matrix.setLookAtM(view,0,cx,cy,cz,targetX,targetY,0,0,1,0);
        Matrix.multiplyMM(vp,0,projection,0,view,0);
        GLES20.glUseProgram(program);
        GLES20.glActiveTexture(GLES20.GL_TEXTURE0);
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,detailTexture);
        GLES20.glUniform1i(uDetail,0);
        GLES20.glUniform3f(uEye,cx,cy,cz);
        GLES20.glUniform1f(uStudioMode,1f);
        GLES20.glUniform1f(uStudioMaterial,m.material);
        if(m.light==0)GLES20.glUniform3f(uStudioLight,-.45f,.82f,.27f);
        if(m.light==1)GLES20.glUniform3f(uStudioLight,.31f,.74f,-.46f);
        if(m.light==2)GLES20.glUniform3f(uStudioLight,-.68f,.20f,.60f);
        if(m.light==3)GLES20.glUniform3f(uStudioLight,.77f,.39f,-.64f);
        GLES20.glUniform3f(uFog,.08f,.11f,.13f);
        GLES20.glUniform1f(uSurface,1f);
        Matrix.setIdentityM(model,0);
        draw(studioWorld,model,1,1,1,0f);
        GLES20.glUniform1f(uSurface,0f);
        Mesh chosen;
        switch(m.item){
            case 0:chosen=studioWarden;break;
            case 1:chosen=studioHushed;break;
            case 2:chosen=studioBoss;break;
            case 3:chosen=studioSword;break;
            case 4:chosen=studioGreatsword;break;
            case 5:chosen=studioLantern;break;
            default:chosen=studioChapel;
        }
        Matrix.setIdentityM(model,0);
        if(m.item==3||m.item==4)Matrix.translateM(model,0,0,.35f,0);
        else if(m.item==5)Matrix.scaleM(model,0,2.4f,2.4f,2.4f);
        else if(m.item==2)Matrix.scaleM(model,0,1.12f,1.12f,1.12f);
        draw(chosen,model,1,1,1,.06f);
        if(m.item<3){
            // Paired weapon on a measured side pedestal; compare material scale.
            drawCube(3.30f,.30f,0,1.1f,.6f,1.1f,.42f,.43f,.45f,0,0);
            Matrix.setIdentityM(model,0);
            Matrix.translateM(model,0,3.3f,.9f,0);
            draw(m.item==2?studioGreatsword:studioSword,model,1,1,1,.08f);
        }
    }
    private Mesh buildStudioStage(){
        Builder b=new Builder();
        // Inlaid checker floor, radial calibration ticks and buttressed hall.
        b.box(0,-.24f,0,20f,.28f,20f,.24f,.27f,.30f);
        for(int i=-10;i<10;i++)for(int j=-10;j<10;j++){
            if((i+j)%2==0)
                b.box(i+.5f,-.08f,j+.5f,.985f,.045f,.985f,
                      .30f,.31f,.34f);
        }
        b.column(0,-.06f,0,2.10f,.68f,.40f,.42f,.45f);
        b.box(0,.70f,0,4.40f,.11f,4.40f,.68f,.57f,.43f);
        for(int k=0;k<32;k++){
            float a=k*(float)(2*Math.PI/32);
            float x=2.05f*(float)Math.sin(a),z=2.05f*(float)Math.cos(a);
            b.box(x,.77f,z,.16f,.075f,.36f,.79f,.63f,.38f);
        }
        for(int i=-1;i<=1;i+=2){
            for(int j=-1;j<=1;j+=2){
                float x=i*7.7f,z=j*7.2f;
                b.column(x,-.08f,z,.72f,6.70f,.38f,.40f,.42f);
                b.rock(x,6.62f,z,.65f,2.2f,.51f,.52f,.51f);
            }
        }
        return b.mesh();
    }
    private Mesh buildStudioChapel(){
        Builder b=new Builder();
        b.box(0,2.2f,0,4.7f,4.5f,7.4f,.47f,.50f,.51f);
        b.pitchedRoof(0,4.5f,0,6.0f,8.1f,2.2f,.27f,.30f,.35f);
        for(int side=-1;side<=1;side+=2){
            for(int i=0;i<4;i++){
                float z=-3.1f+i*2.1f;
                b.column(side*2.55f,-.2f,z,.31f,4.4f,.42f,.44f,.46f);
            }
        }
        for(int i=0;i<3;i++)b.chapelWindow(2.39f,2.65f,-2.2f+i*2.0f);
        // Hand-laid overlapping slate tiles and worn eaves.
        for(int side=-1;side<=1;side+=2){
            for(int row=0;row<12;row++){
                for(int col=0;col<24;col++){
                    float zz=-3.86f+(col+.5f)*.335f;
                    float xx=side*(.17f+row*.246f);
                    float yy=6.65f-row*.187f;
                    float lift=.016f*(float)Math.sin(row*1.82f+col*2.38f);
                    b.box(xx,yy+lift,zz,.29f,.046f,.39f,
                        .31f+row*.004f,.34f,.39f);
                }
            }
        }
        for(int k=0;k<16;k++){
            float a=k*(float)(2*Math.PI/16);
            b.branch(.71f*(float)Math.cos(a),4.1f+.71f*(float)Math.sin(a),3.89f,
                .71f*(float)Math.cos(a+.39f),4.1f+.71f*(float)Math.sin(a+.39f),3.89f,
                .060f,.77f,.62f,.39f);
        }
        b.box(0,2.1f,3.73f,2.0f,3.4f,.22f,.35f,.38f,.41f);
        b.column(-1.2f,0,3.87f,.20f,3.9f,.53f,.54f,.55f);
        b.column(1.2f,0,3.87f,.20f,3.9f,.53f,.54f,.55f);
        return b.mesh();
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
        GLES20.glUniform1f(uSurface,1f);
        draw(staticWorld,model,1,1,1,0);
        GLES20.glUniform1f(uSurface,0f);
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
        // Pilgrim's road: distant lamps and weathered bell fragments.
        for(int i=0;i<8;i++){
            float z=7+i*7.25f;
            int side=i%2==0?-1:1;
            float x=side*7.7f;
            float base=terrain(x,z);
            Matrix.setIdentityM(model,0);
            Matrix.translateM(model,0,x,base+.12f,z);
            Matrix.scaleM(model,0,.82f,1.22f,.82f);
            draw(lanternModel,model,.62f,.67f,.75f,.09f);
            drawOcta(x,base+1.61f,z,.19f,.43f,.19f,
                     i%3==0?.45f:.96f,i%3==0?.67f:.50f,.30f,
                     1.4f+(float)Math.sin(tm*2.5f+i)*.4f,tm*17);
        }
        // Ancient toll gate rune-glass suspended at the far causeway.
        for(int i=0;i<5;i++){
            float r=1.2f+i*.14f,a=i*1.2566f+tm*.08f;
            drawOcta((float)Math.sin(a)*r,7.7f+(float)Math.cos(a)*r*.8f,48f,
                     .12f,.34f,.12f,.63f,.74f,.73f,1.1f,tm*13);
        }
        // Relic runes and occasional blue motes invite exploration.
        drawOcta(6.1f,terrain(6.1f,19)+1.9f,19,.21f,.46f,.21f,.28f,.8f,1f,1.7f,tm*9);
        // Fused custom character models with distinct armor, skeletal and boss silhouettes;
        // weapon pivot is animated independently to keep attack timing readable.
        drawKnight(state.x,terrain(state.x,state.z),state.z,state.heading,
                false,false,tm,state.walkPhase,state.swing,state.dodge);
        for(WorldState.Foe foe:state.foes){
            if(!foe.alive||(foe.boss&&!state.bossTriggered))continue;
            float ang=(float)Math.atan2(state.x-foe.x,state.z-foe.z);
            float tellSwing=foe.windup>0
                ? .57f*foe.windup/(foe.boss?.92f:.72f):0f;
            drawKnight(foe.x,terrain(foe.x,foe.z),foe.z,ang,true,foe.boss,
                    tm,foe.phase,tellSwing,0);
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
    /**
     * One fused, individually sculpted mesh per actor and one independently
     * animated blade. Replaces 25+ cuboid draw calls with two mesh draw calls.
     * The user gains more defined helmets, cloaks, bodies and boss silhouettes
     * without making the GPU traverse dozens of individual armor cuboids.
     */
    private void drawKnight(float x,float y,float z,float yaw,boolean foe,
                            boolean boss,float tm,float walk,float swing,float dodge){
        float bob=(float)Math.sin(walk*1.4f)*.038f;
        float scale=boss?1.13f:1f;
        Mesh actor=boss?bossModel:(foe?hushedModel:wardenModel);
        Matrix.setIdentityM(model,0);
        Matrix.translateM(model,0,x,y+bob,z);
        Matrix.rotateM(model,0,(float)Math.toDegrees(yaw),0,1,0);
        if(dodge>0)Matrix.rotateM(model,0,Math.min(13f,dodge*28f),1,0,0);
        if(boss)Matrix.scaleM(model,0,scale,scale,scale);
        draw(actor,model,1,1,1,foe?.03f:0);
        // Animated sword pivot; purple-blue steel player versus iron boss.
        float phase=swing>0
            ?(float)Math.sin((.57f-swing)/.57f*Math.PI):0f;
        Matrix.setIdentityM(model,0);
        Matrix.translateM(model,0,x,y+bob,z);
        Matrix.rotateM(model,0,(float)Math.toDegrees(yaw),0,1,0);
        if(boss){
            Matrix.translateM(model,0,1.43f,1.15f,.21f);
            Matrix.rotateM(model,0,-14+phase*115,0,0,1);
            Matrix.scaleM(model,0,1.0f,1.0f,1.0f);
            draw(greatswordModel,model,.86f,.84f,.84f,.11f);
        }else{
            Matrix.translateM(model,0,.84f,1.05f,.28f);
            Matrix.rotateM(model,0,-9+phase*128,0,0,1);
            Matrix.scaleM(model,0,.82f,.92f,.82f);
            draw(swordModel,model,foe?.72f:1f,foe?.65f:1f,foe?.64f:1f,foe?0:.08f);
        }
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
        drawCalls++;
        GLES20.glDisableVertexAttribArray(aPos);
        GLES20.glDisableVertexAttribArray(aNormal);
        GLES20.glDisableVertexAttribArray(aColor);
    }
    private void initDetailTexture(){
        byte[] rgba=MaterialTextures.stoneRgba();
        ByteBuffer pixels=ByteBuffer.allocateDirect(rgba.length)
            .order(ByteOrder.nativeOrder());
        pixels.put(rgba);pixels.position(0);
        int[] handles=new int[1];
        GLES20.glGenTextures(1,handles,0);
        detailTexture=handles[0];
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,detailTexture);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MIN_FILTER,
                             GLES20.GL_LINEAR_MIPMAP_LINEAR);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MAG_FILTER,
                             GLES20.GL_LINEAR);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_WRAP_S,
                             GLES20.GL_REPEAT);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_WRAP_T,
                             GLES20.GL_REPEAT);
        GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D,0,GLES20.GL_RGBA,
                            MaterialTextures.SIZE,MaterialTextures.SIZE,0,
                            GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,pixels);
        GLES20.glGenerateMipmap(GLES20.GL_TEXTURE_2D);
        Log.i(TAG,"STONE_MATERIAL size="+MaterialTextures.SIZE+
                  " gpu_bytes="+(rgba.length*4/3));
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
        /** Organic tapered twig cylinder between arbitrary 3D endpoints. */
        void branch(float ax,float ay,float az,float bx,float by,float bz,
                    float radius,float r,float g,float blue){
            float dx=bx-ax,dy=by-ay,dz=bz-az;
            float length=(float)Math.sqrt(dx*dx+dy*dy+dz*dz);
            if(length<.01f)return;
            dx/=length;dy/=length;dz/=length;
            float ux=-dz,uy=0,uz=dx;
            float un=(float)Math.sqrt(ux*ux+uy*uy+uz*uz);
            if(un<.05f){ux=1;uy=0;uz=0;}
            else{ux/=un;uz/=un;}
            float vx=dy*uz-dz*uy,vy=dz*ux-dx*uz,vz=dx*uy-dy*ux;
            for(int i=0;i<7;i++){
                float a=(float)(2*Math.PI*i/7),bb=(float)(2*Math.PI*(i+1)/7);
                float c0=(float)Math.cos(a),s0=(float)Math.sin(a);
                float c1=(float)Math.cos(bb),s1=(float)Math.sin(bb);
                float ra=radius,rb=radius*.58f;
                float[] p=v(ax+(ux*c0+vx*s0)*ra,ay+(uy*c0+vy*s0)*ra,az+(uz*c0+vz*s0)*ra);
                float[] q=v(bx+(ux*c0+vx*s0)*rb,by+(uy*c0+vy*s0)*rb,bz+(uz*c0+vz*s0)*rb);
                float[] r0=v(bx+(ux*c1+vx*s1)*rb,by+(uy*c1+vy*s1)*rb,bz+(uz*c1+vz*s1)*rb);
                float[] s=v(ax+(ux*c1+vx*s1)*ra,ay+(uy*c1+vy*s1)*ra,az+(uz*c1+vz*s1)*ra);
                quad(p,q,r0,s,r*(.80f+.03f*i),g*(.82f+.02f*i),blue*(.80f+.025f*i));
            }
        }
        /** Small sculpted Gothic window, two pointed panes and copper tracery. */
        void chapelWindow(float x,float y,float z){
            // x is the side wall coordinate; all panels lie in a Y/Z plane.
            quad(v(x,y-.85f,z-.54f),v(x,y-.85f,z+.54f),
                 v(x,y+.57f,z+.54f),v(x,y+.57f,z-.54f),.11f,.17f,.20f);
            quad(v(x+.02f,y-.70f,z-.39f),v(x+.02f,y-.70f,z+.39f),
                 v(x+.02f,y+.44f,z+.39f),v(x+.02f,y+.44f,z-.39f),.67f,.50f,.24f);
            branch(x+.05f,y-.78f,z,x+.05f,y+.66f,z,.045f,.39f,.43f,.46f);
            branch(x+.05f,y+.66f,z,x+.05f,y+.28f,z-.45f,.052f,.44f,.49f,.52f);
            branch(x+.05f,y+.66f,z,x+.05f,y+.28f,z+.45f,.052f,.44f,.49f,.52f);
        }
                // Octagonal columns use facets instead of squared voxel silhouettes.
        void column(float x,float baseY,float z,float rad,float height,
                    float red,float green,float blue){
            int sides=8;
            for(int i=0;i<sides;i++){
                float a=i*(float)(2*Math.PI/sides),angle2=(i+1)*(float)(2*Math.PI/sides);
                float ca=(float)Math.cos(a),sa=(float)Math.sin(a);
                float cb=(float)Math.cos(angle2),sb=(float)Math.sin(angle2);
                float tint=.88f+.12f*(float)Math.sin(i*1.9+z*.2f);
                quad(v(x+ca*rad,baseY,z+sa*rad),
                     v(x+ca*rad*.89f,baseY+height,z+sa*rad*.89f),
                     v(x+cb*rad*.89f,baseY+height,z+sb*rad*.89f),
                     v(x+cb*rad,baseY,z+sb*rad),
                     red*tint,green*tint,blue*tint);
            }
            box(x,baseY+height+.10f,z,rad*2.22f,.23f,rad*2.22f,
                red*.88f,green*.91f,blue*.93f);
            box(x,baseY+.13f,z,rad*2.3f,.24f,rad*2.3f,
                red*.85f,green*.86f,blue*.89f);
        }
        void rock(float x,float groundY,float z,float rad,float height,
                  float red,float green,float blue){
            int sides=6;
            float apexX=x+rad*.14f,apexZ=z-rad*.24f;
            for(int i=0;i<sides;i++){
                float a=i*(float)(2*Math.PI/sides),next=(i+1)*(float)(2*Math.PI/sides);
                float radius=rad*(.72f+.22f*(float)Math.sin(i*2.71f+x*.03f));
                float nextRad=rad*(.72f+.22f*(float)Math.sin((i+1)*2.71f+x*.03f));
                float[] p=v(x+(float)Math.cos(a)*radius,groundY,
                    z+(float)Math.sin(a)*radius);
                float[] q=v(x+(float)Math.cos(next)*nextRad,groundY,
                    z+(float)Math.sin(next)*nextRad);
                float[] top=v(apexX,groundY+height,apexZ);
                float light=.75f+i*.055f;
                tri(p,top,q,red*light,green*light,blue*light);
            }
        }
        void pitchedRoof(float x,float y,float z,float width,float depth,float rise,
                         float red,float green,float blue){
            float l=x-width*.5f,r=x+width*.5f,n=z-depth*.5f,f=z+depth*.5f;
            quad(v(l,y,n),v(l,y,f),v(x,y+rise,f),v(x,y+rise,n),red,green,blue);
            quad(v(x,y+rise,n),v(x,y+rise,f),v(r,y,f),v(r,y,n),
                 red*.87f,green*.90f,blue*.97f);
            tri(v(l,y,n),v(x,y+rise,n),v(r,y,n),
                red*.68f,green*.67f,blue*.64f);
            tri(v(r,y,f),v(x,y+rise,f),v(l,y,f),
                red*.72f,green*.68f,blue*.66f);
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
        // Moss and ash-touched scree: batch environmental pieces into one
        // static vertex buffer to protect Android performance.
        for(int i=0;i<260;i++){
            float rz=-4+rng.nextFloat()*86f;
            float rx=(rng.nextBoolean()?1f:-1f)*(3.7f+rng.nextFloat()*19f);
            float height=.05f+rng.nextFloat()*.25f;
            float moss=rng.nextFloat();
            float red=moss>.48f?.25f:.42f;
            float green=moss>.48f?.33f:.39f;
            float blue=moss>.48f?.26f:.36f;
            b.rock(rx,terrain(rx,rz)-.38f,rz,
                   .16f+rng.nextFloat()*.72f,height*2.6f,
                   red,green,blue);
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
        // Staggered freestanding perimeter masonry instead of monolithic slabs.
        for(int side=-1;side<=1;side+=2){
            for(int segment=0;segment<4;segment++){
                float zz=17+segment*11f;
                float wx=side*(16.5f+segment*.8f);
                for(int course=0;course<5;course++){
                    float yy=.35f+course*.75f;
                    for(int brick=0;brick<3;brick++){
                        if(rng.nextFloat()<.16f)continue;
                        float bz=zz+(brick-1)*1.65f+(course%2)*.43f;
                        b.box(wx,yy,bz,1.1f,.69f,1.55f,
                            .34f+rng.nextFloat()*.09f,
                            .36f+rng.nextFloat()*.11f,
                            .38f+rng.nextFloat()*.12f);
                    }
                }
                b.box(wx+side*.63f,1.55f,zz,.51f,3.15f,1.0f,.31f,.33f,.36f);
            }
        }
        // A broken chapel to the left, chimney spires and exterior buttresses.
        b.box(-8,2.2f,9,4.1f,5.5f,8.8f,.47f,.47f,.47f);
        b.pitchedRoof(-8,5.24f,9,6.05f,10.2f,2.35f,.25f,.28f,.32f);
        b.box(-8,5.21f,9,5.8f,.24f,10.2f,.40f,.41f,.43f);
        // Masonry buttresses and inset honey-colored windows on the chapel.
        for(int i=0;i<4;i++){
            float zz=5.6f+i*2.2f;
            for(int side=-1;side<=1;side+=2){
                float xx=-8+side*2.53f;
                b.box(xx,2.26f,zz,.59f,4.2f,.75f,.34f,.38f,.40f);
                b.box(xx,4.43f,zz,.74f,.41f,.91f,.50f,.50f,.51f);
            }
        }
        for(int j=0;j<3;j++){
            float zz=6.4f+j*2.55f;
            b.box(-5.90f,3.20f,zz,.13f,1.50f,1.20f,.33f,.36f,.40f);
            b.chapelWindow(-5.78f,3.20f,zz);
        }
        for(int s=-1;s<=1;s+=2){
            b.box(-8+s*2.3f,6.5f,6.8f,.76f,2.4f,.86f,.51f,.51f,.55f);
        }
        // Gravestones: silhouette clusters avoid blocking the playable track.
        for(int i=0;i<95;i++){
            float x=(rng.nextBoolean()?1:-1)*(5f+rng.nextFloat()*15f);
            float z=rng.nextFloat()*72;
            float ht=.6f+rng.nextFloat()*1.25f;
            if(i%4==0){
                b.column(x,terrain(x,z)-.40f,z,.26f,ht,.42f,.46f,.48f);
                b.box(x,terrain(x,z)+ht-.20f,z,.76f,.17f,.32f,.51f,.53f,.54f);
            }else{
                b.box(x,terrain(x,z)+ht*.5f-.35f,z,.47f,ht,.19f,
                      .37f+rng.nextFloat()*.12f,.42f,.46f);
                if(i%5==0)b.box(x,terrain(x,z)+ht*.72f-.35f,z,
                              .91f,.21f,.27f,.44f,.46f,.47f);
            }
        }
        // Hand-authored branching grammar for 52 dead, gnarled trees.
        // Tapered trunks and forked twigs replace three right-angle cuboids.
        for(int i=0;i<52;i++){
            float x=(rng.nextBoolean()?1:-1)*(7+rng.nextFloat()*15);
            float z=-3+rng.nextFloat()*79;
            float ht=2.7f+rng.nextFloat()*3.2f;
            float root=terrain(x,z)-.34f;
            float bend=(rng.nextFloat()-.5f)*.70f;
            b.branch(x,root,z,x+bend,root+ht,z+.31f,.19f,.24f,.21f,.19f);
            for(int arm=0;arm<4;arm++){
                float angle=arm*1.58f+i*.8f;
                float sy=root+ht*(.48f+arm*.115f);
                float bx=x+bend*(sy-root)/ht;
                float ex=bx+(float)Math.cos(angle)*(1.15f+arm*.19f);
                float ez=z+.31f+(float)Math.sin(angle)*(1.25f+arm*.17f);
                float ey=sy+.68f+arm*.10f;
                b.branch(bx,sy,z+.20f,ex,ey,ez,.085f,.28f,.25f,.23f);
                b.branch(ex,ey,ez,ex+(float)Math.cos(angle+.7f)*.59f,
                         ey+.75f,ez+(float)Math.sin(angle+.7f)*.62f,
                         .048f,.31f,.28f,.25f);
            }
        }
        // Monumental rubble, funerary pillars and collapsed bell fragments.
        for(int i=0;i<32;i++){
            float zz=5+i*2.18f;
            float xx=(i%2==0?-1:1)*(9.5f+rng.nextFloat()*9f);
            float size=.34f+rng.nextFloat()*1.1f;
            b.box(xx,terrain(xx,zz)+size*.2f-.35f,zz,
                size,.42f+size*.35f,size*.84f,.40f,.42f,.43f);
            if(i%5==0)b.box(xx,terrain(xx,zz)+size*.78f,zz,.15f,size*.5f,.15f,
                        .59f,.55f,.49f);
        }
        // Foreground fragments of ruined defensive walls.
        for(int z=12;z<64;z+=10){
            float x=(z%20==12)?-17:18;
            b.box(x,1.8f,z,1.6f,4.3f,5.5f,.43f,.44f,.46f);
            for(int i=-2;i<=2;i++){
                if((i+z)%3!=0)b.box(x,4.25f,z+i,1.9f,1.0f,.85f,.43f,.44f,.47f);
            }
        }
        // Scattered two-triangle grass/ash clumps: tiny silhouettes catch side light.
        for(int i=0;i<320;i++){
            float z=-7+rng.nextFloat()*83f;
            float x=(rng.nextBoolean()?1:-1)*(3.25f+rng.nextFloat()*18f);
            float y=terrain(x,z)-.40f;
            float t=.16f+rng.nextFloat()*.32f;
            float dr=.30f+rng.nextFloat()*.12f;
            b.tri(v(x-.14f,y,z),v(x,y+t,z+.06f),v(x+.13f,y,z),
                  dr*.65f,dr*.81f,dr*.65f);
            if(i%3==0)b.tri(v(x,y,z-.12f),v(x+.04f,y+t*.76f,z),
                            v(x+.10f,y,z+.17f),.37f,.39f,.31f);
        }
                // Broken monoliths and tapered basalt outcrops frame the bridge.
        for(int i=0;i<48;i++){
            float zz=8f+rng.nextFloat()*73f;
            float xx=(rng.nextBoolean()?1:-1)*(12f+rng.nextFloat()*12f);
            float rr=.44f+rng.nextFloat()*1.2f;
            b.rock(xx,terrain(xx,zz)-.44f,zz,rr,.6f+rr*1.1f,
                   .31f,.35f,.39f);
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
            b.column(px,-.40f,z,.88f,height,
                stone,.51f,.53f);
            b.box(px,height+.42f,z,2.2f,.76f,2.2f,.36f,.39f,.43f);
            for(int k=0;k<4;k++){
                b.box(px,height*1.0f+1.05f+k*.45f,z,
                    1.12f,.17f,1.10f,.46f,.49f,.50f);
            }
        }
        b.box(x,height+1.5f,z,width+1.9f,2.2f,1.9f,.42f,.43f,.46f);
        // Keystone and weathered voussoirs give the arch its masonry profile.
        for(int i=0;i<9;i++){
            float xx=x+(i-4)*width/8f;
            b.box(xx,height+.80f+(float)Math.abs(i-4)*.15f,z-.15f,
                width/9.5f,.25f,.8f,.52f,.53f,.55f);
        }
        b.box(x,height+2.9f,z-1.07f,1.03f,.95f,.35f,.69f,.59f,.44f);
        for(int i=-5;i<=5;i++){
            if((i+13)%4==0)continue;
            float px=x+i*(width/11f);
            b.box(px,height+2.87f,z,.59f,.75f,1.83f,.50f,.53f,.57f);
        }
    }
}