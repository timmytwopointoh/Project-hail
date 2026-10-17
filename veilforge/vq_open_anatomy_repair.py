#!/usr/bin/env python3
"""Bounded VQ A2 mesh-based reference correction, no learned visual taste asserted."""
import json,shutil,hashlib
from dataclasses import replace
from pathlib import Path
from vq_open_anatomy_reference import original_reference,evaluate_model
from vq_anatomy_next import build,parse_description
from vq_anatomy_review_next import inspect,render


def run(out,iterations=2,voxel=.021):
    if iterations<1 or iterations>3:raise ValueError('Use 1..3 bounded iterations')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    ref=original_reference('human',1.75,'slender',seed=1300)
    original=replace(parse_description('human slender long legs teal',seed=1300),name='calibrated_human_ranger',height=1.75,garment='tunic',palette='teal')
    best=original
    log=[];curbest=-1
    for step in range(iterations+1):
        if step==0:options=[('baseline',best)]
        else:
            # Paired parameter perturbations, held to documented physical bounds.
            deltas=[('shoulder_ratio',.010),('shoulder_ratio',-.010),
                    ('hip_ratio',.009),('hip_ratio',-.009),
                    ('head_ratio',.009),('head_ratio',-.009),
                    ('leg_ratio',.013),('leg_ratio',-.013)]
            options=[(f'{key}_{delta:+.3f}',replace(best,**{key:getattr(best,key)+delta})) for key,delta in deltas]
        old=curbest;top=None
        for i,(label,sp) in enumerate(options):
            sp=replace(sp,name=f'candidate_{step}_{i}').validate()
            d=out/'tmp';d.mkdir(exist_ok=True)
            result=build(sp,d,voxel=voxel,texture_size=32)
            technical=inspect(result['glb'],sp)
            score=evaluate_model(result['glb'],ref)['scores']['average_silhouette_iou']
            approved=bool(technical['technical_pass'] and (score>curbest+.001))
            log.append({'step':step,'label':label,'target_source':'independent_original_synthetic_silhouette',
                        'parameter_values':{k:getattr(sp,k) for k in ('head_ratio','shoulder_ratio','hip_ratio','leg_ratio','arm_ratio')},
                        'silhouette_iou':score,'technical_pass':technical['technical_pass'],
                        'improvement_over_current':round(score-curbest,6),'accepted':False})
            if approved and (top is None or score>top[0]):
                top=(score,label,sp,result['glb']);
                shutil.copyfile(result['glb'],out/'best_candidate.glb')
            shutil.rmtree(d)
        if top is None:break
        curbest,label,best,src=top
        log[-len(options)+next(i for i,(key,sp) in enumerate(options) if key==label)]['accepted']=True
        print('CORRECTION',step,label,old,'->',curbest,flush=True)
    final=out/'best_candidate.glb'
    assert final.is_file()
    render(final,out/'best_model_render.png',size=(640,800))
    report={'first_iou':log[0]['silhouette_iou'],'best_iou':curbest,
      'absolute_gain':round(curbest-log[0]['silhouette_iou'],6),'iterations_max':iterations,
      'comparison_reference':'independent_original_synthetic_targets_only',
      'not_a_measure_of_human_realism':True,'not_an_automatic_production_approval':True,
      'best_parameters':{k:getattr(best,k) for k in ('head_ratio','shoulder_ratio','hip_ratio','leg_ratio','arm_ratio')},
      'source_glb_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),
      'trials':log,'total_trials':len(log)}
    (out/'repair_log.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--iterations',type=int,default=2)
    a=p.parse_args();print(run(a.out,a.iterations))