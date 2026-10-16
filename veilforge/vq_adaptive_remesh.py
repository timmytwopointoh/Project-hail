#!/usr/bin/env python3
"""VQ M29 conforming adaptive subdivision of real triangulated OBJ sources.

Edge-based refinement: a selected interior edge is always split for BOTH
incident triangles, with exact shared geometric midpoint. Standard green
1-edge/2-edge templates and regular 3-edge red subdivision avoid T-junctions.
Existing OBJ materials, vertex colors, texture seams, normal references,
and hard/boundary edges remain intact. No sculpt displacement is performed.

This is adaptive *subdivision* -- not automatic mesh decimation, deformation-
aware retopology, improved silhouette, or proof of photorealism.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
from engine import read_obj,inspect_obj
from vq_brushes import _face_materials,_normal,_unit,_dot

MAX_VERTICES=250000
MAX_FACES=120000
MAX_EDGES_PER_PASS=8000

def _number(value,lo,hi,label):
    if type(value) not in (int,float) or not math.isfinite(value) or not lo<=value<=hi:
        raise ValueError(f"{label} is not a finite, bounded number")
    return float(value)

def validate_recipe(recipe,materials):
    if not isinstance(recipe,dict) or recipe.get("schema_version")!=1:
        raise ValueError("Adaptive refinement expects schema_version=1")
    keys={"schema_version","center","radius","target_edge_length",
          "max_edges","triangle_budget","materials","crease_angle_deg"}
    if set(recipe)!=keys:
        raise ValueError("Missing or unsupported refinement recipe properties")
    center=recipe["center"]
    if not isinstance(center,list) or len(center)!=3:
        raise ValueError("Refinement center must have three coordinates")
    for coord in center:_number(coord,-1000,1000,"center")
    _number(recipe["radius"],.05,100,"radius")
    _number(recipe["target_edge_length"],.025,20,"target_edge_length")
    _number(recipe["crease_angle_deg"],5,85,"crease_angle_deg")
    for key,lo,hi in (("max_edges",1,MAX_EDGES_PER_PASS),
                      ("triangle_budget",4,MAX_FACES)):
        v=recipe[key]
        if type(v) is not int or not lo<=v<=hi:
            raise ValueError(key+" must be an integer within the budget")
    mats=recipe["materials"]
    if not isinstance(mats,list) or not 1<=len(mats)<=16 or (
        len(set(mats))!=len(mats)) or not set(mats)<=set(materials):
        raise ValueError("Invalid refinement material targets")
    return True

def _face_style(src,face_count):
    active={"o":None,"g":None,"s":None}
    result=[]
    mtllib=[]
    for line in src.read_text(encoding="utf-8").splitlines():
        tokens=line.partition("#")[0].strip().split()
        if not tokens:continue
        key=tokens[0]
        if key in active:active[key]=" ".join(tokens[1:])
        elif key=="mtllib":mtllib.append(line)
        elif key=="f":result.append(tuple(active[k] for k in ("o","g","s")))
    if len(result)!=face_count:raise ValueError("Unaligned OBJ face styles")
    return result,mtllib

def _signed_normal(vertices,face):
    p=[vertices[v[0]][:3] for v in face]
    return _normal(*p)

def _triangle_area(a,b,c):
    n=_normal(a,b,c)
    return .5*math.sqrt(_dot(n,n))

def _canonical(point):
    return tuple(round(x,6) for x in point[:3])

def _mesh_edges(vertices,faces):
    incidence=defaultdict(list)
    face_edges=[]
    normal=[]
    for index,tri in enumerate(faces):
        geom=[_canonical(vertices[v[0]]) for v in tri]
        if len(set(geom))!=3:raise ValueError("Source has geometrically collapsed welded triangle")
        ids=[]
        for i in range(3):
            edge=tuple(sorted((geom[i],geom[(i+1)%3])))
            incidence[edge].append(index);ids.append(edge)
        face_edges.append(ids)
        normal.append(_unit(_signed_normal(vertices,tri)))
    return incidence,face_edges,normal

def _select_edges(verts,faces,face_materials,incidence,face_edges,normals,recipe):
    center=recipe["center"];radius=recipe["radius"]
    min_edge=recipe["target_edge_length"]
    threshold=math.cos(math.radians(recipe["crease_angle_deg"]))
    valid=set(recipe["materials"])
    ranked=[]
    for key,adj in incidence.items():
        if len(adj)!=2:continue   # preserve open borders and nonmanifold seams
        a,b=adj
        if face_materials[a] not in valid or face_materials[b] not in valid:
            continue
        if _dot(normals[a],normals[b])<threshold:
            continue # preserve sharp architectural edges
        midpoint=tuple((key[0][i]+key[1][i])*.5 for i in range(3))
        dist=math.dist(midpoint,center)
        if dist>radius:continue
        length=math.dist(key[0],key[1])
        if length<min_edge:continue
        # Longer and moderately curved edges are prioritized; face
        # selection alone would leave cracks on neighboring triangles.
        curvature=max(0,1-_dot(normals[a],normals[b]))
        falloff=1-dist/radius
        score=(length/min_edge)*(0.65+0.35*falloff)*(1+2*curvature)
        ranked.append((-score,key,tuple(adj)))
    ranked.sort()
    chosen=set()
    face_splits=[0]*len(faces)
    triangle_count=len(faces)
    for _,key,adj in ranked:
        if len(chosen)>=recipe["max_edges"]:break
        increase=len(adj) # each incident triangle gets one added face
        if triangle_count+increase>recipe["triangle_budget"]:continue
        chosen.add(key)
        triangle_count+=increase
        for fi in adj:face_splits[fi]+=1
    return chosen,face_splits,len(ranked),triangle_count

def _interpolate(v0,v1):
    return tuple((v0[i]+v1[i])*.5 for i in range(len(v0)))

def refine(src:Path,recipe:dict,dest:Path):
    """Write a new candidate OBJ + QA JSON. Never mutate the source OBJ."""
    src=Path(src);dest=Path(dest)
    if src.resolve()==dest.resolve():
        raise ValueError("Never overwrite the source OBJ")
    vertices,uvs,normals,faces=read_obj(src)
    if len(vertices)>MAX_VERTICES or len(faces)>MAX_FACES:
        raise ValueError("Source OBJ exceeds bounded refinement capacities")
    materials=_face_materials(src,len(faces))
    validate_recipe(recipe,set(materials))
    if len(faces)>recipe["triangle_budget"]:
        raise ValueError("Source already exceeds candidate triangle budget")
    styles,mtllib=_face_style(src,len(faces))
    incidence,face_edges,unit_normals=_mesh_edges(vertices,faces)
    for i,n in enumerate(unit_normals):
        if _dot(n,n)<.5:raise ValueError(f"Degenerate source triangle at {i}")
    chosen,splits,possible,expected=_select_edges(
        vertices,faces,materials,incidence,face_edges,unit_normals,recipe)
    if not chosen:raise ValueError("No safe interior edges qualify for adaptive refinement")
    new_vertices=list(vertices)
    new_uvs=list(uvs)
    new_normals=list(normals)
    out_faces=[]
    out_mats=[];out_styles=[]
    new_edge_counts={0:0,1:0,2:0,3:0}
    def insert_mid(tri,edge_index):
        p=tri[edge_index]
        q=tri[(edge_index+1)%3]
        vp=new_vertices[p[0]];vq=new_vertices[q[0]]
        new_vertices.append(_interpolate(vp,vq))
        vi=len(new_vertices)-1
        if p[1] is None and q[1] is None:ui=None
        elif p[1] is not None and q[1] is not None:
            new_uvs.append(_interpolate(new_uvs[p[1]],new_uvs[q[1]]))
            ui=len(new_uvs)-1
        else:raise ValueError("Mixed UV presence on same triangle edge")
        if p[2] is None and q[2] is None:ni=None
        elif p[2] is not None and q[2] is not None:
            n=_unit(_interpolate(new_normals[p[2]][:3],new_normals[q[2]][:3]))
            if _dot(n,n)<.5:n=unit_normals[fi]
            new_normals.append(n)
            ni=len(new_normals)-1
        else:raise ValueError("Mixed normals on same triangle edge")
        return (vi,ui,ni)
    for fi,tri in enumerate(faces):
        flags=[edge in chosen for edge in face_edges[fi]]
        nflags=sum(flags)
        new_edge_counts[nflags]+=1
        if not nflags:
            subs=[tri]
        else:
            mids={i:insert_mid(tri,i) for i in range(3) if flags[i]}
            if nflags==1:
                i=flags.index(True)
                a,b,c=(tri[i],tri[(i+1)%3],tri[(i+2)%3])
                m=mids[i]
                subs=[(a,m,c),(m,b,c)]
            elif nflags==2:
                i=next(k for k in range(3) if flags[k] and flags[(k+1)%3])
                a,b,c=(tri[i],tri[(i+1)%3],tri[(i+2)%3])
                m=mids[i];n=mids[(i+1)%3]
                subs=[(a,m,c),(m,n,c),(m,b,n)]
            else:
                a,b,c=tri
                m,n,o=mids[0],mids[1],mids[2]
                subs=[(a,m,o),(m,b,n),(o,n,c),(m,n,o)]
        base=_signed_normal(new_vertices,tri)
        original_area=_triangle_area(*[new_vertices[v[0]][:3] for v in tri])
        subtotal=0.
        for child in subs:
            area=_triangle_area(*[new_vertices[v[0]][:3] for v in child])
            norm=_signed_normal(new_vertices,child)
            if area<=1e-12 or _dot(norm,base)<=0:
                raise ValueError("Subdivision would invert or collapse a face")
            subtotal+=area
            out_faces.append(child);out_mats.append(materials[fi])
            out_styles.append(styles[fi])
        if abs(subtotal-original_area)>max(1e-8,original_area*2e-6):
            raise ValueError("Subdivision changed total planar face area")
    if len(out_faces)!=expected or len(out_faces)>recipe["triangle_budget"]:
        raise ValueError("Adaptive subdivision exceeded planned budget")
    # Explicit single material/group/shading state per triangle preserves
    # the original per-face OBJ topology semantics and UV seam references.
    lines=["# VEYLQUORIN M29 / review-only conforming adaptive subdivided mesh"]
    lines.extend(mtllib)
    for v in new_vertices:lines.append("v "+" ".join(f"{x:.10g}" for x in v))
    for v in new_uvs:lines.append("vt "+" ".join(f"{x:.10g}" for x in v))
    for v in new_normals:lines.append("vn "+" ".join(f"{x:.10g}" for x in v))
    current_mat=None
    current_style=(None,None,None)
    for tri,mat,style in zip(out_faces,out_mats,out_styles):
        for i,k in enumerate(("o","g","s")):
            if style[i]!=current_style[i] and style[i] is not None:
                lines.append(k+" "+style[i])
        current_style=style
        if mat!=current_mat:
            lines.append("usemtl "+mat)
            current_mat=mat
        corners=[]
        for vi,ui,ni in tri:
            item=str(vi+1)
            if ui is not None or ni is not None:
                item+="/"+(str(ui+1) if ui is not None else "")
                if ni is not None:item+="/"+str(ni+1)
            corners.append(item)
        lines.append("f "+" ".join(corners))
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text("\n".join(lines)+"\n",encoding="utf-8")
    try:
        before=inspect_obj(src);after=inspect_obj(dest)
        invariant_keys=("boundary_edges","nonmanifold_edges","degenerate_triangles",
                        "duplicate_triangles")
        issues=[k for k in invariant_keys if before[k]!=after[k]]
        if after["triangles"]!=expected:issues.append("triangles")
        if issues:raise ValueError("Post-export topology invariant failure: "+", ".join(issues))
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    report={"schema_version":1,"engine":"VEYLQUORIN","milestone":"M29",
            "tool":"conforming_adaptive_edge_subdivision",
            "source_obj":src.name,"candidate_obj":dest.name,
            "source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),
            "candidate_sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
            "source_triangles":len(faces),"candidate_triangles":len(out_faces),
            "qualified_interior_edges":possible,
            "edges_selected":len(chosen),"edge_budget":recipe["max_edges"],
            "triangle_budget":recipe["triangle_budget"],
            "source_faces_by_split_count":{str(k):v for k,v in new_edge_counts.items()},
            "geometry_welded_topology_preserved":True,
            "source_face_materials_preserved":True,
            "existing_uv_corner_attributes_preserved":True,
            "new_midpoint_uvs_interpolated":True,
            "new_materials_created":False,"source_modified":False,
            "topology_before":{k:before[k] for k in invariant_keys},
            "topology_after":{k:after[k] for k in invariant_keys},
            "numeric_geometry_gate_passed":True,
            "perceptual_quality_improved_not_established":True,
            "android_emulator_tested":False,"artistic_signoff":False,
            "game_approved":False}
    (dest.parent/(dest.stem+"_remesh_report.json")).write_text(
        json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser(description="Conforming adaptive 3D model source refinement")
    p.add_argument("--obj",type=Path,required=True)
    p.add_argument("--recipe",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    report=refine(a.obj,json.loads(a.recipe.read_text(encoding="utf-8")),a.out)
    print("VQ_M29_CONFORMING_REMESH_PASS",json.dumps({
        "triangles_before":report["source_triangles"],
        "triangles_after":report["candidate_triangles"],
        "edges_selected":report["edges_selected"],
        "technical_gate":report["numeric_geometry_gate_passed"]}))
if __name__=="__main__":main()
