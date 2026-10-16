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
        s.nextItem(-1);
        ok(s.snapshot().item==16,"M28 integrated face must be a separate inspectable model");
        ok(Math.abs(s.snapshot().zoom-1.45f)<.02f,"M28 head must start in closeup");
        s.nextReviewView();
        ok("SIDE".equals(s.reviewViewName()),"M28 orbital side view missing");
        s.focusDetail();
        ok(s.snapshot().zoom<1.3f,"M28 eye-detail view missing");
        s.nextItem(-1);
        ok(s.snapshot().item==15,"M26 learned sculpt candidate must be a separate review slot");
        s.nextReviewView();
        ok("SIDE".equals(s.reviewViewName()),"M26 camera angle control missing");
        s.focusDetail();
        ok(s.snapshot().zoom<1.3f,"M26 face focus must remain available");
        s.nextItem(-1);
        ok(s.snapshot().item==14,"M25 face close-up must be selectable in Testing Grounds");
        ok(Math.abs(s.snapshot().zoom-1.45f)<.01f,"M25 face zoom must start close");
        s.nextReviewView();
        ok("SIDE".equals(s.reviewViewName()),"M25 face profile angle missing");
        s.focusDetail();
        ok(s.snapshot().panX==0f&&s.snapshot().zoom<1.3f,
           "Face focus cannot be offset toward a hand");
        s.nextItem(-1);
        ok(s.snapshot().item==13,"Deformation test must be inspectable in Testing Grounds");
        s.nextReviewView();
        ok("SIDE".equals(s.reviewViewName()),"Deformation test view switching");
        s.nextItem(-1);
        ok(s.snapshot().item==12,"Sculpted hand asset must have its own game viewer");
        s.focusDetail();
        ok(s.snapshot().zoom<1.85f,"Hand sculpt focus should enable close study");
        s.nextReviewView();
        ok("SIDE".equals(s.reviewViewName()),"Sculpted hands four-angle inspection");
        s.nextItem(-1);
        ok(s.snapshot().item==11,"Human studio selection");
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
