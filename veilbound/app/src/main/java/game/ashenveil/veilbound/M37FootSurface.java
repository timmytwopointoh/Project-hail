package game.ashenveil.veilbound;

/**
 * M37 conservative foot sculpt, using anatomical landmarks rather than a
 * uniformly rounded procedural boot:
 *
 * - medial longitudinal arch: elevated plantar skin between heel and ball
 * - flatter lateral weight-bearing column, continuous with the midfoot
 * - dorsal metatarsal slope and first metatarsophalangeal (big-toe) mound
 * - calcaneal heel transition with preserved rear contact region
 *
 * Applied ONLY after the M37 source foot SDF has five distinct toe rays.
 * These are connected-surface vertex deformations, not texture decals.
 * Earlier candidate meshes, old knight, UV/materials and leg bones unchanged.
 */
public final class M37FootSurface {
    private M37FootSurface(){}

    private static final class Zone {
        final int axis;
        final float x,y,z,rx,ry,rz,amplitude;
        Zone(int axis,float x,float y,float z,
             float rx,float ry,float rz,float amplitude){
            this.axis=axis;
            this.x=x;this.y=y;this.z=z;
            this.rx=rx;this.ry=ry;this.rz=rz;this.amplitude=amplitude;
        }
    }
    // The Y values are in RETARGETED model coordinates; arch calculations
    // must not accidentally compare world Y to unscaled source foot Y.
    private static final Zone[] ZONES={
        // Medial arch is higher than the lateral longitudinal arch.
        new Zone(1,.155f,.028f,.145f,.070f,.062f,.115f,.020f),
        new Zone(1,.269f,.035f,.151f,.065f,.059f,.105f,.0030f),
        // Keep the distal metatarsal heads fuller under the ball.
        new Zone(1,.204f,.074f,.311f,.107f,.052f,.071f,-.0035f),
        // Subtle metatarsal extensor slope on upper foot (not a boot toe).
        new Zone(1,.213f,.203f,.232f,.112f,.067f,.110f,.0043f),
        // Hallux MTP joint and lateral toe tendons have different volumes.
        new Zone(1,.137f,.116f,.365f,.050f,.038f,.056f,.0039f),
        new Zone(1,.256f,.110f,.351f,.074f,.036f,.054f,.0025f),
        // The rear calcaneal curve should meet the ankle cleanly.
        new Zone(2,.216f,.121f,-.046f,.094f,.100f,.072f,-.0043f)
    };

    public static ArtKit.Model sculpt(ArtKit.Model source){
        if(source==null||source.vertices==null||source.vertices.length%27!=0)
            throw new IllegalArgumentException("Invalid anatomical foot source");
        float[] out=source.vertices.clone();
        for(int i=0;i<out.length;i+=9){
            float x=out[i],y=out[i+1],z=out[i+2];
            if(Math.abs(x)<.055f||Math.abs(x)>.40f||
               y<-.04f||y>.41f||z<-.19f||z>.56f)
                continue;
            if(!M25SkinPolish.isBodySkin(out[i+6],out[i+7],out[i+8]))
                continue;
            float nx=out[i+3],ny=out[i+4],nz=out[i+5];
            for(int axis:new int[]{2,1}){
                float movement=0f,gx=0f,gy=0f,gz=0f;
                for(Zone q:ZONES){
                    if(q.axis!=axis)continue;
                    float dx=(Math.abs(x)-q.x)/q.rx;
                    float dy=(y-q.y)/q.ry,dz=(z-q.z)/q.rz;
                    float dist=dx*dx+dy*dy+dz*dz;
                    if(dist>13f)continue;
                    float change=q.amplitude*(float)Math.exp(-dist);
                    movement+=change;
                    gx+=-2f*dx*change/q.rx*(x<0f?-1f:1f);
                    gy+=-2f*dy*change/q.ry;
                    gz+=-2f*dz*change/q.rz;
                }
                if(Math.abs(movement)<1.e-8f)continue;
                if(Math.abs(movement)>.022f)
                    throw new IllegalArgumentException("Excessive foot motion");
                float divisor=1f+(axis==1?gy:gz);
                if(!Float.isFinite(divisor)||divisor<.72f)
                    throw new IllegalArgumentException("Foot sculpt folded");
                float component=axis==1?ny:nz;
                float rx=nx-gx*component/divisor,
                      ry=ny-gy*component/divisor,
                      rz=nz-gz*component/divisor;
                float length=(float)Math.sqrt(rx*rx+ry*ry+rz*rz);
                if(!Float.isFinite(length)||length<1e-7f)
                    throw new IllegalArgumentException("Invalid foot normal");
                nx=rx/length;ny=ry/length;nz=rz/length;
                if(axis==1)y+=movement;else z+=movement;
            }
            out[i]=x;out[i+1]=y;out[i+2]=z;
            out[i+3]=nx;out[i+4]=ny;out[i+5]=nz;
        }
        return new ArtKit.Model(out);
    }
}
