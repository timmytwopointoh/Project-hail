package game.ashenveil.veilbound;

/**
 * Non-destructive model inspection. All transforms are inspection-only;
 * nothing here mutates the protagonist, combat progression or world terrain.
 * Angles are radians, model units correspond to the actual game renderer.
 */
public final class ModelStudio {
    public static final String[] ITEMS={
        "BELLWARDEN","HUSHED REVENANT","ASH KNIGHT",
        "WARDEN SWORD","ASH GREATSWORD","EMBER LANTERN","CHAPEL STONEWORK"};
    public static final String[] LIGHTS={"STUDIO","MOONLIT","EMBER","RIM LIGHT"};
    public static final String[] MATERIALS={"PBR-INSPIRED","FLAT ALBEDO","SILHOUETTE","NORMAL VIEW"};

    public static final class Snapshot {
        public final int item,light,material;
        public final float yaw,pitch,zoom,panX,panY;
        public final boolean autoTurn;
        Snapshot(ModelStudio s){
            item=s.item;light=s.light;material=s.material;
            yaw=s.yaw;pitch=s.pitch;zoom=s.zoom;
            panX=s.panX;panY=s.panY;autoTurn=s.autoTurn;
        }
    }
    private int item=0,light=0,material=0;
    private float yaw=.50f,pitch=.14f,zoom=6.2f,panX=0,panY=0;
    private boolean autoTurn=false;
    private static float clamp(float x,float lo,float hi){return Math.max(lo,Math.min(hi,x));}
    public synchronized Snapshot snapshot(){return new Snapshot(this);}
    public synchronized void nextItem(int step){
        item=(item+ITEMS.length+(step%ITEMS.length))%ITEMS.length;
        panX=panY=0;
        zoom=item==2?8.7f:item==6?12f:item==5?3.5f:5.9f;
    }
    public synchronized void nextLight(){light=(light+1)%LIGHTS.length;}
    public synchronized void nextMaterial(){material=(material+1)%MATERIALS.length;}
    public synchronized void toggleTurntable(){autoTurn=!autoTurn;}
    public synchronized void reset(){
        yaw=.50f;pitch=.14f;panX=0;panY=0;
        zoom=item==2?8.7f:item==6?12f:item==5?3.5f:5.9f;
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
