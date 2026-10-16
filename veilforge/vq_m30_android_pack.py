#!/usr/bin/env python3
"""Package a real high-to-low M30 baked normal into an isolated Android glTF scene.

The APK contains only the low-poly source geometry plus baked textures; high
poly is deliberately not smuggled into its render asset. No game code edited.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil
from pathlib import Path
from material_baker import bake as material
from vq_multimaterial_export import export
from vq_mesh_baker import bake as detail_bake

def _sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pack(low,high,scene):
    low=Path(low);high=Path(high);scene=Path(scene)
    if scene.resolve() in (low.resolve(),high.resolve()):
        raise ValueError("Game/test scene cannot overwrite source geometry")
    scene.mkdir(parents=True,exist_ok=True)
    generated=scene/"_build_review"
    details=detail_bake(low,high,generated/"baked",size=128)
    pbr=material("stone",generated/"procedural",size=128,seed=201)
    temp=generated/"source_m30.gltf"
    export(low,temp)
    doc=json.loads(temp.read_text(encoding="utf-8"))
    if len(doc["materials"])!=1 or doc["materials"][0]["name"]!="stone":
        raise ValueError("M30 dedicated material reference invalid")
    dest_bin=scene/"buffers"/"vq_m30_patch.bin"
    dest_bin.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(temp.with_suffix(".bin"),dest_bin)
    doc["buffers"][0]["uri"]="buffers/vq_m30_patch.bin"
    src_files=[
        ("albedo",generated/"procedural"/"albedo.png"),
        ("metallic_roughness",generated/"procedural"/"metallic_roughness.png"),
        ("normal",generated/"baked"/"normal.png"),
        ("ao",generated/"procedural"/"ao.png")]
    img=[]
    for kind,path in src_files:
        if not path.is_file():raise ValueError("Missing source material "+kind)
        uri="textures/vq_m30_patch/"+kind+".png"
        copied=scene/uri
        copied.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,copied)
        img.append({"uri":uri,"mimeType":"image/png"})
    doc["images"]=img
    doc["samplers"]=[{"magFilter":9729,"minFilter":9729,"wrapS":10497,"wrapT":10497}]
    doc["textures"]=[{"source":i,"sampler":0} for i in range(len(img))]
    m=doc["materials"][0]
    p=m["pbrMetallicRoughness"]
    p["baseColorFactor"]=[1,1,1,1]
    p["metallicFactor"]=p["roughnessFactor"]=1
    p["baseColorTexture"]={"index":0}
    p["metallicRoughnessTexture"]={"index":1}
    m["normalTexture"]={"index":2,"scale":1}
    m["occlusionTexture"]={"index":3,"strength":1}
    doc["meshes"][0]["name"]="vq_m30_patch"
    doc["nodes"][0].update({
        "name":"vq_m30_patch",
        "translation":[-1,0,-1],
        "rotation":[0,0,0,1],
        "scale":[1,1,1],
        "extras":{"asset_id":"vq_m30_patch"}})
    doc["extras"].update({
        "milestone":"M30","actual_highpoly_normal_bake":True,
        "high_source_sha256":_sha(high),"low_source_sha256":_sha(low),
        "photorealism_approved":False,"production_approved":False})
    target=scene/"ruin_courtyard_demo.gltf"
    target.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")
    manifest={
        "schema_version":1,"milestone":"M30","scene_gltf_sha256":_sha(target),
        "low_source_sha256":_sha(low),"high_source_sha256":_sha(high),
        "normal_texture_sha256":details["textures"]["normal"]["sha256"],
        "bake_normal_variation_texels":details["meaningful_normal_variation_texels"],
        "textures":{kind:_sha(path) for kind,path in src_files},
        "android_renderer_tested":False,"artistic_approval":False,
        "game_code_changed":False}
    (scene/"vq_m30_probe_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    # Remove intermediary duplicate source files from the APK's asset folder.
    # The baked maps remain copied under textures/vq_m30_patch/.
    shutil.rmtree(generated)
    return manifest

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--low",type=Path,required=True)
    p.add_argument("--high",type=Path,required=True)
    p.add_argument("--scene",type=Path,required=True)
    a=p.parse_args()
    m=pack(a.low,a.high,a.scene)
    print("VQ_M30_REAL_BAKED_SCENE_PASS",m["bake_normal_variation_texels"],"nonflat texels")
if __name__=="__main__":main()
