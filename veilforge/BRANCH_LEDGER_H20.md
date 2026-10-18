# VEILFORGE H20 isolated branch ledger — logcat subscription race

Branch: feature/veilforge-logcat-subscriber-handshake-20261017-h20
Parent SHA: 810e573b97f0d03f9ceee48c6a4725e35d398ceb (H19).
H18 last fully successful baseline: fd1b3da746c2671396578736b401e3a23b6daed2 / run 39087432244 (18/18).
H19 run 39090364319: 15 of 18 jobs succeeded, scene-world emulator failed before first camera view with `TimeoutError: No matching Android logcat event before deadline` at the one-shot startup nonce. Structural aggregator correctly failed 3/4 and LOD was skipped. No camera/geometry quality conclusion follows from this failure.
Original handoff: source 85f634f58d0a5863186b22a90c1fd74292cc8c2b, run 38993296206, artifact 12085917087. Examined original screenshot artifacts 12086056909 (props) and 12085179609 (nature): ceremonial_sword yaw0 is edge-on while later views broaden; ancient_tree is tiny in original framing. Subsequent isolated camera work already exists. Do not reclassify all narrow silhouettes as broken geometry.

## One bounded correction
Scope: `vq_logcat_stream.py`, isolated startup-race regression tests, this ledger and playbook only. ADB `shell log` can emit its unique nonce before `adb logcat` has subscribed; retry the **real** device nonce with a fixed 20-second total deadline and .75-second wait slices. Require that the **live subscriber** actually consumes the matching nonce before capture. Keep fatal GLES, lost subscriber, missing frames, wrong pack, stale frames, 4-emulator structural gate and independent semantic/LOD gates unchanged. No model edits, threshold relaxation, queue changes, auto-promotion or merge.

Before: one device probe, one 15-second wait, scene-world role failed at startup (0/42 captured there, 112/154 overall) on H19. After target: bounded probe retries, scene-world 42/42, all 4 roles 154/154, full 18/18 run, independent semantic/LOD pass, unchanged SHA binding and visual thresholds. These are acceptance targets, not achieved claims until run results confirm. Retain H19 failed-run evidence.

Artistic acceptance, real phone performance, photorealism and final human signoff remain open. H20 SHA/run: PENDING.
