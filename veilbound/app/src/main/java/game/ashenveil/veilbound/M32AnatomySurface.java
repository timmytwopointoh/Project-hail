package game.ashenveil.veilbound;

import java.util.ArrayList;

/**
 * M32B/C/D: real, small, symmetric corrections to the full human anatomy:
 * cheek/jaw/nose planes, clavicle/deltoid transition, knuckle anatomy,
 * foot arch and visible toe webbing. All edits are opt-in and operate on
 * original SKIN positions, not colored facial overlays, hair or shorts.
 *
 * No fake scanned photos, no extra disconnected eye stickers or duplicate
 * body shells. This is a bounded surface study and not finished retopology.
 */
public final class M32AnatomySurface {
    private M32AnatomySurface(){}
    public static final int FACE=0,CHEST_SHOULDER=1,HANDS=2,FEET=3;
    private static final class Zone {
        final int region,axis;
        final float x,y,z,rx,ry,rz,delta;
        Zone(int region,int axis,float x,float y,float z,
             float rx,float ry,float rz,float delta){
            this.region=region;this.axis=axis;
            this.x=x;this.y=y;this.z=z;
            this.rx=rx;this.ry=ry;this.rz=rz;this.delta=delta;
        }
    }
    private static Zone[] zones(){
        ArrayList<Zone> z=new ArrayList<>();
        // Source-retargeted anatomy (M24 y mapping); cheek, jaw, nose bridge.
        z.add(new Zone(FACE,2,.116f,M24BodyRetarget.y(0,2.390f),
            .138f,.080f,.080f,.081f,-.007f));
        z.add(new Zone(FACE,2,.114f,M24BodyRetarget.y(0,2.275f),
            .116f,.080f,.051f,.087f,-.006f));
        z.add(new Zone(FACE,2,.024f,M24BodyRetarget.y(0,2.405f),
            .194f,.037f,.084f,.056f,.005f));
        // Front collarbones should flow into deltoids instead of oversized
        // capsule bumps in the armpit. No actual ribcage motion.
        z.add(new Zone(CHEST_SHOULDER,2,.306f,M24BodyRetarget.y(.306f,1.90f),
            .100f,.092f,.085f,.090f,.007f));
        z.add(new Zone(CHEST_SHOULDER,2,.442f,M24BodyRetarget.y(.442f,1.78f),
            .115f,.086f,.110f,.092f,-.009f));
        z.add(new Zone(CHEST_SHOULDER,2,.187f,M24BodyRetarget.y(.187f,1.72f),
            .217f,.137f,.116f,.110f,-.005f));
        // Four gradual MCP knuckle crests on each hand. Underlying finger
        // shapes are still the original ten real lofted digits.
        for(int k=0;k<4;k++){
            float anatomical=.554f+(k-1.5f)*.067f;
            z.add(new Zone(HANDS,2,anatomical,M24BodyRetarget.y(anatomical,.790f),
                .092f,.019f,.032f,.047f,.0026f));
        }
        z.add(new Zone(HANDS,2,.647f,M24BodyRetarget.y(.647f,.800f),
            .131f,.037f,.048f,.043f,.0025f));
        // A subtle arch underfoot. Lifting local underfoot skin is a REAL
        // 3D Y displacement, not painted arch shading or an extra foot cap.
        z.add(new Zone(FEET,1,.205f,M24BodyRetarget.y(.205f,.080f),
            .206f,.094f,.049f,.100f,.009f));
        z.add(new Zone(FEET,2,.215f,M24BodyRetarget.y(.215f,.10f),
            -.075f,.072f,.093f,.102f,-.004f));
        // Mild toe-web separation at four interdigit gaps per foot.
        for(int gap=0;gap<4;gap++){
            float x=.217f+(gap-1.5f)*.042f;
            z.add(new Zone(FEET,2,x,M24BodyRetarget.y(x,.050f),
                .396f-.012f*(gap+.5f),.012f,.041f,.040f,-.0035f));
        }
        return z.toArray(new Zone[0]);
    }
    private static float[] movedNormal(float nx,float ny,float nz,
             float gx,float gy,float gz,int axis){
        // Analytic inverse transpose of rank-one Jacobian:
        // J = I + e_axis outer(grad f).
        float divisor=1f+(axis==1?gy:gz);
        if(!Float.isFinite(divisor)||divisor<.70f)
            throw new IllegalArgumentException("Folding anatomical surface");
        float nAxis=axis==1?ny:nz;
        float sx=nx-gx*nAxis/divisor,
              sy=ny-gy*nAxis/divisor,
              sz=nz-gz*nAxis/divisor;
        float length=(float)Math.sqrt(sx*sx+sy*sy+sz*sz);
        if(!Float.isFinite(length)||length<1e-8f)
            throw new IllegalArgumentException("Invalid normal under sculpt");
        return new float[]{sx/length,sy/length,sz/length};
    }
    public static ArtKit.Model sculpt(ArtKit.Model source){
        if(source==null||source.vertices==null||source.vertices.length%27!=0)
            throw new IllegalArgumentException("Missing full-body mesh");
        Zone[] all=zones();
        float[] v=source.vertices.clone();
        for(int i=0;i<v.length;i+=9){
            if(!M25SkinPolish.isBodySkin(v[i+6],v[i+7],v[i+8]))
                continue; // preserve nails/eyes/hair/shorts
            float x=v[i],y=v[i+1],depth=v[i+2];
            float nx=v[i+3],ny=v[i+4],nz=v[i+5];
            for(int axis=2;axis>=1;axis--){
                float amount=0,gx=0,gy=0,gz=0;
                for(Zone zone:all){
                    if(zone.axis!=axis)continue;
                    // Both sides use mirrored landmarks, respecting
                    // actual left/right finger offsets and foot silhouette.
                    float side=x<0f?-1f:1f;
                    float px=(Math.abs(x)-zone.x)/zone.rx;
                    float py=(y-zone.y)/zone.ry;
                    float pz=(depth-zone.z)/zone.rz;
                    float distance=px*px+py*py+pz*pz;
                    if(distance>12f)continue;
                    float shifted=zone.delta*(float)Math.exp(-distance);
                    amount+=shifted;
                    gx+=shifted*(-2f*px/zone.rx)*side;
                    gy+=shifted*(-2f*py/zone.ry);
                    gz+=shifted*(-2f*pz/zone.rz);
                }
                if(Math.abs(amount)<1e-8f)continue;
                float[] n=movedNormal(nx,ny,nz,gx,gy,gz,axis);
                nx=n[0];ny=n[1];nz=n[2];
                if(axis==2)depth+=amount;else y+=amount;
            }
            v[i]=x;v[i+1]=y;v[i+2]=depth;
            v[i+3]=nx;v[i+4]=ny;v[i+5]=nz;
        }
        return new ArtKit.Model(v);
    }
}
