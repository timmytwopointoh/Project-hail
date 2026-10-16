#!/usr/bin/env python3
"""VQ M29 real multi-material indexed glTF export after brush/remesh operations.

Unlike the single-material diagnostic preview, this preserves all OBJ material
groups and copies verified textures/PBR factors from the original source glTF.
It does not bake new surface detail, generate tangent vectors or approve assets.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import copy
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct

from engine import read_obj
from factory import MATERIALS
from vq_brushes import _face_materials
from vq_model_tools import check_gltf

FLOAT=5126
UINT32=5125
MAX_TRIANGLES=120000
MAX_IMAGES=128

def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _unit(v):
    m=math.sqrt(sum(x*x for x in v))
    if m<1e-15:raise ValueError("Degenerate face normal")
    return tuple(x/m for x in v)

def _normal(a,b,c):
    p=[b[i]-a[i] for i in range(3)]
    q=[c[i]-a[i] for i in range(3)]
    return _unit((p[1]*q[2]-p[2]*q[1],
                 p[2]*q[0]-p[0]*q[2],
                 p[0]*q[1]-p[1]*q[0]))

def _texture_path(parent,uri):
    if not isinstance(uri,str) or not uri.startswith("textures/") or "\\" in uri or ".." in uri:
        raise ValueError("Unsafe or external glTF texture URI")
    path=(parent/uri).resolve()
    if not path.is_relative_to(parent.resolve()) or path.is_symlink():
        raise ValueError("Texture path escapes source asset directory")
    if path.suffix.lower()!=".png" or not path.is_file():
        raise ValueError("Expected a real local PNG texture")
    return path

def _original_materials(source_gltf,source_manifest,out):
    gltf_path=Path(source_gltf)
    source=json.loads(gltf_path.read_text(encoding="utf-8"))
    if source.get("asset",{}).get("version")!="2.0":
        raise ValueError("Expected glTF 2.0 material reference")
    if source.get("extras",{}).get("production_approved") is True:
        raise ValueError("Source claimed unreviewed production approval")
    manifest=None
    if source_manifest is not None:
        manifest=json.loads(Path(source_manifest).read_text(encoding="utf-8"))
        if _sha(gltf_path)!=manifest.get("gltf_sha256"):
            raise ValueError("Source glTF integrity mismatch")
    sources={}
    for mat in source.get("materials",[]):
        name=mat.get("name","")
        if not name or name in sources:raise ValueError("Invalid source material name")
        sources[name]=copy.deepcopy(mat)
    if not sources:raise ValueError("No source glTF materials")
    images=source.get("images",[])
    if len(images)>MAX_IMAGES:raise ValueError("Excessive image references")
    valid_images={}
    if manifest is not None:
        for name,meta in manifest.get("texture_maps",{}).items():
            for part in meta.get("maps",{}).values():
                valid_images["textures/"+name+"/"+part["file"]]=part["sha256"]
    for img in images:
        uri=img.get("uri","")
        path=_texture_path(gltf_path.parent,uri)
        if manifest is not None and (uri not in valid_images or
                                     _sha(path)!=valid_images[uri]):
            raise ValueError("Texture digest differs from original asset manifest")
        destination=out/uri
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,destination)
    return sources,images,source.get("textures",[]),source.get("samplers",[])

def export(src,out,*,source_gltf=None,source_manifest=None):
    src=Path(src);out=Path(out)
    if src.resolve()==out.resolve():
        raise ValueError("Never overwrite input source")
    if bool(source_manifest) and not source_gltf:
        raise ValueError("Source manifest requires source glTF")
    verts,uvs,normals,faces=read_obj(src)
    if len(faces)>MAX_TRIANGLES:raise ValueError("Too many triangles")
    materials=_face_materials(src,len(faces))
    out.parent.mkdir(parents=True,exist_ok=True)
    if source_gltf is not None:
        reference,images,textures,samplers=_original_materials(
            source_gltf,source_manifest,out.parent)
        missing=set(materials)-set(reference)
        if missing:raise ValueError("Source glTF lacks material assignments: "+str(sorted(missing)))
        material_names=sorted(set(materials))
        mat_def=[reference[n] for n in material_names]
        if images and any(any(c[1] is None for c in face) for face in faces):
            raise ValueError("Material-textured OBJ contains faces without UVs")
    else:
        material_names=sorted(set(materials))
        mat_def=[]
        images=textures=samplers=[]
        for name in material_names:
            factors=MATERIALS.get(name,{"base":[.8,.8,.8,1.],"metallic":0.,
                                       "roughness":.8})
            mat_def.append({"name":name,"pbrMetallicRoughness":{
                "baseColorFactor":factors["base"],
                "metallicFactor":factors["metallic"],
                "roughnessFactor":factors["roughness"]}})
    gltf_buffer=bytearray();views=[];accessors=[];primitives=[]
    def pack(data,components,kind,target,bounds=False):
        while len(gltf_buffer)%4:gltf_buffer.append(0)
        offset=len(gltf_buffer)
        fmt="f" if kind==FLOAT else "I"
        gltf_buffer.extend(struct.pack("<"+fmt*len(data),*data))
        views.append({"buffer":0,"byteOffset":offset,
                      "byteLength":len(gltf_buffer)-offset,"target":target})
        n=len(data)//components
        item={"bufferView":len(views)-1,"componentType":kind,"count":n,
              "type":{1:"SCALAR",2:"VEC2",3:"VEC3",4:"VEC4"}[components]}
        if bounds:
            item["min"]=[min(data[k::components]) for k in range(components)]
            item["max"]=[max(data[k::components]) for k in range(components)]
        accessors.append(item)
        return len(accessors)-1
    face_by_material=defaultdict(list)
    for fi,material in enumerate(materials):face_by_material[material].append(fi)
    exported_vertices=0
    for mat_index,name in enumerate(material_names):
        pos=[];norm=[];uv=[];colors=[];indices=[];seen={}
        for fi in face_by_material[name]:
            tri=faces[fi]
            face_normal=_normal(*[verts[part[0]][:3] for part in tri])
            for vi,ui,ni in tri:
                key=(vi,ui,ni,fi if ni is None else None)
                if key not in seen:
                    seen[key]=len(pos)//3
                    p=verts[vi]
                    pos.extend(p[:3])
                    if ni is not None:
                        try:n=_unit(normals[ni][:3])
                        except ValueError:n=face_normal
                    else:n=face_normal
                    norm.extend(n)
                    if ui is not None:uv.extend(uvs[ui][:2])
                    else:uv.extend((0,0))
                    colors.extend(tuple(max(0,min(1,float(x))) for x in p[3:6])
                                  if len(p)>=6 else (1.,1.,1.))
                indices.append(seen[key])
        attrs={"POSITION":pack(pos,3,FLOAT,34962,True),
               "NORMAL":pack(norm,3,FLOAT,34962),
               "COLOR_0":pack(colors,3,FLOAT,34962)}
        if all(all(c[1] is not None for c in faces[fi]) for fi in face_by_material[name]):
            attrs["TEXCOORD_0"]=pack(uv,2,FLOAT,34962)
        elif source_gltf is not None and images:
            raise ValueError("Textured primitive lacks complete UVs")
        idx=pack(indices,1,UINT32,34963)
        primitives.append({"attributes":attrs,"indices":idx,
                           "material":mat_index,"mode":4})
        exported_vertices+=len(pos)//3
    doc={"asset":{"version":"2.0","generator":"VEYLQUORIN M29 preserved-material exporter"},
         "scene":0,"scenes":[{"nodes":[0]}],
         "nodes":[{"mesh":0,"name":out.stem}],
         "meshes":[{"name":out.stem,"primitives":primitives}],
         "materials":mat_def,"buffers":[{"uri":out.stem+".bin","byteLength":len(gltf_buffer)}],
         "bufferViews":views,"accessors":accessors,
         "extras":{"source_sha256":_sha(src),"triangles":len(faces),
                   "distinct_materials":len(material_names),
                   "indexed_vertices":exported_vertices,
                   "original_material_library_verified":source_manifest is not None,
                   "sculpted_detail_baked":False,
                   "tangent_space_normals_verified":False,
                   "android_emulator_tested":False,
                   "production_approved":False}}
    if images:
        doc["images"]=copy.deepcopy(images)
        doc["textures"]=copy.deepcopy(textures)
        if samplers:doc["samplers"]=copy.deepcopy(samplers)
    out.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")
    (out.parent/(out.stem+".bin")).write_bytes(gltf_buffer)
    check=check_gltf(out)
    if not check["structural_smoke_passed"]:
        raise ValueError("Exported multi-material glTF check failed: "+str(check["errors"]))
    (out.parent/(out.stem+"_export_review.json")).write_text(
        json.dumps({"schema_version":1,"source_sha256":_sha(src),
                    "gltf_sha256":_sha(out),"binary_sha256":_sha(out.parent/(out.stem+".bin")),
                    "images_verified":check["images_verified"],
                    "materials":material_names,"material_count":len(material_names),
                    "source_materials_preserved":source_gltf is not None,
                    "technical_export_gate":True,"production_approved":False},indent=2)+"\n")
    return doc

def main():
    p=argparse.ArgumentParser(description="VQ multi-material glTF export of adaptive source geometry")
    p.add_argument("--obj",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--source-gltf",type=Path)
    p.add_argument("--source-manifest",type=Path)
    args=p.parse_args()
    r=export(args.obj,args.out,source_gltf=args.source_gltf,source_manifest=args.source_manifest)
    print("VQ_MULTIMATERIAL_GLTF_PASS",len(r["materials"]),"materials",
          r["extras"]["triangles"],"triangles",
          len(r.get("images",[])),"textures")
if __name__=="__main__":main()
