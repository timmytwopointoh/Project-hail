"""Create a static, actual geometry GLES2 diagnostic from Kaiyu's rigged GLB.
This Android probe does NOT implement the glTF skin/animation runtime; the
skinned GLB remains the game import target. 3D mesh, true UV/PBR texture,
model topology and Android screenshot evidence are still authentic.
"""
import argparse, json, hashlib
from pathlib import Path
import numpy as np,trimesh

def pack(glb,output):
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    (out/'buffers').mkdir(exist_ok=True);(out/'textures').mkdir(exist_ok=True)
    scene=trimesh.load(glb,force='scene',process=False)
    # Production Z-up -> Android GLES2 viewer Y-up (right-handed rotation -90° about X).
    def rotate(a):return np.stack((a[:,0],a[:,2],-a[:,1]),axis=1).astype('<f4')
    j={'asset':{'version':'2.0','generator':'Kaiyu VEILFORGE GLES2 probe'},'scene':0,'scenes':[{'nodes':[]}],'nodes':[],'meshes':[],'materials':[],'accessors':[],'bufferViews':[],'buffers':[{'uri':'buffers/kaiyu.bin','byteLength':0}], 'textures':[],'images':[], 'samplers':[{'magFilter':9729,'minFilter':9729,'wrapS':10497,'wrapT':10497}], 'extras':{'static_skin_bind_pose_only':True,'skin_animation_tested_on_device':False,'model':'Kaiyu'}}
    binary=bytearray(); material_keys={}; tex_count=0
    def add(arr,typ,comp=5126):
        typmap={5126:'<f4',5125:'<u4'}
        arr=np.asarray(arr,dtype=typmap[comp]);n=len(arr)
        while len(binary)%4:binary.append(0)
        off=len(binary);buf=arr.tobytes();binary.extend(buf)
        vi=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(buf)})
        acc={'bufferView':vi,'componentType':comp,'type':typ,'count':n}
        if typ=='VEC3':acc.update(min=arr.min(0).astype(float).tolist(),max=arr.max(0).astype(float).tolist())
        k=len(j['accessors']);j['accessors'].append(acc);return k
    triangles=0;positions=0
    for i,node in enumerate(scene.graph.nodes_geometry):
        world,name=scene.graph.get(node);m=scene.geometry[name]
        if len(m.faces)==0:continue
        p=trimesh.transform_points(m.vertices,world)
        norms=np.asarray(m.vertex_normals,dtype=float)
        n=norms@np.linalg.inv(world[:3,:3]);n/=np.linalg.norm(n,axis=1,keepdims=True)+1e-12
        attrs={'POSITION':add(rotate(p),'VEC3'),'NORMAL':add(rotate(n),'VEC3')}
        uv=getattr(m.visual,'uv',None)
        if uv is not None and len(uv)==len(p):
            attrs['TEXCOORD_0']=add(np.asarray(uv), 'VEC2')
        mat=getattr(m.visual,'material',None)
        label=getattr(mat,'name','material') if mat is not None else 'material'
        color=getattr(mat,'baseColorFactor',None) if mat is not None else None
        rgb=[float(x)/255 for x in color] if color is not None else [1,1,1,1]
        if len(rgb)==3:rgb+=[1]
        tex=getattr(mat,'baseColorTexture',None) if mat is not None else None
        material_key=(label,tuple(rgb),tex is not None)
        if material_key not in material_keys:
            pbr={'baseColorFactor':rgb,'metallicFactor':float(getattr(mat,'metallicFactor',0) or 0),'roughnessFactor':float(getattr(mat,'roughnessFactor',.7) or .7)}
            if tex is not None and 'TEXCOORD_0' in attrs:
                texid=len(j['textures']);uri=f'textures/kaiyu_{texid:02d}.png'
                tex.convert('RGB').resize((512,256)).save(out/uri)
                j['images'].append({'uri':uri});j['textures'].append({'source':len(j['images'])-1,'sampler':0})
                pbr['baseColorTexture']={'index':texid};tex_count+=1
            mi=len(j['materials']);j['materials'].append({'name':label,'pbrMetallicRoughness':pbr,'doubleSided':True})
            material_keys[material_key]=mi
        indices=add(m.faces.reshape(-1,1),'SCALAR',5125)
        meshid=len(j['meshes']);j['meshes'].append({'name':f'KaiyuPart_{meshid if False else i:03d}',
           'primitives':[{'mode':4,'attributes':attrs,'indices':indices,'material':material_keys[material_key]}]})
        nodeid=len(j['nodes']);j['nodes'].append({'name':node,'mesh':meshid,'translation':[0,0,0], 'rotation':[0,0,0,1], 'scale':[1,1,1], 'extras':{'asset_id':'kaiyu'}})
        j['scenes'][0]['nodes'].append(nodeid);triangles+=len(m.faces);positions+=len(p)
    j['buffers'][0]['byteLength']=len(binary)
    (out/'buffers/kaiyu.bin').write_bytes(binary)
    (out/'kaiyu_scene.gltf').write_text(json.dumps(j,separators=(',',':'))+'\n')
    assert triangles>=100000 and tex_count>=1,(triangles,tex_count)
    report={'glb_sha256':hashlib.sha256(Path(glb).read_bytes()).hexdigest(),'source_rigged_glb':str(glb),'static_android_probe':True,'skin_playback_on_android':False,'source_mesh_nodes':len(j['meshes']),'triangles':triangles,'vertex_count':positions,'embedded_albedo_images':tex_count,'android_scale_orientation':'Y-up conversion, meters','quality_approved':False}
    (out/'kaiyu_android_pack_report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--glb',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args();pack(args.glb,args.out)