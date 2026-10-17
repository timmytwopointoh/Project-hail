#!/usr/bin/env python3
"""Continuous-skin CPU joint-bend test; NOT an embedded glTF skin or animation rig.

A technical test to reveal shoulder/elbow topology behavior early. The skinned
GLB exporter, face morphs, joint limits and animation playback remain open.
"""
from __future__ import annotations
import json,math
from pathlib import Path
import numpy as np
import trimesh
from vq_anatomy_next import anatomy_anchors

def smoothstep(v):
    t=np.clip(v,0,1)
    return t*t*(3-2*t)

def joint_deflection(glb_path,spec,out_path,angle_deg=25):
    if abs(angle_deg)>35:raise ValueError('Only bounded deformation smoke angles supported')
    scene=trimesh.load(glb_path,force='scene',process=False)
    entry=next((m for m in scene.geometry.values() if getattr(getattr(m.visual,'material',None),'name','')=='skin'),None)
    if entry is None:raise ValueError('Missing skin mesh')
    skin=entry.copy()
    x=np.asarray(skin.vertices).copy();before=x.copy()
    a=anatomy_anchors(spec);h=spec.height
    for k,side in enumerate((-1,1)):
        elbow=np.asarray(a['elbows'][k]);wrist=np.asarray(a['wrists'][k]);
        # Near the elbow bend progressively, and leave chest/other limbs still.
        xa=x[:,0]*side
        axial=smoothstep((xa-side*elbow[0]+.09*h)/(.19*h))
        within=np.exp(-((x[:,1]-elbow[1])/(.22*h))**4)
        weights=axial*within
        th=math.radians(angle_deg)*side
        c,s=math.cos(th),math.sin(th)
        rot=np.array([[c,-s,0],[s,c,0],[0,0,1]])
        posed=(x-elbow)@rot.T+elbow
        x+=(posed-x)*weights[:,None]
    skin.vertices=x
    tiny_before=np.count_nonzero(entry.area_faces<1e-10)
    tiny_after=np.count_nonzero(skin.area_faces<1e-10)
    stretch=skin.area_faces/np.maximum(entry.area_faces,1e-12)
    report={'source':str(glb_path),'angle_degrees':angle_deg,
      'max_vertex_displacement_m':float(np.max(np.linalg.norm(x-before,axis=1))),
      'p95_surface_area_ratio':float(np.quantile(stretch,.95)),
      'p05_surface_area_ratio':float(np.quantile(stretch,.05)),
      'watertight_after':bool(skin.is_watertight),
      'near_zero_faces_before':int(tiny_before),'near_zero_faces_after':int(tiny_after),
      'weights_attached_to_glb':False,'animation_exported':False,
      'cpu_deformation_smoke_passed':bool(skin.is_watertight and np.isfinite(x).all()
        and float(np.quantile(stretch,.05))>.45 and float(np.quantile(stretch,.95))<2.0)}
    Path(out_path).parent.mkdir(parents=True,exist_ok=True)
    out_scene=trimesh.Scene();out_scene.add_geometry(skin,geom_name='posed_skin_sample')
    Path(out_path).write_bytes(out_scene.export(file_type='glb'))
    Path(out_path).with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
    return report