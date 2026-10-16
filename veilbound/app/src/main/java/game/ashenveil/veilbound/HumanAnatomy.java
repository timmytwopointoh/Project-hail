package game.ashenveil.veilbound;
import java.util.ArrayList;
/**
 * First human-only sculpt experiment; separate from armored hero.
 * Explicit anatomical profiles rather than armor and generic sphere props.
 * Intentional modest shorts. Original procedural geometry, deterministic ES2.
 * This is a baseline model NOT scanned / photorealistic skin.
 */
public final class HumanAnatomy {
    private HumanAnatomy(){}
    static final ShapeEngine.Palette SKIN=new ShapeEngine.Palette(.67f,.405f,.305f);
    static final ShapeEngine.Palette HIGHLIGHT=new ShapeEngine.Palette(.77f,.51f,.395f);
    static final ShapeEngine.Palette SHADOW=new ShapeEngine.Palette(.49f,.275f,.215f);
    static final ShapeEngine.Palette HAIR=new ShapeEngine.Palette(.16f,.13f,.12f);
    static final ShapeEngine.Palette SHORTS=new ShapeEngine.Palette(.20f,.195f,.19f);
    static ShapeEngine.Ring r(float x,float y,float z,float rx,float rz,float keel){
        return new ShapeEngine.Ring(x,y,z,rx,rz,0,keel);
    }
    static void loft(ArrayList<ArtKit.Model> p,int sides,ShapeEngine.Palette c,ShapeEngine.Ring... rings){
        p.add(ShapeEngine.loft(rings,sides,c));
    }
    public static ArtKit.Model build(boolean lite){
        int n=lite?14:32;
        int m=lite?10:22;
        ArrayList<ArtKit.Model> p=new ArrayList<>();
        // Human abdomen, tapering waist, ribcage and clavicles;
        // surface proportions are authored in character-local units.
        loft(p,n,SKIN,r(0,1.02f,0,.27f,.19f,0),r(0,1.12f,0,.29f,.21f,0),
            r(0,1.26f,0,.27f,.18f,.008f),r(0,1.40f,0,.285f,.195f,.02f),
            r(0,1.55f,0,.35f,.225f,.022f),r(0,1.72f,0,.41f,.26f,.03f),
            r(0,1.84f,0,.40f,.24f,.02f),r(0,1.97f,0,.29f,.17f,.01f),
            r(0,2.04f,0,.15f,.13f,0));
        // Pelvis and modest training shorts, only non-skin section.
        loft(p,n,SHORTS,r(0,.89f,0,.31f,.235f,0),r(0,1.0f,0,.35f,.25f,0),
            r(0,1.12f,0,.325f,.24f,0),r(0,1.19f,0,.275f,.205f,0));
        // Chest has its own curved bilateral pectoral surfaces.
        for(int side=-1;side<=1;side+=2){
            float x=side*.195f;
            loft(p,m,HIGHLIGHT,r(x,1.56f,.15f,.14f,.085f,.016f),
                r(x,1.66f,.17f,.195f,.12f,.022f),
                r(x,1.76f,.16f,.195f,.115f,.01f),
                r(x,1.83f,.11f,.12f,.08f,0));
            // Broad, tapering human upper arm and deltoid.
            float armX=side*.56f;
            loft(p,n,SKIN,r(armX,.91f,.015f,.095f,.09f,0),
                r(armX,1.08f,.015f,.125f,.115f,.01f),
                r(armX,1.26f,0,.14f,.14f,.01f),
                r(armX,1.44f,0,.16f,.155f,.025f),
                r(armX,1.62f,-.015f,.16f,.17f,.015f),
                r(armX,1.82f,-.02f,.205f,.20f,.02f),
                r(armX,1.98f,-.025f,.15f,.15f,.005f));
            // Hand shape with visible wrist/palm, five independent digits.
            loft(p,m,SKIN,r(armX,.71f,.055f,.095f,.065f,0),
                r(armX,.79f,.05f,.125f,.075f,.005f),
                r(armX,.90f,.03f,.11f,.08f,.005f),
                r(armX,.97f,.015f,.088f,.07f,0));
            for(int finger=0;finger<4;finger++){
                float fx=armX+(finger-1.5f)*.045f;
                float low=.55f+.018f*Math.abs(finger-1.5f);
                loft(p,lite?8:12,SKIN,
                    r(fx,low,.09f,.017f,.018f,0),
                    r(fx,.64f,.085f,.022f,.021f,0),
                    r(fx,.75f,.08f,.022f,.021f,0));
            }
            loft(p,m,SKIN,r(armX+side*.125f,.68f,.12f,.028f,.025f,0),
                r(armX+side*.145f,.79f,.10f,.035f,.03f,0),
                r(armX+side*.115f,.89f,.075f,.043f,.038f,0));
            // Leg musculature and glute-to-ankle silhouette.
            float leg=side*.205f;
            loft(p,n,SKIN,r(leg,.14f,.02f,.085f,.08f,0),
                r(leg,.28f,0,.115f,.12f,.01f),
                r(leg,.45f,-.015f,.14f,.15f,.01f),
                r(leg,.59f,-.01f,.125f,.14f,.01f),
                r(leg,.70f,0,.14f,.145f,.005f),
                r(leg,.80f,.01f,.15f,.155f,.005f),
                r(leg,.97f,0,.19f,.185f,.015f),
                r(leg,1.10f,0,.205f,.20f,.025f),
                r(leg,1.20f,-.015f,.165f,.16f,0));
            // Heel-to-toe barefoot geometry, separated from ankle.
            loft(p,m,SKIN,r(leg,.02f,.20f,.135f,.21f,.01f),
                r(leg,.075f,.19f,.15f,.24f,.01f),
                r(leg,.13f,.11f,.115f,.165f,0),
                r(leg,.19f,.045f,.10f,.09f,0));
            for(int toe=0;toe<5;toe++){
                float tx=leg+side*(toe-2)*.043f;
                float z=.39f-.012f*toe;
                loft(p,lite?8:12,SKIN,r(tx,.025f,z,.018f,.032f,0),
                    r(tx,.055f,z-.025f,.024f,.028f,0),
                    r(tx,.079f,z-.06f,.025f,.025f,0));
            }
        }
        // Neck and neck-tendon connection under the head.
        loft(p,m,SKIN,r(0,1.96f,0,.12f,.115f,0),
            r(0,2.07f,0,.125f,.12f,0),
            r(0,2.18f,0,.115f,.11f,0));
        // Anatomically scaled skull, angular jawline and cranium.
        loft(p,n,SKIN,r(0,2.18f,.045f,.10f,.10f,.01f),
            r(0,2.22f,.06f,.155f,.12f,.02f),
            r(0,2.31f,.055f,.18f,.16f,.02f),
            r(0,2.43f,.045f,.19f,.165f,.02f),
            r(0,2.54f,.015f,.18f,.17f,.01f),
            r(0,2.62f,0,.135f,.125f,0),
            r(0,2.65f,0,.055f,.055f,0));
        // Facial anatomy: jaw, nose bridge, brows and low-contrast hair.
        p.add(ShapeEngine.bevelPlate(new float[]{-.06f,2.37f,
            0f,2.43f,.06f,2.37f,.025f,2.28f,-.025f,2.28f},
            .216f,.012f,.012f,HIGHLIGHT,SKIN));
        for(int side=-1;side<=1;side+=2){
            p.add(ShapeEngine.bevelPlate(new float[]{side*.045f,2.46f,
                side*.15f,2.455f,side*.15f,2.425f,side*.045f,2.428f},
                .172f,.005f,.006f,SHADOW,SKIN));
            loft(p,lite?8:12,SKIN,r(side*.186f,2.32f,.02f,.034f,.04f,0),
                r(side*.189f,2.40f,.01f,.045f,.05f,0),
                r(side*.175f,2.46f,.0f,.028f,.025f,0));
        }
        // Short-cropped hair: shaped cap rather than a metal helmet.
        loft(p,n,HAIR,r(0,2.54f,-.01f,.18f,.17f,0),
            r(0,2.60f,-.01f,.177f,.163f,0),
            r(0,2.67f,-.015f,.12f,.115f,0),
            r(0,2.70f,-.015f,.03f,.025f,0));
        return ShapeEngine.combine(p.toArray(new ArtKit.Model[0]));
    }
}
