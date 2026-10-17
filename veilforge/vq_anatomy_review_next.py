#!/usr/bin/env python3
"""VQ A1 independent mesh/landmark quality evidence and VTK offline review renders.
Rendering here is offline VTK software, NOT an Android emulator or artist pass.
"""
from pathlib import Path
import json,hashlib,math
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from vq_anatomy_next import ShapeSpec,anatomy_anchors

def inspect(glb,spec):
    scene=trimesh.load(glb,force='scene',process=False)
    if len(scene.geometry)==0:raise ValueError('Empty scene')
    skin=next((v for v in scene.geometry.values() if getattr(getattr(v.visual,'material',None),'name','')=='skin'),None)
    if skin is None:raise ValueError('Skin geometry missing')
    allverts=np.vstack([m.vertices for m in scene.geometry.values()]); bounds=[allverts.min(axis=0).tolist(),allverts.max(axis=0).tolist()]
    tri=sum(len(m.faces) for m in scene.geometry.values());a=anatomy_anchors(spec)
    height=float(allverts[:,1].max()-allverts[:,1].min())
    # Skin must be a coherent surface; separate hair and clothes are permitted.
    comps=skin.split(only_watertight=False)
    # Check neutral bilateral surface for gross asymmetric mistakes only.
    verts=skin.vertices[::max(1,len(skin.vertices)//8000)]
    kdt=cKDTree(skin.vertices);mirror=verts.copy();mirror[:,0]*=-1
    dd=kdt.query(mirror,k=1)[0]
    mirrored_p90=float(np.percentile(dd,90))
    grounded=abs(float(allverts[:,1].min()))<.07*spec.height
    # Deformation proxy: bound arm surface is locally projected through a bend
    # and measured, but no mesh skin weight / skeletal animation is exported.
    elbow=np.array(a['elbows'][1]); wrist=np.array(a['wrists'][1]); v=np.array(skin.vertices)
    sel=(v[:,0]>elbow[0] and False) if False else (v[:,0]>elbow[0]+.035*spec.height)
    local=v[sel]-elbow
    c,s=math.cos(math.radians(25)),math.sin(math.radians(25))
    bend=np.array([[c,-s,0],[s,c,0],[0,0,1]])
    moved=local@bend.T+elbow
    max_move=float(np.linalg.norm(moved-v[sel],axis=1).max()) if np.any(sel) else 0
    finite=bool(np.isfinite(allverts).all())
    mat_names=sorted(set(getattr(getattr(m.visual,'material',None),'name','') for m in scene.geometry.values()))
    metrics={'source_glb_sha256':hashlib.sha256(Path(glb).read_bytes()).hexdigest(),
      'triangle_count':tri,'material_names':mat_names,
      'bounds':bounds,'total_height_measured':round(height,5),
      'height_to_requested':round(height/spec.height,4),
      'skin_watertight':bool(skin.is_watertight),'skin_components':len(comps),
      'skin_euler_number':int(skin.euler_number),'mirror_nearest_neighbor_p90_m':round(mirrored_p90,5),
      'ground_contact_proxy':grounded,'all_vertices_finite':finite,
      'elbow_bend_25deg_max_vertex_move_m':round(max_move,4),
      'actual_skinning_or_motion_verified':False,
      'reference_likeness_verified':False,'android_emulator_verified':False,'artist_approved':False}
    checks={'finite':finite,'reimport_triangles':tri>1000,'skin_single_component':len(comps)==1,
      'skin_watertight':bool(skin.is_watertight),'bilateral_skin_p90_under_3cm':mirrored_p90<.03,
      'grounding_proxy':grounded,'material_groups':len(mat_names)>=7}
    metrics['checks']=checks
    metrics['technical_pass']=all(checks.values())
    return metrics

def render(glb,destination,view='three_quarter',size=(640,800)):
    import vtk
    sc=trimesh.load(glb,force='scene',process=False)
    renderer=vtk.vtkRenderer()
    renderer.SetBackground(.055,.062,.086)
    renderer.SetUseDepthPeeling(False)
    colors={'skin':(.87,.66,.61),'hair':(.23,.17,.21),'cloth':(.31,.22,.30),
      'iris':(.40,.57,.61),'pupil':(.08,.07,.10),'lip':(.62,.36,.42),
      'sclera':(.95,.88,.86),'trim':(.83,.63,.72),'frill':(.95,.58,.67),'appendage':(.87,.66,.61)}
    for key,m in sc.geometry.items():
        if len(m.faces)==0:continue
        mat=getattr(m.visual,'material',None)
        name=getattr(mat,'name','')
        actual_color=colors.get(name,(.70,.72,.73))
        tex=getattr(mat,'baseColorTexture',None)
        if tex is not None:
            # Read author-supplied baked albedo to display the real palette.
            texsmall=tex.convert('RGB').resize((24,24))
            actual_color=tuple((np.asarray(texsmall).mean(axis=(0,1))/255.).tolist())
        elif mat is not None and hasattr(mat,'baseColorFactor'):
            rgb=np.asarray(mat.baseColorFactor[:3],float)
            actual_color=tuple((rgb/(255 if rgb.max()>1 else 1)).tolist())
        poly=vtk.vtkPolyData();points=vtk.vtkPoints();points.SetNumberOfPoints(len(m.vertices))
        for i,v in enumerate(m.vertices):points.SetPoint(i,*[float(x) for x in v])
        poly.SetPoints(points)
        cells=vtk.vtkCellArray()
        for f in m.faces:
            cell=vtk.vtkTriangle();cell.GetPointIds().SetId(0,int(f[0]));cell.GetPointIds().SetId(1,int(f[1]));cell.GetPointIds().SetId(2,int(f[2]));cells.InsertNextCell(cell)
        poly.SetPolys(cells)
        filt=vtk.vtkPolyDataNormals();filt.SetInputData(poly);filt.SplittingOff();filt.ConsistencyOn();filt.AutoOrientNormalsOff();filt.ComputePointNormalsOn();filt.Update()
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(filt.GetOutputPort())
        actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(*actual_color)
        actor.GetProperty().SetInterpolationToPhong();actor.GetProperty().SetAmbient(.25);actor.GetProperty().SetDiffuse(.72);actor.GetProperty().SetSpecular(.18)
        renderer.AddActor(actor)
    light=vtk.vtkLight();light.SetPosition(-3,5,-4);light.SetFocalPoint(0,1,0);light.SetIntensity(1.05);renderer.AddLight(light)
    back=vtk.vtkLight();back.SetPosition(3,4,4);back.SetFocalPoint(0,1,0);back.SetIntensity(.65);renderer.AddLight(back)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.AddRenderer(renderer);win.SetSize(*size);win.SetMultiSamples(0)
    bounds=np.array(sc.bounds);center=(bounds[0]+bounds[1])/2;maximum=float((bounds[1]-bounds[0]).max());cam=renderer.GetActiveCamera()
    if view=='front':pos=center+np.array([0,0,-max(3.,maximum*2.5)])
    elif view=='side':pos=center+np.array([max(3.,maximum*2.5),0,0])
    else:pos=center+np.array([max(2.,maximum*1.4),max(.4,maximum*.36),-max(2.6,maximum*2.1)])
    cam.SetPosition(*pos.tolist());cam.SetFocalPoint(*center.tolist());cam.SetViewUp(0,1,0);cam.ParallelProjectionOn();cam.SetParallelScale(maximum*.64)
    renderer.ResetCameraClippingRange();win.Render()
    filt=vtk.vtkWindowToImageFilter();filt.SetInput(win);filt.Update()
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(destination));writer.SetInputConnection(filt.GetOutputPort());writer.Write();win.Finalize()
    return str(destination)