#!/usr/bin/env python3
"""Deterministic glTF-compatible tangent VEC4 from indexed OBJ-derived triangles.

Computes area-weighted derivatives and glTF handedness. This is NOT exact
MikkTSpace, AO baking, GPU visual validation, or artistic approval. Rejects
collapsed UVs, invalid normals, nonfinite inputs and unsplit mirrored seams.
"""
from __future__ import annotations
import math

EPS = 1e-12

def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))

def _cross(a, b):
    return (a[1]*b[2]-a[2]*b[1],
            a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])

def _sub(a, b):
    return tuple(x-y for x, y in zip(a, b))

def _unit(v):
    length = math.sqrt(_dot(v, v))
    if length <= EPS or not math.isfinite(length):
        raise ValueError("Degenerate tangent-space vector")
    return tuple(x/length for x in v)

def triangle_handedness(points, texcoords):
    """Return UV orientation for one noncollapsed triangle; reject bad inputs."""
    if len(points) != 3 or len(texcoords) != 3:
        raise ValueError("Expected three triangle corners")
    if any(len(p) != 3 or not all(math.isfinite(v) for v in p) for p in points):
        raise ValueError("Nonfinite or malformed position")
    if any(len(t) != 2 or not all(math.isfinite(v) for v in t) for t in texcoords):
        raise ValueError("Nonfinite or malformed UV")
    e1, e2 = _sub(points[1], points[0]), _sub(points[2], points[0])
    if _dot(_cross(e1, e2), _cross(e1, e2)) <= EPS*EPS:
        raise ValueError("Collapsed geometry triangle")
    du1 = texcoords[1][0]-texcoords[0][0]
    dv1 = texcoords[1][1]-texcoords[0][1]
    du2 = texcoords[2][0]-texcoords[0][0]
    dv2 = texcoords[2][1]-texcoords[0][1]
    det = du1*dv2-du2*dv1
    if abs(det) <= EPS or not math.isfinite(det):
        raise ValueError("Collapsed or singular triangle UV")
    return 1 if det > 0 else -1

def generate_tangents(positions, normals, texcoords, indices):
    """Return flat glTF TANGENT float4 array (T.xyz, handedness w).

    Positions/normals are flattened triples, UVs flattened pairs. A vertex
    cannot be shared by positive- and negative-UV-handedness triangles; the
    caller must split it at mirrored UV seams before this function is called.
    Tangents are Gram-Schmidt orthogonalized against each supplied normal.
    """
    if not positions or len(positions) % 3 or len(normals) != len(positions):
        raise ValueError("Malformed position/normal attribute arrays")
    count = len(positions)//3
    if len(texcoords) != count*2 or not indices or len(indices) % 3:
        raise ValueError("Malformed UV or triangle index arrays")
    if not all(math.isfinite(v) for v in (*positions, *normals, *texcoords)):
        raise ValueError("Nonfinite tangent-space input")
    if any(type(i) is not int or i < 0 or i >= count for i in indices):
        raise ValueError("Triangle index out of bounds")
    tangent_sums = [[0., 0., 0.] for _ in range(count)]
    bitangent_sums = [[0., 0., 0.] for _ in range(count)]
    signs = [0]*count
    for first in range(0, len(indices), 3):
        tri = indices[first:first+3]
        p = [positions[i*3:i*3+3] for i in tri]
        uv = [texcoords[i*2:i*2+2] for i in tri]
        sign = triangle_handedness(p, uv)
        e1, e2 = _sub(p[1], p[0]), _sub(p[2], p[0])
        area = math.sqrt(_dot(_cross(e1, e2), _cross(e1, e2)))
        du1, dv1 = uv[1][0]-uv[0][0], uv[1][1]-uv[0][1]
        du2, dv2 = uv[2][0]-uv[0][0], uv[2][1]-uv[0][1]
        det = du1*dv2-du2*dv1
        tangent = tuple((e1[k]*dv2-e2[k]*dv1)/det for k in range(3))
        bitangent = tuple((e2[k]*du1-e1[k]*du2)/det for k in range(3))
        for i in tri:
            if signs[i] and signs[i] != sign:
                raise ValueError("Mirrored UV seam shares a vertex; split before tangent generation")
            signs[i] = sign
            for k in range(3):
                tangent_sums[i][k] += tangent[k]*area
                bitangent_sums[i][k] += bitangent[k]*area
    result = []
    for i in range(count):
        if not signs[i]:
            raise ValueError("Unreferenced vertex has no tangent basis")
        n = _unit(normals[i*3:i*3+3])
        t = tangent_sums[i]
        t = _unit(tuple(t[k]-_dot(t, n)*n[k] for k in range(3)))
        b = bitangent_sums[i]
        handedness_measure = _dot(_cross(n, t), b)
        if abs(handedness_measure) <= EPS or not math.isfinite(handedness_measure):
            raise ValueError("Ambiguous tangent handedness")
        w = 1 if handedness_measure > 0 else -1
        if w != signs[i]:
            raise ValueError("Inconsistent supplied normal or UV orientation")
        result.extend((*t, float(w)))
    return result
