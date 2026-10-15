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
        s.nextMaterial();s.nextLight();
        ok(s.snapshot().material==1&&s.snapshot().light==1,"Studio lighting and material");
        float old=s.snapshot().yaw;s.toggleTurntable();s.tick(.3f);
        ok(s.snapshot().yaw!=old,"Turntable must rotate");
        s.focusDetail();
        ok(s.snapshot().zoom<2f,"Close inspection must frame hand geometry");
        ok(!s.snapshot().autoTurn,"Close inspection disables turntable");
        s.reset();ok(!s.snapshot().autoTurn,"Reset must disable turntable");
        System.out.println("VEILBOUND_MODEL_STUDIO_PASS camera, zoom, pan, selector, lights, shaders, turntable");
    }
}
