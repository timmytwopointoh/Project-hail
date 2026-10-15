package game.ashenveil.veilbound;

/** Self-contained JVM regression tests: deterministic, no emulator needed. */
public final class WorldRulesTest {
    private static void check(boolean yes,String why){
        if(!yes)throw new AssertionError(why);
    }
    public static void main(String[] args){
        WorldState w=new WorldState();
        check(w.snapshot().mode.equals("title"),"Game must open to title");
        w.start();check(w.snapshot().mode.equals("story"),"Prologue story must show");
        w.start();check(w.snapshot().mode.equals("playing"),"Prologue must be playable");
        float z=w.z;w.movement(0,1);
        for(int i=0;i<30;i++)w.update(.025f);
        w.movement(0,0);
        check(w.z>z+1,"Forward movement must change actual world position");
        w.x=-4.4f;w.z=11f;w.interact();w.update(.033f);
        check(w.snapshot().shrineLit,"Ember shrine must activate");
        check(w.hp==100,"Shrine restores health");
        WorldState.Foe enemy=w.foes[0];
        w.x=enemy.x;w.z=enemy.z-1.5f;w.heading=0;
        float prev=enemy.hp;
        w.attack();
        for(int i=0;i<19;i++)w.update(.024f);
        check(enemy.hp<prev,"Attack must damage a nearby enemy");
        check(w.stamina<100,"Attack must cost stamina");
        float stamina=w.stamina;w.roll();w.update(.027f);
        check(w.dodge>0&&w.invulnerable>0,"Dodge must have a genuine brief invulnerability window");
        check(w.stamina<stamina,"Dodge must cost stamina");
        check(!w.snapshot().objective.isEmpty(),"Objective must be available");
        w.hp=0;w.mode="dead";w.start();
        check(w.mode.equals("playing")&&w.hp==100,"Death must recover at checkpoint");
        check(Math.abs(w.z-11)<.01f,"Checkpoint respawn must use shrine position");
        System.out.println("VEILBOUND_WORLD_RULES_PASS movement, attack, stamina, dodge, shrine, respawn, quest");
    }
}