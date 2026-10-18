# H21 screenshot visibility evidence playbook

Use real, hash-verified Android emulator screenshots only. Preserve the canonical 14 yaw/pitch angles, source SHA, APK SHA, and every rejected capture.

For each 192x192 center-cropped color silhouette, record normalized bounding width and height. Bind the lowest-coverage and strongest-coverage views to their camera angles. If the weakest view is narrow and another view has a tall, visible broadside, label `possible_edge_on_view`. If the weak view remains tall but low in mask coverage, label `low_color_contrast_or_thin_geometry`. Otherwise label `framing_or_visibility_review`.

These labels are hypotheses, never missing-geometry proof, artistic quality scores, or permission to change models. Keep every original review warning and its priority. The handoff validates indices, camera pairs, metric bounds and the no-artistic-approval flag. The dynamic review proposals are separate from the static queue backlog.

Run the full 18-job factory and verify 4 Android 15 roles, 154 accepted frames, strict structural/semantic/LOD gates and identical APK digest. Never auto-merge or promote an asset.
