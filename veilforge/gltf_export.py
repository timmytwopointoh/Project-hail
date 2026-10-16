#!/usr/bin/env python3
"""Offline glTF 2.0 exporter for real VEILFORGE geometry and procedural PBR maps.

Produces an indexed mesh with POSITION/NORMAL/UV/COLOR and a material; no
skinning, morph targets, physically based rendering or automatic LOD is claimed.
"""
import argparse
import json
import math
from pathlib import Path
import shutil
import struct
import zlib
from engine import read_obj, write_png, MeshError

FLOAT = 5126
UINT = 5125

def _unpack_gray_png(path: Path):
    data=path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Bad material PNG signature")
    offset=8
    compressed=bytearray()
    width=height=None
    while offset<len(data):
        n=struct.unpack(">I",data[offset:offset+4])[0]
        tag=data[offset+4:offset+8]
        payload=data[offset+8:offset+8+n]
        if len(payload)!=n or offset+12+n>len(data):
            raise ValueError("Broken material PNG")
        if tag==b"IHDR":
            width,height,depth,color,_,_,_=struct.unpack(">IIBBBBB",payload)
            if depth!=8 or color!=0:
                raise ValueError("Expected 8bit gray map")
        elif tag==b"IDAT":
            compressed.extend(payload)
        elif tag==b"IEND":
            break
        offset+=12+n
    if not width or not height or width>8192 or height>8192:
        raise ValueError("Bad material map dimensions")
    raw=zlib.decompress(compressed)
    if len(raw)!=height*(width+1):
        raise ValueError("Bad material map scanline length")
    rows=[]
    for y in range(height):
        s=y*(width+1)
        if raw[s]!=0:
            raise ValueError("Unsupported material PNG row filter")
        rows.append(raw[s+1:s+width+1])
    return width,height,b"".join(rows)

def _packed_metallic_roughness(material_dir: Path, dest: Path):
    w,h,rough=_unpack_gray_png(material_dir/"roughness.png")
    wm,hm,metal=_unpack_gray_png(material_dir/"metallic.png")
    if (w,h)!=(wm,hm):
        raise ValueError("PBR map dimensions mismatch")
    # glTF defines G=roughness, B=metallic; red channel unused.
    pixels=bytearray(w*h*3)
    for i,(r,m) in enumerate(zip(rough,metal)):
        pixels[i*3:i*3+3]=bytes((255,r,m))
    write_png(dest,w,h,3,pixels)

def export(src: Path, dest: Path, *, material_dir=None, profile="skin", double_sided=False):
    v,tex,norm,faces=read_obj(src)
    dest.parent.mkdir(parents=True,exist_ok=True)
    positions=[];normals=[];uvs=[];colors=[];indices=[]
    lookup={}
    for face_number,face in enumerate(faces):
        p=[v[c[0]] for c in face]
        a=[p[1][i]-p[0][i] for i in range(3)]
        b=[p[2][i]-p[0][i] for i in range(3)]
        fallback=(a[1]*b[2]-a[2]*b[1],
                  a[2]*b[0]-a[0]*b[2],
                  a[0]*b[1]-a[1]*b[0])
        for vi,ui,ni in face:
            # Hard vertex splits for un-normaled source faces are intentional.
            key=(vi,ui,ni,face_number if ni is None else None)
            if key not in lookup:
                lookup[key]=len(positions)//3
                vertex=v[vi]
                positions.extend(vertex[:3])
                if ni is not None:
                    normal=norm[ni][:3]
                else:
                    normal=fallback
                mag=math.sqrt(sum(n*n for n in normal))
                if mag<1e-12:
                    normal=(0,1,0)
                    mag=1
                normals.extend(c/mag for c in normal)
                uvs.extend(tex[ui][:2] if ui is not None else (0,0))
                colors.extend(tuple(max(0,min(1,float(c))) for c in vertex[3:6])
                              if len(vertex)>=6 else (1,1,1))
            indices.append(lookup[key])
    if not positions or not indices:
        raise MeshError("No usable mesh")
    bin_data=bytearray()
    views=[]
    accessors=[]
    def add(data,components,fmt,comp_type,target,minimum=None,maximum=None):
        while len(bin_data)%4:
            bin_data.append(0)
        offset=len(bin_data)
        flat=list(data)
        bin_data.extend(struct.pack("<"+fmt*len(flat),*flat))
        view=len(views)
        views.append({"buffer":0,"byteOffset":offset,
                      "byteLength":len(bin_data)-offset,"target":target})
        acc={"bufferView":view,"componentType":comp_type,"count":len(flat)//components,
             "type":{1:"SCALAR",2:"VEC2",3:"VEC3"}[components]}
        if minimum is not None:
            acc["min"]=minimum;acc["max"]=maximum
        accessors.append(acc)
        return len(accessors)-1
    minv=[min(positions[j::3]) for j in range(3)]
    maxv=[max(positions[j::3]) for j in range(3)]
    p=add(positions,3,"f",FLOAT,34962,minv,maxv)
    n=add(normals,3,"f",FLOAT,34962)
    t=add(uvs,2,"f",FLOAT,34962)
    c=add(colors,3,"f",FLOAT,34962)
    ind=add(indices,1,"I",UINT,34963)
    primitive={"attributes":{"POSITION":p,"NORMAL":n,"TEXCOORD_0":t,"COLOR_0":c},
               "indices":ind,"material":0,"mode":4}
    factors={"skin":(0,.65),"steel":(.92,.35),"stone":(0,.8),
             "cloth":(0,.85),"leather":(0,.7)}
    if profile not in factors:
        raise ValueError("Unsupported PBR profile")
    metallic,roughness=factors[profile]
    mat={"name":profile,"doubleSided":bool(double_sided),
         "pbrMetallicRoughness":{"baseColorFactor":[1,1,1,1],
             "metallicFactor":metallic,"roughnessFactor":roughness}}
    images=[]
    textures=[]
    def bind_texture(filename):
        source=dest.parent/(dest.stem+"_"+filename)
        if filename=="metallic_roughness.png":
            _packed_metallic_roughness(material_dir,source)
        else:
            shutil.copyfile(material_dir/filename,source)
        img=len(images)
        images.append({"uri":source.name})
        idx=len(textures)
        textures.append({"source":img})
        return idx
    if material_dir is not None:
        material_dir=Path(material_dir)
        mat["pbrMetallicRoughness"]["baseColorTexture"]={
            "index":bind_texture("albedo.png")}
        mat["pbrMetallicRoughness"]["metallicRoughnessTexture"]={
            "index":bind_texture("metallic_roughness.png")}
        mat["normalTexture"]={"index":bind_texture("normal.png")}
        mat["occlusionTexture"]={"index":bind_texture("ao.png")}
        # Avoid double-applying roughness/metallic factors to mapped channels.
        mat["pbrMetallicRoughness"]["metallicFactor"]=1.0
        mat["pbrMetallicRoughness"]["roughnessFactor"]=1.0
    document={
        "asset":{"version":"2.0","generator":"VEILFORGE M1.1 original-asset exporter"},
        "scene":0,"scenes":[{"nodes":[0]}],
        "nodes":[{"name":dest.stem,"mesh":0}],
        "meshes":[{"name":dest.stem,"primitives":[primitive]}],
        "materials":[mat],
        "buffers":[{"uri":dest.stem+".bin","byteLength":len(bin_data)}],
        "bufferViews":views,"accessors":accessors,
        "extras":{"source_file":src.name,"triangles":len(faces),
                  "manually_approved":False,"rigged":False,
                  "lod_generated":False,"photorealism_verified":False}
    }
    if images:
        document["images"]=images;document["textures"]=textures
    dest.write_text(json.dumps(document,indent=2)+"\n",encoding="utf-8")
    (dest.parent/(dest.stem+".bin")).write_bytes(bin_data)
    return document

def main():
    p=argparse.ArgumentParser(description="Export an original triangulated OBJ to engine-neutral glTF 2.0")
    p.add_argument("--obj",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--material-dir",type=Path)
    p.add_argument("--profile",default="skin",choices=["skin","steel","stone","leather","cloth"])
    p.add_argument("--double-sided",action="store_true",help="Retain open cape/cloth visibility when removing duplicated back faces")
    a=p.parse_args()
    manifest=export(a.obj,a.out,material_dir=a.material_dir,profile=a.profile,double_sided=a.double_sided)
    print("VEILFORGE_GLTF_PASS",a.out,manifest["extras"]["triangles"],"triangles")
if __name__=="__main__":
    main()
