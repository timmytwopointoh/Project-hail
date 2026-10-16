package game.ashenveil.veilbound;

/**
 * Deterministic full-body Bellwarden pose sequencer, no allocations per frame.
 * Torso anticipation and sword sweep use the exact collision timeline.
 * Values are angular degrees; capsule-like rigid armor limbs stay at fixed
 * anatomical pivots, and cloak independently follows the shoulder line.
 */
public final class HeroPose {
    private HeroPose(){}
    public static final class Frame {
        public float bob,rootPitch,rootYaw,rootRoll,leftArmPitch,rightArmPitch;
        public float leftArmRoll,rightArmRoll,leftLegPitch,rightLegPitch;
        public float mantlePitch,mantleYaw,guardLean,breath;
    }
    private static float clamp(float v,float min,float max){
        return Math.max(min,Math.min(max,v));
    }
    private static float smooth(float v){v=clamp(v,0f,1f);return v*v*(3f-2f*v);}
    /** Calculated onto reused Frame: does not allocate while drawing. */
    public static void sample(Frame p,float tm,float phase,float movement,
                              float fatigue,float attackRemaining,float dodgeRemaining,
                              float stagger){
        float move=clamp(movement,0f,1f);
        float tired=clamp(fatigue,0f,1f);
        float stride=(float)Math.sin(phase*1.4f);
        float impact=(float)Math.cos(phase*2.8f);
        float breathFrequency=1.9f+2.8f*tired;
        p.breath=(float)Math.sin(tm*breathFrequency)*(.026f+.048f*tired);
        float stance=(float)Math.sin(tm*.54f)*.72f*(1f-move);
        float attack=attackRemaining>0?
                CombatMotion.progress(attackRemaining):-1f;
        float anticipation=attack<0?0f:smooth(attack/.29f);
        float contact=attack<0?0f:smooth((attack-.29f)/.46f);
        float follow=attack<0?0f:smooth((attack-.73f)/.27f);
        float hit=clamp(stagger*2.7f,0f,1f);
        float evade=dodgeRemaining>0?
                (float)Math.sin(Math.PI*clamp(1f-dodgeRemaining/.48f,0f,1f)):0f;
        float shoulderWindup=-27f*anticipation*(1f-contact);
        float shoulderStrike=78f*contact-24f*follow;
        p.guardLean=anticipation*(1f-contact);
        p.bob=.035f*move*(1f-impact)+p.breath*.36f-evade*.13f;
        // Anticipatory counter-rotation and physical follow through across
        // shoulders, pelvis and arms rather than just rotating the weapon.
        p.rootYaw=8f*stance/7f+28f*anticipation-74f*contact+34f*follow;
        p.rootPitch=3.0f*move+17f*contact*(1f-follow)+
                    tired*p.breath*40f+12f*hit+22f*evade;
        p.rootRoll=stance+3.8f*stride*move+7f*evade+9f*hit;
        p.leftArmPitch=-13f-24f*stride*move+12f*p.guardLean+
                       19f*contact-18f*evade;
        p.rightArmPitch=15f+23f*stride*move+
                        shoulderWindup-shoulderStrike+20f*evade;
        p.leftArmRoll=-8f+8f*stance*.3f+21f*contact;
        p.rightArmRoll=-23f-26f*anticipation+42f*contact-14f*follow;
        p.leftLegPitch=30f*stride*move-32f*evade;
        p.rightLegPitch=-30f*stride*move+25f*evade;
        // The cape lags the upper body and catches movement, with controlled
        // counter-sway; this is not simulated cloth/skin weight painting.
        p.mantlePitch=-4f-8f*move*(.5f+.5f*impact)+
                      6f*contact-12f*evade-35f*p.breath;
        p.mantleYaw=-.28f*p.rootYaw+4.5f*(float)Math.sin(tm*1.2f)*move;
    }
}
