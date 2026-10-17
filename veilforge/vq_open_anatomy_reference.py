#!/usr/bin/env python3
"""Original VQ A2 *synthetic design* anatomical references and calibrated evaluations.
No third-party mesh/photo is ingested. Synthetic = design targets, NOT scanned anatomy.
This module deliberately constructs target silhouette independently of the VQ SDF.
X horizontal, Y vertical, front = -Z, meters; orthographic fixed canvas.
"""
from pathlib import Path
from hashlib import sha256
import json,math
import numpy as np
import cv2

SOURCE_URLS={
 'cdc_measurement_dictionary':'https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/BMX_J.htm',
 'cdc_anthropometry_manuals':'https://wwwn.cdc.gov/Nchs/Nhanes/continuousnhanes/manuals.aspx?Cycle=2021-2023',
 'smithsonian_cc0_policy':'https://www.si.edu/openaccess/faq',
 'us_federal_work_copyright_law':'https://uscode.house.gov/us/usc/119-118/t17/s105/',
}
# Artist-authored 3D-design reference, NOT a claim of measured population statistics.
# Ratios: shoulder and hip are HALF distance from center, not full shoulder width.
PROFILE={
 'human':(.149,.133,.125,.502,.365),
 'elf':(.141,.124,.113,.523,.377),
 'orc':(.142,.166,.146,.486,.375),
 'axolotl':(.212,.145,.128,.435,.360),
 'feline':(.158,.130,.122,.508,.377),
 'dwarf':(.169,.156,.151,.415,.350),
 'automaton':(.144,.147,.129,.510,.365),
}

def original_reference(species='human',height=1.75,variant='neutral',seed=0):
    if species not in PROFILE:raise ValueError('Unknown reference anatomy family')
    if variant not in ('neutral','slender','stocky','long_legged','heroic'):raise ValueError('Unknown visual style')
    head,shoulder,hip,leg,arm=PROFILE[species]
    adj={'neutral':(1,1,1,1,1), 'slender':(1.01,.91,.94,1.03,1.02),
         'stocky':(1.02,1.115,1.09,.94,.98),'long_legged':(.98,.98,.98,1.085,1.02),
         'heroic':(1.02,1.12,1.01,1.01,1.02)}[variant]
    rng=np.random.default_rng(seed+567)
    jitter=rng.uniform(-.013,.013,5)
    head,shoulder,hip,leg,arm=[round(float(v*a*(1+j)),6) for v,a,j in zip((head,shoulder,hip,leg,arm),adj,jitter)]
    return {'reference_id':f'synthetic_{species}_{variant}_{seed:04d}',
       'kind':'original_synthetic_anatomy_design_reference','species':species,'variant':variant,
       'height_m':height,'ratios':dict(zip(('head_ratio','shoulder_ratio','hip_ratio','leg_ratio','arm_ratio'),(head,shoulder,hip,leg,arm))),
       'provenance':{'created_by':'Original deterministic VQ reference code',
        'source_material':'hand_authored_shape_targets_and_seeded_variations_only',
        'external_photos_or_3d_meshes_imported':False,'independent_of_VQ_anatomy_SDF':True,
        'data_class':'synthetic_design_data_not_empirical_anthropometry',
        'intended_use':'parameter_regression_and_geometry QA; NOT photo-realism label',
        'notes':'CDC documents measurement definitions; no NHANES record values were incorporated.',
        'reference_urls':SOURCE_URLS}}

def landmarks(ref):
    h=ref['height_m'];r=ref['ratios'];hd=r['head_ratio']*h
    # Independent artists' mannequin target, does not call VQ generator anchors.
    top=h; head_y=h-hd*.51;neck_base=h-hd*1.15
    sy=neck_base-.028*h;hip_y=r['leg_ratio']*.96*h
    s=r['shoulder_ratio']*h; hips=r['hip_ratio']*h
    out={'crown':[0,top,0], 'chin':[0,h-hd,-.035*h], 'nose':[0,head_y-.11*hd,-.065*h],
         'mouth':[0,head_y-.29*hd,-.071*h], 'sternum':[0,sy-.10*h,-.09*h],
         'navel':[0,hip_y+.12*h,-.087*h], 'pelvis':[0,hip_y,0]}
    for side,ss in [('left',-1),('right',1)]:
        out.update({
          f'{side}_eye':[ss*hd*.20,head_y+.06*hd,-.063*h],
          f'{side}_shoulder':[ss*s,sy,0],
          f'{side}_elbow':[ss*(s+.41*r['arm_ratio']*h),sy-.055*h,0],
          f'{side}_wrist':[ss*(s+.83*r['arm_ratio']*h),sy-.115*h,0],
          f'{side}_fingertip':[ss*(s+(r['arm_ratio']+.09)*h),sy-.115*h,0],
          f'{side}_hip':[ss*hips*.72,hip_y,0],
          f'{side}_knee':[ss*hips*.75,hip_y*.54,0],
          f'{side}_ankle':[ss*hips*.80,.087*h,0],
          f'{side}_toe':[ss*hips*.80,.043*h,-.075*h],
        })
    return out

def target_mask(ref,axis='front',size=512):
    """Independent convex-union anatomy envelope, a silhouette-only artist proxy."""
    if axis not in ('front','side'):raise ValueError('Unknown camera axis')
    h=ref['height_m'];r=ref['ratios']; lm=landmarks(ref)
    M=np.zeros((size,size),np.uint8)
    def pixel(x,y):return (round(size*.5+(x/h)*size*.45),round(size*.93-(y/h)*size*.84))
    def ell(x,y,rx,ry):
        center=pixel(x,y);rad=(max(1,int(rx/h*size*.45)),max(1,int(ry/h*size*.84)))
        cv2.ellipse(M,center,rad,0,0,360,255,-1,lineType=cv2.LINE_AA)
    def rod(a,b,r0):
        pa=pixel(a[0],a[1]);pb=pixel(b[0],b[1]);
        cv2.line(M,pa,pb,255,max(1,int(r0/h*size*.70)),lineType=cv2.LINE_AA)
        for p in (pa,pb):cv2.circle(M,p,max(1,int(r0/h*size*.35)),255,-1,lineType=cv2.LINE_AA)
    head=h*r['head_ratio'];sh=r['shoulder_ratio']*h;hips=r['hip_ratio']*h
    yc=h-head*.51;sy=lm['left_shoulder'][1];hip=lm['left_hip'][1]
    if axis=='front':
        ell(0,yc,head*.39,head*.51)
        ell(0,(sy+hip)*.5,sh*.93,(sy-hip)*.55)
        ell(0,hip,hips*.95,.105*h)
        rod((0,yc-head*.33,0),(0,sy-.035*h,0),.071*h)
        for side in ('left','right'):
            rod(lm[f'{side}_shoulder'],lm[f'{side}_elbow'],.099*h)
            rod(lm[f'{side}_elbow'],lm[f'{side}_wrist'],.073*h)
            rod(lm[f'{side}_wrist'],lm[f'{side}_fingertip'],.038*h)
            rod(lm[f'{side}_hip'],lm[f'{side}_knee'],.12*h)
            rod(lm[f'{side}_knee'],lm[f'{side}_ankle'],.083*h)
            ell(lm[f'{side}_ankle'][0],.051*h,.050*h,.043*h)
    else:
        ell(0,yc,head*.37,head*.51)
        ell(0,(sy+hip)*.5,.108*h,(sy-hip)*.56)
        ell(0,hip,.12*h,.10*h)
        rod((0,yc-head*.31,0),(0,sy,0),.071*h)
        for side in ('left','right'):
            rod((0,hip,0),(0,hip*.54,0),.11*h)
            rod((0,hip*.54,0),(0,.089*h,0),.082*h)
        ell(0,.051*h,.097*h,.044*h)
    return M

def mesh_mask(glb,axis='front',size=512,include_clothing=False):
    import trimesh
    scene=trimesh.load(glb,force='scene',process=False)
    vertices=[];faces=[]
    for m in scene.geometry.values():
        name=getattr(getattr(m.visual,'material',None),'name','')
        if not include_clothing and name!='skin':continue
        if len(m.faces)<1:continue
        start=sum(len(v) for v in vertices)
        vertices.append(np.asarray(m.vertices))
        faces.append(np.asarray(m.faces)+start)
    if not vertices:raise ValueError('No subject skin')
    v=np.vstack(vertices);f=np.vstack(faces)
    h=float(v[:,1].max()-v[:,1].min());height=float(v[:,1].max());
    if axis=='front':x=v[:,0]
    elif axis=='side':x=v[:,2]
    else:raise ValueError('Unknown axis')
    projected=np.stack((size*.5+x/height*size*.45,size*.93-(v[:,1]/height)*size*.84),axis=1)
    projected=np.rint(projected).astype(np.int32)
    dst=np.zeros((size,size),np.uint8)
    cv2.fillPoly(dst,projected[f],255,lineType=cv2.LINE_8)
    return dst

def silhouette_score(candidate,reference):
    cand=candidate>127;ref=reference>127
    return round(float(np.count_nonzero(cand&ref)/max(1,np.count_nonzero(cand|ref))),6)

def evaluate_model(glb,ref,out=None,size=512):
    scores={};paths={}
    for axis in ('front','side'):
        reference=target_mask(ref,axis,size)
        candidate=mesh_mask(glb,axis,size)
        scores[f'{axis}_silhouette_iou']=silhouette_score(candidate,reference)
        if out:
            out=Path(out);out.mkdir(parents=True,exist_ok=True)
            # Difference image diagnostic: overlapping=light, target-only=amber, mesh-only=magenta.
            match=np.zeros((size,size,3),np.uint8)
            match[(candidate>0)&(reference>0)]=(211,215,223)
            match[(candidate==0)&(reference>0)]=(52,171,234)
            match[(candidate>0)&(reference==0)]=(175,59,185)
            p=out/f'{axis}_silhouette_difference.png';cv2.imwrite(str(p),match);paths[axis]=str(p)
    scores['average_silhouette_iou']=round(sum(scores.values())/2,6)
    scores.update({'reference_kind':'independent_original_synthetic_design_only',
        'not_real_human_ground_truth':True,'not_a_photorealism_or_likeness_pass':True})
    return {'scores':scores,'diagnostics':paths}

def generate_dataset(destination,count=140,seed=2701):
    if count<20:raise ValueError('At least 20 references required')
    out=Path(destination);out.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(seed);rows=[]
    families=tuple(PROFILE);styles=('neutral','slender','stocky','long_legged','heroic')
    for i in range(count):
        species=families[i%len(families)];variant=styles[(i//len(families))%len(styles)]
        h=round(float(rng.uniform(1.47,1.98) if species not in ('dwarf','axolotl') else rng.uniform(1.20,1.55)),4)
        row=original_reference(species,h,variant,seed+i*31)
        row['landmarks_m']=landmarks(row)
        row['set']='test' if (i//len(families))%7==0 else ('validation' if (i//len(families))%7==1 else 'training')
        rows.append(row)
    (out/'synthetic_landmarks.json').write_text(json.dumps({'schema':'vq.original-synthetic-references.v1',
       'not_empirical':True,'training_copyrighted_or_external_assets':False,
       'measurement_definitions_not_training_records':SOURCE_URLS,
       'entries':rows},indent=2)+'\n')
    checksum=sha256((out/'synthetic_landmarks.json').read_bytes()).hexdigest()
    manifest={'schema':'vq.reference-provenance.v1','count':len(rows),
       'training':sum(x['set']=='training' for x in rows),
       'validation':sum(x['set']=='validation' for x in rows),'test':sum(x['set']=='test' for x in rows),
       'rights':'original synthetic numeric design targets and references; third-party records/meshes not imported',
       'upstream_engine_license':'Existing Project-hail proprietary rights unchanged',
       'data_sha256':checksum,'sources_checked':SOURCE_URLS,'external_data_ingested':False}
    (out/'reference_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    for i in (0,1,2,3,4,5,6):
        row=rows[i]
        for axis in ('front','side'):
            cv2.imwrite(str(out/f'{row["reference_id"]}_{axis}.png'),target_mask(row,axis,320))
    return manifest