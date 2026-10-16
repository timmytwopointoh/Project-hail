#!/usr/bin/env python3
"""VQ sculpt / smooth / stamp brushes for arbitrary triangulated OBJ sources.

Non-destructive review-only geometry candidates. These are topology-preserving
vertex tools, NOT raw face duplication, adaptive remeshing, Blender sculpting,
automatic anatomy recognition or artistic approval.

Safety: welded-coordinate symmetry across UV vertex splits; boundary,
nonmanifold, cross-material and sharp-edge pins; bounded radial strength;
no material/UV/face-index edits; per-stroke provenance; source hash unchanged.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re

from engine import inspect_obj, read_obj

MAX_FACES=120000
MAX_VERTICES=250000
MAX_STROKES=12
MAX_TOTAL_DISPLACEMENT=.055
SAFE_ID=re.compile(r"^[a-z][a-z0-9_-]{1,39}$")

def _sub(a,b):
    return tuple(a[i]-b[i] for i in range(3))
def _dot(a,b):
    return sum(a[i]*b[i] for i in range(3))
def _cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def _unit(v):
    length=math.sqrt(_dot(v,v))
    return tuple(x/length for x in v) if length>1e-12 else (0.,0.,0.)
def _normal(a,b,c):
    return _cross(_sub(b,a),_sub(c,a))
def _smoothstep(t):
    return t*t*(3-2*t)
def _falloff(point,center,radius):
    r=math.dist(point,center)/radius
    return _smoothstep(1-r) if r<1 else 0.
def _pattern(point,center,radius,seed,kind):
    if kind!="roughen":
        return 1.
    # Source-centered procedural micro pattern: a stamp replays exactly the
    # same local motif in a different location, never raw mesh triangles.
    dx,dy,dz=((point[i]-center[i])/radius for i in range(3))
    phase=seed*.0311
    return .58+.42*math.sin(dx*16.3+dy*4.1+phase)*math.cos(dz*13.7-dy*5.1-phase)

def validate_recipe(recipe,available_materials):
    if not isinstance(recipe,dict) or recipe.get("schema_version")!=1:
        raise ValueError("Unsupported VQ brush recipe version")
    strokes=recipe.get("strokes")
    if not isinstance(strokes,list) or not 1<=len(strokes)<=MAX_STROKES:
        raise ValueError("VQ requires one to twelve bounded brush strokes")
    if set(recipe)-{"schema_version","strokes"}:
        raise ValueError("Unknown VQ recipe fields")
    seen={}
    for stroke in strokes:
        if not isinstance(stroke,dict):
            raise ValueError("Brush stroke must be an object")
        op=stroke.get("op")
        common={"id","op","center","radius","strength","materials"}
        allowed=common|({"kind","seed"} if op=="sculpt" else
                        {"iterations"} if op=="smooth" else
                        {"from"} if op=="stamp" else set())
        if op not in ("sculpt","smooth","stamp") or set(stroke)!=allowed:
            raise ValueError("Unsupported or incomplete VQ stroke recipe")
        name=stroke["id"]
        if not isinstance(name,str) or not SAFE_ID.fullmatch(name) or name in seen:
            raise ValueError("Duplicate/unsafe brush identity")
        center=stroke["center"]
        if not isinstance(center,list) or len(center)!=3 or any(
            type(x) not in (float,int) or not math.isfinite(x) or abs(x)>1000
            for x in center):
            raise ValueError("Bad brush center")
        for field,low,high in (("radius",.05,100),("strength",.00001,
                               .04 if op=="sculpt" else 1.)):
            value=stroke[field]
            if type(value) not in (int,float) or not math.isfinite(value) or not low<=value<=high:
                raise ValueError("Bad brush radius/strength")
        mats=stroke["materials"]
        if not isinstance(mats,list) or not 1<=len(mats)<=12 or (
            len(set(mats))!=len(mats)) or not set(mats)<=set(available_materials):
            raise ValueError("Brush materials missing/unknown")
        if op=="sculpt":
            if stroke["kind"] not in ("raise","carve","roughen"):
                raise ValueError("Unknown sculpt tip")
            if type(stroke["seed"]) is not int or not 0<=stroke["seed"]<2147483647:
                raise ValueError("Invalid procedural motif seed")
        elif op=="smooth":
            if type(stroke["iterations"]) is not int or not 1<=stroke["iterations"]<=4:
                raise ValueError("Smoothing iterations out of range")
        else:
            if stroke["from"] not in seen or seen[stroke["from"]]["op"]!="sculpt":
                raise ValueError("Stamp requires a previous sculpt stroke as source")
            if set(mats)!=set(seen[stroke["from"]]["materials"]):
                raise ValueError("Stamp must target the original sculpt's materials")
        seen[name]=stroke
    return True

def _face_materials(src,expected):
    current="default"
    mats=[]
    for line in src.read_text(encoding="utf-8").splitlines():
        tokens=line.split()
        if not tokens:continue
        if tokens[0]=="usemtl":
            if len(tokens)!=2 or not SAFE_ID.fullmatch(tokens[1]):
                raise ValueError("Unsafe/unsupported OBJ material identifier")
            current=tokens[1]
        elif tokens[0]=="f":
            mats.append(current)
    if len(mats)!=expected:raise ValueError("OBJ material face count mismatch")
    return mats

def _graph(verts,faces,materials):
    # Weld separate OBJ indices representing the same exact position without
    # discarding their distinct UV, normal or vertex-color attributes.
    groups={}
    members=defaultdict(list)
    by_vertex=[]
    for i,v in enumerate(verts):
        key=tuple(round(x,6) for x in v[:3])
        group=groups.setdefault(key,len(groups))
        members[group].append(i)
        by_vertex.append(group)
    pos=[tuple(verts[members[i][0]][:3]) for i in range(len(groups))]
    neighbors=[set() for _ in pos]
    incident=[set() for _ in pos]
    edge_faces=defaultdict(list)
    normals=[]
    for fi,face in enumerate(faces):
        ids=[by_vertex[v[0]] for v in face]
        norm=_unit(_normal(*[pos[k] for k in ids]))
        normals.append(norm)
        for k in ids:incident[k].add(fi)
        for i in range(3):
            a,b=ids[i],ids[(i+1)%3]
            if a==b:continue
            neighbors[a].add(b)
            neighbors[b].add(a)
            edge_faces[tuple(sorted((a,b)))].append(fi)
    protected=set()
    # Pin all open/nonmanifold boundaries and hard object creases; don't smooth
    # cube corners into blobs or weld unrelated material shells together.
    for (a,b),fs in edge_faces.items():
        unsafe=(len(fs)!=2 or materials[fs[0]]!=materials[fs[1]])
        if len(fs)==2:
            unsafe=unsafe or _dot(normals[fs[0]],normals[fs[1]])<math.cos(math.radians(72))
        if unsafe:protected.update((a,b))
    group_materials=[{materials[f] for f in fis} for fis in incident]
    avg_norm=[]
    for i,fs in enumerate(incident):
        total=[0.,0.,0.]
        for f in fs:
            for j in range(3):total[j]+=normals[f][j]
        n=_unit(total)
        if _dot(n,n)<.5:protected.add(i)
        avg_norm.append(n)
        if len(group_materials[i])!=1:protected.add(i)
    # Smallest incident edge length limits displacement relative to tessellation.
    shortest=[min((math.dist(pos[i],pos[n]) for n in neighbors[i]),default=0.) for i in range(len(pos))]
    return pos,by_vertex,members,neighbors,protected,group_materials,avg_norm,shortest

def _rewrite_obj(src,out,new_positions,by_vertex,faces,original_normals):
    content=src.read_text(encoding="utf-8").splitlines(keepends=True)
    # Update normal definitions from actual new face geometry. Keep the face's
    # vn index layout and every UV reference unchanged, including hard seams.
    accum=[[0.,0.,0.] for _ in original_normals]
    for face in faces:
        a,b,c=(new_positions[by_vertex[v[0]]] for v in face)
        raw=_normal(a,b,c)
        for vertex in face:
            idx=vertex[2]
            if idx is not None:
                for j in range(3):accum[idx][j]+=raw[j]
    remapped=[_unit(p) for p in accum]
    vertex_index=normal_index=0
    output=[]
    for line in content:
        head=line.partition("#")[0].strip().split()
        if head and head[0]=="v":
            old=head[1:]
            xyz=new_positions[by_vertex[vertex_index]]
            if any(not math.isfinite(v) for v in xyz):
                raise ValueError("Brush generated nonfinite vertex position")
            output.append("v "+" ".join(format(x,".10g") for x in xyz)+
                          (" "+" ".join(old[3:]) if len(old)>3 else "")+"\n")
            vertex_index+=1
        elif head and head[0]=="vn":
            old=head[1:]
            n=remapped[normal_index]
            if _dot(n,n)<.5:
                n=original_normals[normal_index][:3]
            output.append("vn "+" ".join(format(x,".10g") for x in n)+
                          (" "+" ".join(old[3:]) if len(old)>3 else "")+"\n")
            normal_index+=1
        else:
            output.append(line)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text("".join(output),encoding="utf-8")

def _deform_positions(positions,orig,allowed,weights,deltas,max_amount):
    # Strictly bounded per-stroke and total relative to original geometry.
    result=[]
    moved=0;max_shift=0.
    for i,p in enumerate(positions):
        if i in allowed and weights[i]>0:
            candidate=tuple(p[j]+deltas[i][j]*weights[i] for j in range(3))
            deviation=_sub(candidate,orig[i])
            length=math.sqrt(_dot(deviation,deviation))
            if length>MAX_TOTAL_DISPLACEMENT:
                candidate=tuple(orig[i][j]+deviation[j]*MAX_TOTAL_DISPLACEMENT/length
                                for j in range(3))
        else:
            candidate=p
        delta=math.dist(p,candidate)
        if delta>1e-10:moved+=1
        max_shift=max(max_shift,delta)
        result.append(candidate)
    return result,moved,max_shift

def apply_brushes(src:Path,recipe:dict,dest:Path,*,require_change=True):
    if src.resolve()==dest.resolve():
        raise ValueError("Brush must never overwrite original model")
    vertices,uvs,normals,faces=read_obj(src)
    if len(faces)>MAX_FACES or len(vertices)>MAX_VERTICES:
        raise ValueError("Brush model exceeds bounded geometry capacity")
    materials=_face_materials(src,len(faces))
    validate_recipe(recipe,set(materials))
    original,by_vertex,members,neighbors,protected,groups_mats,norms,shortest=_graph(
        vertices,faces,materials)
    active=list(original)
    records=[]
    preceding={}
    for stroke in recipe["strokes"]:
        op=stroke["op"]
        kind=stroke.get("kind")
        center=stroke["center"]
        radius=stroke["radius"]
        strength=stroke["strength"]
        if op=="stamp":
            pattern_source=preceding[stroke["from"]]
            kind=pattern_source["kind"]
            seed=pattern_source["seed"]
            # A stamp borrows the motif and source displacement amplitude, NOT
            # source vertices, topology, normals or UVs.
            amplitude=pattern_source["strength"]*strength
        else:
            seed=stroke.get("seed",0)
            amplitude=strength
        targets={i for i in range(len(active)) if i not in protected and (
            groups_mats[i] and next(iter(groups_mats[i])) in stroke["materials"])}
        weights=[_falloff(active[i],center,radius) for i in range(len(active))]
        before=list(active)
        if op in ("sculpt","stamp"):
            deviations=[]
            for i,p in enumerate(before):
                noise=_pattern(p,center,radius,seed,kind)
                signed=-1 if kind=="carve" else 1
                radial=min(amplitude,shortest[i]*.10,MAX_TOTAL_DISPLACEMENT)
                deviations.append(tuple(signed*noise*radial*norms[i][k] for k in range(3)))
            active,moved,maximum=_deform_positions(before,original,targets,weights,
                                                   deviations,amplitude)
        else:
            moved=0;maximum=0.
            # Taubin lambda/mu smoothing reduces roughness while mitigating
            # Laplacian shrink. All hard/material/boundary groups stay pinned.
            for _ in range(stroke["iterations"]):
                for coefficient in (.44*strength,-.46*strength):
                    previous=list(active)
                    deltas=[]
                    for i,p in enumerate(previous):
                        neighbor=[previous[k] for k in neighbors[i]]
                        if neighbor:
                            average=tuple(sum(pt[k] for pt in neighbor)/len(neighbor)
                                          for k in range(3))
                            # Normal-only filtering retains UV tangent layout
                            # and avoids sideways smearing of anatomical shape.
                            diff=_sub(average,p)
                            disp=_dot(diff,norms[i])*coefficient
                            disp=max(-shortest[i]*.10,min(shortest[i]*.10,disp))
                            deltas.append(tuple(disp*norms[i][k] for k in range(3)))
                        else:
                            deltas.append((0.,0.,0.))
                    active,_,_= _deform_positions(previous,original,targets,weights,
                                                    deltas,.04)
            distances=[math.dist(a,b) for a,b in zip(before,active)]
            moved=sum(x>1e-10 for x in distances)
            maximum=max(distances,default=0.)
        records.append({
            "id":stroke["id"],"op":op,"source_stroke":stroke.get("from"),
            "materials":stroke["materials"],"groups_moved":moved,
            "max_stroke_displacement":round(maximum,9),
            "pinned_topology_groups":len(protected),
            "mesh_faces_inserted":0,"uv_references_modified":0,
            "approved_for_game":False})
        preceding[stroke["id"]]=stroke
    if require_change and not any(s["groups_moved"] for s in records):
        raise ValueError("All requested brush operations were pinned or outside geometry")
    dest.parent.mkdir(parents=True,exist_ok=True)
    _rewrite_obj(src,dest,active,by_vertex,faces,normals)
    original_check=inspect_obj(src);updated=inspect_obj(dest)
    changes=[x for x in ("triangles","boundary_edges","nonmanifold_edges",
                        "degenerate_triangles","duplicate_triangles")
             if original_check[x]!=updated[x]]
    if changes:
        dest.unlink(missing_ok=True)
        raise ValueError("Rejected brush: changed geometric integrity metrics "+", ".join(changes))
    if any(_dot(_unit(_normal(*[original[by_vertex[v[0]]] for v in face])),
                _unit(_normal(*[active[by_vertex[v[0]]] for v in face]))) < .20
           for face in faces):
        dest.unlink(missing_ok=True)
        raise ValueError("Rejected brush: surface triangle orientation changed")
    report={
        "schema_version":1,"engine":"VEYLQUORIN","tool":"adaptive-surface-brushes",
        "source":src.name,"output":dest.name,
        "source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),
        "candidate_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
        "source_vertices":len(vertices),"unique_geometry_vertices":len(original),
        "source_triangles":len(faces),"candidate_triangles":len(faces),
        "topology_pinned_groups":len(protected),
        "strokes":records,"integrity_metrics_before":{
            k:original_check[k] for k in ("boundary_edges","nonmanifold_edges",
                                          "degenerate_triangles","duplicate_triangles")},
        "integrity_metrics_after":{
            k:updated[k] for k in ("boundary_edges","nonmanifold_edges",
                                   "degenerate_triangles","duplicate_triangles")},
        "uvs_and_face_references_preserved":True,
        "raw_geometry_copy_paste_performed":False,
        "source_mesh_preserved":True,
        "technical_geometry_gate_passed":True,
        "artistic_approval":False,"android_emulator_verified":False,
        "photorealism_verified":False,"ready_for_game":False}
    path=dest.parent/(dest.stem+"_brush_review.json")
    path.write_text(json.dumps(report,indent=2)+"\n")
    return report

def main():
    parser=argparse.ArgumentParser(description="VQ topology-preserving sculpt, smooth and stamp tool")
    parser.add_argument("--obj",required=True,type=Path)
    parser.add_argument("--recipe",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    a=parser.parse_args()
    r=apply_brushes(a.obj,json.loads(a.recipe.read_text(encoding="utf-8")),a.out)
    print("VQ_BRUSH_QA_PASS",json.dumps({
        "strokes":len(r["strokes"]),"triangles":r["source_triangles"],
        "groups_moved":sum(row["groups_moved"] for row in r["strokes"]),
        "unchanged_topology":r["technical_geometry_gate_passed"]}))
if __name__=="__main__":main()
