package game.ashenveil.veilbound;

/**
 * Deterministic UV unwrap for OBJ/DCC export of the original hero mesh.
 * Uses dominant-normal axis projective UVs and correctly tiles the existing
 * original 2x2 micro-material atlas. Not a hand-authored seam/UV unwrap.
 *
 * The runtime shader instead samples these exact 2x2 material cells in
 * OBJECT SPACE. Object coordinates mean armor grain travels with the hero
 * rather than sliding across the character as the world moves.
 */
public final class MaterialMapping {
    private MaterialMapping(){}
    private static float fract(float x){return x-(float)Math.floor(x);}
    public static int tile(float r,float g,float b){
        boolean gold=b*1.25f<=r&&r>=.47f;
        boolean steel=b>=.44f&&b>=r*.91f;
        boolean cloth=b>=r*1.13f&&r<.46f;
        return gold||steel?SurfaceAtlas.STEEL:
               cloth?SurfaceAtlas.CLOTH:SurfaceAtlas.LEATHER;
    }
    public static float[] uv(float x,float y,float z,
                             float nx,float ny,float nz,
                             float r,float g,float b){
        float ax=Math.abs(nx),ay=Math.abs(ny),az=Math.abs(nz);
        float u,v;
        if(ay>.62f){u=x;v=z;}
        else if(ax>az){u=z;v=y;}
        else{u=x;v=y;}
        int id=tile(r,g,b);
        float offsetU=(id%2)*.5f,offsetV=(id/2)*.5f;
        // Six-pixel safe gutter at each atlas tile boundary; texture grain
        // repeats inside a cell but will not sample a neighboring material.
        return new float[]{offsetU+.006f+.488f*fract(u*3.12f),
                           offsetV+.006f+.488f*fract(v*3.12f)};
    }
}
