package game.ashenveil.veilbound;

import java.util.ArrayList;
import java.util.Arrays;

/**
 * Entire Bellwarden rebuilt as original topology-driven anatomical armor,
 * rather than an old collection of inflated spheres and decorative beads.
 *
 * A complete human-proportioned profile is designed in seven joint regions:
 * torso/pelvis, mirrored articulated shoulder/arms and leg assemblies,
 * separate curved visor/helmet, and a bespoke pleated cloth surface.
 * All pieces have sculptural cross sections that vary in TWO dimensions.
 *
 * Production quality limitations: rigid joint segmentation, faceted seam
 * normals and procedural colors, not weight-painted skinning or scanned PBR.
 */
public final class BellwardenAnatomy {
    private BellwardenAnatomy(){}
    private static final float TAU=(float)(Math.PI*2);
    private static final ShapeEngine.Palette
        IRON=new ShapeEngine.Palette(.40f,.49f,.54f),
        POLISH=new ShapeEngine.Palette(.53f,.61f,.64f),
        EDGE=new ShapeEngine.Palette(.68f,.67f,.57f),
        DARK=new ShapeEngine.Palette(.20f,.29f,.34f),
        MAIL=new ShapeEngine.Palette(.28f,.33f,.38f),
        GOLD=new ShapeEngine.Palette(.77f,.60f,.36f),
        LEATHER=new ShapeEngine.Palette(.29f,.25f,.23f),
        VISOR=new ShapeEngine.Palette(.075f,.12f,.17f),
        GLOW=new ShapeEngine.Palette(.16f,.70f,.58f);

    private static ShapeEngine.Ring r(float x,float y,float z,
                                      float rx,float rz,float keel){
        return new ShapeEngine.Ring(x,y,z,rx,rz,0,keel);
    }
    private static void add(ArrayList<ArtKit.Model> pieces,ShapeEngine.Palette tint,
                            int sides,ShapeEngine.Ring... rings){
        pieces.add(ShapeEngine.loft(rings,sides,tint));
    }
    private static void plate(ArrayList<ArtKit.Model> meshes,float[] outline,
                              float front,float rise,float thickness,
                              ShapeEngine.Palette face,ShapeEngine.Palette edge){
        meshes.add(ShapeEngine.bevelPlate(outline,front,rise,thickness,face,edge));
    }
    private static class Cloth {
        float[] data=new float[24000];int length;
        private void emit(float[] p,float nx,float ny,float nz,
                          float rr,float gg,float bb){
            if(length+9>data.length)data=Arrays.copyOf(data,data.length*2);
            data[length++]=p[0];data[length++]=p[1];data[length++]=p[2];
            data[length++]=nx;data[length++]=ny;data[length++]=nz;
            data[length++]=rr;data[length++]=gg;data[length++]=bb;
        }
        void triangle(float[] a,float[] b,float[] c,float rr,float gg,float blue){
            float ux=b[0]-a[0],uy=b[1]-a[1],uz=b[2]-a[2];
            float vx=c[0]-a[0],vy=c[1]-a[1],vz=c[2]-a[2];
            float nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx;
            float l=(float)Math.sqrt(nx*nx+ny*ny+nz*nz);
            if(l<.000001f)return;
            emit(a,nx/l,ny/l,nz/l,rr,gg,blue);
            emit(b,nx/l,ny/l,nz/l,rr,gg,blue);
            emit(c,nx/l,ny/l,nz/l,rr,gg,blue);
        }
        ArtKit.Model finish(){return new ArtKit.Model(Arrays.copyOf(data,length));}
    }
    private static float[] clothPoint(int col,int row,int cols,int rows){
        float u=col/(float)cols,t=row/(float)rows;
        float angle=u*TAU;
        float width=.92f+t*.57f;
        float x=(u-.5f)*width;
        float y=1.96f-t*1.72f;
        float pleat=.055f*(float)Math.cos(angle*7)*(.30f+.70f*t);
        float z=-.54f-.15f*t+pleat-.07f*t*t;
        // Irregular hand-cut hem: no perfectly horizontal cape edge.
        y+=t*t*(.045f*(float)Math.cos(angle*3)+.014f*(float)Math.sin(angle*11));
        return new float[]{x,y,z};
    }
    private static ArtKit.Model drapedMantle(boolean mobile){
        int cols=mobile?15:42, rows=mobile?15:45;
        Cloth cloth=new Cloth();
        for(int y=0;y<rows;y++)for(int x=0;x<cols;x++){
            float[] a=clothPoint(x,y,cols,rows);
            float[] b=clothPoint(x+1,y,cols,rows);
            float[] c=clothPoint(x+1,y+1,cols,rows);
            float[] d=clothPoint(x,y+1,cols,rows);
            float weave=(float)Math.cos(TAU*x/Math.max(3,cols/4));
            float rr=.21f+.012f*weave,gg=.19f+.007f*weave,bb=.24f+.025f*weave;
            // Two-sided cloth, even while GLES2 backface culling is enabled.
            cloth.triangle(a,b,c,rr,gg,bb);
            cloth.triangle(a,c,d,rr,gg,bb);
            cloth.triangle(c,b,a,rr*.80f,gg*.80f,bb*.84f);
            cloth.triangle(d,c,a,rr*.80f,gg*.80f,bb*.84f);
        }
        return cloth.finish();
    }
    /**
     * Full replacement mesh, same 9-float vertex ABI consumed by the game.
     * Detail is selected when assembled, not dynamically rebuilt each frame.
     */
    public static ArtKit.Model build(boolean mobile){
        final int ringSides=mobile?16:38;
        final int narrowSides=mobile?12:28;
        ArrayList<ArtKit.Model> sculpt=new ArrayList<>();

        // 1: anatomically tapered under-armor: pelvic girdle, waist,
        // broad ribcage, narrowing shoulder/neck transition.
        add(sculpt,MAIL,ringSides,
            r(0,.78f,-.015f,.26f,.22f,.035f),
            r(0,.93f,-.015f,.30f,.25f,.04f),
            r(0,1.10f,-.01f,.30f,.245f,.04f),
            r(0,1.29f,-.025f,.305f,.25f,.055f),
            r(0,1.44f,-.02f,.36f,.275f,.06f),
            r(0,1.60f,-.035f,.425f,.285f,.065f),
            r(0,1.77f,-.04f,.445f,.29f,.07f),
            r(0,1.90f,-.04f,.36f,.27f,.045f),
            r(0,2.03f,-.045f,.19f,.19f,.01f)
        );
        // 2: exterior forged cuirass with hollow flank concavity + keel.
        add(sculpt,IRON,ringSides,
            r(0,1.12f,.10f,.295f,.26f,.075f),
            r(0,1.25f,.125f,.345f,.27f,.08f),
            r(0,1.38f,.115f,.39f,.31f,.105f),
            r(0,1.55f,.095f,.43f,.31f,.115f),
            r(0,1.71f,.075f,.445f,.30f,.095f),
            r(0,1.81f,.055f,.425f,.28f,.075f),
            r(0,1.94f,.025f,.25f,.22f,.035f)
        );
        // Ornamental breastplate is TWO peaked non-round metal panels.
        plate(sculpt,new float[]{-.40f,1.59f,-.23f,1.76f,-.035f,1.72f,
            -.03f,1.28f,-.24f,1.22f,-.405f,1.39f},
            .40f,.035f,.023f,POLISH,DARK);
        plate(sculpt,new float[]{.035f,1.72f,.23f,1.76f,.40f,1.59f,
            .405f,1.39f,.24f,1.22f,.03f,1.28f},
            .40f,.035f,.023f,POLISH,DARK);
        // Center keel and bell sigil are carved pointed metal contours.
        plate(sculpt,new float[]{-.072f,1.77f,0,1.92f,.072f,1.77f,
            .038f,1.37f,0,1.30f,-.038f,1.37f},
            .435f,.024f,.021f,GOLD,IRON);
        // Overlapping leather/steel belt, not a spherical hip.
        add(sculpt,LEATHER,narrowSides,
            r(0,.91f,.012f,.33f,.29f,.015f),
            r(0,.975f,.015f,.38f,.30f,.02f),
            r(0,1.04f,.015f,.38f,.29f,.022f),
            r(0,1.12f,.01f,.34f,.27f,.01f));
        plate(sculpt,new float[]{-.08f,.98f,0,1.065f,.08f,.98f,
            .08f,.91f,0,.885f,-.08f,.91f},
            .36f,.036f,.02f,GOLD,DARK);
        // The ring of overlapping corset splints is an actual independent
        // array of angular forged trapezoids.
        for(int side=-1;side<=1;side+=2){
            for(int i=0;i<3;i++){
                float x=side*(.12f+.12f*i);
                plate(sculpt,new float[]{x-side*.043f,1.20f,
                    x+side*.045f,1.20f,x+side*.055f,1.05f,
                    x-side*.032f,1.05f},
                    .345f-i*.012f,.014f,.013f,DARK,GOLD);
            }
        }

        for(int side=-1;side<=1;side+=2){
            float x=side*.665f;

            // 3: anatomy of articulated shoulder to forearm: narrowing
            // upper biceps, elbow hinge, wrist and segmented gauntlet.
            add(sculpt,MAIL,narrowSides,
                r(x,1.02f,.05f,.14f,.135f,0),
                r(x,1.21f,.045f,.20f,.16f,.015f),
                r(x,1.40f,-.005f,.215f,.20f,.025f),
                r(x,1.62f,-.04f,.22f,.215f,.035f),
                r(x,1.83f,-.045f,.25f,.24f,.035f),
                r(x,2.02f,-.065f,.18f,.19f,0));
            // Forged pauldron: stepped shoulder ridge moves into collar.
            add(sculpt,POLISH,ringSides,
                r(x,1.68f,-.05f,.23f,.23f,.03f),
                r(x,1.78f,-.05f,.31f,.27f,.045f),
                r(x,1.91f,-.065f,.355f,.30f,.065f),
                r(x,2.01f,-.075f,.325f,.27f,.055f),
                r(x,2.11f,-.07f,.14f,.13f,.01f));
            // Separate overlapping plates slide visually over upper arm.
            add(sculpt,IRON,narrowSides,
                r(x,1.42f,.025f,.205f,.18f,.012f),
                r(x,1.54f,.025f,.255f,.235f,.040f),
                r(x,1.63f,-.015f,.245f,.235f,.040f),
                r(x,1.74f,-.03f,.205f,.20f,.015f));
            // Elbow articulation and tapered vambrace (NOT a circular tube).
            add(sculpt,IRON,ringSides,
                r(x,1.07f,.13f,.15f,.135f,.025f),
                r(x,1.18f,.115f,.18f,.165f,.04f),
                r(x,1.34f,.06f,.22f,.195f,.07f),
                r(x,1.46f,.02f,.235f,.215f,.08f),
                r(x,1.52f,.015f,.19f,.18f,.02f));
            plate(sculpt,new float[]{x-side*.19f,1.18f,
                x,1.46f,x+side*.19f,1.18f,
                x+side*.14f,1.08f,x-side*.15f,1.08f},
                .255f,.035f,.02f,POLISH,DARK);
            // Human hand silhouette and four individually forged gauntlet
            // fingers, not a single featureless mitten/ball.
            add(sculpt,LEATHER,narrowSides,
                r(x, .92f,.145f,.135f,.115f,.012f),
                r(x,1.02f,.14f,.165f,.15f,.02f),
                r(x,1.14f,.12f,.17f,.145f,.026f));
            for(int finger=0;finger<4;finger++){
                float px=x+side*(finger-1.5f)*.060f;
                float base=.92f+.015f*(finger==1?1:0);
                add(sculpt,IRON,mobile?8:12,
                    r(px,base,.215f,.022f,.035f,.003f),
                    r(px,base+.075f,.205f,.03f,.039f,.006f),
                    r(px,base+.13f,.195f,.028f,.035f,.005f));
            }

            // 4: legs join higher at hips; thigh thigh-shell tapers inward
            // and knees are separate pointed edge plates.
            float lx=side*.29f;
            add(sculpt,MAIL,narrowSides,
                r(lx,.58f,.085f,.16f,.16f,.015f),
                r(lx,.74f,.055f,.20f,.21f,.025f),
                r(lx,.93f,.015f,.235f,.23f,.04f),
                r(lx,1.10f,-.025f,.255f,.23f,.045f),
                r(lx,1.18f,-.03f,.205f,.20f,.015f));
            add(sculpt,IRON,ringSides,
                r(lx,.74f,.10f,.17f,.21f,.02f),
                r(lx,.84f,.10f,.22f,.25f,.035f),
                r(lx,.97f,.075f,.245f,.25f,.055f),
                r(lx,1.10f,.02f,.25f,.22f,.06f),
                r(lx,1.17f,-.005f,.20f,.17f,.01f));
            // 5: tapered boot and greave are a single continuous forged
            // silhouette. The foot extends forward more than the ankle.
            add(sculpt,LEATHER,narrowSides,
                r(lx,.04f,.22f,.16f,.31f,.045f),
                r(lx,.14f,.17f,.20f,.33f,.055f),
                r(lx,.22f,.10f,.18f,.22f,.04f),
                r(lx,.31f,.05f,.155f,.15f,.02f));
            add(sculpt,IRON,ringSides,
                r(lx,.20f,.075f,.155f,.165f,.03f),
                r(lx,.30f,.08f,.17f,.195f,.045f),
                r(lx,.48f,.075f,.205f,.22f,.07f),
                r(lx,.62f,.055f,.22f,.22f,.075f),
                r(lx,.74f,.07f,.205f,.205f,.055f),
                r(lx,.82f,.09f,.17f,.19f,.015f));
            // Angled knee defense with independent crest and rim.
            plate(sculpt,new float[]{lx-side*.19f,.80f,
                lx,.89f,lx+side*.19f,.80f,
                lx+side*.14f,.67f,lx,.615f,lx-side*.14f,.67f},
                .34f,.07f,.028f,POLISH,DARK);
            plate(sculpt,new float[]{lx-side*.145f,.58f,
                lx,.62f,lx+side*.145f,.58f,
                lx+side*.11f,.31f,lx,.27f,lx-side*.11f,.31f},
                .33f,.032f,.02f,IRON,GOLD);
            // Tassets are distinct hand-outlined overlap plates above legs.
            plate(sculpt,new float[]{lx-side*.225f,1.04f,
                lx,1.095f,lx+side*.22f,1.04f,
                lx+side*.175f,.78f,lx,.69f,lx-side*.17f,.78f},
                .30f,.032f,.020f,DARK,GOLD);
        }

        // 6: neck, armet and brow. Multi-section steel helmet profile has
        // everted visor cheeks and a strong center ridge; never sphere heads.
        add(sculpt,MAIL,narrowSides,
            r(0,1.99f,-.03f,.16f,.16f,0f),
            r(0,2.08f,-.035f,.20f,.19f,.025f),
            r(0,2.20f,-.025f,.205f,.205f,.03f));
        add(sculpt,IRON,ringSides,
            r(0,2.10f,.00f,.22f,.235f,.025f),
            r(0,2.18f,0f,.30f,.265f,.052f),
            r(0,2.30f,0f,.345f,.28f,.068f),
            r(0,2.45f,-.015f,.345f,.295f,.076f),
            r(0,2.59f,-.020f,.31f,.265f,.065f),
            r(0,2.71f,-.025f,.235f,.20f,.03f),
            r(0,2.78f,-.025f,.12f,.11f,.015f),
            r(0,2.81f,-.025f,.035f,.035f,.0f));
        // Genuine recessed visor opening, multiple angular pieces and
        // horizontal light wells, high contrast for head readability.
        plate(sculpt,new float[]{-.305f,2.39f,-.24f,2.425f,
            -.08f,2.418f,0,2.39f,.08f,2.418f,.24f,2.425f,
            .305f,2.39f,.17f,2.32f,0,2.31f,-.17f,2.32f},
            .306f,.012f,.014f,VISOR,IRON);
        plate(sculpt,new float[]{-.27f,2.405f,-.13f,2.422f,
            -.035f,2.395f,-.04f,2.36f,-.22f,2.365f},
            .33f,.006f,.007f,GLOW,DARK);
        plate(sculpt,new float[]{.035f,2.395f,.13f,2.422f,
            .27f,2.405f,.22f,2.365f,.04f,2.36f},
            .33f,.006f,.007f,GLOW,DARK);
        plate(sculpt,new float[]{-.09f,2.73f,0f,2.85f,.09f,2.73f,
            .065f,2.36f,0f,2.26f,-.065f,2.36f},
            .318f,.04f,.025f,EDGE,GOLD);
        // Lower articulated faceguard (bevor) extends below the visor.
        plate(sculpt,new float[]{-.25f,2.325f,-.18f,2.25f,
            0f,2.105f,.18f,2.25f,.25f,2.325f,
            0f,2.29f},.313f,.016f,.027f,IRON,DARK);
        for(int side=-1;side<=1;side+=2){
            plate(sculpt,new float[]{side*.24f,2.47f,side*.33f,2.47f,
                side*.38f,2.30f,side*.27f,2.16f,side*.20f,2.26f},
                .207f,.026f,.021f,IRON,GOLD);
        }

        // 7: cape is a hand-draped two-sided grid, no floating spheres.
        sculpt.add(drapedMantle(mobile));
        // Actual collar edge, shaped in cross-sections rather than beads.
        add(sculpt,GOLD,narrowSides,
            r(0,1.95f,-.09f,.33f,.23f,.005f),
            r(0,2.005f,-.09f,.34f,.24f,.009f),
            r(0,2.055f,-.09f,.245f,.19f,.004f));

        return ShapeEngine.combine(sculpt.toArray(new ArtKit.Model[0]));
    }
}
