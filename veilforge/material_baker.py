#!/usr/bin/env python3
"""VEILFORGE M5 procedural UV-aligned material maps (source, not scanned PBR).

Generates deterministic, tileable base color, tangent-space normal, packed
glTF metallic/roughness (G=roughness, B=metallic), and occlusion PNGs. These
maps are input to the mobile material-viewer and future high-poly baking, not
proof of realistic materials or physically accurate BRDF rendering.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
from engine import _noise, _clamp, write_png
from factory import MATERIALS, AssetError

def bake(name, out:Path, *, size=128, seed=0):
    if name not in MATERIALS:raise AssetError("Unknown surface material")
    if size not in (64,128,256,512):raise AssetError("Unsupported material resolution")
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    m=MATERIALS[name]
    base=[round(255*c) for c in m["base"][:3]]
    rough=int(round(m["roughness"]*255));metal=int(round(m["metallic"]*255))
    height=bytearray(size*size);albedo=bytearray(size*size*3)
    packed=bytearray(size*size*3);normal=bytearray(size*size*3)
    ao=bytearray(size*size)
    seed=seed%2147483647
    for y in range(size):
        for x in range(size):
            n1=_noise(x,y,seed+73,size)
            n2=_noise(x*2,y*2,seed+31,size*2)
            # Directional but tileable grain for wood; stones and cloth use
            # isotropic multi-frequency variation; metals use fine scratches.
            if name in ("wood","dark_wood","bark"):
                grain=_noise(x//3,y*2,seed+17,size)
                v=.56*n1+.19*n2+.25*grain
            elif name in ("steel","iron","bronze"):
                v=.48*n1+.40*n2+.12*_noise(x,y*4,seed+9,size*4)
            else:
                v=.62*n1+.38*n2
            i=y*size+x
            height[i]=_clamp(v*255)
            variation={"stone":.17,"stone_trim":.11,"earth":.21,"grass":.25,
                       "bark":.20,"leaf":.19,"wood":.16,"dark_wood":.16,
                       "steel":.10,"iron":.13,"bronze":.13,"leather":.12}[name]
            for c in range(3):
                albedo[i*3+c]=_clamp(base[c]*(1+(v-.5)*2*variation))
            packed[i*3:i*3+3]=bytes((255,_clamp(rough+(v-.5)*26),
                                        _clamp(metal+(v-.5)*12 if metal else 0)))
            ao[i]=_clamp(242+(v-.5)*20)
    for y in range(size):
        for x in range(size):
            i=y*size+x
            dx=(int(height[y*size+(x+1)%size])-int(height[y*size+(x-1)%size]))/255
            dy=(int(height[((y+1)%size)*size+x])-int(height[((y-1)%size)*size+x]))/255
            vec=(-dx*.8,-dy*.8,1.)
            length=math.sqrt(sum(v*v for v in vec))
            for c in range(3):
                normal[i*3+c]=_clamp((vec[c]/length*.5+.5)*255)
    files={"albedo":("albedo.png",albedo,3),
           "metallic_roughness":("metallic_roughness.png",packed,3),
           "normal":("normal.png",normal,3),
           "ao":("ao.png",ao,1)}
    manifest={}
    for key,(filename,data,chans) in files.items():
        path=out/filename
        write_png(path,size,size,chans,bytes(data))
        manifest[key]={"file":filename,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    summary={"schema_version":1,"material":name,"resolution":[size,size],
             "seed":seed,"maps":manifest,"source":"original procedural tiling",
             "physically_based_reference_approved":False,
             "normal_is_tangent_space":True,
             "gltf_packed_metallic_roughness":True}
    (out/"bake_manifest.json").write_text(json.dumps(summary,indent=2)+"\n")
    return summary
