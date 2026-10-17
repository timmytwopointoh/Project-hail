# VQ / Trion private per-device learning loop

This isolated prototype adds an **actual small trainable neural preference network** (5 input features, four tanh hidden nodes, two tanh outputs) to VQ Studio. The feature vector is an explicitly limited geometric-style signal, **not an open-vocabulary object recognition model**, and it is not a fine-tuned Qwen. Each installation creates a private seed and saves weight matrices in its own Android SharedPreferences. No cross-device synchronization, telemetry, image upload or user data sharing. Geometry changes are bounded to +/-15%, never modifying explicit FORGE plans.

Unknown concept -> **needs_details** with a specific question -> user supplies named parts and approximate dimensions -> original procedural FORGE/1 mesh is built and validated -> user approves or corrects proportions inside Trion -> corrections perform bounded on-device SGD on private weights. New proposals still need approval; a good source-level mesh does not imply correct anatomy, realistic materials, game-ready animation, or human approval.

The present clarification grammar is deliberately transparent:
`base box 2 1 1 center; dome ellipsoid 1.3 .7 1.3 top`
Supported placements: center, top, bottom, left, right, front, back. The question adapts to characters, outfits or other structures. Future Trion Qwen prompting can translate informal answers to this restricted language, but the unmodified Qwen cannot yet guarantee such translation.

Verification gate (pure Java with actual procedural OBJ geometry):
```sh
javac -d /tmp/vq-learning vq-studio/app/src/main/java/com/trioncompasitor/vqstudio/{OfflineGeometry,ForgeSpec,ForgeLang2,VQPersonalizer,VQActiveLearning}.java vq-studio/tests/VQLearningSelfTest.java
java -cp /tmp/vq-learning com.trioncompasitor.vqstudio.VQLearningSelfTest
```

Release needs paired Android/emulator confirmation. No CI artifacts or automatic phone jobs are activated. Keep the users' requested model and its approval separate from low-level geometry checks.
