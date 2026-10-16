#!/usr/bin/env python3
"""VEILFORGE M2 — conservative export topology cleanup.

Original game meshes stay untouched. Only *exact* coincident duplicate triangles
are removed and only small, simple, locally near-planar boundary loops are capped.
Intended cloth rims, incomplete objects and large gaps are NOT auto-capped.
Every mutation is explicitly reported, requires QA and visual review.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
from engine import inspect_obj, read_obj, MeshError

def key(point):
    return tuple(round(v, 5) for v in point[:3])

def edge(a, b):
    return (a, b) if a < b else (b, a)

def _area2(a,b,c):
    ab=[b[i]-a[i] for i in range(3)]
    ac=[c[i]-a[i] for i in range(3)]
    cr=(ab[1]*ac[2]-ab[2]*ac[1],
        ab[2]*ac[0]-ab[0]*ac[2],
        ab[0]*ac[1]-ab[1]*ac[0])
    return sum(v*v for v in cr)

def _loop_metrics(loop):
    span=max(math.dist(a,b) for i,a in enumerate(loop) for b in loop[i+1:])
    perimeter=sum(math.dist(loop[i],loop[(i+1)%len(loop)]) for i in range(len(loop)))
    # A simple planarity gate: all points must be close to the first
    # non-collinear triangular plane. A diagonal "fan" is disallowed otherwise.
    base=loop[0]
    best=None
    for i in range(1,len(loop)-1):
        a=[loop[i][j]-base[j] for j in range(3)]
        b=[loop[i+1][j]-base[j] for j in range(3)]
        n=(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
        mag=math.sqrt(sum(q*q for q in n))
        if mag>1e-10:
            best=tuple(q/mag for q in n)
            break
    if best is None:
        return span,perimeter,float("inf")
    off=max(abs(sum(best[j]*(p[j]-base[j]) for j in range(3))) for p in loop)
    return span,perimeter,off

def _boundary(verts, faces):
    incidences=defaultdict(list)
    source_corner={}
    for tri in faces:
        ks=[key(verts[c[0]]) for c in tri]
        for v,c in zip(ks,tri):
            source_corner.setdefault(v,c)
        for i in range(3):
            if ks[i]==ks[(i+1)%3]:
                continue
            incidences[edge(ks[i],ks[(i+1)%3])].append((ks[i],ks[(i+1)%3]))
    boundary=[directions[0] for directions in incidences.values() if len(directions)==1]
    nonmanifold=sum(len(directions)>2 for directions in incidences.values())
    return boundary,nonmanifold,source_corner

def _loops(boundary):
    adjacency=defaultdict(set)
    for a,b in boundary:
        adjacency[a].add(b)
        adjacency[b].add(a)
    visited=set()
    closed=[]
    incomplete=0
    for start in sorted(adjacency):
        if start in visited:
            continue
        stack=[start]
        component=set()
        while stack:
            v=stack.pop()
            if v in component:
                continue
            component.add(v)
            stack.extend(adjacency[v]-component)
        visited.update(component)
        if not all(len(adjacency[v])==2 for v in component):
            incomplete+=1
            continue
        first=min(component)
        points=[first]
        prev=None
        cur=first
        for step in range(len(component)):
            choices=sorted(adjacency[cur]-({prev} if prev is not None else set()))
            if not choices:
                break
            nxt=choices[0]
            if nxt==first:
                break
            if nxt in points:
                break
            points.append(nxt)
            prev,cur=cur,nxt
        if len(points)==len(component) and first in adjacency[points[-1]]:
            closed.append(points)
        else:
            incomplete+=1
    return closed,incomplete

def repair_obj(src:Path, dest:Path, *, mode="human", max_hole_vertices=12,
               max_hole_diameter=.16, max_hole_nonplanarity=.012):
    """Never edit or replace src; produce auditable independent candidate OBJ."""
    if src.resolve()==dest.resolve():
        raise ValueError("Source must never be overwritten")
    if mode not in ("human","assembly","diagnose"):
        raise ValueError("Unknown repair mode")
    verts,uvs,norms,original=read_obj(src)
    unique=set()
    cleaned=[]
    duplicate=0
    for tri in original:
        sig=tuple(sorted(key(verts[c[0]]) for c in tri))
        if len(set(sig))!=3:
            # Don't silently remove irregular triangles as a repair.
            cleaned.append(tri)
            continue
        if sig in unique:
            duplicate+=1
            continue
        unique.add(sig)
        cleaned.append(tri)
    boundary,nonmanifold,corners=_boundary(verts,cleaned)
    candidates,incomplete=_loops(boundary)
    capped=[]
    skipped=[]
    # M24 correction: hole caps must be constrained by existing edge
    # incidences. Pure planarity is insufficient: the old repair introduced
    # seven new nonmanifold edges and four zero-area faces in a human mesh.
    # Whole cap-loops fail closed without changing the original OBJ.
    occupied=Counter()
    face_signatures=set()
    for tri in cleaned:
        vertices=[key(verts[c[0]]) for c in tri]
        face_signatures.add(tuple(sorted(vertices)))
        for i in range(3):
            occupied[edge(vertices[i],vertices[(i+1)%3])]+=1
    if mode=="human":
        # Do not invent watertight joints on models with nonmanifold edges.
        if nonmanifold==0:
            directed=set(boundary)
            for ring in candidates:
                if len(ring)<3 or len(ring)>max_hole_vertices:
                    skipped.append({"edges":len(ring),"center":[round(sum(p[k] for p in ring)/len(ring),4) for k in range(3)],"reason":"size"});continue
                diameter,perimeter,nonplanarity=_loop_metrics(ring)
                if diameter>max_hole_diameter or nonplanarity>max_hole_nonplanarity:
                    skipped.append({"edges":len(ring),"center":[round(sum(p[k] for p in ring)/len(ring),4) for k in range(3)],"diameter":round(diameter,5),
                        "nonplanarity":round(nonplanarity,5),"reason":"geometry"});continue
                # Construct fan in the winding opposite to the boundary edges.
                if (ring[0],ring[1]) not in directed:
                    ring=list(reversed(ring))
                faces=[]
                for i in range(1,len(ring)-1):
                    a,b,c=ring[0],ring[i+1],ring[i]
                    if _area2(a,b,c)<1e-16:
                        faces=[]
                        break
                    faces.append((corners[a],corners[b],corners[c]))
                if faces:
                    proposed=Counter()
                    signatures=set()
                    valid=True
                    for face in faces:
                        keys=[key(verts[c[0]]) for c in face]
                        signature=tuple(sorted(keys))
                        if len(set(keys))!=3 or _area2(*keys)<1.e-14 or (
                                signature in face_signatures or signature in signatures):
                            valid=False
                            break
                        signatures.add(signature)
                        for k in range(3):
                            e=edge(keys[k],keys[(k+1)%3])
                            proposed[e]+=1
                            if occupied[e]+proposed[e]>2:
                                valid=False
                                break
                        if not valid:break
                    if valid:
                        capped.extend(faces)
                        occupied.update(proposed)
                        face_signatures.update(signatures)
                    else:
                        skipped.append({"edges":len(ring),"reason":"manifold-or-degenerate-protection"})
                else:
                    skipped.append({"edges":len(ring),"reason":"fan degeneracy"})
    else:
        skipped=[{"edges":len(c),"reason":"intentional open or mixed surface"} for c in candidates]
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("w",encoding="utf-8") as stream:
        stream.write("# VEILFORGE M2 CLEANED EXPORT; original source remains unchanged\n")
        stream.write("# Back-to-back coincident faces removed for export, not in Android runtime\n")
        for v in verts:
            stream.write("v "+" ".join(format(x,".9g") for x in v)+"\n")
        for v in uvs:
            stream.write("vt "+" ".join(format(x,".9g") for x in v)+"\n")
        for v in norms:
            stream.write("vn "+" ".join(format(x,".9g") for x in v)+"\n")
        for tri in cleaned+capped:
            def ref(c):
                return str(c[0]+1)+(
                    "/"+str(c[1]+1) if c[1] is not None and c[2] is None else
                    "//"+str(c[2]+1) if c[1] is None and c[2] is not None else
                    "/"+str(c[1]+1)+"/"+str(c[2]+1)
                    if c[1] is not None else "")
            stream.write("f "+" ".join(ref(c) for c in tri)+"\n")
    before=inspect_obj(src)
    after=inspect_obj(dest)
    report={
        "schema_version":1,"mode":mode,"source":str(src),"candidate":str(dest),
        "input_triangles":len(original),"coincident_faces_removed":duplicate,
        "small_hole_triangles_inserted":len(capped),
        "boundary_loops_found":len(candidates),"boundary_components_unresolved":incomplete,
        "skipped_boundary_loops":skipped[:100],
        "before":{"triangles":before["triangles"],"boundary_edges":before["boundary_edges"],
                  "nonmanifold_edges":before["nonmanifold_edges"],
                  "degenerate_triangles":before["degenerate_triangles"]},
        "after":{"triangles":after["triangles"],"boundary_edges":after["boundary_edges"],
                 "nonmanifold_edges":after["nonmanifold_edges"],
                 "degenerate_triangles":after["degenerate_triangles"]},
        "topology_improved":(
            after["nonmanifold_edges"]<=before["nonmanifold_edges"] and
            after["degenerate_triangles"]<=before["degenerate_triangles"] and
            (mode!="human" or after["boundary_edges"]<=before["boundary_edges"])),
        "boundary_edge_delta":after["boundary_edges"]-before["boundary_edges"],
        "open_rims_preserved":mode!="human",
        "closed_oriented_manifold_automatically_proven":False,
        "ready_for_game":False,"manual_visual_review_required":True,
        "safe_export_candidate":after["nonmanifold_edges"]==0 and
            after["degenerate_triangles"]==0,
    }
    (dest.parent/(dest.stem+"_topology_report.json")).write_text(
        json.dumps(report,indent=2)+"\n",encoding="utf-8")
    if not report["topology_improved"]:
        raise MeshError("Topology cleanup increased invalid edge counts")
    return report

def main():
    p=argparse.ArgumentParser(description="Conservative, non-destructive topology cleanup")
    p.add_argument("--obj",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--mode",choices=["human","assembly","diagnose"],default="human")
    p.add_argument("--max-hole-vertices",type=int,default=12)
    p.add_argument("--max-hole-diameter",type=float,default=.16)
    a=p.parse_args()
    report=repair_obj(a.obj,a.out,mode=a.mode,max_hole_vertices=a.max_hole_vertices,
                      max_hole_diameter=a.max_hole_diameter)
    print("VEILFORGE_TOPOLOGY",json.dumps({k:report[k] for k in (
        "coincident_faces_removed","small_hole_triangles_inserted",
        "boundary_loops_found","before","after","safe_export_candidate")}))
if __name__=="__main__":
    main()
