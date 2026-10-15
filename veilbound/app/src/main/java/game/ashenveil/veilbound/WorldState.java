package game.ashenveil.veilbound;

import java.util.Arrays;

/**
 * Deterministic Android-free game simulation; OpenGL and Canvas only display
 * state. Camera, hit arc, lock-on and loot are owned by the same simulation.
 */
public final class WorldState {
    public static final int REQUIRED_SIGILS=2;
    public static final class Foe {
        public final String name;
        public float x,z,hp;
        public final float maxHp;
        public final boolean boss;
        public float windup,recovery,stagger,phase,moving,bleed,attackPose;
        public boolean alive=true,counted=false;
        Foe(String name,float x,float z,float hp,boolean boss){
            this.name=name;this.x=x;this.z=z;this.hp=hp;this.maxHp=hp;this.boss=boss;
        }
    }
    public static final class Stain {
        public final float x,z,radius,angle,born;
        Stain(float x,float z,float r,float a,float birth){
            this.x=x;this.z=z;this.radius=r;this.angle=a;this.born=birth;
        }
    }
    public static final class Snapshot {
        public final String mode,message,objective,targetName;
        public final int health,stamina,fragments,foes,totalKills,targetIndex;
        public final float x,z,cameraYaw,bossHealth,swing,dodge,exertion;
        public final boolean shrineLit,bossAlive,dialogue;
        Snapshot(WorldState w){
            mode=w.mode;message=w.message;objective=w.objective();
            health=(int)Math.ceil(w.hp);stamina=(int)Math.ceil(w.stamina);
            fragments=w.fragments;totalKills=w.totalKills;
            int a=0;for(Foe f:w.foes)if(f.alive)a++;foes=a;
            x=w.x;z=w.z;cameraYaw=w.cameraYaw;swing=w.swing;dodge=w.dodge;
            exertion=w.exertion;
            shrineLit=w.shrineLit;bossAlive=w.foes[3].alive;
            bossHealth=w.foes[3].hp;dialogue=w.dialogueTimer>0;
            targetIndex=w.lockTarget;
            targetName=targetIndex>=0?w.foes[targetIndex].name:"";
        }
    }
    public float x=0f,z=3f,heading=0f,cameraYaw=0f,hp=100f,stamina=100f;
    public float swing=0,dodge=0,invulnerable=0,attackTime=0,time=0f;
    public float hurtFlash=0,impactFlash=0,walkPhase=0f,exertion=0f,motionBlend=0f;
    public String mode="title",message="THE BELLS REMEMBER",checkpointMessage="";
    public final ModelStudio studio=new ModelStudio();
    public boolean shrineLit=false,bossTriggered=false;
    public int fragments=0,totalKills=0,lockTarget=-1;
    public final Foe[] foes={
        new Foe("Hushed Watcher",-3.8f,24f,70,false),
        new Foe("Hushed Watcher",4.4f,32f,70,false),
        new Foe("Ashbound Guard",-2f,43f,92,false),
        new Foe("The Ash Knight",0f,54f,260,true)
    };
    public final Stain[] stains=new Stain[44];
    public int stainCount=0;
    public float dialogueTimer=0;
    private float moveX=0,moveY=0,orbitDelta=0;
    private boolean attackQueued=false,rollQueued=false,interactQueued=false,lockQueued=false;
    private final boolean[] swingHit=new boolean[4];
    private float checkpointX=0,checkpointZ=3;
    private float messageTimer=7;
    private float dodgeDx=0,dodgeDz=1;
    private int stainCursor=0,spills=0;

    public synchronized Snapshot snapshot(){return new Snapshot(this);}
    public synchronized void movement(float horizontal,float vertical){
        moveX=CombatMotion.clamp(horizontal,-1,1);
        moveY=CombatMotion.clamp(vertical,-1,1);
    }
    public synchronized void orbit(float delta){orbitDelta+=delta;}
    public synchronized void attack(){attackQueued=true;}
    public synchronized void roll(){rollQueued=true;}
    public synchronized void interact(){interactQueued=true;}
    public synchronized void toggleLock(){lockQueued=true;}

    public synchronized void enterStudio(){mode="lab";studio.reset();}
    public synchronized void exitStudio(){mode="title";}
    public synchronized void start(){
        if(mode.equals("title")){mode="story";message="A kingdom held its breath. One bell still calls to you.";messageTimer=1000;}
        else if(mode.equals("story")){mode="playing";message="FIND THE LAST EMBER";messageTimer=5;}
        else if(mode.equals("dead")){respawn();}
        else if(mode.equals("victory")){mode="title";}
    }
    public synchronized void dismissStory(){
        if(mode.equals("story"))start();
        else if(mode.equals("playing")&&dialogueTimer>0)dialogueTimer=0;
    }
    public synchronized void respawn(){
        x=checkpointX;z=checkpointZ;hp=100;stamina=100;invulnerable=2;dodge=0;
        swing=0;attackTime=0;lockTarget=-1;exertion=0;motionBlend=0;
        for(Foe f:foes)if(!f.boss&&!f.counted){
            f.alive=true;f.hp=f.maxHp;f.windup=0;f.recovery=0;f.stagger=0;
        }
        if(foes[3].hp<=0){foes[3].hp=foes[3].maxHp;foes[3].alive=true;}
        mode="playing";message="THE EMBER ENDURES";messageTimer=3;
    }
    private String objective(){
        if(mode.equals("victory"))return "THE FIRST BELL HAS FALLEN";
        if(!shrineLit)return "FIND THE EMBER SHRINE";
        if(fragments<REQUIRED_SIGILS)return "GATHER TWO ASH SIGILS  "+fragments+"/2";
        if(foes[3].alive)return "CROSS THE RUINED CAUSEWAY";
        return "THE FIRST BELL AWAKENS";
    }
    private void notify(String text,float seconds){
        message=text;messageTimer=seconds;dialogueTimer=seconds;
    }
    private static float dist(float ax,float az,float bx,float bz){
        return (float)Math.hypot(ax-bx,az-bz);
    }
    private boolean eligible(Foe f){
        return f.alive&&(!f.boss||bossTriggered);
    }
    private int nearestTarget(){
        float near=13.5f;int best=-1;
        for(int i=0;i<foes.length;i++){
            Foe f=foes[i];if(!eligible(f))continue;
            float d=dist(x,z,f.x,f.z);
            if(d<near){near=d;best=i;}
        }
        return best;
    }
    private void interactNow(){
        if(dist(x,z,-4.4f,11f)<4.1f){
            shrineLit=true;checkpointX=-4.4f;checkpointZ=11;
            hp=100;stamina=100;
            notify("EMBER RESTORED  —  THE DEAD WILL RISE AGAIN",4.4f);
        }else if(dist(x,z,6.1f,19f)<4.4f){
            notify("INSCRIPTION: WE DID NOT RING THE BELLS TO WARN THE DEAD.",5.5f);
        }else if(dist(x,z,0,58f)<5f&&!foes[3].alive){
            mode="victory";message="WE WERE NEVER KEEPING DARKNESS OUT.";messageTimer=1000;
        }else{
            notify("NOTHING ANSWERS YOUR CALL",1.5f);
        }
    }
    private void spill(Foe f) {
        // Fixed-size deterministic decal pool; remains on the world surface.
        for(int k=0;k<2;k++){
            float a=(float)(spills*2.3999632+k*1.79);
            float offset=k==0?.12f:.39f;
            float px=f.x+(float)Math.cos(a)*offset;
            float pz=f.z+(float)Math.sin(a)*offset;
            float size=(f.boss?.55f:.36f)*(k==0?1f:.68f);
            Stain stain=new Stain(px,pz,size,a,time);
            stains[stainCursor]=stain;
            stainCursor=(stainCursor+1)%stains.length;
            stainCount=Math.min(stains.length,stainCount+1);
        }
        spills++;f.bleed=.58f;impactFlash=.25f;
    }
    private void strike(float oldProgress,float newProgress){
        if(newProgress<CombatMotion.ACTIVE_START||oldProgress>CombatMotion.ACTIVE_END)return;
        for(int i=0;i<foes.length;i++){
            Foe f=foes[i];
            if(!eligible(f)||swingHit[i])continue;
            float bearing=(float)Math.atan2(f.x-x,f.z-z);
            float radius=dist(x,z,f.x,f.z);
            if(!CombatMotion.hits(radius,CombatMotion.wrap(bearing-heading),
                    oldProgress,newProgress))continue;
            swingHit[i]=true;
            f.hp-=f.boss?24:44;
            f.stagger=.37f;
            f.windup=0;
            f.recovery=Math.max(f.recovery,.30f);
            // Move away from the blade's impact without teleporting into walls.
            if(radius>.001f){
                f.x=CombatMotion.clamp(f.x+(f.x-x)/radius*.11f,-15.7f,15.7f);
                f.z=CombatMotion.clamp(f.z+(f.z-z)/radius*.11f,-.8f,61.8f);
            }
            spill(f);
            if(f.hp<=0){
                f.hp=0;f.alive=false;totalKills++;
                if(lockTarget==i)lockTarget=-1;
                if(f.boss){
                    notify("THE KNIGHT FALLS. THE TRUTH WAITS AT THE BELL.",7);
                }else if(!f.counted&&fragments<REQUIRED_SIGILS){
                    f.counted=true;
                    fragments=Math.min(REQUIRED_SIGILS,fragments+1);
                    notify("ASH SIGIL RECOVERED  "+fragments+"/2",2.1f);
                }else{
                    f.counted=true;
                    notify("THE WATCHER FALLS  —  NO MORE SIGILS NEEDED",2.1f);
                }
            }
        }
    }
    public synchronized void update(float dt){
        dt=CombatMotion.clamp(dt,0,.045f);
        time+=dt;
        if(mode.equals("lab"))studio.tick(dt);
        if(!mode.equals("playing")){
            orbitDelta=0;attackQueued=false;rollQueued=false;lockQueued=false;return;
        }
        fragments=Math.min(REQUIRED_SIGILS,fragments);
        messageTimer=Math.max(0,messageTimer-dt);
        dialogueTimer=Math.max(0,dialogueTimer-dt);
        if(messageTimer==0)message="";
        invulnerable=Math.max(0,invulnerable-dt);
        hurtFlash=Math.max(0,hurtFlash-dt*2.5f);
        impactFlash=Math.max(0,impactFlash-dt*2.4f);
        for(Foe f:foes){
            f.bleed=Math.max(0,f.bleed-dt);
            f.attackPose=Math.max(0,f.attackPose-dt);
        }
        float oldSwing=swing;
        swing=Math.max(0,swing-dt);
        attackTime=Math.max(0,attackTime-dt);
        dodge=Math.max(0,dodge-dt);
        stamina=Math.min(100,stamina+(dodge>0?7:19)*dt);
        if(lockQueued){
            lockTarget=lockTarget>=0?-1:nearestTarget();
            lockQueued=false;
        }
        if(lockTarget>=0&&(!eligible(foes[lockTarget])||
                dist(x,z,foes[lockTarget].x,foes[lockTarget].z)>17f)){
            lockTarget=nearestTarget();
        }
        if(lockTarget>=0){
            Foe target=foes[lockTarget];
            float targetYaw=(float)Math.atan2(target.x-x,target.z-z);
            cameraYaw+=CombatMotion.wrap(targetYaw-cameraYaw)*Math.min(1f,dt*4f);
        }else{
            cameraYaw+=orbitDelta;
        }
        orbitDelta=0;
        cameraYaw=CombatMotion.wrap(cameraYaw);

        float mx=moveX,my=moveY;
        float len=(float)Math.hypot(mx,my);
        if(len>1){mx/=len;my/=len;len=1;}
        // Screen-right remains -X when yaw=0 (chase-camera handedness).
        float dx=(float)(-Math.cos(cameraYaw)*mx+Math.sin(cameraYaw)*my);
        float dz=(float)( Math.sin(cameraYaw)*mx+Math.cos(cameraYaw)*my);
        if(lockTarget>=0){
            Foe target=foes[lockTarget];
            heading=(float)Math.atan2(target.x-x,target.z-z);
        }else if(len>.11f)heading=(float)Math.atan2(dx,dz);
        if(rollQueued&&dodge<=0&&stamina>=27){
            stamina-=27;dodge=.48f;invulnerable=.41f;
            dodgeDx=len>.1f?dx:(float)Math.sin(heading);
            dodgeDz=len>.1f?dz:(float)Math.cos(heading);
            exertion=CombatMotion.clamp(exertion+.27f,0,1);
        }
        rollQueued=false;
        if(attackQueued&&attackTime<=0&&dodge<=.03f&&stamina>=21){
            stamina-=21;
            attackTime=.75f;swing=CombatMotion.DURATION;oldSwing=swing;
            Arrays.fill(swingHit,false);
            exertion=CombatMotion.clamp(exertion+.10f,0,1);
        }
        attackQueued=false;
        if(interactQueued){interactNow();interactQueued=false;}
        boolean moving=len>.09f||dodge>0;
        float desiredMove=moving?1f:0f;
        motionBlend+=(desiredMove-motionBlend)*Math.min(1f,dt*8f);
        if(moving){
            float speed=dodge>0?10.4f:(attackTime>0?2.1f:4.4f);
            float vx=(dodge>0?dodgeDx:dx)*speed*dt;
            float vz=(dodge>0?dodgeDz:dz)*speed*dt;
            x=CombatMotion.clamp(x+vx,-15.8f,15.8f);
            z=CombatMotion.clamp(z+vz,-1f,62f);
            if(z>47f&&fragments<REQUIRED_SIGILS)z=47f;
            walkPhase+=dt*speed*2.5f;
            exertion=CombatMotion.clamp(exertion+dt*(dodge>0?.40f:.18f),0,1);
        }else{
            exertion=CombatMotion.clamp(exertion-dt*.105f,0,1);
        }
        if(oldSwing>0){
            strike(CombatMotion.progress(oldSwing),CombatMotion.progress(swing));
        }
        if(z>45&&fragments>=REQUIRED_SIGILS&&!bossTriggered){
            bossTriggered=true;
            notify("THE ASH KNIGHT: YOU ARE TOO LATE, BELLWARDEN.",5.5f);
        }
        for(Foe f:foes){
            if(!eligible(f))continue;
            float distance=dist(x,z,f.x,f.z);
            if(f.stagger>0){f.stagger=Math.max(0,f.stagger-dt);f.moving*=.87f;continue;}
            if(f.recovery>0){f.recovery=Math.max(0,f.recovery-dt);f.moving*=.88f;continue;}
            if(f.windup>0){
                f.windup-=dt;f.moving*=.82f;
                if(f.windup<=0){
                    f.attackPose=.35f; // visible follow-through at the impact beat
                    if(dist(x,z,f.x,f.z)<(f.boss?3.6f:2.6f)&&invulnerable<=0){
                        hp-=f.boss?29:16;
                        hurtFlash=.65f;invulnerable=.68f;
                        if(hp<=0){
                            hp=0;mode="dead";
                            message="YOU HAVE FALLEN. THE EMBER STILL BURNS.";
                            messageTimer=1000;lockTarget=-1;
                        }
                    }
                    f.recovery=f.boss?.95f:1.2f;
                }
                continue;
            }
            if(distance<15&&distance>(f.boss?2.8f:1.8f)){
                float speed=f.boss?1.2f:1.55f;
                f.x+=(x-f.x)/Math.max(.01f,distance)*speed*dt;
                f.z+=(z-f.z)/Math.max(.01f,distance)*speed*dt;
                f.moving=Math.min(1f,f.moving+dt*5f);
                f.phase+=dt*speed*5f;
            }else f.moving=Math.max(0,f.moving-dt*4f);
            if(distance<(f.boss?3.45f:2.45f))f.windup=f.boss?.92f:.72f;
        }
    }
}
