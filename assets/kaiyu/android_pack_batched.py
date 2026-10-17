"""Kaiyu isolated Android STATIC preview: material batch, no skin playback claims.
Based on inspected M7 technique. Preserves every source triangle and texture.
"""
import argparse,collections,hashlib,json
from pathlib import Path
import numpy as np
import trimesh

def pack(glb,out):
 glb=Path(glb);out=Path(out);out.mkdir(parents=True,exist_ok=True)
 (out/"buffers").mkdir(exist_ok=True);(out/"textures").mkdir(exist_ok=True)
 scene=trimesh.load(glb,force="scene",process=False)
 groups=collections.OrderedDict();input_triangles=0;input_nodes=0
 for node in sorted(scene.graph.nodes_geometry):
  transform,name=scene.graph.get(node);mesh=scene.geometry[name]
  if not len(mesh.faces):continue
  material=getattr(mesh.visual,"material",None)
  label=getattr(material,"name","material") if material else "material"
  color=getattr(material,"baseColorFactor",None) if material else None
  rgba=tuple(float(v)/255 for v in color) if color is not None else (1.,1.,1.,1.)
  if len(rgba)==3:rgba+= (1.,)
  uv=getattr(mesh.visual,"uv",None)
  image=getattr(material,"baseColorTexture",None) if material else None
  key=(label,rgba,uv is not None,image is not None)
  if key not in groups:
   groups[key]={"p":[],"n":[],"uv":[],"f":[],"offset":0,"material":material,"image":image}
  g=groups[key];transform=np.asarray(transform,dtype=float)
  positions=trimesh.transform_points(mesh.vertices,transform)
  normals=np.asarray(mesh.vertex_normals,dtype=float)@np.linalg.inv(transform[:3,:3])
  normals/=np.linalg.norm(normals,axis=1,keepdims=True)+1e-15
  g["p"].append(np.stack((positions[:,0],positions[:,2],-positions[:,1]),axis=1).astype("<f4"))
  g["n"].append(np.stack((normals[:,0],normals[:,2],-normals[:,1]),axis=1).astype("<f4"))
  if uv is not None:g["uv"].append(np.asarray(uv,dtype="<f4"))
  g["f"].append(np.asarray(mesh.faces,dtype="<u4")+g["offset"])
  g["offset"]+=len(positions);input_triangles+=len(mesh.faces);input_nodes+=1
 scene_doc={"asset":{"version":"2.0","generator":"Kaiyu M12 static material-batched Android GLES probe"},
   "scene":0,"scenes":[{"nodes":[]}],"nodes":[],"meshes":[],"materials":[],
   "accessors":[],"bufferViews":[],"buffers":[{"uri":"buffers/kaiyu.bin","byteLength":0}],
   "textures":[],"images":[],"samplers":[{"magFilter":9729,"minFilter":9729,"wrapS":10497,"wrapT":10497}],
   "extras":{"model":"Kaiyu","static_skin_bind_pose_only":True,"skin_playback_on_android":False,"game_ready":False}}
 blob=bytearray()
 def acc(data,kind,component=5126):
  arr=np.asarray(data,dtype="<f4" if component==5126 else "<u4")
  if arr.ndim==1:arr=arr.reshape(-1,1)
  blob.extend(b"\x00"*((-len(blob))%4))
  offset=len(blob);raw=arr.tobytes();blob.extend(raw)
  view=len(scene_doc["bufferViews"])
  scene_doc["bufferViews"].append({"buffer":0,"byteOffset":offset,"byteLength":len(raw)})
  item={"bufferView":view,"componentType":component,"type":kind,"count":len(arr)}
  if kind=="VEC3":item.update(min=arr.min(axis=0).astype(float).tolist(),max=arr.max(axis=0).astype(float).tolist())
  idx=len(scene_doc["accessors"]);scene_doc["accessors"].append(item);return idx
 output_triangles=0
 for i,(key,group) in enumerate(groups.items()):
  label,rgba,hasuv,hastex=key
  points=np.concatenate(group["p"]);norm=np.concatenate(group["n"]);faces=np.concatenate(group["f"])
  assert np.isfinite(points).all() and np.isfinite(norm).all() and np.max(faces)<len(points)
  attrs={"POSITION":acc(points,"VEC3"),"NORMAL":acc(norm,"VEC3")}
  if hasuv:
   uv=np.concatenate(group["uv"]);assert len(uv)==len(points) and np.isfinite(uv).all()
   attrs["TEXCOORD_0"]=acc(uv,"VEC2")
  material=group["material"]
  pbr={"baseColorFactor":list(rgba),
       "metallicFactor":float(getattr(material,"metallicFactor",0) or 0),
       "roughnessFactor":float(getattr(material,"roughnessFactor",.7) or .7)}
  if hastex:
   assert hasuv
   t=len(scene_doc["textures"]);uri=f"textures/kaiyu_{t:02d}.png"
   group["image"].convert("RGB").resize((512,256)).save(out/uri)
   scene_doc["images"].append({"uri":uri})
   scene_doc["textures"].append({"source":len(scene_doc["images"])-1,"sampler":0})
   pbr["baseColorTexture"]={"index":t}
  m=len(scene_doc["materials"]);material_json={"name":label,"pbrMetallicRoughness":pbr,"doubleSided":True}
  if rgba[3]<.999:material_json["alphaMode"]="BLEND"
  scene_doc["materials"].append(material_json)
  idx=acc(faces.reshape(-1),"SCALAR",5125)
  mid=len(scene_doc["meshes"])
  scene_doc["meshes"].append({"name":f"Kaiyu_batch_{i:02d}","primitives":[{"mode":4,"attributes":attrs,"indices":idx,"material":m}]})
  nid=len(scene_doc["nodes"])
  scene_doc["nodes"].append({"name":f"Kaiyu_batch_{i:02d}","mesh":mid,
                             "translation":[0,0,0],"rotation":[0,0,0,1],
                             "scale":[1,1,1],"extras":{"asset_id":"kaiyu"}})
  scene_doc["scenes"][0]["nodes"].append(nid);output_triangles+=len(faces)
 scene_doc["buffers"][0]["byteLength"]=len(blob)
 (out/"buffers/kaiyu.bin").write_bytes(blob)
 (out/"kaiyu_scene.gltf").write_text(json.dumps(scene_doc,separators=(",",":"))+"\n")
 assert input_triangles==output_triangles>=100000
 assert len(scene_doc["meshes"])<input_nodes
 assert scene_doc["images"]
 report={"source_model_sha256":hashlib.sha256(glb.read_bytes()).hexdigest(),
         "source_triangles":input_triangles,"android_probe_triangles":output_triangles,
         "source_mesh_nodes":input_nodes,"batched_material_nodes":len(scene_doc["meshes"]),
         "embedded_albedo_images":len(scene_doc["images"]),
         "static_bind_pose_only":True,"android_skin_playback_verified":False,
         "android_rendering_verified":False,"reference_likeness_approved":False}
 (out/"kaiyu_m12_probe_report.json").write_text(json.dumps(report,indent=2)+"\n")
 return report

if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--glb",required=True);p.add_argument("--out",required=True)
 a=p.parse_args();print(json.dumps(pack(a.glb,a.out),indent=2))
