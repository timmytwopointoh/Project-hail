package game.ashenveil.veilbound;

/** Gameplay regressions reproduced from physical-device player feedback. */
public final class CombatGameplayTest {
    private static void check(boolean x,String why){if(!x)throw new AssertionError(why);}
    private static void step(WorldState w,int ticks){for(int i=0;i<ticks;i++)w.update(.025f);}
    public static void main(String[] args) {
        WorldState w=new WorldState();w.start();w.start();
        w.x=w.foes[0].x;w.z=w.foes[0].z-1.7f;w.heading=0;
        w.toggleLock();w.update(.025f);
        check(w.snapshot().targetIndex==0,"Lock-on must choose nearest visible target");
        w.movement(1,0);step(w,45);
        check(w.exertion>.12f,"Movement must cause heavier breathing");
        w.movement(0,0);float fatigue=w.exertion;step(w,70);
        check(w.exertion<fatigue,"Idle pose must gradually recover breath");
        w.x=w.foes[0].x;w.z=w.foes[0].z-1.3f;w.heading=0;
        w.lockTarget=-1;w.attackTime=0;w.stamina=100;
        float hp=w.foes[0].hp;w.attack();step(w,29);
        check(w.foes[0].hp<hp,"Physical frontal swing must connect");
        check(w.stainCount>=2,"Contact creates green floor splatter");
        float firstStain=w.stains[0].born;step(w,50);
        check(w.stains[0]!=null&&w.stains[0].born==firstStain,
              "Floor splatter remains after the hit");
        // Kill all three regular enemies: only two required quest items exist.
        for(int i=0;i<3;i++){
            WorldState.Foe f=w.foes[i];
            f.hp=1;f.alive=true;f.stagger=0;f.recovery=0;f.windup=0;
            w.x=f.x;w.z=f.z-1.5f;w.heading=0;w.lockTarget=-1;
            w.attackTime=0;w.swing=0;w.stamina=100;w.attack();step(w,30);
            check(!f.alive,"Target "+i+" must be defeated");
        }
        check(w.fragments==2,"Cannot display three out of two sigils");
        check(!w.snapshot().objective.contains("3/2"),"HUD counter must be capped");
        w.x=1;w.z=1;w.heading=0;w.lockTarget=-1;
        WorldState.Foe back=w.foes[0];back.alive=true;back.hp=70;
        back.x=1;back.z=-.5f;
        w.attackTime=0;w.swing=0;w.stamina=100;
        w.attack();step(w,28);
        check(back.hp==70,"A forward sword arc must not strike behind the player");
        System.out.println("VEILBOUND_COMBAT_GAMEPLAY_PASS lock breathing blood sigil_cap rear_hit");
    }
}