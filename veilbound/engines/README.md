# VEILBOUND — Team production engines (M13)

Each specialist has its own **separate GitHub Actions runner, isolated process,
output directory and QA artifact**, while all six use one audited Java geometry
and game-state kernel. This is concrete computational engine access; it is not
six copies of Blender, six trained AI models, or six unrestricted shell users.

| Team | Actual engine output | Editable AI-owned sources |
|---|---|---|
| Models | **bellwarden_forged_armor.obj**: new profiled/keel/outlined plates | `ShapeEngine.java`, `CinematicArtKit.java`, `DetailArtKit.java`, `ObjMeshLoader.java` |
| Animation | **hero_pose_180_frames.csv**: frame-by-frame head, feet, torso, cape, swing | `HeroPose.java`, `CombatMotion.java`, `CharacterRig.java` |
| Materials | **material_albedo.png**, **material_normal_roughness.png**: actual original 512px atlases | `MaterialTextures.java`, `SurfaceAtlas.java`, `ArtKit.java` |
| World | **carved_cenotaph.obj**: existing stage geometry reconstructed as an OBJ | `EnvironmentKit.java` |
| Combat | **combat_swing_phases.csv**: continuous real physics swing timing | `WorldState.java` |
| Studio | **bellwarden_studio_preview.obj**: independent character export | `ModelStudio.java` |

Use [GitHub Actions / Six Isolated Production Engines](https://github.com/timmytwopointoh/Project-hail/actions/workflows/veilbound-team-engines.yml), select branch `feature/veilbound-m13-loading-sculpt-engines`, run manually (or push a change to the appropriate engine source). The matrix executes all six teams and archives six separately named artifacts. The Java entry point is `veilbound/tools/TeamEngineCLI.java`; CI runs `veilbound/scripts/team_engine_check.py` and fails if a real mesh, curve file, PNG, or report is missing. Every artifact is local, original, reproducible and subject to review.

## Sculpting instead of disguised primitive duplication

`ShapeEngine.loft(Ring[], sides, Palette)` generates a connected surface from
hand-controlled cross sections. Each ring can specify **width, depth, height,
offset, keel/raised chest ridge and twist**. Plate silhouettes can use
`ShapeEngine.bevelPlate(xy, backDepth, ridgeHeight, thickness, face, edge)`.
These forge edged polygonal shapes, not spheres with painted trim. All
vertices have geometric face normals and native Android-compatible RGB.
`ShapeEngine.bellwardenForgedPlates(mobile)` currently supplies twelve
profiled pieces to the existing animated hero. Source profiles can be edited
by the models worker and validated by `ShapeEngineTest` before review.

This is a first-generation procedural modeling kernel, not Blender:
there is no brush-based topology sculpting, UV-unwrapping, skin weighting,
full cloth simulation, or imported photogrammetry in this system. The
separate OBJ exports let external DCC artists refine the shape later.
Blender/headless or advanced procedural mesh tools could be installed in
the same isolated team jobs for higher-fidelity later milestones.

## AI worker safeguards

Open-weight local coding AIs remain text-only, generating **scoped proposals**
with exact source matches. Updated allowlists let the modeling team edit
`ShapeEngine.java` and animation team edit `HeroPose.java`. Proposals
must pass trusted Java tests. No engine runs an AI-authored command, merges
unreviewed sources or accesses signing keys. `BootAssets` deliberately prepares only production content needed at
phone startup; **none of these development engines runs in the installed APK**.

## Real Android loading pipeline

1. Native splash paints immediately with an original Bellwarden launcher icon.
2. `BootAssets.prepare()` asynchronously sculpts hero high+low LOD,
   composes the combat weapon, rigs the head/cape/limbs, prepares flagstones,
   cenotaphs, reliquaries and roots, then bakes 128px stone detail and paired
   512px albedo/normal-roughness atlases. All percent updates correspond to
   completed work on that background thread.
3. Only after preparation, the OpenGL thread compiles shaders and uploads
   model buffers and texture atlases. The title menu is revealed **after
   its first rendered frame**, avoiding an unresponsive black screen.
4. `VEILBOUND_BOOT` logcat stages and `00_startup_loading.png` are captured
   by the Android 15 emulator. Java loader and shape tests are mandatory.

The previous M12 tested APK is retained separately. SwiftShader GPU FPS is
not a Moto G 2025 hardware benchmark; test the downloaded M13 build on device.
