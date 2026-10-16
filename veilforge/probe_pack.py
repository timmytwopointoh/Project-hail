#!/usr/bin/env python3
"""Inject real M2 high-detail exported meshes into M3 Android scene test pack.

Combines standards-compliant glTF binary chunks, accessors, materials and mesh
primitives. Does NOT rasterize models into fake screenshots or transform source
models; the Android probe still has to import/draw them on its virtual GPU.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil

class PackError(ValueError):
    pass

DEFAULT_PLACEMENTS={
    "human_repaired": (-1.05, 0.35, -.20),
    "bellwarden_full_anatomy_repaired": (1.18, .25, -.25),
}
def pack(scene_dir,assets):
    scene_dir=Path(scene_dir)
    primary=scene_dir/"ruin_courtyard_demo.gltf"
    data=json.loads(primary.read_text(encoding="utf-8"))
    if data.get("asset",{}).get("version")!="2.0" or (
        data.get("extras",{}).get("production_approved") is not False):
        raise PackError("Unapproved or invalid base scene")
    if len(assets)>2 or set(assets)-set(DEFAULT_PLACEMENTS):
        raise PackError("Only explicitly audited M2 hero samples accepted")
    sources={}
    for name,src in sorted(assets.items()):
        if not re.fullmatch(r"[a-z0-9_]{2,64}",name):
            raise PackError("Invalid asset id")
        gltf_path=Path(src)
        source=json.loads(gltf_path.read_text(encoding="utf-8"))
        source_bin=gltf_path.with_suffix(".bin")
        if not source_bin.is_file():
            raise PackError("Missing source glTF binary")
        if source.get("asset",{}).get("version")!="2.0":
            raise PackError("Requires glTF 2.0 source")
        if any(field in source for field in ("images","textures","skins","animations","extensionsRequired")):
            raise PackError("Not allowed to silently strip rich glTF structures")
        if len(source.get("meshes",[]))!=1 or len(source.get("buffers",[]))!=1:
            raise PackError("Only single-buffer source geometry supported")
        if source["buffers"][0]["byteLength"]!=source_bin.stat().st_size:
            raise PackError("Source glTF binary size mismatch")
        if source.get("extras",{}).get("manually_approved") is not False:
            raise PackError("Cannot assume artist approval")
        uri="buffers/"+name+".bin"
        dest=scene_dir/uri;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source_bin,dest)
        source_bytes=gltf_path.read_bytes()
        sources[name]={"source_sha256":hashlib.sha256(source_bytes).hexdigest(),
                       "binary_sha256":hashlib.sha256(dest.read_bytes()).hexdigest()}
        buffer_base=len(data["buffers"])
        view_base=len(data["bufferViews"])
        accessor_base=len(data["accessors"])
        material_base=len(data["materials"])
        data["buffers"].append({"uri":uri,"byteLength":dest.stat().st_size})
        for view in source["bufferViews"]:
            row=copy.deepcopy(view);row["buffer"]=buffer_base
            data["bufferViews"].append(row)
        for acc in source["accessors"]:
            row=copy.deepcopy(acc);row["bufferView"]+=view_base
            data["accessors"].append(row)
        for mat in source["materials"]:
            row=copy.deepcopy(mat)
            row["name"]=name+"/"+mat.get("name","material")
            data["materials"].append(row)
        mesh=copy.deepcopy(source["meshes"][0])
        mesh["name"]=name
        for primitive in mesh["primitives"]:
            primitive["attributes"]={k:v+accessor_base for k,v in primitive["attributes"].items()}
            primitive["indices"]+=accessor_base
            primitive["material"]+=material_base
        meshindex=len(data["meshes"])
        data["meshes"].append(mesh)
        xyz=DEFAULT_PLACEMENTS[name]
        node={"name":name,"mesh":meshindex,"translation":list(xyz),
              "rotation":[0,0,0,1],"scale":[1,1,1],
              "extras":{"asset_id":name,"source":"M2 high-detail export"}}
        data["scenes"][0]["nodes"].append(len(data["nodes"]))
        data["nodes"].append(node)
    data["extras"]["m2_character_samples"]=sorted(sources)
    data["extras"]["production_approved"]=False
    primary.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    (scene_dir/"android_probe_sources.json").write_text(json.dumps({
        "schema_version":1,"source_character_models":sources,
        "scene_node_count":len(data["nodes"]),
        "scene_mesh_count":len(data["meshes"]),
        "user_approved_for_game":False},indent=2)+"\n")
    return data

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--scene",type=Path,required=True)
    p.add_argument("--human",type=Path,required=True)
    p.add_argument("--armor",type=Path,required=True)
    a=p.parse_args()
    data=pack(a.scene,{"human_repaired":a.human,
                      "bellwarden_full_anatomy_repaired":a.armor})
    print("VEILFORGE_ANDROID_CHARACTER_PACK_PASS",len(data["meshes"]),
          "meshes",len(data["nodes"]),"nodes")

if __name__=="__main__":
    main()
