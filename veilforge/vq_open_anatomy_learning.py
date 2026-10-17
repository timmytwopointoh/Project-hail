#!/usr/bin/env python3
"""VQ A2/A3 small NumPy MLP predicting ORIGINAL SYNTHETIC target ratios.

No reference images, real anatomical measurements or published models used as
training data. Pure NumPy avoids name conflicts with VQ's legacy queue.py and
allows deterministic CPU-side inference without scikit-learn.
"""
import json,hashlib
from pathlib import Path
import numpy as np
from vq_open_anatomy_reference import PROFILE

STYLES=('neutral','slender','stocky','long_legged','heroic')
KEYS=('head_ratio','shoulder_ratio','hip_ratio','leg_ratio','arm_ratio')
FAMILIES=tuple(PROFILE)

def encode(item):
    return np.asarray([float(item['species']==s) for s in FAMILIES]+
                      [float(item['variant']==v) for v in STYLES]+[item['height_m']/2.],dtype=float)

def train(dataset,out):
    rows=json.loads(Path(dataset).read_text())['entries']
    x=np.array([encode(e) for e in rows]);y=np.array([[e['ratios'][v] for v in KEYS] for e in rows])
    ti=np.array([i for i,r in enumerate(rows) if r['set']=='training'])
    vi=np.array([i for i,r in enumerate(rows) if r['set']=='validation'])
    hi=np.array([i for i,r in enumerate(rows) if r['set']=='test'])
    mu=y[ti].mean(0);sig=np.maximum(y[ti].std(0),.001)
    target=(y-mu)/sig
    rng=np.random.default_rng(72);hidden=14;lr=.030
    W=rng.normal(0,.16,(x.shape[1],hidden));b=np.zeros(hidden)
    V=rng.normal(0,.14,(hidden,target.shape[1]));c=np.zeros(target.shape[1])
    params=[W,b,V,c];velocity=[np.zeros_like(v) for v in params];variance=[np.zeros_like(v) for v in params]
    best=None
    for epoch in range(1400):
        a=np.tanh(x[ti]@W+b);pred=a@V+c
        grad=2*(pred-target[ti])/len(ti)
        grads=[x[ti].T@((grad@V.T)*(1-a*a)),((grad@V.T)*(1-a*a)).sum(0),a.T@grad,grad.sum(0)]
        for j,(p,g) in enumerate(zip(params,grads)):
            velocity[j]=.9*velocity[j]+.1*g;variance[j]=.999*variance[j]+.001*g*g
            p-=lr*(velocity[j]/(1-.9**(epoch+1)))/(np.sqrt(variance[j]/(1-.999**(epoch+1)))+1e-8)
        if epoch%100==0:
            va=np.mean(np.abs((np.tanh(x[vi]@W+b)@V+c)*sig+mu-y[vi]))
            if best is None or va<best[0]:best=(float(va),[p.copy() for p in params])
    W,b,V,c=best[1]
    def err(ids):
        p=(np.tanh(x[ids]@W+b)@V+c)*sig+mu
        return float(np.mean(np.abs(p-y[ids]))),float(np.mean(np.abs(y[ids]-mu)))
    ev,basev=err(vi);et,baset=err(hi)
    weights={'schema':'vq.original-synthetic-param-net.v2','trained_on_real_anatomy':False,
      'source_dataset_sha256':hashlib.sha256(Path(dataset).read_bytes()).hexdigest(),
      'semantic_inputs':list(FAMILIES+STYLES)+['height_over_two'],
      'target_outputs':list(KEYS),'activation':'tanh','target_mu':mu.tolist(),'target_std':sig.tolist(),
      'layers':[{'w':W.tolist(),'b':b.tolist()},{'w':V.tolist(),'b':c.tolist()}],
      'optimizer':'deterministic-numpy-adam','best_validation_selected':True}
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/'A2_synthetic_profile_weights.json').write_text(json.dumps(weights,separators=(',',':'))+'\n')
    report={'train':len(ti),'validation':len(vi),'heldout_test':len(hi),
      'validation_mae_ratios':round(ev,6),'heldout_mae_ratios':round(et,6),
      'validation_constant_baseline_mae_ratios':round(basev,6),
      'heldout_constant_baseline_mae_ratios':round(baset,6),
      'real_anatomy_learning_verified':False,'valid_human_appearance_scoring':False,
      'runtime_numpy_inference_possible':True,'mobile_runtime_integrated':False}
    (out/'A2_synthetic_learning_report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--dataset',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();print(train(a.dataset,a.out))