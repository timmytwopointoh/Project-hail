#!/usr/bin/env python3
"""VQ UV-01: read-only, geometry-derived UV distortion and seam diagnostics.

Measures per-triangle UV Jacobian singular-value ratio (anisotropy), UV area
and texel density without changing meshes or claiming image/artist acceptance.
Mirrored islands and cross-chart seams are reported, not auto-repaired.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
from statistics import median
from engine import MeshError, read_obj

MAX_FACES = 250_000
MAX_EXAMPLES = 32


def _xyz(vertex):
    return tuple(round(float(x), 6) for x in vertex[:3])


def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _edge_key(a, b, uv_a, uv_b):
    """Pair each geometric endpoint with its own UV to avoid false seam matches."""
    if a <= b:
        return (a, b), (uv_a, uv_b)
    return (b, a), (uv_b, uv_a)


def audit_obj(source: Path, *, texture_resolution: int = 1024,
              stretch_threshold: float = 8.0, max_examples: int = 20):
    if type(texture_resolution) is not int or not 64 <= texture_resolution <= 8192:
        raise ValueError("texture_resolution must be an integer in [64,8192]")
    if (type(stretch_threshold) not in (int, float) or
            not math.isfinite(stretch_threshold) or not 1.01 <= stretch_threshold <= 100):
        raise ValueError("stretch_threshold must be finite in [1.01,100]")
    if type(max_examples) is not int or not 0 <= max_examples <= MAX_EXAMPLES:
        raise ValueError("max_examples outside bounded diagnostic range")
    source = Path(source)
    before_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    vertices, uv, _, faces = read_obj(source)
    if len(faces) > MAX_FACES:
        raise MeshError("UV audit exceeds face budget")
    edge_uses = defaultdict(list)
    missing = collapsed = degenerate = mirrored = stretched = 0
    valid = []
    samples = []
    for face_index, face in enumerate(faces):
        if any(c[1] is None for c in face):
            missing += 1
            continue
        points = [tuple(float(x) for x in vertices[c[0]][:3]) for c in face]
        tex = [tuple(float(x) for x in uv[c[1]][:2]) for c in face]
        if not all(math.isfinite(x) for point in points + tex for x in point):
            raise MeshError("Nonfinite UV or geometry")
        for i in range(3):
            a, b = i, (i + 1) % 3
            ek, mapping = _edge_key(_xyz(points[a]), _xyz(points[b]),
                                    tuple(round(x, 8) for x in tex[a]),
                                    tuple(round(x, 8) for x in tex[b]))
            edge_uses[ek].append(mapping)
        e1 = tuple(points[1][i] - points[0][i] for i in range(3))
        e2 = tuple(points[2][i] - points[0][i] for i in range(3))
        cross = (e1[1]*e2[2] - e1[2]*e2[1],
                 e1[2]*e2[0] - e1[0]*e2[2],
                 e1[0]*e2[1] - e1[1]*e2[0])
        area_3d = 0.5 * math.sqrt(_dot(cross, cross))
        du1, dv1 = tex[1][0] - tex[0][0], tex[1][1] - tex[0][1]
        du2, dv2 = tex[2][0] - tex[0][0], tex[2][1] - tex[0][1]
        det = du1*dv2 - dv1*du2
        if not math.isfinite(area_3d) or not math.isfinite(det):
            raise MeshError("UV audit numeric overflow")
        if area_3d <= 1e-12:
            degenerate += 1
            continue
        if abs(det) <= 1e-12:
            collapsed += 1
            continue
        if det < 0:
            mirrored += 1
        dpdu = tuple((e1[i]*dv2 - e2[i]*dv1)/det for i in range(3))
        dpdv = tuple((e2[i]*du1 - e1[i]*du2)/det for i in range(3))
        aa, bb, cc = _dot(dpdu, dpdu), _dot(dpdu, dpdv), _dot(dpdv, dpdv)
        discriminant = math.hypot(aa-cc, 2*bb)
        maximum = (aa + cc + discriminant)/2
        # Stable smallest singular value via area ratio avoids cancellation.
        product = (2*area_3d/abs(det))**2
        if not math.isfinite(maximum) or maximum <= 0 or not math.isfinite(product):
            raise MeshError("Invalid UV metric")
        stretch = maximum / math.sqrt(product)
        density = texture_resolution * math.sqrt(abs(det)/(2*area_3d))
        if not math.isfinite(stretch) or not math.isfinite(density):
            raise MeshError("UV metric overflow")
        stretched += stretch > stretch_threshold
        valid.append((face_index, stretch, density))
        samples.append((stretch, face_index, density))
    nonmanifold = sum(len(v) > 2 for v in edge_uses.values())
    boundary = sum(len(v) == 1 for v in edge_uses.values())
    seams = sum(len(v) == 2 and v[0] != v[1] for v in edge_uses.values())
    continuous = sum(len(v) == 2 and v[0] == v[1] for v in edge_uses.values())
    median_density = median(row[2] for row in valid) if valid else None
    density_outliers = (sum(x[2] > median_density*4 or x[2] < median_density/4
                            for x in valid) if median_density else 0)
    samples.sort(key=lambda row: (-row[0], row[1]))
    after_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if after_hash != before_hash:
        raise MeshError("Source changed during UV audit")
    return {
        "schema_version": 1, "milestone": "UV-01", "source": source.name,
        "source_sha256": before_hash, "triangles": len(faces),
        "texture_resolution": texture_resolution,
        "stretch_threshold": stretch_threshold,
        "faces_with_missing_uv": missing,
        "collapsed_uv_faces": collapsed,
        "degenerate_geometry_faces": degenerate,
        "valid_faces": len(valid), "mirrored_uv_faces": mirrored,
        "high_stretch_faces": stretched,
        "max_stretch": max((row[1] for row in valid), default=None),
        "median_stretch": median(row[1] for row in valid) if valid else None,
        "median_texels_per_world_unit": median_density,
        "density_outlier_faces_4x": density_outliers,
        "boundary_edges": boundary, "nonmanifold_edges": nonmanifold,
        "uv_seam_edges": seams, "uv_continuous_edges": continuous,
        "worst_faces": [{"face_index": index, "stretch": round(stretch, 6),
                         "texels_per_world_unit": round(density, 6)}
                        for stretch, index, density in samples[:max_examples]],
        "technical_integrity_passed": (missing == collapsed == degenerate == nonmanifold == 0
                                       and len(valid) == len(faces)),
        "distortion_threshold_is_diagnostic_only": True,
        "black_seam_pixel_review_completed": False,
        "artistic_reference_approved": False,
        "ready_for_game": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only VQ UV stretch/seam diagnostics")
    parser.add_argument("--obj", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--texture-resolution", type=int, default=1024)
    parser.add_argument("--stretch-threshold", type=float, default=8.0)
    args = parser.parse_args()
    if args.obj.resolve() == args.out.resolve():
        raise SystemExit("Cannot overwrite the input OBJ")
    result = audit_obj(args.obj, texture_resolution=args.texture_resolution,
                       stretch_threshold=args.stretch_threshold)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("VQ_UV01_AUDIT", json.dumps({key: result[key] for key in
          ("source_sha256", "valid_faces", "collapsed_uv_faces", "high_stretch_faces",
           "nonmanifold_edges", "technical_integrity_passed")}))
    if not result["technical_integrity_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
