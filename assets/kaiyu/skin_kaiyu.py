"""Kaiyu M1: convert segmented tail and six pairs of gill parts to real glTF 2.0 skins.
Preserves all source materials and animation. The input geometry is a prototype, so
passing rig tests is not proof of reference-sheet visual fidelity.
"""
from pathlib import Path
import argparse, json, struct, math
import numpy as np

TYPE={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
DTYPE={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}

def unpack(path):
    raw=Path(path).read_bytes()
    magic,version,total=struct.unpack_from('<4sII',raw)
    assert magic==b'glTF' and version==2 and total==len(raw)
    p=12; chunks={}
    while p<len(raw):
        n,tag=struct.unpack_from('<I4s',raw,p);p+=8;chunks[tag]=raw[p:p+n];p+=n
    return json.loads(chunks[b'JSON']),bytearray(chunks[b'BIN\x00'])

def write(path,j,b):
    j['buffers'][0]['byteLength']=len(b)
    jj=json.dumps(j,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    jj+=b' '*((-len(jj))%4)
    bb=bytes(b)+b'\x00'*((-len(b))%4)
    Path(path).write_bytes(struct.pack('<4sII',b'glTF',2,12+8+len(jj)+8+len(bb))+
           struct.pack('<I4s',len(jj),b'JSON')+jj+
           struct.pack('<I4s',len(bb),b'BIN\x00')+bb)

def data(j,b,ai):
    a=j['accessors'][ai];view=j['bufferViews'][a['bufferView']]
    t=np.dtype(DTYPE[a['componentType']]);shape=(a['count'],TYPE[a['type']]);size=t.itemsize*shape[1]
    off=view.get('byteOffset',0)+a.get('byteOffset',0)
    stride=view.get('byteStride',size)
    assert stride>=size
    if stride==size:return np.frombuffer(b,dtype=t,count=a['count']*shape[1],offset=off).reshape(shape).copy()
    return np.stack([np.frombuffer(b,dtype=t,count=shape[1],offset=off+i*stride) for i in range(a['count'])])

def add(j,b,arr,type_,comp=5126):
    if comp==5126:arr=np.asarray(arr,dtype='<f4')
    elif comp==5123:arr=np.asarray(arr,dtype='<u2')
    else:arr=np.asarray(arr,dtype='<u4')
    while len(b)%4:b.append(0)
    off=len(b);chunk=arr.tobytes();b.extend(chunk)
    vi=len(j['bufferViews']);j['bufferViews'].append(dict(buffer=0,byteOffset=off,byteLength=len(chunk)))
    acc=dict(bufferView=vi,componentType=comp,count=len(arr),type=type_)
    if type_ in ('SCALAR','VEC3'):
        acc['min']=np.min(arr,axis=0).astype(float).tolist()
        acc['max']=np.max(arr,axis=0).astype(float).tolist()
    idx=len(j['accessors']);j['accessors'].append(acc)
    return idx

def local(node):
    if 'matrix' in node:return np.asarray(node['matrix'],dtype=float).reshape(4,4,order='F')
    t=np.eye(4);t[:3,3]=node.get('translation',[0,0,0]);
    x,y,z,w=node.get('rotation',[0,0,0,1])
    r=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    t[:3,:3]=r@np.diag(node.get('scale',[1,1,1]));return t

def rest_matrices(j):
    par={}
    for i,n in enumerate(j['nodes']):
        for kid in n.get('children',[]):par[kid]=i
    cache={}
    def world(i):
        if i not in cache:cache[i]=(world(par[i]) if i in par else np.eye(4))@local(j['nodes'][i])
        return cache[i]
    return [world(i) for i in range(len(j['nodes']))],par

def smoothstep(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)

def rig(input_file,output_file,report_file):
    j,b=unpack(input_file)
    wm,parents=rest_matrices(j)
    names={n.get('name',''):i for i,n in enumerate(j['nodes'])}
    skin_stats=[]
    # 7 skins: one seamless-weighting tail, plus six individual gill branches.
    groups=[('Tail', [f'Tail_{n:02}' for n in range(1,5)])]
    for lr in 'LR':
        for n in range(1,4):groups.append((f'Gill_{lr}_{n}',[f'Gill_{lr}_{n}_Root',f'Gill_{lr}_{n}_Tip']))
    for label,bones in groups:
        ids=[names[n] for n in bones];centers=np.array([wm[i][:3,3] for i in ids])
        children=[i for i,n in enumerate(j['nodes']) if 'mesh' in n and any(n.get('name','').startswith(bone+'_') for bone in bones)]
        assert children,(label,bones)
        inv=np.linalg.inv(np.stack([wm[i] for i in ids]))
        ibm=np.stack([a.T.reshape(16) for a in inv]).astype('<f4')
        skin_idx=len(j.setdefault('skins',[]))
        j['skins'].append({'name':f'Kaiyu_{label}_Deform','joints':ids,'inverseBindMatrices':add(j,b,ibm,'MAT4')})
        mesh={'name':f'Kaiyu_{label}_Skinned','primitives':[]}
        unique_joints=set();vertex_count=0;nonrigid=0
        for i in children:
            n=j['nodes'][i]; old=j['meshes'][n['mesh']]
            for prim in old['primitives']:
                pos=data(j,b,prim['attributes']['POSITION']).astype(float)
                if prim.get('indices') is not None:ix=data(j,b,prim['indices']).reshape(-1)
                else:ix=np.arange(len(pos))
                wpos=(np.c_[pos,np.ones(len(pos))]@wm[i].T)[:,:3]
                if label=='Tail':
                    # arc-length projected coordinate from actual center-line, not raw world X.
                    seg=centers[1:]-centers[:-1];segl=np.linalg.norm(seg,axis=1)
                    along=np.r_[0,np.cumsum(segl)]
                    diff=wpos[:,None,:]-centers[:-1][None,:,:]
                    t=np.clip(np.sum(diff*seg[None,:,:],axis=2)/(segl**2)[None,:],0,1)
                    proj=centers[:-1][None,:,:]+t[:,:,None]*seg[None,:,:]
                    sq=np.sum((proj-wpos[:,None,:])**2,axis=2)
                    near=np.argmin(sq,axis=1)
                    u=along[near]+t[np.arange(len(pos)),near]*segl[near]
                    # smooth Gaussian influence across real neighboring segment pivots
                    width=np.maximum(.14,np.mean(segl)*.9)
                    weights=np.exp(-.5*((u[:,None]-along[None,:])/width)**2)
                    weights/=weights.sum(axis=1,keepdims=True)
                else:
                    v=centers[1]-centers[0]
                    u=np.dot(wpos-centers[0],v)/max(1e-8,np.dot(v,v))
                    # early membrane stays anchored to root while end swings with tip
                    tip_w=smoothstep((u-.03)/1.18)
                    weights=np.stack([1-tip_w,tip_w],axis=1)
                # Rank top 4 contributors and renormalize; glTF takes 4 joint slots.
                order=np.argsort(-weights,axis=1)[:,:4];inds=np.zeros((len(pos),4),dtype='<u2');wts=np.zeros((len(pos),4),dtype='<f4')
                for k in range(order.shape[1]):
                    inds[:,k]=order[:,k];wts[:,k]=weights[np.arange(len(pos)),order[:,k]]
                wts/=wts.sum(axis=1,keepdims=True)
                unique_joints.update(map(int,order.reshape(-1)))
                nonrigid+=int(np.sum(np.sum(wts>.02,axis=1)>=2))
                # NORMAL attributes should be absent if original mesh had none; glTF viewers calculate as needed.
                attrs={'POSITION':add(j,b,wpos,'VEC3'),'JOINTS_0':add(j,b,inds,'VEC4',5123),'WEIGHTS_0':add(j,b,wts,'VEC4')}
                if 'TEXCOORD_0' in prim['attributes']:
                    uv=data(j,b,prim['attributes']['TEXCOORD_0']).astype('<f4')
                    attrs['TEXCOORD_0']=add(j,b,uv,'VEC2')
                newprim={'attributes':attrs,'indices':add(j,b,ix.reshape(-1,1),'SCALAR',5125),'mode':prim.get('mode',4)}
                if 'material' in prim:newprim['material']=prim['material']
                mesh['primitives'].append(newprim)
                vertex_count+=len(pos)
            # Remove only old rendered mesh. Preserve original animated bone nodes.
            del n['mesh']
        mesh_id=len(j['meshes']);j['meshes'].append(mesh)
        node_id=len(j['nodes']);j['nodes'].append({'name':f'Kaiyu_{label}_Skinned_Mesh','mesh':mesh_id,'skin':skin_idx})
        j['scenes'][j.get('scene',0)]['nodes'].append(node_id)
        skin_stats.append({'group':label,'joints':len(ids),'joint_names':bones,'vertices':vertex_count,'nonrigid_vertices':nonrigid,'primitives':len(mesh['primitives']),'linked':True})
    # Avoid rendering primitive-only geometry with broken roundtrip normals.
    j.setdefault('asset',{}).setdefault('extras',{}).update({'KaiyuRigMilestone':'M1-skinning', 'referenceLikenessVerified':False})
    write(output_file,j,b)
    report={'milestone':'M1 skin-weighted gills and tail','skins':len(groups),'rigged_groups':skin_stats,
            'deforming_vertices':sum(x['nonrigid_vertices'] for x in skin_stats),
            'animation_channels':len(j.get('animations',[{}])[0].get('channels',[])),
            'game_import': 'requires a glTF skin/animation-aware importer',
            'art_approved':False,'android_verified':False}
    Path(report_file).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input',default='/mnt/data/kaiyu_axolotl_prototype.glb');ap.add_argument('--output',default='/mnt/data/kaiyu_skinned_m1.glb');ap.add_argument('--report',default='/mnt/data/kaiyu_skin_m1_report.json')
    a=ap.parse_args();rig(a.input,a.output,a.report)