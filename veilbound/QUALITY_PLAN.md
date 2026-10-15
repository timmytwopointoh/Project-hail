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
