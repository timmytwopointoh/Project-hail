package game.ashenveil.veilbound;

/** Independent postcondition for the narrow real-model Studio repair pilot.
 * This file is NOT included in normal pre-patch baseline tests because the
 * original game intentionally fails the NaN gesture robustness check.
 */
public final class StudioFiniteGestureAcceptanceTest {
    private StudioFiniteGestureAcceptanceTest() {}
    private static void finite(String field, float value) {
        if (Float.isNaN(value) || Float.isInfinite(value))
            throw new AssertionError("Studio camera state poisoned: " + field);
    }
    public static void main(String[] args) {
        ModelStudio studio = new ModelStudio();
        studio.orbit(Float.NaN, Float.NaN);
        studio.pan(Float.NaN, Float.NaN);
        studio.dolly(Float.NaN);
        ModelStudio.Snapshot snapshot = studio.snapshot();
        finite("yaw", snapshot.yaw);
        finite("pitch", snapshot.pitch);
        finite("zoom", snapshot.zoom);
        finite("panX", snapshot.panX);
        finite("panY", snapshot.panY);

        studio.reset();
        studio.orbit(0.20f, -0.10f);
        snapshot = studio.snapshot();
        if (Math.abs(snapshot.yaw - .70f) > .00001f ||
            Math.abs(snapshot.pitch - .02f) > .00001f)
            throw new AssertionError("Valid touch orbit behavior regressed");
        System.out.println("VEILBOUND_STUDIO_FINITE_GESTURE_PASS");
    }
}
