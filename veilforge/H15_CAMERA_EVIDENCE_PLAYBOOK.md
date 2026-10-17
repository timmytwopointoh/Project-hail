# H15 sword camera evidence playbook

Validated before: run 39067049952, source 350151ad86264b26ac5980babe870872d0999e61, props artifact 12114185198. Validated after: run 39072830533, source 44bff23aa7f7bc9874a97d147868b1b0c4752ed9, props artifact 12116056704.

Both passed 18/18 jobs, four Android 15 emulators, 154 accepted frames, independent structural/semantic/LOD review. All 42 props frames in each artifact were pixel-distinct. Sword min foreground: .00062391 -> .00151910; max: .01038954 -> .02541775; mean: .00441972 -> .01092820 (2.473x). The thin edge-on blade is intentional. No mesh edits.

Original run 38993296206 had stale adjacent frames. H13 run 39071499467 accepted a chest screenshot as sword; rejected artifact 12115067670 must remain rejected. The independent comparator checks decoded pixels, exact SHA and all 14 yaw/pitch views, even when PNG metadata changes. Do not delete rejected candidates or promote assets.

Run: python3 veilforge/vq_android_camera_evidence.py --before h12.zip --after h14.zip --asset ceremonial_sword --out sword.json

This is inspection occupancy, NOT artistic quality, photorealism, physical phone performance, or unrestricted self-repair. Dynamic review tasks never execute automatically.
