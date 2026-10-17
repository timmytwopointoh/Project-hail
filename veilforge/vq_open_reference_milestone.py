#!/usr/bin/env python3
"""A2 cross-species synthetic reference QA run: real GLBs, transparent metrics."""
import argparse,sys,time,hashlib,json
from dataclasses import replace
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from vq_anatomy_next import parse_description,build
from vq_anatomy_review_next import inspect,render
from vq_open_anatomy_reference import original_reference,evaluate_model,generate_dataset
from vq_open_anatomy_learning import train
from vq_shape_gate_next import gate

TASKS=[
  ('human slender long legs teal','human_ranger',1.75,'tunic','teal','slender'),
  ('axolotl chibi large eyes robe','axolotl_bard',1.46,'robes','rose','neutral'),
  ('orc muscular earth','orc_guardian',2.03,'tunic','earth','heroic'),
  ('elf long legs slender','elf_noble',1.88,'robes','teal','long_legged'),
  ('feline slender','feline_dancer',1.73,'bodysuit','earth','slender'),
  ('dwarf muscular','dwarf_smith',1.43,'tunic','earth','heroic'),
]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--previous',default='');ap.add_argument('--voxel',type=float,default=.022);a=ap.parse_args()
    root=Path(a.out);root.mkdir(parents=True,exist_ok=True)
    start=time.monotonic();reference=generate_dataset(root/'original_references',140)
    learning=train(root/'original_references'/'synthetic_landmarks.json',root/'learning')
    results=[];shots=[]
    for i,(prompt,name,height,garment,palette,variant) in enumerate(TASKS):
        spec=replace(parse_description(prompt,seed=1300+i*83),name=name,height=height,garment=garment,palette=palette)
        folder=root/'candidates'/name
        built=build(spec,folder,voxel=a.voxel,texture_size=64)
        quality=inspect(built['glb'],spec)
        ref=original_reference(spec.species,height,variant,seed=1300+i*83)
        rec=evaluate_model(built['glb'],ref,folder/'mask_comparison')
        baseline=None
        previous=Path(a.previous)/'candidates'/name/(name+'.glb')
        if previous.is_file():
            baseline=evaluate_model(previous,ref)['scores']
        verdict=gate(quality)
        img=folder/'review.png';render(built['glb'],img,size=(450,580))
        shots.append((name,img))
        record={'name':name,'species':spec.species,'original_synthetic_target':ref,
           'glb':str(built['glb']),'glb_sha256':hashlib.sha256(Path(built['glb']).read_bytes()).hexdigest(),
           'triangles':built['triangle_count'],'geometry_checks':quality['checks'],'geometry_pass':quality['technical_pass'],
           'new_synthetic_silhouette_scores':rec['scores'],'previous_synthetic_silhouette_scores':baseline,
           'game_ready':verdict['game_ready'],'game_ready_failures':verdict['failures']}
        results.append(record)
        print('BENCH',name,'technical',quality['technical_pass'],'iou',rec['scores']['average_silhouette_iou'],
              'previous',None if baseline is None else baseline['average_silhouette_iou'],flush=True)
    cols=3;rows=2;sheet=Image.new('RGB',(3*450,rows*616),(13,16,24));draw=ImageDraw.Draw(sheet)
    for i,(name,p) in enumerate(shots):
        x=i%cols*450;y=i//cols*616
        draw.text((x+12,y+12),name.replace('_',' ').title()+' - VQ A2',fill='white')
        with Image.open(p) as im:sheet.paste(im,(x,y+34))
    sheet.save(root/'VQ_A2_New_Character_Review.png')
    hist=[]
    for r in results:
        old=r['previous_synthetic_silhouette_scores'];new=r['new_synthetic_silhouette_scores'];
        if old:hist.append({'name':r['name'],'before':old['average_silhouette_iou'],'after':new['average_silhouette_iou'],
        'change':round(new['average_silhouette_iou']-old['average_silhouette_iou'],6)})
    report={'milestone':'vq-a2-open-original-reference-loop','date':'2026-10-17',
      'reference_count':reference['count'],'reference_rights':reference['rights'],
      'real_external_anatomy_licensed_records_ingested':0,'technique':'Original synthetic independent targets, bounded param corrections, PCHIP garment loft and welded normals',
      'training':learning,'models_built':len(results),'technical_passes':sum(r['geometry_pass'] for r in results),
      'game_ready':0,'reference_evaluated_models':len(hist),
      'average_synthetic_mask_iou_before':round(float(np.mean([x['before'] for x in hist])),6) if hist else None,
      'average_synthetic_mask_iou_after':round(float(np.mean([x['after'] for x in hist])),6) if hist else None,
      'comparable_per_model':hist,'models':results,
      'real_world_anatomy_validated':False,'reference_camera_photorealism_validated':False,
      'production_art_quality_approved':False,'android_emulator_tested':False,
      'run_seconds':round(time.monotonic()-start,2)}
    (root/'VQ_A2_TEST_REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':main()