# FORGE/1 — Offline construction language (v1)

The model is an assembly of **freshly generated geometry**, not a collection
of premade assets. Coordinates use meters and Y-up.

A structured model instruction looks like this:

```text
FORGE/1
model articulated_fox_study
part torso ellipsoid 0 1 0 1.4 .7 .6
part left_ear taper -.45 1.65 0 .2 .5 .2
part right_ear taper .45 1.65 0 .2 .5 .2
part leg_left cylinder -.4 .45 0 .24 .9 .24
part leg_right cylinder .4 .45 0 .24 .9 .24
```

Each `part` line gives a unique identifier, tool, center X/Y/Z and
width/height/depth in meters. Accepted tools are `box`, `ellipsoid`,
`taper`, and `cylinder`. A model accepts 1–64 named parts. All dimensions
must be positive and bounded; invalid coordinates, duplicate names, unknown
tools and oversized outputs are rejected.

A short ordinary-language request ("a large ancient tree with branches")
is translated conservatively using original algorithms for basic vegetation,
blades, containers and hills. Unsupported objects such as complex animated
humans, dragons, photorealistic characters, complex vehicles or arbitrary
buildings **must not** be represented falsely as a generic substitute. A
future, larger planner can propose the above part language, but VQ validates
it before meshing.

## A remembered technique is not a mesh

After VQ successfully generates and parses the final mesh, the private
SQLite database records only its named-part dimensional plan, triangle count,
source hash, timestamp and verified-use count. Enter "Use previous construction
technique, make it wider" or "Use last technique, make it taller" in Trion.
VQ reads the last verified plan, transforms its dimensions, and generates
fresh source triangles. No previous OBJ is copied or used as an asset pack.

Every job writes two original OBJ revisions in the private model repository;
auto-follow in VQ Studio loads only a changed validated revision and preserves
the interactive 3D camera.

**Current limits:** This milestone establishes structure, syntax, parameter
bounds and regenerated geometry. It does not implement inverse graphics,
free-form language comprehension for every possible object, skinning,
animation, realistic material baking or human-likeness QA. Work toward those
features through additional verified geometry tools and reference checks.

## FORGE/2 — Relative geometry and symmetry

```text
FORGE/2
model simple_robot
part torso box 0 1 0 1 1 .5
part head capsule 0 0 0 .5 .6 .5
attach head torso top 0.03
part ear_l taper -.3 0 .0 .12 .32 .12
attach ear_l head top 0
mirror ear_l ear_r x
```

New construction tools are `capsule`, `ring` (horizontal torus in X/Z),
and `ring_z` (upright torus in X/Y for wheel rims). All surfaces are newly
generated parametric vertices. The `attach CHILD PARENT FACE GAP` rule
supports top, bottom, left, right, front, and back, with a bounded
nonnegative gap in meters. `mirror SOURCE NEW_NAME x|z` duplicates
dimensions and reflects the source center across the selected axis.

The two operations execute sequentially; names must already exist, and
mirror destinations must be unique. Parts, bounds, offsets, triangle counts
and output size are validated. Resolved absolute dimensions are persisted
as replayable instructions, **not** copied mesh files. Tests validate
actual mesh topology changes, head-on-body attachment, symmetric geometry,
bridge rails on opposite deck edges and upright wheel orientation.

Offline natural-language coverage now includes elementary robot assemblies,
bridges and wheels in addition to FORGE/1 families. This is **not yet**
inverse graphics, skeletal joint animation, surface continuity at seams,
or visually faithful reconstruction of arbitrary characters and objects.
