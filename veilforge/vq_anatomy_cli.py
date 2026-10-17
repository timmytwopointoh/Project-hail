#!/usr/bin/env python3
"""VQ A3 text -> original mesh -> GLB -> QA -> optional screenshots.

Review-only export; no auto-promotion, external model downloads, or GitHub
Actions calls. The outputs are engineering prototypes, not clinical anatomy.
"""
from __future__ import annotations
import argparse, json, hashlib
from dataclasses import replace
from pathlib import Path
from vq_anatomy_next import parse_description, build
from vq_anatomy_review_next import inspect, render
from vq_shape_gate_next import gate

def run(prompt,out,*,voxel=.016,seed=19,preview=False):
    root=Path(out);root.mkdir(parents=True,exist_ok=True)
    spec=parse_description(prompt,seed=seed)
    candidate=build(spec,root,voxel=voxel,texture_size=64)
    review=inspect(candidate['glb'],spec)
    decision=gate(review)
    images={}
    if preview:
        for angle in ('front','side','three_quarter'):
            image=root/(spec.name+'_'+angle+'.png')
            render(candidate['glb'],image,view=angle,size=(480,620))
            images[angle]=str(image)
    report={'milestone':'VQ A3 detailed anatomy','prompt':prompt,
            'source':'original VQ implicit construction and A3 geometric landmarks',
            'spec':candidate['spec'],'asset_glb':str(candidate['glb']),
            'asset_sha256':hashlib.sha256(Path(candidate['glb']).read_bytes()).hexdigest(),
            'triangle_count':candidate['triangle_count'],
            'qa':review,'promotion_gate':decision,'previews':images,
            'actual_skinning_verified':False,'real_anatomy_validated':False,
            'photorealism_artist_approved':False,'android_emulator_verified':False}
    (root/'vq_a3_qa.json').write_text(json.dumps(report,indent=2,default=str)+'\n')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prompt',required=True);p.add_argument('--out',required=True)
    p.add_argument('--voxel',type=float,default=.016)
    p.add_argument('--seed',type=int,default=19)
    p.add_argument('--preview',action='store_true')
    args=p.parse_args()
    if args.voxel<.009 or args.voxel>.035: p.error('Voxel must be between .009 and .035 meters')
    report=run(args.prompt,args.out,voxel=args.voxel,seed=args.seed,preview=args.preview)
    print(json.dumps({'glb':report['asset_glb'],'triangles':report['triangle_count'],
       'technical_pass':report['qa']['technical_pass'],
       'promotion_status':report['promotion_gate']['status']}))

if __name__=='__main__':main()