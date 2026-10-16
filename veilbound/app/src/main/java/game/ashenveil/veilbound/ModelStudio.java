package game.ashenveil.veilbound;

/**
 * Non-destructive model inspection. All transforms are inspection-only;
 * nothing here mutates the protagonist, combat progression or world terrain.
 * Angles are radians, model units correspond to the actual game renderer.
 */
public final class ModelStudio {
    public static final String[] ITEMS={
        "BELLWARDEN","HUSHED REVENANT","ASH KNIGHT",
        "WARDEN SWORD","ASH GREATSWORD","EMBER LANTERN","CHAPEL STONEWORK",
        "FRACTURED FLAGSTONE","FUNERARY CENOTAPH","IRON RELIQUARY","ANCIENT ROOT CLUSTER","HUMAN BASE (SKIN TEST)","M23 HAND SCULPT","IMPORTED OBJ"};
    public static final String[] LIGHTS={"STUDIO","MOONLIT","EMBER","RIM LIGHT"};
    public static final String[] MATERIALS={"PBR-INSPIRED","FLAT ALBEDO","SILHOUETTE","NORMAL VIEW","EDGE WIRES"};

    public static final class Snapshot {
        public final int item,light,material;
        public final float yaw,pitch,zoom,panX,panY;
        public final boolean autoTurn,ultraMesh;
        Snapshot(ModelStudio s){
            item=s.item;light=s.light;material=s.material;
            yaw=s.yaw;pitch=s.pitch;zoom=s.zoom;
            panX=s.panX;panY=s.panY;autoTurn=s.autoTurn;ultraMesh=s.ultraMesh;
        }
    }
    private int item=0,light=0,material=0;
    private float yaw=.50f,pitch=.12f,zoom=4.50f,panX=0,panY=0;
    private boolean autoTurn=false,ultraMesh=true;
    private int reviewView=0;
    private static final float[] REVIEW_YAWS={0f,1.5707963f,3.14159265f,5.497787f};
    private static final String[] REVIEW_NAMES={"FRONT","SIDE","BACK","3/4"};
    /** Repeatable camera angles for actual geometry review and emulator QA. */
    public synchronized void nextReviewView(){
        if(item!=11&&item!=12)return;
        reviewView=(reviewView+1)%4;
        yaw=REVIEW_YAWS[reviewView];pitch=.055f;
        zoom=4.15f;panX=0;panY=0;autoTurn=false;
    }
    public synchronized String reviewViewName(){return REVIEW_NAMES[reviewView];}
    private static float clamp(float x,float lo,float hi){return Math.max(lo,Math.min(hi,x));}
    public synchronized Snapshot snapshot(){return new Snapshot(this);}
    public synchronized void nextItem(int step){
        item=(item+ITEMS.length+(step%ITEMS.length))%ITEMS.length;
        panX=panY=0;
        if(item==11||item==12){reviewView=0;yaw=0f;pitch=.055f;autoTurn=false;}
        zoom=item==2?6.80f:item==6?12f:item==5?3.2f:
            item==7?3.30f:item==8?4.25f:item==9?5.0f:item==10?5.0f:4.50f;
    }
    public synchronized void selectImported(){item=ITEMS.length-1;reset();zoom=5.3f;}
    public synchronized void nextLight(){light=(light+1)%LIGHTS.length;}
    public synchronized void nextMaterial(){material=(material+1)%MATERIALS.length;}
    public synchronized void toggleTurntable(){autoTurn=!autoTurn;}
    public synchronized void toggleMeshDetail(){ultraMesh=!ultraMesh;}
    /** Focus fine geometry—especially hands, knuckles and gauntlets. */
    public synchronized void focusDetail(){
        autoTurn=false;
        if(item==11||item==12){
            // World-space hand center is y~1.55: the skin mesh is placed
            // on the studio plinth at +0.82 and its fingers/palm span
            // local y~0.49..1.02. The camera's baseline target is 2.12.
            // Previous -1.38 aimed at y=0.74 (feet!), hiding the fingers.
            // Keep the right hand centered, with enough room for its thumb.
            yaw=.12f;pitch=-.06f;panX=.56f;panY=-.57f;zoom=1.45f;
            return;
        }
        yaw=.18f;pitch=.08f;
        panX=item==2?1.1f:.65f;
        panY=item==2?-.40f:-.34f;
        zoom=item==2?2.90f:2.45f;
    }
    public synchronized void reset(){
        yaw=.50f;pitch=.12f;panX=0;panY=0;
        zoom=item==2?6.80f:item==6?12f:item==5?3.2f:
            item==7?3.30f:item==8?4.25f:item==9?5.0f:item==10?5.0f:4.50f;
        autoTurn=false;
    }
    public synchronized void orbit(float dx,float dy){
        yaw+=clamp(dx,-1.4f,1.4f);
        pitch=clamp(pitch+dy,-1.15f,1.18f);
        while(yaw>6.283185f)yaw-=6.283185f;
        while(yaw<0)yaw+=6.283185f;
    }
    public synchronized void dolly(float amount){
        zoom=clamp(zoom* (float)Math.exp(clamp(amount,-1.15f,1.15f)),1.05f,24f);
    }
    public synchronized void pan(float horizontal,float vertical){
        panX=clamp(panX+horizontal,-4.2f,4.2f);
        panY=clamp(panY+vertical,-3.2f,3.2f);
    }
    public synchronized void tick(float dt){
        if(autoTurn)yaw=(yaw+dt*.29f)%6.283185f;
    }
}
