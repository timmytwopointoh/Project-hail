"""Independent Kaiyu M3 structural assertion (rig, skin, material, morph clips)."""
import os,json,hashlib
from pathlib import Path
import numpy as np
from skin_kaiyu import unpack,data
BASE=Path(os.environ.get('KAIYU_OUT','/mnt/data/kaiyu_m3'))
P=BASE/'kaiyu_game_m3.glb';J,B=unpack(P)
mesh_map={m.get('name',''):m for m in J['meshes']}
assert len(J['skins'])==7
assert len(J['animations'])==2
assert len(J['animations'][0]['channels'])==22
assert len(J['animations'][1]['channels'])==8
assert len(J.get('images',[]))>=1
assert len(J.get('textures',[]))>=1
names=['Happy','Excited','Laughing','Surprised','Angry','Sad','Worried','Flirty','Sleepy']
morphed=[]
for m in J['meshes']:
    x=m.get('extras',{}).get('targetNames')
    if not x:continue
    assert x==names and len(m['weights'])==9
    for prim in m['primitives']:
        n=len(data(J,B,prim['attributes']['POSITION']))
        assert len(prim['targets'])==9
        vals=[]
        for target in prim['targets']:
            v=data(J,B,target['POSITION'])
            assert v.shape==(n,3) and np.isfinite(v).all()
            vals.append(float(np.max(np.linalg.norm(v,axis=1))))
        assert max(vals)>.0001
    morphed.append(m['name'])
assert len(morphed)==8
for ch in J['animations'][1]['channels']:
    assert ch['target']['path']=='weights'
    sm=J['animations'][1]['samplers'][ch['sampler']]
    ts=data(J,B,sm['input']).reshape(-1)
    w=data(J,B,sm['output']).reshape(-1)
    assert len(ts)==10 and len(w)==90 and abs(sum(w)-9)<.001
skin_nodes=[n for n in J['nodes'] if 'skin' in n]
assert len(skin_nodes)==7
rig_norms=[]
for node in skin_nodes:
    mesh=J['meshes'][node['mesh']]
    for prim in mesh['primitives']:
        wt=data(J,B,prim['attributes']['WEIGHTS_0'])
        assert np.max(np.abs(wt.sum(axis=1)-1))<1e-4
        if mesh['name']=='Kaiyu_Tail_Skinned':
            assert 'TEXCOORD_0' in prim['attributes']
        rig_norms.append(float(np.max(np.abs(wt.sum(axis=1)-1))))
r={'milestone':'M3 genuine face morph and articulated skin','game_file':P.name,'source_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'animation_clips':len(J['animations']),'skinned_groups':len(J['skins']),'animated_spring_bone_channels':22,'facial_expression_states':10,'morphed_head_meshes':morphed,'weighted_vertex_max_error':max(rig_norms),'albedo_images':len(J['images']),'android_static_render_verified':False,'android_skin_animation_verified':False,'reference_likeness_approved':False,'game_ready':False}
(BASE/'kaiyu_m3_validation.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))