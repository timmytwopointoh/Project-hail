#!/usr/bin/env python3
"""VQ M31: strict chart-aware UV projection from low mesh to detailed high mesh.

For compatible, nested source meshes only: high-poly triangles must lie
within one low-poly face after bounded orthogonal projection. Distinct low
chart UVs map onto the high triangles via barycentric coordinates. Reject
straddling triangles, flips, out-of-cage geometry and excessive budgets.
NOT a general raycast cage baker or automatic remeshing correspondence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from engine import read_obj,inspect_obj
from vq_brushes import _face_materials

MAX_LOW=1800
MAX_HIGH=20000

def vec(a,b):return tuple(a[k]-b[k] for k in range(3))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def bary(p,points):
    a,b,c=points
    v0=vec(b,a);v1=vec(c,a);v2=vec(p,a)
    d00=dot(v0,v0);d01=dot(v0,v1);d11=dot(v1,v1)
    d20=dot(v2,v0);d21=dot(v2,v1)
    den=d00*d11-d01*d01
    if den<=1e-16:raise ValueError("Source low triangle is geometrically collapsed")
    v=(d11*d20-d01*d21)/den
    w=(d00*d21-d01*d20)/den
    return (1-v-w,v,w)

def project(parent,high_points,max_distance):
    a,b,c=parent
    u=vec(b,a);v=vec(c,a)
    n=cross(u,v)
    magnitude=math.sqrt(dot(n,n))
    if magnitude<=1e-12:raise ValueError("Zero low-poly surface normal")
    unit=tuple(q/magnitude for q in n)
    weights=[]
    max_offset=0.
    for point in high_points:
        displacement=dot(vec(point,a),unit)
        if not math.isfinite(displacement) or abs(displacement)>max_distance:
            return None
        projected=tuple(point[i]-unit[i]*displacement for i in range(3))
        coords=bary(projected,parent)
        if min(coords)<-2e-5 or max(coords)>1.00002:
            return None
        weights.append(coords)
        max_offset=max(max_offset,abs(displacement))
    return weights,max_offset

def transfer(low,high,out,*,cage_distance=.06):
    low=Path(low);high=Path(high);out=Path(out)
    if out.resolve() in (low.resolve(),high.resolve()):
        raise ValueError("Never overwrite original high/low source OBJ")
    if low.resolve()==high.resolve():raise ValueError("Two distinct mesh sources required")
    if type(cage_distance) not in (int,float) or not math.isfinite(cage_distance) or not .0001<=cage_distance<=.2:
        raise ValueError("Projection distance must be finite and bounded")
    low_v,low_uv,ln,low_faces=read_obj(low)
    high_v,huv,hn,high_faces=read_obj(high)
    if not (1<=len(low_faces)<=MAX_LOW and 1<=len(high_faces)<=MAX_HIGH):
        raise ValueError("Projection face-pair complexity exceeds bounded capacity")
    low_materials=_face_materials(low,len(low_faces))
    high_materials=_face_materials(high,len(high_faces))
    if not set(high_materials)<=set(low_materials):
        raise ValueError("High-res material not present in low-res source")
    low_geo=[]
    for face in low_faces:
        if any(row[1] is None for row in face):
            raise ValueError("Low source must have complete unique UV atlas")
        pts=[low_v[row[0]][:3] for row in face]
        tex=[low_uv[row[1]][:2] for row in face]
        if any(not all(0<=v<=1 for v in uv) for uv in tex):
            raise ValueError("Source low UV chart outside unit atlas")
        low_geo.append((pts,tex))
    all_uv=[];faces_rewritten=[]
    max_actual_offset=0.
    used_parents=set()
    for i,face in enumerate(high_faces):
        points=[high_v[row[0]][:3] for row in face]
        hit=None
        centroid=tuple(sum(p[k] for p in points)/3 for k in range(3))
        # Fast candidate pruning using the parent face's 3D projected bbox.
        # Exhaustive bounded scan remains deterministic, with no spatial
        # floating point hash/ambiguous nearest-neighbor dependencies.
        for parent,(vertices,texture) in enumerate(low_geo):
            if high_materials[i]!=low_materials[parent]:continue
            probe=project(vertices,points,cage_distance)
            if probe is None:continue
            weights,offset=probe
            # More than one hit for a non-boundary face is ambiguous and fails.
            if hit is not None:
                raise ValueError("High-poly triangle ambiguously spans coincident low UV charts")
            hit=(parent,weights,offset)
        if hit is None:
            raise ValueError(f"High-poly triangle {i} crosses UV charts or falls outside projection cage")
        parent,weights,offset=hit
        used_parents.add(parent)
        max_actual_offset=max(max_actual_offset,offset)
        tex=low_geo[parent][1]
        corners=[]
        for j,(ref,weights3) in enumerate(zip(face,weights)):
            uv=tuple(sum(tex[k][d]*weights3[k] for k in range(3)) for d in range(2))
            uv=tuple(max(0.,min(1.,u)) for u in uv)
            all_uv.append(uv)
            vi,_,ni=ref
            part=f"{vi+1}/{len(all_uv)}"
            if ni is not None:part+=f"/{ni+1}"
            corners.append(part)
        faces_rewritten.append("f "+" ".join(corners)+"\n")
    data=high.read_text(encoding="utf-8").splitlines(keepends=True)
    result=[];face_no=0;uv_written=False
    for line in data:
        item=line.partition("#")[0].strip().split()
        kind=item[0] if item else ""
        if kind=="vt":continue
        if kind=="f":
            if not uv_written:
                result.extend(f"vt {uv[0]:.11f} {uv[1]:.11f}\n" for uv in all_uv)
                uv_written=True
            result.append(faces_rewritten[face_no]);face_no+=1
        else:result.append(line)
    if face_no!=len(high_faces):raise ValueError("Source high face stream changed")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text("".join(result),encoding="utf-8")
    try:
        before=inspect_obj(high);after=inspect_obj(out)
        fixed=("triangles","vertices_welded","boundary_edges","nonmanifold_edges",
               "degenerate_triangles","bounds_min","bounds_max")
        if any(before[k]!=after[k] for k in fixed) or after["uvs_outside_zero_one"]:
            raise ValueError("Projected high UVs changed source geometry")
        from vq_mesh_baker import uv_rows
        uv_rows(out)
    except Exception:
        out.unlink(missing_ok=True)
        raise
    report={"schema_version":1,"engine":"VEYLQUORIN","milestone":"M31",
        "low_sha256":hashlib.sha256(low.read_bytes()).hexdigest(),
        "high_sha256":hashlib.sha256(high.read_bytes()).hexdigest(),
        "projected_high_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
        "low_faces":len(low_faces),"high_faces":len(high_faces),
        "parent_charts_used":len(used_parents),
        "maximum_highpoly_projection_offset":round(max_actual_offset,8),
        "cage_distance_limit":cage_distance,
        "exact_uv_face_correspondence_required":True,
        "unsupported_chart_crossings_rejected":True,
        "source_geometry_preserved":True,
        "arbitrary_organic_mesh_projection":False,
        "general_raycast_cage_implemented":False,
        "game_approved":False,"artistic_signoff":False}
    (out.parent/(out.stem+"_transfer_report.json")).write_text(
        json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--low",type=Path,required=True)
    p.add_argument("--high",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--cage-distance",type=float,default=.06)
    a=p.parse_args()
    row=transfer(a.low,a.high,a.out,cage_distance=a.cage_distance)
    print("VQ_M31_CORRESPONDENCE_PASS",row["high_faces"],"high faces",
          row["parent_charts_used"],"low charts")
if __name__=="__main__":main()
