package game.ashenveil.veilbound;
public final class ModelStudioTest {
    private static void ok(boolean c,String message){if(!c)throw new AssertionError(message);}
    public static void main(String[] args){
        ModelStudio s=new ModelStudio();
        ok(s.snapshot().item==0,"Must start Bellwarden");
        for(int i=0;i<ModelStudio.ITEMS.length;i++)s.nextItem(1);
        ok(s.snapshot().item==0,"Selector must wrap");
        s.nextItem(-1);
        ok(s.snapshot().item==ModelStudio.ITEMS.length-1,"Reverse selector wrap");
        s.orbit(2,100);ok(s.snapshot().pitch<=1.18f,"Pitch upper clamp");
        s.orbit(-1,-200);ok(s.snapshot().pitch>=-1.15f,"Pitch lower clamp");
        s.dolly(-300);ok(s.snapshot().zoom>=1.05f,"Camera cannot clip model");
        s.dolly(300);ok(s.snapshot().zoom<=24.0f,"Camera max range");
        s.pan(999,-999);ok(Math.abs(s.snapshot().panX)<=4.2f,"Pan X safe");
        ok(Math.abs(s.snapshot().panY)<=3.2f,"Pan Y safe");
        for(int i=0;i<ModelStudio.MATERIALS.length;i++)s.nextMaterial();
        ok(s.snapshot().material==0,"Materials must cycle all supported inspection modes");
        s.selectImported();
        ok(s.snapshot().item==ModelStudio.ITEMS.length-1,"File import must select last studio slot");
        ok(s.snapshot().ultraMesh,"Ultra sculpt should be the default");
        s.toggleMeshDetail();
        ok(!s.snapshot().ultraMesh,"LOD comparison must switch off ultra mesh");
        s.toggleMeshDetail();
        ok(s.snapshot().ultraMesh,"LOD comparison must switch back");
        s.nextMaterial();s.nextLight();
        ok(s.snapshot().material==1&&s.snapshot().light==1,"Studio lighting and material");
        float old=s.snapshot().yaw;s.toggleTurntable();s.tick(.3f);
        ok(s.snapshot().yaw!=old,"Turntable must rotate");
        s.focusDetail();
        ok(s.snapshot().zoom>1.80f&&s.snapshot().zoom<3f,"Detail framing should capture full glove without clipping");
        ok(!s.snapshot().autoTurn,"Close inspection disables turntable");
        s.reset();ok(!s.snapshot().autoTurn,"Reset must disable turntable");

        // Regression: invalid touch and clock deltas previously poisoned the
        // camera with NaN. Ignore them instead of jumping to clamp boundaries.
        ModelStudio.Snapshot stable=s.snapshot();
        s.orbit(Float.NaN,Float.NaN);
        s.pan(Float.NaN,Float.POSITIVE_INFINITY);
        s.dolly(Float.NaN);
        s.dolly(Float.NEGATIVE_INFINITY);
        s.toggleTurntable();s.tick(Float.NaN);s.tick(Float.POSITIVE_INFINITY);
        ModelStudio.Snapshot safe=s.snapshot();
        ok(safe.yaw==stable.yaw&&safe.pitch==stable.pitch,
            "Invalid orbit/tick inputs must not move or poison camera");
        ok(safe.zoom==stable.zoom&&safe.panX==stable.panX&&safe.panY==stable.panY,
            "Invalid pan/dolly inputs must preserve stable camera");
        ok(!Float.isNaN(safe.yaw)&&!Float.isNaN(safe.pitch)&&!Float.isNaN(safe.zoom),
            "All camera state must remain finite");
        s.toggleTurntable();
        s.orbit(.20f,-.10f);
        ok(Math.abs(s.snapshot().yaw-.70f)<.00001f,
            "Normal finite yaw orbit must remain unchanged");
        ok(Math.abs(s.snapshot().pitch-.02f)<.00001f,
            "Normal finite pitch orbit must remain unchanged");
        s.pan(Float.NaN,.25f);
        ok(s.snapshot().panX==0f&&s.snapshot().panY==.25f,
            "One invalid axis must not suppress valid movement on other axis");
        System.out.println("VEILBOUND_MODEL_STUDIO_PASS camera, zoom, pan, selector, lights, shaders, turntable");
    }
}
