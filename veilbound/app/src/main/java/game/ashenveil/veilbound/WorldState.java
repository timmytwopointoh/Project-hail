package game.ashenveil.veilbound;

/**
 * Deterministic, Android-independent game rules; render and UI never decide hits.
 * All mutable state accessed from the GL thread or synchronized snapshot/input calls.
 */
public final class WorldState {
    public static final class Foe {
        public final String name;
        public float x,z,hp;
        public final float maxHp;
        public final boolean boss;
        public float windup, recovery, stagger, phase;
        public boolean alive=true, counted=false;
        Foe(String name,float x,float z,float hp,boolean boss) {
            this.name=name;this.x=x;this.z=z;this.hp=hp;this.maxHp=hp;this.boss=boss;
        }
    }
    public static final class Snapshot {
        public final String mode, message, objective;
        public final int health, stamina, fragments, foes, totalKills;
        public final float x,z,cameraYaw, bossHealth, swing, dodge;
        public final boolean shrineLit, bossAlive, dialogue;
        Snapshot(WorldState w) {
            mode=w.mode;message=w.message;objective=w.objective();
            health=(int)Math.ceil(w.hp);stamina=(int)Math.ceil(w.stamina);
            fragments=w.fragments;totalKills=w.totalKills;
            int a=0;for(Foe f:w.foes)if(f.alive)a++;foes=a;
            x=w.x;z=w.z;cameraYaw=w.cameraYaw;swing=w.swing;dodge=w.dodge;
            shrineLit=w.shrineLit;bossAlive=w.foes[3].alive;
            bossHealth=w.foes[3].hp;dialogue=w.dialogueTimer>0;
        }
    }

    public float x=0f,z=3f, heading=0f, cameraYaw=0f, hp=100f, stamina=100f;
    public float swing=0, dodge=0, invulnerable=0, attackTime=0, time=0f;
    public float hurtFlash=0, impactFlash=0, walkPhase=0f;
    public String mode="title", message="THE BELLS REMEMBER", checkpointMessage="";
    public boolean shrineLit=false, bossTriggered=false;
    public int fragments=0,totalKills=0;
    public final Foe[] foes={
        new Foe("Hushed Watcher",-3.8f,24f,70,false),
        new Foe("Hushed Watcher",4.4f,32f,70,false),
        new Foe("Ashbound Guard",-2f,43f,92,false),
        new Foe("The Ash Knight",0f,54f,260,true)
    };
    public float dialogueTimer=0;
    private float moveX=0,moveY=0,orbitDelta=0;
    private boolean attackQueued=false,rollQueued=false,interactQueued=false;
    private boolean attackLanded=false;
    private float checkpointX=0,checkpointZ=3;
    private float messageTimer=7;
    private float lastBossHit=0;
    private float dodgeDx=0,dodgeDz=1;
    private int defeated=0;

    public synchronized Snapshot snapshot(){return new Snapshot(this);}
    public synchronized void movement(float horizontal,float vertical){
        moveX=Math.max(-1,Math.min(1,horizontal));
        moveY=Math.max(-1,Math.min(1,vertical));
    }
    public synchronized void orbit(float delta){orbitDelta+=delta;}
    public synchronized void attack(){attackQueued=true;}
    public synchronized void roll(){rollQueued=true;}
    public synchronized void interact(){interactQueued=true;}

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
        for(Foe f:foes)if(!f.boss&&!f.counted){f.alive=true;f.hp=f.maxHp;f.windup=0;f.recovery=0;}
        if(foes[3].hp<=0){foes[3].hp=foes[3].maxHp;foes[3].alive=true;}
        mode="playing";message="THE EMBER ENDURES";messageTimer=3;
    }
    private String objective(){
        if(mode.equals("victory"))return "THE FIRST BELL HAS FALLEN";
        if(!shrineLit)return "FIND THE EMBER SHRINE";
        if(fragments<2)return "GATHER TWO ASH SIGILS  "+fragments+"/2";
        if(foes[3].alive)return "CROSS THE RUINED CAUSEWAY";
        return "THE FIRST BELL AWAKENS";
    }
    private void notify(String text,float seconds){message=text;messageTimer=seconds;dialogueTimer=seconds;}
    private static float dist(float ax,float az,float bx,float bz){
        return (float)Math.hypot(ax-bx,az-bz);
    }
    private void interactNow(){
        if(dist(x,z,-4.4f,11f)<4.1f){
            shrineLit=true;checkpointX=-4.4f;checkpointZ=11;
            hp=100;stamina=100;notify("EMBER RESTORED  —  THE DEAD WILL RISE AGAIN",4.4f);
        } else if(dist(x,z,6.1f,19f)<4.4f){
            notify("INSCRIPTION: WE DID NOT RING THE BELLS TO WARN THE DEAD.",5.5f);
        } else if(dist(x,z,0,58f)<5f&&!foes[3].alive){
            mode="victory";message="WE WERE NEVER KEEPING DARKNESS OUT.";messageTimer=1000;
        } else {
            notify("NOTHING ANSWERS YOUR CALL",1.5f);
        }
    }
    public synchronized void update(float dt){
        dt=Math.max(0,Math.min(dt,.045f));
        time+=dt;
        if(!mode.equals("playing")){orbitDelta=0;return;}
        cameraYaw+=orbitDelta;orbitDelta=0;
        if(cameraYaw>6.283f)cameraYaw-=6.283f;
        if(cameraYaw<0)cameraYaw+=6.283f;
        messageTimer=Math.max(0,messageTimer-dt);
        dialogueTimer=Math.max(0,dialogueTimer-dt);
        if(messageTimer==0)message="";
        invulnerable=Math.max(0,invulnerable-dt);
        hurtFlash=Math.max(0,hurtFlash-dt*2.5f);
        impactFlash=Math.max(0,impactFlash-dt*2.4f);
        swing=Math.max(0,swing-dt);
        if(attackTime>0)attackTime-=dt;
        if(dodge>0)dodge=Math.max(0,dodge-dt);
        stamina=Math.min(100,stamina+(dodge>0?7:19)*dt);

        // Camera-relative move; action lock imposes deliberate attack cadence.
        float mx=moveX,my=moveY;
        float len=(float)Math.hypot(mx,my);
        if(len>1){mx/=len;my/=len;len=1;}
        float dx=(float)(Math.cos(cameraYaw)*mx+Math.sin(cameraYaw)*my);
        float dz=(float)(-Math.sin(cameraYaw)*mx+Math.cos(cameraYaw)*my);
        if(len>.11f)heading=(float)Math.atan2(dx,dz);
        if(rollQueued&&dodge<=0&&stamina>=27){
            stamina-=27;dodge=.48f;invulnerable=.41f;
            dodgeDx=len>.1f?dx:(float)Math.sin(heading);
            dodgeDz=len>.1f?dz:(float)Math.cos(heading);
        }
        rollQueued=false;
        if(attackQueued&&attackTime<=0&&dodge<=.03f&&stamina>=21){
            stamina-=21;attackTime=.57f;swing=.57f;attackLanded=false;
        }
        attackQueued=false;
        if(interactQueued){interactNow();interactQueued=false;}
        boolean isMoving=len>.09f||dodge>0;
        if(isMoving){
            float speed=dodge>0?10.4f:(attackTime>0?2.1f:4.4f);
            float vx=(dodge>0?dodgeDx:dx)*speed*dt, vz=(dodge>0?dodgeDz:dz)*speed*dt;
            x=Math.max(-15.8f,Math.min(15.8f,x+vx));
            z=Math.max(-1f,Math.min(62f,z+vz));
            if(z>47f&&fragments<2)z=47f; // The gate cannot be bypassed.
            walkPhase+=dt*speed*2.5f;
        }

        if(attackTime<=.40f&&attackTime>=.22f&&!attackLanded){
            attackLanded=true;
            for(Foe f:foes){
                if(!f.alive || (f.boss&&!bossTriggered))continue;
                float d=dist(x,z,f.x,f.z);
                if(d>2.9f)continue;
                float ang=(float)Math.atan2(f.x-x,f.z-z);
                float align=(float)Math.cos(ang-heading);
                if(align<-.20f)continue;
                f.hp-=f.boss?24:44;f.stagger=.34f;
                impactFlash=.25f;
                if(f.hp<=0){
                    f.alive=false;totalKills++;
                    if(!f.boss&&!f.counted){fragments++;f.counted=true;}
                    if(f.boss){notify("THE KNIGHT FALLS. THE TRUTH WAITS AT THE BELL.",7);}
                    else{notify("ASH SIGIL RECOVERED  "+fragments+"/2",2.1f);}
                }
            }
        }
        if(z>45&&fragments>=2&&!bossTriggered){
            bossTriggered=true;notify("THE ASH KNIGHT: YOU ARE TOO LATE, BELLWARDEN.",5.5f);
        }
        for(Foe f:foes){
            if(!f.alive||(f.boss&&!bossTriggered))continue;
            float distance=dist(x,z,f.x,f.z);
            if(f.stagger>0){f.stagger=Math.max(0,f.stagger-dt);continue;}
            if(f.recovery>0){f.recovery-=dt;continue;}
            if(f.windup>0){
                f.windup-=dt;
                if(f.windup<=0){
                    if(dist(x,z,f.x,f.z)<(f.boss?3.6f:2.6f)&&invulnerable<=0){
                        hp-=f.boss?29:16;
                        hurtFlash=.65f;invulnerable=.68f;
                        if(hp<=0){hp=0;mode="dead";message="YOU HAVE FALLEN. THE EMBER STILL BURNS.";messageTimer=1000;}
                    }
                    f.recovery=f.boss?.95f:1.2f;
                }
                continue;
            }
            if(distance<15&&distance>(f.boss?2.8f:1.8f)){
                float speed=(f.boss?1.2f:1.55f);
                f.x+=(x-f.x)/Math.max(.01f,distance)*speed*dt;
                f.z+=(z-f.z)/Math.max(.01f,distance)*speed*dt;
            }
            if(distance<(f.boss?3.45f:2.45f))f.windup=f.boss?.92f:.72f;
            f.phase+=dt;
        }
    }
}