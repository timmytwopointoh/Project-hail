#!/usr/bin/env python3
"""Reference-aware acceptance gate, bounded anatomy parameter correction, and logs.
Visual quality cannot be auto-approved by technical geometry measurements.
"""
from __future__ import annotations
from dataclasses import replace,asdict
from pathlib import Path
import json,math
from vq_anatomy_next import ShapeSpec,parse_description

TARGET_PROFILES={
 'human':dict(head_ratio=.135,shoulder_ratio=.245,hip_ratio=.174,leg_ratio=.495,eye_scale=1.0),
 'elf':dict(head_ratio=.123,shoulder_ratio=.231,hip_ratio=.160,leg_ratio=.525,eye_scale=1.0),
 'orc':dict(head_ratio=.129,shoulder_ratio=.302,hip_ratio=.194,leg_ratio=.493,eye_scale=1.0),
 'axolotl':dict(head_ratio=.205,shoulder_ratio=.224,hip_ratio=.160,leg_ratio=.418,eye_scale=1.15),
 'feline':dict(head_ratio=.146,shoulder_ratio=.226,hip_ratio=.161,leg_ratio=.515,eye_scale=1.0),
 'dwarf':dict(head_ratio=.152,shoulder_ratio=.292,hip_ratio=.215,leg_ratio=.408,eye_scale=1.0),
 'automaton':dict(head_ratio=.122,shoulder_ratio=.264,hip_ratio=.178,leg_ratio=.515,eye_scale=1.0)}

def proxy_proportion_error(spec,target=None):
    t=target or TARGET_PROFILES[spec.species]
    return round(sum(abs(getattr(spec,k)-v)/max(.01,v) for k,v in t.items())/len(t),6)

def bounded_shape_repair(spec,reference_targets=None,max_iterations=5):
    """Numerical repair toward explicit style targets, not a learned eye or sculpt."""
    target=reference_targets or TARGET_PROFILES[spec.species]
    trace=[];curr=spec
    for iteration in range(max_iterations):
        before=proxy_proportion_error(curr,target)
        updates={k:getattr(curr,k)+.48*(goal-getattr(curr,k)) for k,goal in target.items()}
        cand=replace(curr,**updates).validate()
        after=proxy_proportion_error(cand,target)
        trace.append({'iteration':iteration+1,'before_error':before,'after_error':after,
                      'technique':'bounded_numeric_landmark_parameter_correction'})
        if after>=before:break
        curr=cand
        if after<.006:break
    return curr,trace

def gate(metrics,*,reference_metrics=None,rig_evidence=None,android_evidence=None,artist_signed_off=False):
    technical=metrics.get('technical_pass',False)
    # Reference metrics must come from independently supplied/calibrated target views.
    reference_ok=(reference_metrics is not None and reference_metrics.get('source_validated') is True
       and float(reference_metrics.get('landmark_mean_error_norm',1))<=.04
       and float(reference_metrics.get('silhouette_iou',0))>=.86)
    motion_ok=bool(rig_evidence and rig_evidence.get('skin_weights_checked') and
                   rig_evidence.get('joint_bend_validated'))
    runtime_ok=bool(android_evidence and android_evidence.get('fresh_emulator_frame_verified'))
    checks={'technical':technical,'visual_reference':reference_ok,
            'skinned_deformation':motion_ok,'android_runtime':runtime_ok,
            'human_art_approval':bool(artist_signed_off)}
    return {'schema':'vq/production-gate/1','checks':checks,
            'candidate_technically_usable':technical,'game_ready':all(checks.values()),
            'status':'APPROVED' if all(checks.values()) else 'REVIEW_REQUIRED',
            'failures':[n for n,v in checks.items() if not v]}