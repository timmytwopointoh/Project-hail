#!/usr/bin/env python3
"""Reference-aware shape comparison. Needs REAL independently sourced views.
Masks alone cannot certify art direction, photorealism, shading, rig or a game.
"""
from pathlib import Path
from hashlib import sha256
import json
import numpy as np
from PIL import Image

def evaluate_masks(candidate_path,reference_path,*,threshold=128):
    c=np.asarray(Image.open(candidate_path).convert('L'))>=threshold
    r=np.asarray(Image.open(reference_path).convert('L'))>=threshold
    if c.shape!=r.shape:raise ValueError('Candidate/reference masks require matched calibrated pixel dimensions')
    union=np.count_nonzero(c|r)
    iou=float(np.count_nonzero(c&r)/union) if union else 0.0
    return {'silhouette_iou':round(iou,6),'pixels':int(c.size),
        'candidate_sha256':sha256(Path(candidate_path).read_bytes()).hexdigest(),
        'reference_sha256':sha256(Path(reference_path).read_bytes()).hexdigest(),
        'same_camera_not_automatically_verified':True}

def evaluate_landmarks(candidate:dict,reference:dict,*,scale_m:float):
    if scale_m<=0 or not np.isfinite(scale_m):raise ValueError('Positive reference scale required')
    if set(candidate)!=set(reference) or len(candidate)<8:raise ValueError('At least eight matched 3D landmarks required')
    a=np.array([candidate[k] for k in sorted(candidate)],dtype=float)
    b=np.array([reference[k] for k in sorted(reference)],dtype=float)
    if a.shape!=(len(candidate),3) or b.shape!=a.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Each 3D landmark must contain three finite coordinates')
    err=np.linalg.norm(a-b,axis=1)/scale_m
    return {'landmark_mean_error_norm':float(err.mean()),'landmark_p90_error_norm':float(np.percentile(err,90)),
            'count':len(candidate),'requires_independent_reference_rights_verification':True}