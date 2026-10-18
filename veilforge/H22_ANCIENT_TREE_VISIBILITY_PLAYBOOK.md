# H22 — bounded ancient_tree shadow-side Android visibility trial

Source parent: `91ab9b01c731a34e87b13dfb4074e6bde1860518` (H21 successful 18/18 factory run `39096410349`). Original verified source: `85f634f58d0a5863186b22a90c1fd74292cc8c2b`, run `38993296206`, review-task artifact `12085917087`. Preserve these commits and all rejected Android frames as immutable evidence.

## Screenshot diagnosis (not an artistic score)

Downloaded H21 real Android 15 Pixel 7 `nature-mobile` screenshot artifact `12125490027`, semantic report `12124961191`, and dynamic review tasks `12123904783`. All 14 `ancient_tree` views show two intentionally separated tree instances. The low-coverage view is yaw 225/pitch 15 (index 9), SHA256 `5aa67bc608d972cf0b5d143b4dca13d5f10a3a211828f0f382e05e78f1d02805`; strongest is yaw 50/pitch 42 (index 2), SHA256 `82bb02bb43185538da96524f18eb7dd317f20eaec9f4cddde69db3f2fb65301d`. Semantic mask coverage minimum `0.00200`, maximum `0.03418`, low-view bbox width `0.29688`, height `0.47396`. This is **not** a proven missing mesh or clipping issue: both trees are present and their silhouette is tall. Their shadow-side foliage appears unusually dark against the existing clear color.

The sword's yaw 0 thin profile is an intentional edge-on angle; yaw 250 visibly shows its broadside. No sword geometry/camera changes are justified by the low mask alone.

## Single candidate and measurable acceptance

Only in the independent Android probe when `filter == ancient_tree`, change the approximate shader's diffuse ambient floor from `0.22` to `0.38`, preserving `1.0` direct-lit response and all normal/AO/material samplers. Keep every other filter (including `scene`) at `0.22`. No model, atlas, gameplay, camera, semantic threshold, queue, workflow, or auto-promotion changes. This is a **QA renderer visibility experiment**, not calibrated PBR or a game art upgrade.

After the full 18-job factory finishes, download the actual Pixel 7 screenshots and independent semantic JSON. Compare identical yaw 225/pitch 15 and yaw 50/pitch 42 masks (not overall Android foreground_fraction, which includes UI). Require four Android 15 roles, 154 real-angle accepted frames, identical APK digest, all structural/semantic/LOD gates, and no new clipped/blank/replayed frames. Record before/after per-angle coverage and bounding extents and inspect screenshots for washed-out foliage; reject/revert if the measured visibility or visual coherence worsens. Passing technical gates alone is not artistic signoff. Preserve rejected captures.

The dynamic `veilforge-android-next-iteration-tasks` artifact is review proposals only; it is not `veilforge/queue_backlog.json` and cannot automatically rewrite, approve, or merge models. Real-phone performance, realistic PBR, anatomy, 34 canonical milestones, 13 efficiency milestones and final human-artistic acceptance remain open.
