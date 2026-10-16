#!/usr/bin/env python3
"""VEILFORGE M3 scene-pack compiler — actual multi-asset glTF 2.0 scenes.

Takes audited source assets, instances them with transforms, and produces a
standalone multi-buffer glTF package. No game importer, lighting, physics, or
navigation performance is asserted. Inputs are catalog IDs, never shell code.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
from factory import AssetError, load_catalog

MAX_INSTANCES=200

def load_scenes(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version")!=1 or not isinstance(data.get("scenes"),list):
        raise AssetError("Invalid scenes version or list")
    result={}
    for scene in data["scenes"]:
        if not isinstance(scene,dict) or set(scene)!={"id","instances"}:
            raise AssetError("Invalid scene fields")
        name=scene["id"]
        if not isinstance(name,str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,63}",name) or name in result:
            raise AssetError("Invalid/duplicate scene id")
        placements=scene["instances"]
        if not isinstance(placements,list) or not 1<=len(placements)<=MAX_INSTANCES:
            raise AssetError("Scene must have 1–200 instances")
        seen=set()
        for item in placements:
            if not isinstance(item,dict) or set(item)!={"id","asset","position","yaw","scale"}:
                raise AssetError("Invalid scene instance")
            if not isinstance(item["id"],str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,63}",item["id"]) or item["id"] in seen:
                raise AssetError("Invalid/duplicate scene instance ID")
            seen.add(item["id"])
            if not isinstance(item["asset"],str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,63}",item["asset"]):
                raise AssetError("Invalid instance asset")
            pos=item["position"]
            if not isinstance(pos,list) or len(pos)!=3 or any(
                    isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>10000
                    for v in pos):
                raise AssetError("Invalid instance position")
            for attr in ("yaw","scale"):
                v=item[attr]
                if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v):
                    raise AssetError("Nonfinite transform")
            if abs(item["yaw"])>360 or not .05<=item["scale"]<=20:
                raise AssetError("Transform exceeds audited range")
        result[name]=scene
    if not result:raise AssetError("Empty scenes pack")
    return result

def find_assets(root):
    found={}
    for file in Path(root).rglob("asset_manifest.json"):
        record=json.loads(file.read_text(encoding="utf-8"))
        ident=record.get("id")
        if ident in found:
            raise AssetError("Duplicate artifact for "+str(ident))
        found[ident]=(file.parent,record)
    return found

def compile_scene(catalog,scenes,scene_id,assets_root,out):
    recipes=load_catalog(catalog)
    layouts=load_scenes(scenes)
    if scene_id not in layouts:raise AssetError("Scene id not found")
    layout=layouts[scene_id]
    source=find_assets(assets_root)
    deps=sorted({item["asset"] for item in layout["instances"]})
    for ident in deps:
        if ident not in recipes or ident not in source:
            raise AssetError("Missing validated catalog asset "+ident)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/"buffers").mkdir(exist_ok=True)
    document={"asset":{"version":"2.0","generator":"VEILFORGE M3 scene pack"},
              "scene":0,"scenes":[{"name":scene_id,"nodes":[]}],
              "nodes":[],"meshes":[],"materials":[],"buffers":[],
              "images":[],"textures":[],"samplers":[],
              "bufferViews":[],"accessors":[],
              "extras":{"scene_id":scene_id,"instances":len(layout["instances"]),
                        "asset_dependencies":deps,"production_approved":False,
                        "lighting_baked":False,"collision_ready":False,
                        "navmesh_ready":False}}
    mesh_for={}
    provenance={}
    for ident in deps:
        folder,manifest=source[ident]
        assetfile=folder/(ident+".gltf")
        binfile=folder/(ident+".bin")
        if not assetfile.is_file() or not binfile.is_file():
            raise AssetError("Missing source glTF or buffer "+ident)
        content=assetfile.read_bytes()
        if hashlib.sha256(content).hexdigest()!=manifest["gltf_sha256"]:
            raise AssetError("Source glTF integrity failed "+ident)
        gltf=json.loads(content)
        if gltf.get("asset",{}).get("version")!="2.0" or len(gltf.get("meshes",[]))!=1:
            raise AssetError("Unsupported glTF source "+ident)
        if gltf.get("skins") or gltf.get("animations") or gltf.get("extensionsRequired"):
            raise AssetError("Unsupported skin/animation/extensions; never silently strip")
        buffers=gltf.get("buffers",[])
        if len(buffers)!=1 or buffers[0].get("uri")!=ident+".bin" or (
            binfile.stat().st_size!=buffers[0].get("byteLength")):
            raise AssetError("Source binary linkage invalid "+ident)
        if manifest.get("production_approved") is not False:
            raise AssetError("Unreviewed promotion state is invalid")
        copy_name="buffers/"+ident+".bin"
        shutil.copyfile(binfile,out/copy_name)
        buffer_index=len(document["buffers"])
        document["buffers"].append({"uri":copy_name,"byteLength":binfile.stat().st_size})
        view_base=len(document["bufferViews"])
        accessor_base=len(document["accessors"])
        material_base=len(document["materials"])
        image_base=len(document["images"])
        texture_base=len(document["textures"])
        sampler_base=len(document["samplers"])
        # Copy only safe, hashes-verified authored material maps. All texture
        # paths remain relative to the scene glTF and are unique per asset.
        source_maps=manifest.get("texture_maps",{})
        allowed_hashes={}
        for name,recipe in source_maps.items():
            for map_name,meta in recipe["maps"].items():
                allowed_hashes["textures/"+name+"/"+meta["file"]]=meta["sha256"]
        for image in gltf.get("images",[]):
            uri=image.get("uri","")
            if uri not in allowed_hashes or image.get("mimeType")!="image/png":
                raise AssetError("Texture not recorded in provenance: "+uri)
            data=(folder/uri).read_bytes()
            if hashlib.sha256(data).hexdigest()!=allowed_hashes[uri]:
                raise AssetError("Texture bytes differ from baked manifest "+uri)
            new_uri="textures/"+ident+"/"+uri.removeprefix("textures/")
            output_file=out/new_uri;output_file.parent.mkdir(parents=True,exist_ok=True)
            output_file.write_bytes(data)
            row=copy.deepcopy(image);row["uri"]=new_uri
            document["images"].append(row)
        for sampler in gltf.get("samplers",[]):
            document["samplers"].append(copy.deepcopy(sampler))
        for tex in gltf.get("textures",[]):
            row=copy.deepcopy(tex)
            row["source"]+=image_base
            if "sampler" in row:row["sampler"]+=sampler_base
            document["textures"].append(row)
        for view in gltf["bufferViews"]:
            clone=copy.deepcopy(view);clone["buffer"]=buffer_index
            document["bufferViews"].append(clone)
        for accessor in gltf["accessors"]:
            clone=copy.deepcopy(accessor)
            clone["bufferView"]+=view_base
            document["accessors"].append(clone)
        for material in gltf["materials"]:
            clone=copy.deepcopy(material)
            clone["name"]=ident+"/"+material["name"]
            fields=[clone.get("pbrMetallicRoughness",{}).get("baseColorTexture"),
                    clone.get("pbrMetallicRoughness",{}).get("metallicRoughnessTexture"),
                    clone.get("normalTexture"),clone.get("occlusionTexture")]
            for field in fields:
                if field is not None:field["index"]+=texture_base
            document["materials"].append(clone)
        clone=copy.deepcopy(gltf["meshes"][0])
        clone["name"]=ident
        for primitive in clone["primitives"]:
            primitive["attributes"]={k:v+accessor_base for k,v in primitive["attributes"].items()}
            primitive["indices"]+=accessor_base
            primitive["material"]+=material_base
        mesh_for[ident]=len(document["meshes"])
        document["meshes"].append(clone)
        provenance[ident]={"geometry_sha256":manifest["obj_sha256"],
                           "source_gltf_sha256":manifest["gltf_sha256"],
                           "category":manifest["category"],
                           "source_triangles":manifest["triangles"]}
    for item in layout["instances"]:
        a=math.radians(item["yaw"])*.5
        node={"name":item["id"],"mesh":mesh_for[item["asset"]],
              "translation":item["position"],
              "rotation":[0,math.sin(a),0,math.cos(a)],
              "scale":[item["scale"]]*3,
              "extras":{"asset_id":item["asset"]}}
        document["scenes"][0]["nodes"].append(len(document["nodes"]))
        document["nodes"].append(node)
    (out/(scene_id+".gltf")).write_text(json.dumps(document,indent=2)+"\n",encoding="utf-8")
    report={"schema_version":1,"scene":scene_id,"instances":len(layout["instances"]),
            "unique_asset_sources":len(deps),"binary_files":len(document["buffers"]),
            "texture_images":len(document["images"]),
            "source_provenance":provenance,
            "glTF":scene_id+".gltf",
            "production_approved":False,"renderer_verified":False,
            "physical_device_tested":False}
    (out/"scene_manifest.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser(description="Build actual multi-asset game-world glTF with instances")
    p.add_argument("--catalog",type=Path,default=Path("veilforge/catalog.json"))
    p.add_argument("--scenes",type=Path,default=Path("veilforge/scenes.json"))
    p.add_argument("--id",required=True)
    p.add_argument("--assets-root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    report=compile_scene(args.catalog,args.scenes,args.id,args.assets_root,args.out)
    print("VEILFORGE_SCENE_PACK_PASS",report["scene"],"instances",report["instances"],
          "sources",report["unique_asset_sources"])
if __name__=="__main__":
    main()
