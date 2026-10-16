#!/usr/bin/env python3
"""VQ GEO-02 read-only, material-aware regional topology evidence.

This audit never repairs, deletes or rewrites source geometry. Open rims can be
intentional; an automated pass is NOT approval to cap a hole or ship a model.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
from engine import MeshError, read_obj

def _key(v):
    return tuple(round(float(x), 5) for x in v[:3])

def _edge(a, b):
    return (a, b) if a < b else (b, a)

def _materials(path):
    material = "default"
    result = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.partition("#")[0].strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        kind = parts[0]
        value = parts[1] if len(parts)>1 else ""
        if kind == "usemtl":
            material = value.strip() or "default"
        elif kind == "f":
            result.append(material)
    return result

def _area_squared(a, b, c):
    u = [b[i]-a[i] for i in range(3)]
    v = [c[i]-a[i] for i in range(3)]
    cross = (u[1]*v[2]-u[2]*v[1],
             u[2]*v[0]-u[0]*v[2],
             u[0]*v[1]-u[1]*v[0])
    return sum(x*x for x in cross)

def inspect_regions(path: Path):
    """Return deterministic defect counts per geometric connected component."""
    path = Path(path)
    vertices, uvs, normals, faces = read_obj(path)
    materials = _materials(path)
    if len(materials) != len(faces):
        raise MeshError("Face/material stream mismatch")
    parents = list(range(len(faces)))
    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i
    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parents[max(a,b)] = min(a,b)

    edges = defaultdict(list)
    first_geom = set()
    first_semantic = set()
    face_defects = []
    for i, (face, material) in enumerate(zip(faces, materials)):
        pts = [_key(vertices[c[0]]) for c in face]
        degenerate = len(set(pts)) != 3 or _area_squared(*pts) < 1e-16
        geom = tuple(sorted(pts))
        attrs = [
            (pts[j],
             tuple(round(x,8) for x in uvs[c[1]][:2]) if c[1] is not None else None,
             tuple(round(x,8) for x in normals[c[2]][:3]) if c[2] is not None else None)
            for j,c in enumerate(face)]
        semantic = (geom, material, tuple(sorted(attrs, key=repr)))
        # Distinct material/UV/normal layers must not be mistaken for
        # disposable exact duplicate geometry.
        exact = semantic in first_semantic
        overlay = geom in first_geom and not exact
        first_geom.add(geom)
        first_semantic.add(semantic)
        face_defects.append((degenerate, exact, overlay))
        for j in range(3):
            a,b = pts[j],pts[(j+1)%3]
            if a != b:
                edges[_edge(a,b)].append((i,a,b))

    for uses in edges.values():
        if len(uses)>1:
            for other in uses[1:]:
                union(uses[0][0],other[0])
    regions = {}
    for i,(face,material) in enumerate(zip(faces,materials)):
        root = find(i)
        row = regions.setdefault(root,{
            "first_face":i,"triangles":0,"materials":Counter(),
            "degenerate_triangles":0,"exact_duplicate_triangles":0,
            "semantic_overlay_triangles":0,"boundary_edges":0,
            "nonmanifold_edges":0,"orientation_conflict_edges":0,
            "welded_vertices":set()})
        row["first_face"]=min(row["first_face"],i)
        row["triangles"]+=1
        row["materials"][material]+=1
        d,e,o=face_defects[i]
        row["degenerate_triangles"]+=int(d)
        row["exact_duplicate_triangles"]+=int(e)
        row["semantic_overlay_triangles"]+=int(o)
        row["welded_vertices"].update(_key(vertices[c[0]]) for c in face)
    for uses in edges.values():
        root=find(uses[0][0])
        row=regions[root]
        if len(uses)==1: row["boundary_edges"]+=1
        elif len(uses)>2: row["nonmanifold_edges"]+=1
        elif uses[0][1:]==uses[1][1:]:
            row["orientation_conflict_edges"]+=1

    ordered=[]
    for row in sorted(regions.values(),key=lambda x:x["first_face"]):
        row["materials"]=dict(sorted(row["materials"].items()))
        row["welded_vertices"]=len(row["welded_vertices"])
        ordered.append(row)
    totals={key:sum(r[key] for r in ordered) for key in (
        "triangles","degenerate_triangles","exact_duplicate_triangles",
        "semantic_overlay_triangles","boundary_edges","nonmanifold_edges",
        "orientation_conflict_edges")}
    return {
        "schema_version":1,"engine":"VEYLQUORIN","milestone":"GEO-02",
        "tool":"read_only_regional_topology_audit",
        "source_name":path.name,
        "source_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "regions":ordered,"region_count":len(ordered),"totals":totals,
        "welded_uv_seams_not_boundaries":True,
        "semantic_overlays_preserved":True,
        "no_automatic_hole_filling":True,
        "closed_manifold_candidate":(
            totals["boundary_edges"]==0 and totals["nonmanifold_edges"]==0
            and totals["degenerate_triangles"]==0
            and totals["exact_duplicate_triangles"]==0
            and totals["orientation_conflict_edges"]==0),
        "source_modified":False,"artistic_signoff":False,
        "physical_device_tested":False,"game_approved":False}

def main():
    parser=argparse.ArgumentParser(description="Read-only regional OBJ topology audit")
    parser.add_argument("--obj",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    if args.obj.resolve()==args.out.resolve() or args.out.exists():
        raise ValueError("Never overwrite source or existing topology evidence")
    report=inspect_regions(args.obj)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open("x",encoding="utf-8") as stream:
        json.dump(report,stream,indent=2)
        stream.write("\n")
    print("VQ_GEO02_REGIONAL_AUDIT",report["source_sha256"],report["region_count"],
          report["totals"])

if __name__=="__main__":
    main()
