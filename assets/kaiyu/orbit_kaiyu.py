"""Real geometry VQ-compatible 14-angle offline review; NOT Android screenshots."""
import math, json, hashlib
import numpy as np,trimesh, vtk
from vtk.util.numpy_support import numpy_to_vtk
from PIL import Image,ImageDraw
from pathlib import Path
BASE=Path('/mnt/data');P=BASE/'kaiyu_skinned_m2.glb'; OUT=BASE/'kaiyu_vq_m2';OUT.mkdir(exist_ok=True)
s=trimesh.load(P,force='scene',process=False)
ren=vtk.vtkRenderer();ren.SetBackground(.12,.082,.124)
rw=vtk.vtkRenderWindow();rw.SetOffScreenRendering(1);rw.SetSize(400,510);rw.SetMultiSamples(4);rw.AddRenderer(ren)
triangles=0;materials={}
for n in s.graph.nodes_geometry:
    matrix,geom=s.graph.get(n);mesh=s.geometry[geom]
    xyz=trimesh.transform_points(mesh.vertices,matrix)
    poly=vtk.vtkPolyData();points=vtk.vtkPoints();points.SetData(numpy_to_vtk(np.ascontiguousarray(xyz),deep=True));poly.SetPoints(points)
    # Fill vtk triangles efficiently without hand-created vtkTriangle per face.
    faces=np.asarray(mesh.faces,dtype=np.int64);cells=vtk.vtkCellArray()
    c=np.column_stack((np.full(len(faces),3,dtype=np.int64),faces)).reshape(-1)
    cells.SetCells(len(faces),vtk.vtkIdTypeArray()) if False else None
    for f in faces:
        tri=vtk.vtkTriangle()
        for k in range(3):tri.GetPointIds().SetId(k,int(f[k]))
        cells.InsertNextCell(tri)
    poly.SetPolys(cells)
    norm=vtk.vtkPolyDataNormals();norm.SetInputData(poly);norm.SetSplitting(False);norm.Update()
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(norm.GetOutputPort())
    actor=vtk.vtkActor();actor.SetMapper(mapper)
    mat=getattr(mesh.visual,'material',None)
    rgba=getattr(mat,'baseColorFactor',None)
    col=[min(1,max(0,float(c)/255)) for c in rgba[:3]] if rgba is not None else [.86,.65,.72]
    actor.GetProperty().SetColor(*col);actor.GetProperty().SetAmbient(.45);actor.GetProperty().SetDiffuse(.62)
    actor.GetProperty().SetSpecular(.15);actor.GetProperty().SetInterpolationToPhong();actor.GetProperty().SetBackfaceCulling(False)
    ren.AddActor(actor);triangles+=len(faces)
light=vtk.vtkLight();light.SetPosition(-3,-6,9);light.SetIntensity(1.25);ren.AddLight(light)
light2=vtk.vtkLight();light2.SetPosition(4,5,8);light2.SetIntensity(.65);ren.AddLight(light2)
cam=ren.GetActiveCamera();cam.SetFocalPoint(0,.19,1.03);cam.SetViewUp(0,0,1);cam.SetViewAngle(26)
rows=[];images=[]
for i in range(14):
    yaw=i*360/14.;pitch=12 if i%2==0 else 24
    R=4.6;rad=math.radians(yaw);e=math.radians(pitch)
    cam.SetPosition(R*math.sin(rad)*math.cos(e), -R*math.cos(rad)*math.cos(e),1.0+R*math.sin(e))
    ren.ResetCameraClippingRange();rw.Render()
    win=vtk.vtkWindowToImageFilter();win.SetInput(rw);win.SetInputBufferTypeToRGB();win.ReadFrontBufferOff();win.Update()
    writer=vtk.vtkPNGWriter();writer.SetInputConnection(win.GetOutputPort()); path=OUT/f'kaiyu_angle_{i:02d}.png';writer.SetFileName(str(path));writer.Write()
    im=Image.open(path).convert('RGB');images.append(im)
    pix=np.asarray(im)
    contrast=float(np.std(pix))
    assert contrast>8,(i,contrast)
    rows.append({'index':i,'yaw_degrees':yaw,'pitch_degrees':pitch,'pixels':list(im.size),'stddev':round(contrast,2),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
sheet=Image.new('RGB',(400*7,560*2),(27,17,35));draw=ImageDraw.Draw(sheet)
for i,im in enumerate(images):
    x=(i%7)*400;y=(i//7)*560
    sheet.paste(im,(x,y+34))
    draw.text((x+15,y+10),f'ANGLE {i:02d}  YAW {rows[i]["yaw_degrees"]:.1f}  PITCH {rows[i]["pitch_degrees"]}',fill=(255,197,219))
sheet.save(BASE/'kaiyu_vq_14_angle_m2.png')
report={'mode':'actual 3D GLB geometry offline diagnostic (not Android)', 'views':rows,'angle_count':len(rows),'visible_triangles':triangles,'orbit_report':str(BASE/'kaiyu_vq_14_angle_m2.png'), 'technical_nonblank':True,'rendering':'VTK software renderer','actual_vq_service_test':False,'android_emulator_pass':False,'artistic_approval':False}
(OUT/'inspection_report.json').write_text(json.dumps(report,indent=2))
print('FOURTEEN_REAL_GEOMETRY_VIEW_PASS',len(rows),'triangles',triangles)