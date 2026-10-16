#!/usr/bin/env python3
"""VEYLQUORIN M30 mesh-derived high-to-low tangent-space normal and signed height bake.

High/low source must use a unique, non-overlapping UV0 atlas within [0,1].
Samples actual high-poly geometric normals by barycentric UV projection onto
the original low-mesh per-pixel tangent frame. Not a fake painted bump map.
Writes review-only normal.png, height.png, strict pixel evidence and hashes.

Limitations: this is UV-correspondence-based baking, not raycast cage projection,
AO, material authoring, Blender Cycles or photorealism validation.
"""
from __future__ import annotations
from collections import defaultdict
import argparse
import hashlib
import json
import math
from pathlib import Path
from engine import read_obj, write_png

MAX_FACES=150000
MAX_PIXELS=512*512

def sub(a,b):return tuple(a[i]-b[i] for i in range(3))
def add(a,b):return tuple(a[i]+b[i] for i in range(3))
def dot(a,b):return sum(a[i]*b[i] for i in range(3))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):
    magnitude=math.sqrt(dot(a,a))
    if magnitude<1e-10:raise ValueError("Zero length vector in material bake")
    return tuple(x/magnitude for x in a)
def mix(p,q,t):return tuple(p[i]*(1-t)+q[i]*t for i in range(3))
def barycentric(uv,a,b,c):
    v0=(b[0]-a[0],b[1]-a[1])
    v1=(c[0]-a[0],c[1]-a[1])
    v2=(uv[0]-a[0],uv[1]-a[1])
    den=v0[0]*v1[1]-v1[0]*v0[1]
    if abs(den)<1e-11:raise ValueError("Collapsed triangle UV island")
    v=(v2[0]*v1[1]-v1[0]*v2[1])/den
    w=(v0[0]*v2[1]-v2[0]*v0[1])/den
    return (1-v-w,v,w)
def interpolate(tri,weights):
    return tuple(sum(tri[j][i]*weights[j] for j in range(3)) for i in range(len(tri[0])))
def encode_normal(x):
    return round(max(0,min(255,(x*.5+.5)*255)))
def uv_rows(src):
    verts,uv,normals,faces=read_obj(Path(src))
    if len(faces)>MAX_FACES:raise ValueError("High/low source exceeds face budget")
    rows=[]
    for face in faces:
        if any(part[1] is None for part in face):
            raise ValueError("Bake needs explicit UV on every mesh corner")
        points=[verts[v[0]][:3] for v in face]
        texture=[uv[v[1]][:2] for v in face]
        if any(not all(math.isfinite(v) and -1e-8<=v<=1+1e-8 for v in pt)
               for pt in texture):
            raise ValueError("Baking cannot safely use tiled/overflow UVs; unwrap into unique UV atlas first")
        n=norm(cross(sub(points[1],points[0]),sub(points[2],points[0])))
        uv_cross=(texture[1][0]-texture[0][0])*(texture[2][1]-texture[0][1])-(
                  texture[1][1]-texture[0][1])*(texture[2][0]-texture[0][0])
        if abs(uv_cross)<1e-10:raise ValueError("UV triangle collapsed")
        rows.append((points,texture,n,face))
    if not rows:raise ValueError("No faces to bake")
    # Shared actual source geometry adjacency; not normal-index seams.
    total=defaultdict(lambda:[0.,0.,0.])
    for points,_,_,_ in rows:
        raw=cross(sub(points[1],points[0]),sub(points[2],points[0]))
        for pt in points:
            key=tuple(round(x,6) for x in pt)
            for k in range(3):total[key][k]+=raw[k]
    vertex_norms=[]
    for points,_,_,_ in rows:
        vertex_norms.append([norm(total[tuple(round(x,6) for x in p)]) for p in points])
    return rows,vertex_norms

def tangent_frame(points,texture,n):
    d1=sub(points[1],points[0]);d2=sub(points[2],points[0])
    u1=texture[1][0]-texture[0][0];v1=texture[1][1]-texture[0][1]
    u2=texture[2][0]-texture[0][0];v2=texture[2][1]-texture[0][1]
    det=u1*v2-u2*v1
    if abs(det)<1e-12:raise ValueError("Tangent frame singular")
    tangent=tuple((d1[k]*v2-d2[k]*v1)/det for k in range(3))
    tangent=norm(tuple(tangent[k]-dot(tangent,n)*n[k] for k in range(3)))
    sign=1 if det>0 else -1
    bitangent=tuple(x*sign for x in cross(n,tangent))
    return tangent,bitangent,n

def raster(rows,vertex_norms,size,*,frame=False):
    lookup=[None]*(size*size)
    overlaps=0
    for fi,(positions,texture,normal,face) in enumerate(rows):
        xs=[pt[0] for pt in texture];ys=[pt[1] for pt in texture]
        xlo=max(0,int(math.floor(min(xs)*size-.5)))
        xhi=min(size-1,int(math.ceil(max(xs)*size-.5)))
        ylo=max(0,int(math.floor(min(ys)*size-.5)))
        yhi=min(size-1,int(math.ceil(max(ys)*size-.5)))
        tbn=tangent_frame(positions,texture,normal) if frame else None
        for y in range(ylo,yhi+1):
            for x in range(xlo,xhi+1):
                uv=((x+.5)/size,(y+.5)/size)
                weights=barycentric(uv,*texture)
                if min(weights)<-2e-7:continue
                pos=interpolate(positions,weights)
                n=norm(interpolate(vertex_norms[fi],weights))
                sample=(pos,n,tbn)
                idx=y*size+x
                older=lookup[idx]
                if older is not None:
                    # Adjacent triangles share UV edges and same geometric
                    # location; true stacked atlas islands are dangerous.
                    if math.dist(older[0],pos)>1e-3:
                        overlaps+=1
                    continue
                lookup[idx]=sample
    if overlaps:
        raise ValueError(f"Overlapping UV islands at {overlaps} texels; no ambiguous bake")
    return lookup

def bake(low,high,out,*,size=128,height_limit=.08):
    if type(size) is not int or size not in (64,128,256,512):
        raise ValueError("Supported output size: 64,128,256,512")
    if type(height_limit) not in (float,int) or not math.isfinite(height_limit) or not 0<height_limit<=.2:
        raise ValueError("Height displacement must have finite upper bound")
    low,high,out=Path(low),Path(high),Path(out)
    if low.resolve()==high.resolve():raise ValueError("A distinct high-detail source is required")
    if low.resolve().is_relative_to(out.resolve()) or high.resolve().is_relative_to(out.resolve()):
        raise ValueError("Never bake over original source files")
    if size*size>MAX_PIXELS:raise ValueError("Pixel budget exceeded")
    low_rows,low_normals=uv_rows(low)
    high_rows,high_normals=uv_rows(high)
    low_pixels=raster(low_rows,low_normals,size,frame=True)
    high_pixels=raster(high_rows,high_normals,size)
    common=0;norm_rgbs=bytearray(size*size*3)
    heights=bytearray(size*size)
    tilted=0;max_angle=0;max_height=0;unmatched=0
    for i,(a,b) in enumerate(zip(low_pixels,high_pixels)):
        if a is None or b is None:
            # Empty texels become neutral, but large uncovered islands fail.
            norm_rgbs[i*3:i*3+3]=bytes((128,128,255))
            heights[i]=128
            if (a is None)!=(b is None):unmatched+=1
            continue
        p,_,tbn=a;high_p,high_n,_=b
        t,bitangent,n=tbn
        local=norm((dot(high_n,t),dot(high_n,bitangent),dot(high_n,n)))
        if local[2]<.15:
            raise ValueError("High-poly normal flipped relative to original low-poly face")
        norm_rgbs[i*3:i*3+3]=bytes(encode_normal(k) for k in local)
        height=dot(sub(high_p,p),n)
        if abs(height)>height_limit+1e-8:
            raise ValueError("High-poly displacement exceeds calibrated ray/cage height limit")
        heights[i]=round(max(0,min(255,127.5+127.5*height/height_limit)))
        max_height=max(max_height,abs(height))
        angle=math.degrees(math.acos(max(-1,min(1,local[2]))))
        max_angle=max(max_angle,angle)
        if angle>3:tilted+=1
        common+=1
    if not common or common<size*size*.60:
        raise ValueError("Insufficient overlapping high/low UV coverage")
    if unmatched>size*size*.01:
        raise ValueError("High- and low-poly UV atlas mismatch")
    if tilted<common*.02:
        raise ValueError("High-res source lacks meaningful baked curvature; do not fabricate detail")
    out.mkdir(parents=True,exist_ok=True)
    normal=out/"normal.png";height=out/"height.png"
    write_png(normal,size,size,3,bytes(norm_rgbs))
    write_png(height,size,size,1,bytes(heights))
    result={"schema_version":1,"engine":"VEYLQUORIN","milestone":"M30",
            "method":"high-to-low shared unique-UV mesh normal projection",
            "low_source_sha256":hashlib.sha256(low.read_bytes()).hexdigest(),
            "high_source_sha256":hashlib.sha256(high.read_bytes()).hexdigest(),
            "resolution":[size,size],"texels_sampled":common,
            "texels_unmatched":unmatched,
            "textured_coverage_fraction":round(common/(size*size),6),
            "meaningful_normal_variation_texels":tilted,
            "max_high_poly_normal_angle_deg":round(max_angle,4),
            "max_high_poly_height_world_units":round(max_height,7),
            "height_encoding_positive_span":height_limit,
            "textures":{"normal":{"path":normal.name,"sha256":hashlib.sha256(normal.read_bytes()).hexdigest()},
                        "height":{"path":height.name,"sha256":hashlib.sha256(height.read_bytes()).hexdigest()}},
            "geometric_surface_used":True,"ao_baked":False,
            "raycast_cage_projection_used":False,"source_files_untouched":True,
            "android_emulator_verified":False,"artistic_signoff":False,
            "production_approved":False}
    (out/"bake_manifest.json").write_text(json.dumps(result,indent=2)+"\n")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--low",type=Path,required=True)
    p.add_argument("--high",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--size",type=int,default=128)
    a=p.parse_args()
    m=bake(a.low,a.high,a.out,size=a.size)
    print("VQ_M30_MESH_NORMAL_BAKE_PASS",json.dumps({
        "texels":m["texels_sampled"],"tilted":m["meaningful_normal_variation_texels"],
        "max_angle_deg":m["max_high_poly_normal_angle_deg"]}))
if __name__=="__main__":main()
