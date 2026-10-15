package game.ashenveil.veilbound;

/**
 * A single animation timeline shared by collision rules and the OpenGL sword.
 * +Z is forward; angles turn clockwise toward +X in character local space.
 * All functions are deterministic and need no Android runtime.
 */
public final class CombatMotion {
    private CombatMotion() {}
    public static final float DURATION=.64f;
    public static final float ACTIVE_START=.31f, ACTIVE_END=.77f;
    public static final float RANGE=2.55f;
    public static float clamp(float x,float lo,float hi){return Math.max(lo,Math.min(hi,x));}
    public static float smooth(float x) {
        x=clamp(x,0f,1f);
        return x*x*(3f-2f*x);
    }
    public static float progress(float remaining){
        return clamp(1f-Math.max(0f,remaining)/DURATION,0f,1f);
    }
    public static float bladeBearing(float progress){
        // Chamber on the right, strike through the front, finish on the left.
        float travel=smooth((progress-.20f)/.57f);
        return (float)Math.toRadians(67f-134f*travel);
    }
    public static float bladePitch(float progress){
        // Raise the blade in anticipation, then level it through contact.
        return 16f+69f*smooth(progress/.30f)-13f*smooth((progress-.76f)/.24f);
    }
    public static float wrap(float a){
        while(a>(float)Math.PI)a-=(float)(Math.PI*2);
        while(a<-(float)Math.PI)a+=(float)(Math.PI*2);
        return a;
    }
    public static boolean hits(float radius,float enemyRelativeBearing,
                               float startProgress,float endProgress) {
        if(radius<.35f||radius>RANGE)return false;
        float a=Math.max(ACTIVE_START,Math.min(startProgress,endProgress));
        float b=Math.min(ACTIVE_END,Math.max(startProgress,endProgress));
        if(b<a)return false;
        float bearing=wrap(enemyRelativeBearing);
        // Prevent hits behind the back or beyond the arc.
        if(Math.abs(bearing)>1.39f)return false;
        float first=bladeBearing(a),last=bladeBearing(b);
        return bearing>=Math.min(first,last)-.235f
            && bearing<=Math.max(first,last)+.235f;
    }
}
