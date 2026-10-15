# VEILBOUND — Full Production Roadmap and Quality Gates

## North star
An original, atmospheric, story-led third-person dark-fantasy action RPG for
Android, with deliberate sword combat, readable enemy tells, exploration,
choices that affect quest outcomes, and art directed to a coherent premium look.
Inspiration: the exploration density of large fantasy RPGs and the tension of
methodical action combat. No copyrighted characters, names, mechanics assets or lore.

## Narrative bible (original)
**The world:** Avenfall, a kingdom where seven ward bells were said to keep the
sun alive. With six silent, ash rains each dusk and the dead wake as *Hushed*.
**The player:** the final Bellwarden, revenant sworn to restore the bells but
missing memories of having helped forge them.
**Companion:** Orla, a scribe preserved in a glass reliquary; unreliable but
never simply deceitful.
**Prologue:** Reach a ruined chapel through Mourning Vale, survive Hushed
sentinels, rekindle the ember shrine and challenge the Ash Knight guarding the
bridge. The knight says: 'We were never keeping darkness out.'
**Moral choice:** release the truth or mend the ancient lie; future endings
branch at the third bell.
**Visual palette:** weathered basalt, moon-silver, burnt gold, dead blue mist
and isolated amber flames. Original silhouettes, original heraldry.

## Milestones (do not collapse into one aspirational claim)
- **M0 — Foundation:** Gradle native Android, real 3D renderer, scene visible,
  controller, camera, packaged APK, crash-free boot, golden screenshot.
- **M1 — Vertical slice:** small explorable 3D region, combat, roll, death,
  checkpoint, interact prompt, opening lore beat, miniboss/bridge gate.
- **M2 — Visual bar:** bespoke modular fortress/ruins mesh kits, textured PBR or
  stylized physically inspired materials, dynamic sky and volumetric fog,
  water, particles, silhouettes, baked lighting and dynamic characters.
- **M3 — Character animation:** rigged models, blended locomotion, attacks,
  stagger, death, hit reactions, camera collision and lock-on.
- **M4 — Story and quests:** written/voiced dialogue, branching choice,
  journal, inventory, NPC schedules, map/fast travel, save/load.
- **M5 — World expansion:** interconnected zones and landmarks, encounter
  varieties, exploration rewards, real boss phases and checkpoints.
- **M6 — Premium polish:** profiling across Android GPUs, frame pacing, sound,
  accessibility, controller support, localization, QA and release signing.

## Acceptance gates for each build
1. Android Gradle assembles real APK; verify manifest, package, native classes.
2. Android emulator boots, installs, launches, screenshot is not blank/black.
3. Story screen can be dismissed and responsive joystick/camera controls work.
4. Attack, roll and interact have measurable state transition and screen effects.
5. Combat hit distance and stamina rules unit-tested (no infinite free attacks).
6. No use of WebView or HTML to impersonate native 3D.
7. Preserve a known-good APK, never silently overwrite signed app/install data.
8. Logs and screenshots retained; any failure reported and fixed before merge.
9. Measure FPS and frame timing on target hardware: prioritize stable 30+ FPS,
   adapt detail on weaker devices, aim for 60 where possible.
10. Real-device play test required before declaring production quality.

## Iteration process
Plan → implement smallest vertical improvement → compile/static checks →
emulator install/controls/screenshot → compare against prior reference →
inspect logs → repair → repeat → tag accepted artifact → next milestone.
Avoid unused assets/classes and keep assets traceable and original.

## Technical choice
Native Java Activity + GLSurfaceView + OpenGL ES 2.0 fallback renderer using
shader-based diffuse lighting and depth fog. ES2 coverage broadens device
compatibility; later ES3/Vulkan path can be adopted if profiling warrants.
Renderer builds static geometry once and keeps dynamic drawcalls bounded.
Android recommends GLSurfaceView and Renderer as the starting point for Java GL.
Reference: https://developer.android.com/develop/ui/views/graphics/opengl/about-opengl

## M0.4–M0.6 visual improvement iteration (October 2026)

- **Gameplay defect fixed:** camera-relative joystick right vector is
  `(-cos(yaw), +sin(yaw))`. Regression tests cover default and 90° cameras.
- **M0.4 native mesh kit:** new pure-Java procedural `ArtKit` generates Bellwarden,
  Hushed revenant, Ash Knight, longsword, greatsword and lanterns. Silhouette,
  triangle-budget, normals, finite-value and vertex-color preflight tests run on
  the JVM without starting Android.
- **Renderer cleanup:** retire >25 cube draw calls per character and unused
  old cloth/torso builders. Render each fused actor with a separate animated weapon.
- **M0.5 environment:** branching taper-cylinder dead trees, Gothic window
  tracery, varied grave markers, atmospheric ash vegetation and modular stone.
  Static geometry is batched to one draw call.
- **M0.6 atmosphere:** GPU lighting/fog preserved, shrine effects, combat
  telegraphs and performance diagnostics sampled at most once per ~1.35 seconds.
- **New QA gate:** `qa_analyze.py` generates image brightness/detail/contrast
  measurements, identifies GL runtime errors and extracts frame/drawcall stats.
  This is an automated risk signal, not proof of premium visual quality.
- **Release rule:** accept only a passing Android emulator workflow and
  keep M0.3 available as rollback. M0.7 proper skeletal rigging and animation,
  full authored PBR texture assets, dynamic global illumination and
  professional art direction remain future work.

## Performance budget

- Actor meshes: each ≤1,800 triangles; total six kit meshes ≤6,500 triangles.
- OpenGL ES2-compatible materials and lighting, one static batched world mesh.
- Avoid per-frame mesh generation. Use render telemetry to verify draw-call
  reductions; emulator FPS is not a real-phone measurement.
- Frame pacing: consider Android Game Development Kit Swappy after native
  integration and profiling; no unsupported claim of Swappy integration.

## M0.8 — Studio cinematics, close-up topology and material realism

- Preserve emulator-verified M0.7 source on a distinct branch.
- `CinematicArtKit`: non-destructive sculpt layer over the tested `DetailArtKit`
  with mathematically smooth normals, curved breastplates, laminated pauldrons,
  fluted helmets, double-sided pleated mantles, rib reliefs and fuller bevels.
  The gameplay model remains an independent lightweight Level of Detail.
- `SurfaceAtlas`: deterministic 512×512 RGBA diffuse and normal-roughness
  atlases for weathered limestone, hammered steel, cloth, and leather.
  Bound lazily to GLES2 texture units 1/2 while older gameplay pipeline uses
  its original detail map on texture unit 0.
- Studio-only shader approximates microfacet BRDF highlights, roughness,
  normal perturbation, image-based fill/rim and richer colored keys.
  It is PBR-inspired shading, not physically calibrated photogrammetry.
- Toggle **SCULPT: ULTRA / LITE** in the studio for side-by-side visual and
  frame-cost comparisons. Existing import and wireframe modes are maintained.
- Preflight validates each detailed surface, finite normals, albedo variability,
  metal/cloth roughness difference, imported OBJ and existing combat rules.
- Emulator checks model Atelier launch, 512px maps initialized, true
  original-scene navigation, close-up, boss, wireframe, architecture, and mesh LOD.
- APK size is not an arbitrary target: prioritize visual quality while measuring
  runtime memory and actual Motorola Moto G 2025 performance.
- Remaining professional-asset work: authentic UV-authoring, physical normal/
  ORM textures and color-managed lighting, artist-authored sculpted geometry,
  facial topology, imported rigged GLB with skeleton and motion clips.
