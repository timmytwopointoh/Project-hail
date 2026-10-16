"""Kaiyu M3: add genuine glTF 2.0 face expression POSITION morph targets.
A 10-pose sampler is added independently of the 22-channel spring idle loop.
No invented emotive images: these are real mesh-vertex delta blend shapes.
"""
import argparse, json
import numpy as np
from pathlib import Path
from skin_kaiyu import unpack,data,add,write

EXPRESSIONS=['Neutral','Happy','Excited','Laughing','Surprised','Angry','Sad','Worried','Flirty','Sleepy']
# Eyes squint factor, widening factor, smile stretch, mouth vertical change.
STYLE={
 'Happy':(.52,0,1.17,.004), 'Excited':(.26,0,1.31,.014),
 'Laughing':(.83,0,1.42,.018), 'Surprised':(0,.22,.65,-.018),
 'Angry':(.20,0,.92,-.008), 'Sad':(.35,0,.85,-.009),
 'Worried':(.12,.07,.90,-.004), 'Flirty':(.12,0,1.12,.006),
 'Sleepy':(.75,0,.83,-.007),
}

def expression_delta(name, positions,shape):
    p=np.asarray(positions,dtype=float);x,y,z=p.T
    squint,widen,smile,move=STYLE[shape]
    delta=np.zeros_like(p)
    if name in ('Head_white_Geometry','Head_eye_black_Geometry','Head_eye_rose_Geometry','Head_eye_pink_Geometry','Head_eye_shine_Geometry'):
        # Both eyes have local center x=+-0.147, z=0.033. Close by
        # contracting soft tissue/iris geometry along z, not hiding meshes.
        strength=squint*np.ones(len(x))
        if shape=='Flirty':strength=np.where(x<0,.90,.10)
        delta[:,2]=(z-.037)*(-strength+widen)
        # happy eyes tilt slightly up at outer corner
        if shape in ('Happy','Excited','Laughing','Flirty'):
            delta[:,2]+=.010*np.sign(x)*(x-np.sign(x)*.147)
        if shape in ('Angry','Sad','Worried'):
            delta[:,2]+=(.015 if shape=='Sad' else -.012 if shape=='Angry' else .02)*(-np.sign(x)*(x-np.sign(x)*.147))
    elif name=='Head_hair_shadow_Geometry':
        mask=(z>.14)&(z<.255)&(y<-.26)&(np.abs(x)<.29)
        dirx=(x-np.sign(x)*.147)
        slope={'Happy':.013,'Excited':.025,'Laughing':.02,'Surprised':.04,'Angry':-.075,'Sad':.067,'Worried':.08,'Flirty':.026,'Sleepy':-.018}[shape]
        delta[:,2]=np.where(mask,slope*dirx,.0)
    elif name=='Head_burgundy_Geometry':
        mask=(np.abs(x)<.1)&(y<-.265)&(z<-.11)&(z>-.28)
        delta[:,0]=np.where(mask,x*(smile-1),0)
        delta[:,2]=np.where(mask,move,0)
        if shape in ('Sad','Angry','Worried'):
            delta[:,2]+=np.where(mask,(z+.17)*(-.45 if shape=='Sad' else -.85),0)
    elif name=='Head_blush_Geometry':
        delta[:,2]+=(.006 if shape in ('Happy','Excited','Flirty') else -.004 if shape=='Sad' else 0)
    return delta.astype('<f4')

def apply(src,out,report):
    j,b=unpack(src)
    node_map={n.get('name',''):i for i,n in enumerate(j['nodes'])}
    changed=[]
    for name in ('Head_white_Geometry','Head_eye_black_Geometry','Head_eye_rose_Geometry','Head_eye_pink_Geometry','Head_eye_shine_Geometry','Head_hair_shadow_Geometry','Head_burgundy_Geometry','Head_blush_Geometry'):
        ni=node_map[name];node=j['nodes'][ni]
        mesh=j['meshes'][node['mesh']]
        for prim in mesh['primitives']:
            p=data(j,b,prim['attributes']['POSITION'])
            targets=[];sizes=[]
            for shape in EXPRESSIONS[1:]:
                diff=expression_delta(name,p,shape)
                targets.append({'POSITION':add(j,b,diff,'VEC3')})
                sizes.append(float(np.linalg.norm(diff,axis=1).max()))
            prim['targets']=targets
        mesh['weights']=[0.]*9
        mesh.setdefault('extras',{})['targetNames']=EXPRESSIONS[1:]
        node['weights']=[0.]*9
        changed.append({'mesh':name,'vertex_count':len(p),'max_displacement_m':round(max(sizes),4)})
    times=np.arange(10,dtype='<f4')
    timeacc=add(j,b,times.reshape(-1,1),'SCALAR')
    anim={'name':'Kaiyu_Face_10_Expressions','samplers':[],'channels':[]}
    for item in changed:
        ni=node_map[item['mesh']]
        val=np.zeros((len(EXPRESSIONS),9),dtype='<f4')
        for f in range(1,len(EXPRESSIONS)):val[f,f-1]=1
        acc=add(j,b,val.reshape(-1,1),'SCALAR')
        si=len(anim['samplers']);anim['samplers'].append({'input':timeacc,'output':acc,'interpolation':'STEP'})
        anim['channels'].append({'sampler':si,'target':{'node':ni,'path':'weights'}})
    j.setdefault('animations',[]).append(anim)
    j.setdefault('asset',{}).setdefault('extras',{})['KaiyuExpressionMilestone']='M3-10-distinct-face-states'
    write(out,j,b)
    result={'schema':1,'milestone':'M3 expression blend shapes','expressions':EXPRESSIONS,'expression_count':len(EXPRESSIONS),'morph_target_count_per_mesh':9,'morphed_meshes':changed,'face_demo_animation_channels':len(anim['channels']),'previous_idle_motion_preserved':True,'android_expression_playback_verified':False,'character_likeness_approved':False}
    Path(report).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True);parser.add_argument('--output',required=True);parser.add_argument('--report',required=True)
    a=parser.parse_args();apply(a.input,a.output,a.report)