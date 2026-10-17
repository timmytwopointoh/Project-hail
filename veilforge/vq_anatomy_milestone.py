#!/usr/bin/env python3
"""VQ A1 on-demand deterministic 10-character shape/texture/QA lab.
Use python3 veilforge/vq_anatomy_milestone.py --out build/vq-a1.
No GitHub Actions, no emulator claims, no permanent model library promotion.
"""
from __future__ import annotations
import argparse,json,hashlib,sys,time
from dataclasses import replace
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from vq_anatomy_next import parse_description,build
from vq_anatomy_review_next import inspect,render
from vq_shape_gate_next import gate,proxy_proportion_error,bounded_shape_repair
from vq_shape_learning_next import train_synthetic_export,accept_reference_dataset,infer_synthetic
from engine import inspect_obj
from vq_model_tools import check_gltf,read_obj,projected_frames

TASKS=[
 ('human slender long legs teal','human_ranger',1.75,'tunic','teal'),
 ('axolotl chibi large eyes robe','axolotl_bard',1.46,'robes','rose'),
 ('orc muscular earth','orc_guardian',2.03,'tunic','earth'),
 ('elf long legs slender','elf_noble',1.88,'robes','teal'),
 ('feline slender','feline_dancer',1.73,'bodysuit','earth'),
 ('dwarf muscular','dwarf_smith',1.43,'tunic','earth'),
 ('automaton muscular','automaton_warden',1.95,'bodysuit','metal'),
 ('human chibi large eyes','human_chibi',1.34,'robes','rose'),
 ('human muscular earth','human_warrior',1.84,'tunic','earth'),
 ('axolotl teal robe','axolotl_scholar',1.54,'robes','teal')]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--voxel',type=float,default=.021);p.add_argument('--limit',type=int,default=10)
    p.add_argument('--render',action='store_true')
    a=p.parse_args();assert .012<=a.voxel<=.03 and 1<=a.limit<=10
    out=a.out;out.mkdir(parents=True,exist_ok=True)
    started=time.monotonic();report=[];shots=[]
    # Deliberately malformed anatomy specimen (saved as recipe only).
    malformed=replace(parse_description('human',seed=99),name='correction_probe',head_ratio=.21,shoulder_ratio=.31,leg_ratio=.39)
    repaired,trace=bounded_shape_repair(malformed)
    assert proxy_proportion_error(repaired)<proxy_proportion_error(malformed)
    correction={'input_ratios':{k:getattr(malformed,k) for k in ('head_ratio','shoulder_ratio','leg_ratio')},
       'output_ratios':{k:getattr(repaired,k) for k in ('head_ratio','shoulder_ratio','leg_ratio')},
       'before_error':proxy_proportion_error(malformed),'after_error':proxy_proportion_error(repaired),
       'iterations':trace,'note':'Proxy error against authored shape targets, not aesthetic/reality score'}
    (out/'correction_probe.json').write_text(json.dumps(correction,indent=2)+'\n')
    for i,(description,name,h,outfit,palette) in enumerate(TASKS[:a.limit]):
        spec=replace(parse_description(description,seed=1300+i*83),name=name,height=h,garment=outfit,palette=palette)
        folder=out/'candidates'/name
        built=build(spec,folder,voxel=a.voxel,texture_size=64)
        technical=inspect(built['glb'],spec)
        obj=inspect_obj(Path(built['obj']))
        gltf=check_gltf(Path(built['gltf']))
        technical['checks']['vq_obj_near_degenerate_rate_under_0p1pct']=obj['degenerate_triangles']/max(1,obj['triangles'])<.001
        technical['warning_near_degenerate_faces']=obj['degenerate_triangles']
        technical['checks']['vq_gltf_links']=gltf['structural_smoke_passed']
        technical['technical_pass']=all(technical['checks'].values())
        acceptance=gate(technical)
        item={'name':name,'description':description,'spec':built['spec'],
          'triangles':built['triangle_count'],'skin_triangles':built['body_faces'],
          'glb_reimport_faces':built['glb_faces_reimported'],
          'glb_sha256':sha(built['glb']),
          'gltf_sha256':sha(built['gltf']),
          'reference_evaluation':'unavailable_without_licensed_reference_labeled_views',
          'vq_source_geometry':{k:obj[k] for k in ('triangles','degenerate_triangles','boundary_edges','nonmanifold_edges')},
          'glTF_structural_smoke':gltf,'technical':technical,'promotion':acceptance}
        (folder/'validation.json').write_text(json.dumps(item,indent=2)+'\n')
        report.append(item)
        if a.render and i in (0,1,2,3,4,5,6,7,8,9):
            # Render key faces and silhouettes from exported GLB, never generation imagery.
            path=out/'screenshots'/f'{name}_threequarter.png';path.parent.mkdir(exist_ok=True)
            render(built['glb'],path,size=(390,520));shots.append((name,path))
        print('MODEL',i+1,name,'triangles',built['triangle_count'],'geometry',technical['technical_pass'],flush=True)
    training=train_synthetic_export(out/'learning')
    (out/'dataset_rights_template.json').write_text(json.dumps({'examples':[],
        'required':['source','license','consent_or_rights','sha256','landmarks_3d','split'],
        'example_provenance':'Attach licensed 3D landmarks and matched views before real training'},indent=2)+'\n')
    dataset_fail_closed=False
    try:accept_reference_dataset(out/'dataset_rights_template.json')
    except ValueError:dataset_fail_closed=True
    assert dataset_fail_closed
    # Compare validated source mesh on 14 repeatable diagnostic camera angles.
    sample=report[0]['name'];sample_obj=out/'candidates'/sample/(sample+'.obj')
    verts,uvs,normals,faces=read_obj(sample_obj)
    model_angles=projected_frames(verts,faces,out/'14_angle_evidence',size=200)
    record={'milestone':'VQ_A1_anatomy_reference_gate','schema_version':1,
      'models_tested':len(report),'technical_passed':sum(bool(x['technical']['technical_pass']) for x in report),
      'production_approved':0,'training':training,'numeric_correction':correction,
      '14_angle_inspection':True,'14_angle_views_expected':14,
      'actual_reference_likeness_measured':False,'actual_rig_skinning_tested':False,
      'actual_android_emulator_tested':False,'all_models_original_procedural':True,
      'run_time_seconds':round(time.monotonic()-started,2),
      'files':[{'name':x['name'],'sha256':x['glb_sha256'],'triangles':x['triangles'],
                'technical_pass':x['technical']['technical_pass']} for x in report],
      'techniques_reusable':['voxelized_smooth_union_skin','parametric_joint_proportions',
       'continuous_face_sculpt_features','five_finger_sdf_hand','material_preserving_vq_gltf',
       'procedural_PBR_maps','glb_reimport_gate','objective_bilateral_sdf_audit',
       'numeric_shape_parameter_repair','synthetic_rule_apprentice_model','rights_provenance_fail_closed',
       'production_review_gate']}
    (out/'milestone_report.json').write_text(json.dumps(record,indent=2)+'\n')
    if shots:
        w=390;h=520;names=[x[0] for x in shots]
        cols=min(5,len(shots));rows=(len(shots)+cols-1)//cols
        sheet=Image.new('RGB',(cols*w,rows*(h+34)),(16,19,27));d=ImageDraw.Draw(sheet)
        for i,(name,p) in enumerate(shots):
            x=i%cols*w;y=i//cols*(h+34)
            with Image.open(p) as im:sheet.paste(im,(x,y+34))
            d.text((x+10,y+8),name.replace('_',' ').title(),fill=(240,238,244))
        sheet.save(out/'VQ_A1_Character_Review.png')
    print('VQ_A1_COMPLETE',json.dumps({k:record[k] for k in ('models_tested','technical_passed','production_approved','run_time_seconds')}))
    return record

if __name__=='__main__':main()