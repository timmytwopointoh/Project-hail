#!/usr/bin/env python3
"""VEILFORGE M27: non-destructive, material-scoped triangle-center sculpt layers.

Source polygons, edge geometry, vertex colors, materials, and UV edge endpoints
are preserved. Each selected triangle is subdivided into three around its
interior centroid. Small signed relief along the ORIGINAL face normal adds
real 3D geometry without moving any original mesh edge or seam.

This is a portable procedural source-sculpt tool, not automatic artistic
sculpting, retopology, watertightness or a high-poly DCC substitute.
"""
from __future__ import annotations

import hashlib
import math
from collections import defaultdict

SCULPT_MODES=("micro_relief",)
MAX_LAYERS=3

def _noise3(x,y,z,seed):
    # Reproducible smooth 3D value noise independent of Python hash seeds.
    def h(a,b,c):
        raw=f"{seed}:{a}:{b}:{c}".encode("ascii")
        return int.from_bytes(hashlib.blake2s(raw,digest_size=4).digest(),"big")/4294967295
    px,py,pz=(math.floor(i) for i in (x,y,z))
    tx,ty,tz=(v-math.floor(v) for v in (x,y,z))
    tx,ty,tz=(v*v*(3-2*v) for v in (tx,ty,tz))
    def blend(a,b,t):return a+(b-a)*t
    lower=blend(blend(h(px,py,pz),h(px+1,py,pz),tx),
                blend(h(px,py+1,pz),h(px+1,py+1,pz),tx),ty)
    upper=blend(blend(h(px,py,pz+1),h(px+1,py,pz+1),tx),
                blend(h(px,py+1,pz+1),h(px+1,py+1,pz+1),tx),ty)
    return blend(lower,upper,tz)*2-1

def validate_layers(layers,allowed_materials):
    if not isinstance(layers,list) or len(layers)>MAX_LAYERS:
        raise ValueError("Sculpt layers must be a bounded list (max three)")
    seen=set()
    for row in layers:
        if not isinstance(row,dict):
            raise ValueError("Sculpt layer must be an object")
        required={"id","mode","amplitude","frequency","materials"}
        optional={"center","radius","enabled"}
        if set(row)-required-optional or not required.issubset(row):
            raise ValueError("Sculpt layer has missing/unsupported fields")
        name=row["id"]
        if not isinstance(name,str) or not (2<=len(name)<=40) or not (
                name[0].isalpha() and all(x.islower() or x.isdigit() or x in "-_" for x in name)):
            raise ValueError("Unsafe sculpt layer id")
        if name in seen:raise ValueError("Duplicate sculpt layer id")
        seen.add(name)
        if row["mode"] not in SCULPT_MODES:
            raise ValueError("Unsupported sculpt mode")
        for k,lo,hi in (("amplitude",.0001,.025),("frequency",.20,40)):
            v=row[k]
            if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi:
                raise ValueError("Sculpt "+k+" outside bounded range")
        mats=row["materials"]
        if not isinstance(mats,list) or not 1<=len(mats)<=8 or len(set(mats))!=len(mats) or not set(mats)<=set(allowed_materials):
            raise ValueError("Sculpt layer materials unsupported")
        if "enabled" in row and type(row["enabled"]) is not bool:
            raise ValueError("Sculpt enabled must be boolean")
        spatial="center" in row or "radius" in row
        if spatial and not ("center" in row and "radius" in row):
            raise ValueError("Spatial masks require center and radius")
        if spatial:
            xyz=row["center"]
            if not isinstance(xyz,list) or len(xyz)!=3 or any(
                type(v) not in (float,int) or not math.isfinite(v) or abs(v)>1000 for v in xyz):
                raise ValueError("Invalid sculpt mask center")
            r=row["radius"]
            if type(r) not in (int,float) or not math.isfinite(r) or not .05<=r<=100:
                raise ValueError("Invalid sculpt mask radius")
    return True

def _falloff(center,row):
    if "center" not in row:return 1.
    distance=math.dist(center,row["center"])/row["radius"]
    if distance>=1:return 0.
    # C1-continuous smooth radial region mask, no sharp sculpt boundary.
    t=1-distance
    return t*t*(3-2*t)

def apply_layers(source, layers, seed, *, triangle_budget=55000):
    """Returns NEW Mesh plus numeric report, without editing input source.

    Subdivision does not move original edges, preventing cracks across UV
    seams or neighboring faces. It CAN reveal the existing source geometry's
    nonmanifold surfaces and is not approved for skin deformation automatically.
    """
    from factory import Mesh, MATERIALS, AssetError, _norm, _cross, _vec
    validate_layers(layers,MATERIALS)
    if isinstance(seed,bool) or not isinstance(seed,int) or seed<0 or seed>2147483647:
        raise AssetError("Invalid sculpt seed")
    if not 0<source.triangle_count<=triangle_budget:
        raise AssetError("Invalid input sculpt triangle budget")
    current=source
    history=[]
    for layer_index,row in enumerate(layers):
        before=current.triangle_count
        target=set(row["materials"])
        active=row.get("enabled",True)
        estimate=sum(len(faces)*(3 if active and mat in target else 1)
                     for mat,faces in current.parts.items())
        if estimate>triangle_budget:
            raise AssetError("Sculpt layer would exceed quality-tier triangle budget")
        next_mesh=Mesh()
        selected=0;displaced=0;max_shift=0.;degenerate_fallbacks=0
        for material,faces in current.parts.items():
            for face in faces:
                a,b,c,n,uv,tint=face
                if not active or material not in target:
                    next_mesh.parts[material].append(face)
                    continue
                selected+=1
                center=tuple((a[k]+b[k]+c[k])/3 for k in range(3))
                tc=tuple(sum(v[k] for v in uv)/3 for k in range(2))
                falloff=_falloff(center,row)
                # Noise never depends on traversal order / worker process.
                f=row["frequency"]
                seed_offset=seed+101*layer_index
                fluctuation=_noise3(center[0]*f,center[1]*f,center[2]*f,seed_offset)
                second=_noise3(center[0]*f*2,center[1]*f*2,center[2]*f*2,seed_offset+97)
                amount=row["amplitude"]*falloff*(.75*fluctuation+.25*second)
                shortest=min(math.dist(a,b),math.dist(b,c),math.dist(c,a))
                amount=max(-.12*shortest,min(.12*shortest,amount))
                apex=tuple(center[k]+amount*n[k] for k in range(3))
                children=((a,b,apex,uv[0],uv[1],tc),
                          (b,c,apex,uv[1],uv[2],tc),
                          (c,a,apex,uv[2],uv[0],tc))
                accepted=[]
                try:
                    for p,q,r,pt,qt,rt in children:
                        norm=_norm(_cross(_vec(p,q),_vec(p,r)))
                        if sum(norm[k]*n[k] for k in range(3))<=.55:
                            raise AssetError("Sculpt child triangle flipped too far")
                        accepted.append((p,q,r,norm,(pt,qt,rt),tint))
                except AssetError:
                    # Zero-strength split remains valid and visually equivalent
                    # for any numerically brittle source triangle.
                    apex=center
                    accepted=[]
                    for p,q,pt,qt in ((a,b,uv[0],uv[1]),(b,c,uv[1],uv[2]),(c,a,uv[2],uv[0])):
                        norm=_norm(_cross(_vec(p,q),_vec(p,apex)))
                        accepted.append((p,q,apex,norm,(pt,qt,tc),tint))
                    degenerate_fallbacks+=1
                    amount=0.
                next_mesh.parts[material].extend(accepted)
                if abs(amount)>1e-10:displaced+=1
                max_shift=max(max_shift,abs(amount))
        history.append({
            "id":row["id"],"mode":row["mode"],"enabled":active,
            "source_triangles":before,"result_triangles":next_mesh.triangle_count,
            "faces_subdivided":selected,"centroids_displaced":displaced,
            "max_displacement_model_units":round(max_shift,9),
            "numeric_fallbacks":degenerate_fallbacks,
            "original_edges_displaced":0,"uv_edge_endpoints_moved":0,
            "materials":sorted(target),
            "artist_approved":False})
        current=next_mesh
    return current,{
        "schema_version":1,"layer_count":len(layers),
        "source_triangles":source.triangle_count,
        "result_triangles":current.triangle_count,
        "layers":history,"non_destructive_source_preserved":True,
        "original_edge_vertices_unchanged":True,
        "glTF_export_test_required":True,
        "android_visual_validation_required":True,
        "photorealism_verified":False,
        "manual_aesthetic_approval_required":True}
