#!/usr/bin/env python3
"""UV-01 read-only source-derived OBJ distortion audit.

Measures local UV-to-world anisotropy and area-equivalent texel density.
Not a UV overlap, black-seam pixel, renderer or artistic approval test.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from engine import read_obj
from vq_uv_seams import seam_counts

MAX_SOURCE_BYTES = 128 * 1024 * 1024


def _threshold(value, name, minimum):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    if not math.isfinite(value) or value < minimum:
        raise ValueError(f"{name} must be finite and >= {minimum}")
    return float(value)


def _weighted_median(rows):
    rows = sorted(rows)
    target = sum(weight for _, weight in rows) / 2
    seen = 0.0
    for value, weight in rows:
        seen += weight
        if seen >= target:
            return value
    raise ValueError("No positive-area triangles")


def audit_obj(path, *, max_anisotropy=4.0, max_density_ratio=2.0,
              texture_size=1024, strict=False):
    """Compute singular-value stretch and world-area-weighted density.

    Negative UV winding is not intrinsically wrong. Strict thresholds are
    conservative opt-in checks, not an automatic production release gate.
    """
    limit = _threshold(max_anisotropy, "max_anisotropy", 1)
    density_limit = _threshold(max_density_ratio, "max_density_ratio", 1)
    if type(texture_size) is not int or not 128 <= texture_size <= 8192:
        raise ValueError("texture_size must be an integer in [128, 8192]")
    if type(strict) is not bool:
        raise ValueError("strict must be boolean")
    path = Path(path)
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError("Missing, unsafe or over-budget source OBJ")
    vertices, uvs, _, faces = read_obj(path)
    if not uvs:
        raise ValueError("Missing source UV coordinates")
    anisotropies, densities = [], []
    winding = {"+": 0, "-": 0}
    outside = 0
    for index, face in enumerate(faces):
        if any(corner[1] is None for corner in face):
            raise ValueError(f"Missing source UV coordinates on triangle {index}")
        p = [vertices[c[0]][:3] for c in face]
        t = [uvs[c[1]][:2] for c in face]
        if any(q < 0 or q > 1 for point in t for q in point):
            outside += 1
        a = [p[1][i] - p[0][i] for i in range(3)]
        b = [p[2][i] - p[0][i] for i in range(3)]
        cross = (a[1]*b[2]-a[2]*b[1],
                 a[2]*b[0]-a[0]*b[2],
                 a[0]*b[1]-a[1]*b[0])
        world_double_area = math.hypot(*cross)
        du1, dv1 = t[1][0]-t[0][0], t[1][1]-t[0][1]
        du2, dv2 = t[2][0]-t[0][0], t[2][1]-t[0][1]
        det = du1*dv2 - dv1*du2
        if world_double_area <= 1e-12:
            raise ValueError(f"Collapsed 3D triangle {index}")
        if abs(det) <= 1e-12:
            raise ValueError(f"Collapsed UV triangle {index}")
        winding["+" if det > 0 else "-"] += 1
        # UV-to-world Jacobian columns; singular-value ratio is scale free.
        dxdu = [(dv2*a[i]-dv1*b[i])/det for i in range(3)]
        dxdv = [(-du2*a[i]+du1*b[i])/det for i in range(3)]
        g11 = sum(q*q for q in dxdu)
        g22 = sum(q*q for q in dxdv)
        g12 = sum(dxdu[i]*dxdv[i] for i in range(3))
        largest_eigen = (g11+g22+math.hypot(g11-g22, 2*g12))/2
        area_scale = world_double_area/abs(det)
        anisotropy = largest_eigen/area_scale
        density = math.sqrt(area_scale)
        if not all(math.isfinite(q) and q > 0 for q in (anisotropy, density)):
            raise ValueError(f"Unbounded UV Jacobian on triangle {index}")
        anisotropies.append(anisotropy)
        densities.append((density, world_double_area/2))
    seams = seam_counts(path)  # Reject welded nonmanifold edges.
    median = _weighted_median(densities)
    factors = [max(d/median, median/d) for d, _ in densities]
    stretched = sum(a > limit + 1e-9 for a in anisotropies)
    uneven = sum(d > density_limit + 1e-9 for d in factors)
    ranked = sorted(anisotropies)
    result = {
        "schema_version": 1, "milestone": "UV-01",
        "source": path.name,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "triangle_count": len(faces), "uv_seams": seams,
        "positive_uv_winding_triangles": winding["+"],
        "negative_uv_winding_triangles": winding["-"],
        "mixed_uv_winding": bool(winding["+"] and winding["-"]),
        "triangles_with_uv_outside_unit_square": outside,
        "max_anisotropy": round(max(anisotropies), 6),
        "p95_anisotropy": round(ranked[math.ceil(.95*len(ranked))-1], 6),
        "anisotropy_threshold": limit,
        "anisotropy_outlier_triangles": stretched,
        "median_area_equivalent_world_units_per_uv": round(median, 8),
        "median_area_equivalent_texels_per_world_unit": round(texture_size/median, 6),
        "texture_size": texture_size,
        "max_density_deviation_factor": round(max(factors), 6),
        "density_ratio_threshold": density_limit,
        "density_outlier_triangles": uneven,
        "strict_threshold_pass": stretched == 0 and uneven == 0,
        "uv_overlap_checked": False,
        "black_seam_pixels_checked": False,
        "android_render_verified": False,
        "artist_reference_approved": False,
        "production_approved": False,
    }
    if strict and not result["strict_threshold_pass"]:
        raise ValueError("UV distortion thresholds exceeded")
    return result


def main():
    parser = argparse.ArgumentParser(description="Read-only OBJ UV distortion audit")
    parser.add_argument("--obj", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-anisotropy", type=float, default=4)
    parser.add_argument("--max-density-ratio", type=float, default=2)
    parser.add_argument("--texture-size", type=int, default=1024)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    result = audit_obj(args.obj, max_anisotropy=args.max_anisotropy,
                       max_density_ratio=args.max_density_ratio,
                       texture_size=args.texture_size, strict=args.strict)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print("VQ_UV01_SOURCE_AUDIT", result["source_sha256"],
          result["triangle_count"], result["strict_threshold_pass"])


if __name__ == "__main__":
    main()
