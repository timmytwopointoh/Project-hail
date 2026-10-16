package game.ashenveil.veilbound;

/**
 * CPU-only startup bundle prepared on one background Java thread before the
 * first GL surface. Real geometry and texture work happens under the splash,
 * not in cosmetic timer callbacks. No network, analytics or downloaded assets.
 *
 * Immutable references are passed to the GL thread only after construction;
 * OpenGL uploads and shader compilation remain on the GL context thread.
 */
public final class BootAssets {
    public interface Progress { void stage(int percent,String description); }
    public final ArtKit.Model hero,heroLite,premiumSword;
    public final CharacterRig.Parts heroRig,heroLiteRig;
    public final ArtKit.Model flagstone,cenotaph,reliquary,roots;
    public final byte[] stoneRgba;
    public final SurfaceAtlas.Pair atlas;
    private BootAssets(ArtKit.Model hero,ArtKit.Model heroLite,
                       ArtKit.Model premiumSword,CharacterRig.Parts rig,
                       CharacterRig.Parts liteRig,ArtKit.Model flagstone,
                       ArtKit.Model cenotaph,ArtKit.Model reliquary,
                       ArtKit.Model roots,byte[] stone,SurfaceAtlas.Pair atlas){
        this.hero=hero;this.heroLite=heroLite;this.premiumSword=premiumSword;
        this.heroRig=rig;this.heroLiteRig=liteRig;
        this.flagstone=flagstone;this.cenotaph=cenotaph;
        this.reliquary=reliquary;this.roots=roots;
        this.stoneRgba=stone;this.atlas=atlas;
    }
    public static BootAssets prepare(Progress update){
        update.stage(5,"Reading offline game resources");
        ArtKit.Model hero=CinematicArtKit.bellwarden();
        update.stage(20,"Forging shaped Bellwarden armor");
        ArtKit.Model lite=CinematicArtKit.bellwardenLite();
        ArtKit.Model sword=CinematicArtKit.sword();
        update.stage(35,"Rigging the player and movement");
        CharacterRig.Parts rig=CharacterRig.split(hero,false,false);
        CharacterRig.Parts liteRig=CharacterRig.split(lite,false,false);
        HeroPose.sample(new HeroPose.Frame(),.1f,.2f,.1f,0f,0f,0f,0f);
        update.stage(49,"Preparing the ancient stone and reliquaries");
        ArtKit.Model stone=EnvironmentKit.flagstone();
        ArtKit.Model tomb=EnvironmentKit.cenotaph();
        ArtKit.Model iron=EnvironmentKit.reliquary();
        ArtKit.Model roots=EnvironmentKit.rootFan();
        update.stage(62,"Baking stone surface detail");
        byte[] small=MaterialTextures.stoneRgba();
        update.stage(72,"Baking steel, leather and cloth materials");
        SurfaceAtlas.Pair atlas=SurfaceAtlas.bake();
        update.stage(85,"Transferring prepared meshes to the renderer");
        return new BootAssets(hero,lite,sword,rig,liteRig,stone,tomb,iron,roots,
                              small,atlas);
    }
}
