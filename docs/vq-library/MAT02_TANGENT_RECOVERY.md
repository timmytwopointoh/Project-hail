# MAT-02 tangent source recovery and technical review (2026-10-16)

## Exact branches and evidence

- Engine implementation branch: `feature/veilforge-mat02-tangent-basis-20261016`.
- Verified implementation commit: `40f1519078d3340266e99d7d6d434934a6cbb938`.
- Full factory CI: https://github.com/timmytwopointoh/Project-hail/actions/runs/38945940215
  (18 jobs, source regression suite, eight asset producers, four independent
  Android 15 roles, real screenshot gates and both LOD/semantic reviewers).
- Archive/recovery branch: `feature/vq-library-snapshot-mat02-20261016`,
  derived from the verified implementation SHA. Its head includes this guide,
  the technique playbook and evidence ledger. The archive workflow verifies
  every tracked source file and its SHA256. The archive job's source commit
  SHA, not just the implementation SHA, is the correct restore target.
- Prior fully verified source snapshot and older Library ZIPs remain intact.
  The playable VEILBOUND and ECHOFORM game branches were not changed.

## Reproduce the tangent export

From the checked-out repository root with Python 3.11:

```bash
python3 -m unittest discover -s veilforge/tests -p 'test_vq_tangent*.py' -v
python3 veilforge/vq_tangent_export.py \
  --obj path/to/real_source.obj \
  --out build/vq_tangent/model.gltf \
  --tangents
```

When preserving original PBR material maps, also provide
`--source-gltf path/to/source.gltf` and
`--source-manifest path/to/asset_manifest.json`. The output directory must
not be the original source material directory. The new exporter stages all
outputs and does not overwrite original OBJ, textures or existing package files.

The glTF `TANGENT` accessor is a VEC4 float attribute. `xyz` is a unit
tangent orthogonal to the supplied normal, and `w` is +1 or -1 for the
bitangent reconstruction `cross(N,T)*w`. Mirrored UV triangles are split
by normal-index seams in a temporary derived OBJ. Tests verify the expected
six indexed vertices and `[+1,+1,+1,-1,-1,-1]` handedness for a two-face
mirrored fixture. Original and derived source hashes are recorded.

## Strict limits

This is a **partial MAT-02 engineering milestone**, not finished normal/AO
baking or MikkTSpace conformance. The Android factory regression used its
existing assets and did not import the new opt-in tangent glTF. It cannot
prove tangent-specific GLES normal lighting, artistic realism, human/creature
anatomy, physical phone performance or game-ready signoff. Those gates remain
open and require separate real-source Android and hardware evidence.
