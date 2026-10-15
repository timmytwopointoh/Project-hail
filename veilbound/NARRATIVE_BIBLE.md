# VEILBOUND — Narrative & World Bible v0.1
**Spoilers follow.** A self-contained original dark-fantasy world and moral arc.

## Promise to the player
The pilgrimage is about restoring a dying realm—but every restoration
reveals that the thing you're saving may have been built on a deliberate lie.
Combat expresses grief and duty, not simple monster hunting. Bosses speak,
remember, and have reasons to resist the player.

## History
Two hundred years ago, Avenfall survived the Long Dimming by raising seven
enormous ward bells. The bells were said to ward off the dark, but they were
not alarms. They were locks. Each bell pinned down one of the seven memories
of **Ilyra**, a celestial being whose living grief could make people remember
the lives they never got to live. The rulers feared a population impossible
to deceive, and chained her grief beneath their capital.

The bellwardens originally escorted pilgrims, then slowly became jailors.
The player participated in the first ringing, but that memory was stripped
from their armor and soul. After the sixth bell breaks, an old oath revives
the last Bellwarden. They wake in a field of black funeral grass.

## Characters
- **The Bellwarden** — player character, armored revenant, silent when the
  player remains silent; eventually chooses what kind of duty matters.
- **Orla Vey** — a historian preserved as a blue ember inside a cracked
  reliquary. Knows the bells are seals, refuses to disclose why she broke
  the sixth. Promises truth in exchange for an escort.
- **The Ash Knight, Caelen** — first miniboss; once the Bellwarden's sworn
  shield. His final words: "We were never keeping darkness out."
- **The Choir Without Mouths** — hollowed knights whose attacks begin as
  ritual motions. They were compelled to guard their own burial places.
- **King Regent Severin** — built his reign on the idea that peace requires
  a shared myth. Antagonist but not cartoonishly evil.
- **Ilyra** — not a final monster to kill: a consciousness that cannot
  distinguish revenge from justice until the player's choices give it form.

## Act structure
### I — Mourning Vale
The last ember shrine, drowned chapel, old pilgrim causeway and Ash Knight.
Collect two ash sigils to reach the boss, ignite the shrine for a checkpoint,
recover a scratched inscription that contradicts the official history.
Final reveal leads to Orla's reliquary and the fractured bell road.

### II — Salt & Bone
The drowned city of Cindermere. A flooded cathedral, survivors bargaining
for memory, a boss that wears the voice of the Bellwarden's mentor.
Choice: save the living by surrendering a truthful memory, or preserve
the memory and abandon part of the city to the rising tide.

### III — The Palace of Silent Hours
Cathedral-machine where bells ring without sound, political factions trying
to control the player's testimony, revelation of the original oath.
Major branching point: break the remaining seals or replace the old lie
with a new voluntary covenant.

### IV — The Hollow Sun
Reach the star wound beneath the capital. Confront Ilyra and the Regent.
Conclusions based on mercy, secrets uncovered, and alliances protected:
**The Unbound Dawn**, **The Last Bell**, **A Chorus of Ash**.

## Prologue scene beats and environmental storytelling
1. **Awakening** — camera opens on moon and bell tower. Subtitle:
   "The sixth bell died at sundown. The seventh still knows your name."
   The first touch begins the pilgrimage.
2. **Ember shrine** — copper sigil flickers within a stone plinth. Lit
   shrine becomes recovery checkpoint. Message: "The ember remembers you."
3. **Broken chapel** — wall plaque: "The bells did not warn the dead.
   They taught the living what to forget." Hidden inscription optional.
4. **Hushed sentinels** — hollow armor wrapped in ash, ritual sword tells.
   Defeating them recovers ash sigils that unlock the causeway.
5. **Ash Knight** — before attack: "Turn back, Bellwarden. You were here
   when we buried the sky." During second phase, lights on broken statues
   turn amber. On defeat: "We were never keeping darkness out."
6. **Seventh bell** — victory is an uneasy discovery, not pure triumph:
   the final bell releases one truthful whisper from the imprisoned star.

## Tone and aesthetic rules
- Understated, precise dialogue; no long exposition during combat.
- Contrast silence with dramatic bells/low strings instead of constant music.
- A unique visual language: thorn crowns, rings of copper in wet basalt,
  moon-blue crystalline embers, silver cloth and dying yellow grass.
- Hero shapes remain readable against a desaturated environment.
- Lighting should direct discovery: warm = sanctuary, cold blue = hidden
  truth, arterial red = enemy windup.
- Build original meshes/materials/foley; no borrowed game assets.

## Choices and flags for implementation milestones
- `shrineKindled`, `relicInscriptionRead`, `orlaTrust`,
  `caelenMemoryRecalled`, `cindermereSaved`, `sealsBroken`
- Save format must version flags and support migration.
- Branches change NPC availability, side quests, boss lines and ending.
- No false choices where both buttons silently produce the same outcome.
