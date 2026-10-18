# VEILFORGE H19 — independent LOD screenshot provenance

Origin: source 85f634f58d0a5863186b22a90c1fd74292cc8c2b, run 38993296206, handoff artifact 12085917087.
Latest successful baseline: H18 SHA fd1b3da746c2671396578736b401e3a23b6daed2, run 39087432244, 18/18 successful jobs, 4 Android 15 emulators, 154 accepted frames, independent semantic/LOD review.
Inspected original props screenshots artifact 12086056909 and H18 props artifact 12121147743: ceremonial_sword yaw0 is a genuine edge-on blade, while yaw225 and yaw250 show a broadside blade; no missing sword mesh inferred. H13 had already improved QA camera framing; do not re-edit geometry on the strength of a silhouette threshold.

## Scoped source defect
The LOD comparator previously read image paths and yaw/pitch from the two manifests without independently binding them to the canonical 14 camera views, source SHA, APK SHA, and actual PNG bytes. If its own downloaded inputs were altered or mislabeled after the structural reviewer ran, LOD could report a normal silhouette IoU from substituted frames. This is a reproducible code-level acceptance gap, not proof of compromised production screenshots.

## H19 correction
Add a read-only LOD evidence validator: require one scene-world and one nature-mobile report, canonical paths and yaw/pitch for 14 views per gate LOD, valid identical 40-hex source commits and 64-hex APK digests, and SHA-256 of each of the 28 actual PNGs. Fail closed on mismatches before opening frames. Preserve the existing IoU heuristic and warning threshold, all 4-emulator upstream gates, all models and games. Include positive 28-frame synthetic and negative tamper/camera/source/APK tests. LOD JSON records the verified origin.

Acceptance requires a fresh 18/18 run including 4 emulators, 154 screenshots, and both independent reviews. Passing is only technical screenshot integrity, not photorealism, artistic approval or physical-device performance. Rejected candidates are retained; no auto-merge or asset promotion.
