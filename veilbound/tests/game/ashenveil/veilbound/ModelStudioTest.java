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
        ok(!s.snapshot().vesperAsset,"OBJ import must not activate Vesper-only controls");
        s.selectVesperPose(2);
        ok(s.snapshot().pose==0,"OBJ import must reject Vesper-only poses");
        s.selectVesper();
        ok(s.snapshot().vesperAsset,"GLB import must activate Vesper-only controls");
        ok(Math.abs(s.snapshot().zoom-3.80f)<.01f,"Vesper camera must frame character closer");
        ok(s.snapshot().pose==0,"New Vesper GLB import resets to idle");
        s.selectVesperPose(1);ok(s.snapshot().pose==1,"T-pose button selects T-pose");
        s.selectVesperPose(2);ok(s.snapshot().pose==2,"Leg-up button selects leg-up");
        s.selectVesperPose(3);ok(s.snapshot().pose==3,"Dance button selects dance");
        s.selectVesperPose(99);ok(s.snapshot().pose==3,"Invalid pose index must not change pose");
        s.selectVesperPose(0);ok(s.snapshot().pose==0,"Idle button restores idle");

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
        s.nextItem(-1);
        ok(s.snapshot().item==11,"Human studio selection");
        s.selectVesperPose(2);
        ok(s.snapshot().pose==0,"Non-Vesper assets cannot enter Vesper pose modes");

        s.focusDetail();
        ModelStudio.Snapshot hand=s.snapshot();
        ok(Math.abs(2.12f+hand.panY-(.82f+.73f))<.15f,
           "Hand close-up must target the actual world-space fingers");
        ok(Math.abs(hand.panX-.554f)<.15f,"Hand center must be visible");
        ok(hand.zoom>1.25f&&hand.zoom<1.85f,"Close-up distance");
        s.nextReviewView();
        ok("SIDE".equals(s.reviewViewName()),"Human review cycle preserved");
        System.out.println("VEILBOUND_MODEL_STUDIO_PASS camera, zoom, pan, selector, lights, shaders, turntable");
    }
}
