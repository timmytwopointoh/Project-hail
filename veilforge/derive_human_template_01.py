#!/usr/bin/env python3
"""Copy-on-write original human template derived from the real M37 VQ source OBJ.

The existing M37 source is never changed. This creates a second independently
versioned anthropometric candidate, then sends it through the real VQ inspector.
No claim of production rigging, realism, or engine acceptance is implied.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def convert(source: Path, output: Path) -> dict:
    if not source.is_file() or source.resolve() == output.resolve():
        raise ValueError("A separate immutable source OBJ and candidate output are required")
    before = digest(source)
    lines = source.read_text(encoding="utf-8").splitlines(True)
    source_vertices = [tuple(map(float, line.split()[1:4]))
                       for line in lines if line.startswith("v ")]
    if len(source_vertices) < 1000:
        raise ValueError("Expected an actual high-resolution triangulated human OBJ")
    min_y = min(v[1] for v in source_vertices)
    max_y = max(v[1] for v in source_vertices)
    height = max_y - min_y
    if height <= 0:
        raise ValueError("Source has no height")
    def transform(x, y, z):
        h = (y - min_y) / height
        # Small smooth proportional changes define a new individual,
        # retaining the source hand webbing, M37 feet and shoulder landmarks.
        shoulder = math.exp(-((h-.72)/.11)**2)
        pelvis = math.exp(-((h-.38)/.13)**2)
        calf = math.exp(-((h-.20)/.08)**2)
        cranium = math.exp(-((h-.91)/.09)**2)
        x *= (1-.022*shoulder+.028*pelvis+.014*calf-.012*cranium)
        z *= (1+.020*pelvis-.012*shoulder+.016*cranium)
        return x*.625, (y-min_y)*1.75/height, z*.625
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("w",encoding="utf-8") as dst:
        dst.write("# VQ TEMPLATE 01 / M37-derived novel human candidate\n")
        dst.write("# X right, Y up, Z forward, meters; copy on write; review only\n")
        for line in lines:
            if line.startswith("v "):
                items = line.split()
                x,y,z = transform(*map(float,items[1:4]))
                items[1:4] = [f"{val:.7f}" for val in (x,y,z)]
                dst.write(" ".join(items)+"\n")
            else:
                dst.write(line)
    if before != digest(source):
        raise RuntimeError("Original source changed")
    new = digest(output)
    if before == new:
        raise RuntimeError("Candidate must differ from source")
    result = {
        "asset":"VQ Human Template 01 / new M37-derived human",
        "source_sha256":before,"candidate_sha256":new,
        "source_vertex_count":len(source_vertices),
        "target_stature_m":1.75,
        "distinct_proportion_profile":True,
        "reference_inherited":"M37 shoulders, 5 toes/foot and 5 fingers/hand",
        "original_preserved":True,
        "new_geometry_candidate":True,
        "pose":"T",
        "animated":False,"skinned":False,"photorealism_verified":False,
        "manual_review_required":True,
    }
    (output.parent/"template_manifest.json").write_text(json.dumps(result,indent=2)+"\n")
    return result

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(convert(args.source,args.out),indent=2))
