"""Verify real glTF skinning and measurable animation deformation of Kaiyu M1."""
import json, numpy as np, math, struct, os
from pathlib import Path
from kaiyu_skin_m1 import unpack,data,rest_matrices,local
p=Path(os.environ.get('KAIYU_OUT','/mnt/data'))/'kaiyu_skinned_m2.glb';j,b=unpack(p)
assert j['asset']['version']=='2.0'
assert len(j['skins'])==7
assert len(j['animations'])==1 and len(j['animations'][0]['channels'])==22
assert len(j['materials'])>=10
wm,parent=rest_matrices(j)
outputs={}; animated_node=set()
for ch in j['animations'][0]['channels']:
    idx=ch['target']['node']; sm=j['animations'][0]['samplers'][ch['sampler']];
    times=data(j,b,sm['input']).reshape(-1)
    rotations=data(j,b,sm['output']);assert np.max(np.abs(np.linalg.norm(rotations,axis=1)-1))<1e-4
    assert abs(times[0])<1e-7 and abs(times[-1]-2.4)<1e-4
    assert ch['target']['path']=='rotation'
    outputs[idx]=(times,rotations); animated_node.add(idx)

def animworld(frame):
    cache={}
    def world(i):
        n=j['nodes'][i]
        if i in outputs:
            time,rots=outputs[i];q=rots[frame];n=n.copy();n['rotation']=list(map(float,q))
        return (world(parent[i]) if i in parent else np.eye(4))@local(n)
    return {i:world(i) for i in range(len(j['nodes']))}
frame=8; posed=animworld(frame)
results=[];total_tri=0
for n in j['nodes']:
    if 'skin' not in n:continue
    skin=j['skins'][n['skin']]
    mesh=j['meshes'][n['mesh']]
    ibm=data(j,b,skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    joint_indices=skin['joints']
    disps=[];blends=[];amounts=[];maxerr=0
    for prim in mesh['primitives']:
        pos=data(j,b,prim['attributes']['POSITION'])
        joints=data(j,b,prim['attributes']['JOINTS_0']).astype(int)
        weights=data(j,b,prim['attributes']['WEIGHTS_0'])
        idxs=data(j,b,prim['indices']).reshape(-1)
        assert len(idxs)%3==0
        total_tri+=len(idxs)//3
        assert joints.shape==(len(pos),4) and weights.shape==joints.shape
        assert np.all((joints>=0)&(joints<len(joint_indices)))
        assert abs(weights.sum(axis=1)-1).max()<2e-5
        assert np.isfinite(pos).all() and np.isfinite(weights).all()
        assert prim.get('material',-1)>=0
        hom=np.c_[pos,np.ones(len(pos))]
        rest=np.zeros((len(pos),3));deformed=np.zeros((len(pos),3))
        for slot in range(4):
            for joint_local in np.unique(joints[:,slot]):
                mask=(joints[:,slot]==joint_local);bone=joint_indices[joint_local]
                rest_matrix=wm[bone]@ibm[joint_local]
                new_matrix=posed[bone]@ibm[joint_local]
                rest[mask]+=weights[mask,slot,None]*(hom[mask]@rest_matrix.T)[:,:3]
                deformed[mask]+=weights[mask,slot,None]*(hom[mask]@new_matrix.T)[:,:3]
        maxerr=max(maxerr,float(np.max(np.linalg.norm(rest-pos,axis=1))))
        disps.extend(np.linalg.norm(deformed-rest,axis=1).tolist())
        blends.extend(np.sum(weights>.02,axis=1).tolist())
    assert maxerr<2e-5, (n['name'],maxerr)
    assert max(disps)>.002,(n['name'],max(disps))
    assert max(blends)>=2
    results.append({'mesh':n['name'],'max_movement_mm':round(1000*max(disps),2),'median_movement_mm':round(1000*float(np.median(disps)),2),'weighted_vertex_count':sum(x>=2 for x in blends),'bind_error_mm':round(maxerr*1000,5)})
assert len(results)==7
assert total_tri>1000
assert all(x['weighted_vertex_count']>100 for x in results)
report={'schema':1,'label':'Kaiyu M1 deformation structural check','source_glb':p.name,'glb_bytes':p.stat().st_size,'source_triangles_from_skinned_primitives':total_tri,'skins':len(results),'animation_channels':len(animated_node),'sample_frame':frame,'sample_time_sec':float(times[frame]),'passes':{'gltf_structure':True,'joint_weights':True,'inverse_bind_rest_correct':True,'measured_real_deformation':True,'source_materials_preserved':True},'groups':results,'emulator_android_pass':False,'reference_likeness_pass':False,'production_ready':False}
(Path(os.environ.get('KAIYU_OUT','/mnt/data'))/'kaiyu_m2_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))