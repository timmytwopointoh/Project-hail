#!/usr/bin/env python3
"""Optional CPU-only synthetic recipe approximator and strictly licensed dataset gate.
Only learns author-written shape rules. Does NOT learn real anatomical appearance.
Export format uses float arrays and a pure NumPy inference path for later mobile port.
"""
from __future__ import annotations
from pathlib import Path
import json,hashlib,random
import numpy as np
from vq_anatomy_next import parse_description

SPECIES=('human','elf','orc','axolotl','feline','dwarf','automaton')
ATTR=('chibi','slender','muscular','long legs','short legs','large eyes','robe','teal')
TARGETS=('head_ratio','shoulder_ratio','hip_ratio','leg_ratio','eye_scale')

def encode(text):
    s=text.lower();return np.array([int(word in s) for word in SPECIES+ATTR],np.float64)

def make_synthetic_dataset(size=840,seed=27):
    rng=random.Random(seed)
    xs=[];ys=[];prompts=[]
    for i in range(size):
        words=[rng.choice(SPECIES)]
        for k in ATTR:
            if rng.random()<.23:words.append(k)
        prompt=' '.join(words)
        spec=parse_description(prompt,seed=i+1)
        xs.append(encode(prompt));ys.append([getattr(spec,k) for k in TARGETS]);prompts.append(prompt)
    return np.asarray(xs),np.asarray(ys),prompts

def train_synthetic_export(out,seed=27):
    from sklearn.neural_network import MLPRegressor
    x,y,prompts=make_synthetic_dataset(seed=seed)
    rng=np.random.default_rng(seed);ids=rng.permutation(len(x));train=ids[:672];test=ids[672:]
    # Normalizing target dimensions prevents head_ratio from dominating eye scale.
    center=y[train].mean(axis=0);scale=np.maximum(y[train].std(axis=0),.001)
    m=MLPRegressor(hidden_layer_sizes=(36,24),activation='tanh',solver='lbfgs',random_state=seed,max_iter=600)
    m.fit(x[train],(y[train]-center)/scale)
    guess=m.predict(x[test])*scale+center
    baseline=np.repeat(center[None,:],len(test),axis=0)
    mae=float(np.mean(np.abs(guess-y[test])/scale));base=float(np.mean(np.abs(baseline-y[test])/scale))
    weights={'schema':'vq/synthetic-rule-apprentice/v1','activation':'tanh',
      'input_vocabulary':list(SPECIES+ATTR),'output_parameters':list(TARGETS),
      'target_mean':center.tolist(),'target_std':scale.tolist(),
      'layers':[{'weights':w.tolist(),'bias':b.tolist()} for w,b in zip(m.coefs_,m.intercepts_)],
      'not_trained_on_real_anatomy':True,'not_a_photo_or_3d_foundation_model':True,
      'runtime':'numpy_reference; ONNX/TFLite integration not implemented'}
    out=Path(out);out.mkdir(exist_ok=True,parents=True)
    (out/'synthetic_recipe_model.json').write_text(json.dumps(weights,separators=(',',':'))+'\n')
    report={'training_source':'deterministic_VQ_handwritten_recipe_rules',
      'training_examples':len(train),'heldout_examples':len(test),'seed':seed,
      'mean_absolute_error_normalized':mae,'baseline_mean_absolute_error_normalized':base,
      'heldout_improvement_against_constant_mean':round((1-mae/base)*100,2),
      'synthetic_labels_only':True,'trained_on_real_reference_anatomy':False,
      'fidelity_to_real_faces_validated':False,'ready_for_mobile':False,
      'promotable_to_production':False}
    (out/'synthetic_train_report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

def infer_synthetic(path,prompt):
    m=json.loads(Path(path).read_text());a=encode(prompt)
    for layer in m['layers']:
        a=np.tanh(a@np.asarray(layer['weights'])+np.asarray(layer['bias']))
    out=a*np.asarray(m['target_std'])+np.asarray(m['target_mean'])
    return {k:float(x) for k,x in zip(m['output_parameters'],out)}

def accept_reference_dataset(manifest_path):
    """Fail closed: disallow training on unlicensed/unsigned or unverifiable data."""
    manifest=json.loads(Path(manifest_path).read_text())
    examples=manifest.get('examples',[])
    if not examples:raise ValueError('No licensed reference examples')
    for e in examples:
        if not all(e.get(k) for k in ('source','license','consent_or_rights','sha256','landmarks_3d','split')):
            raise ValueError('Source/rights/landmarks/split provenance incomplete')
        if e['split'] not in ('train','validation','test'):
            raise ValueError('Unknown data split')
    if len(set(e['sha256'] for e in examples))!=len(examples):raise ValueError('Duplicate source hashes')
    return True