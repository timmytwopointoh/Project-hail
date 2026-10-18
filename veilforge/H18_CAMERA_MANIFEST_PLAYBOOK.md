# VEILFORGE H18 camera manifest binding playbook

Branch: feature/veilforge-camera-manifest-binding-20261017-h18
Parent: b1b3be1f3d064efde6867607daf8995cc5b51e3b
Origin: run 38993296206, task artifact 12085917087.
Before: run 39080109415, 18/18 successful jobs, four Android emulators, 154 captures, independent semantic and LOD passes.

Real screenshot inspection: props artifacts 12086056909 and 12118412446. Sword yaw0 is intentionally edge-on, not missing geometry; yaw225 and yaw250 show broadside. H13 improved framing. Five semantic visibility warnings remain review proposals.

Verified code defect: independent structural reviewer checked screenshot digests and counts without enforcing the canonical yaw/pitch and image name at each of 14 indices. A mislabeled distinct frame could pass that structural check. This is not evidence that a production screenshot was mislabeled.

Bounded correction: require canonical camera angle and filename in android_review.py, reject mismatches before reading the image. New synthetic regression builds a complete 154-PNG manifest and verifies wrong yaw and wrong image mapping are rejected. All original renderer, model, camera, GLES, provenance, replay, semantic, LOD and human-signoff gates stay unchanged.

Acceptance: new full 18-job factory, eight asset workers, one verified GLES APK, four Android 15 emulators, 154 real frames and independent reviews. Preserve rejected candidates. No claim of improved silhouettes, photorealism, real-phone performance or artistic approval. No merge or promotion.
