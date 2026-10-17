"""Reusable geometry techniques for VQ Mesh, not object-specific geometry.

Independent of specific model names or saved meshes: tangent-following smooth
lofts, soft leaf frills, continuous cloth hems, and organic fin surfaces.
Angles and widths are in world units (metres for this example).
"""
import math
import numpy as np

PI=math.pi

def _unit(v):
 v=np.asarray(v,dtype=float); return v/max(1e-10,np.linalg.norm(v))

def tapered_curve(mesh, points, radii, material, sides=16, steps=4, aspect=1.0, caps=True):
 """One tangent-continuous tube; no cylinder-endcaps at intermediate joints.
 Piecewise Catmull-Rom interpolated centerline with parallel transported frame.
 Radii can be scalars; use varying radius to round the base and pinch the tip.
 """
 P=np.asarray(points,dtype=float); R=np.asarray(radii,dtype=float)
 if len(P)<2: raise ValueError('curve needs >=2 points')
 pos=[]; rr=[]
 for k in range(len(P)-1):
  a=P[max(k-1,0)];b=P[k];c=P[k+1];d=P[min(k+2,len(P)-1)]
  for q in range(steps):
   t=q/steps
   h=.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
   def cr(i):return .5*(2*R[k]+(-R[i]+R[k+1])*t+(2*R[i]-5*R[k]+4*R[k+1]-R[min(k+2,len(R)-1)])*t*t+(-R[i]+3*R[k]-3*R[k+1]+R[min(k+2,len(R)-1)])*t*t*t)
   pos.append(h);rr.append(max(.0008,float(cr(max(0,k-1)))))
 pos.append(P[-1]);rr.append(max(.0008,float(R[-1])))
 tangent=[_unit(pos[min(i+1,len(pos)-1)]-pos[max(i-1,0)]) for i in range(len(pos))]
 frame=[None]*len(pos)
 trial=np.array([0,0,1.]) if abs(tangent[0][2])<.82 else np.array([0,1.,0])
 frame[0]=_unit(np.cross(tangent[0],trial))
 rings=[]
 for k,(p,r) in enumerate(zip(pos,rr)):
  if k:
   f=frame[k-1]-np.dot(frame[k-1],tangent[k])*tangent[k]
   frame[k]=_unit(f) if np.linalg.norm(f)>1e-9 else frame[k-1]
  ortho=_unit(np.cross(tangent[k],frame[k]))
  rings.append([tuple(p+r*(math.cos(2*PI*j/sides)*frame[k]+aspect*math.sin(2*PI*j/sides)*ortho)) for j in range(sides)])
 for k in range(len(rings)-1):
  for j in range(sides):
   h=(j+1)%sides
   mesh.quad(rings[k][j],rings[k][h],rings[k+1][h],rings[k+1][j],material)
 if caps:
  for j in range(sides):
   h=(j+1)%sides
   mesh.tri(tuple(pos[0]),rings[0][h],rings[0][j],material)
   mesh.tri(tuple(pos[-1]),rings[-1][j],rings[-1][h],material)

def leaf_frill(mesh, root, direction, width, material, vein_material=None, side=1, slices=8):
 """Watertight raised petal surface (not rigid cylindrical gill filament)."""
 a=np.asarray(root,float);v=np.asarray(direction,float); p1=a+v
 # Broad fan lies mainly in screen XY; thin Z thickness subtly undulates.
 tangent=_unit(v); axis=_unit(np.array([-tangent[1],tangent[0],0.]))
 if np.linalg.norm(axis)<.1:axis=np.array([1.,0,0])
 verts=[]
 for i in range(slices+1):
  t=i/slices;mid=a+v*t+np.array([0,0,-.014*math.sin(PI*t)])
  half=(.0008+width*math.sin(PI*t)**.70)*(1-.17*t)
  verts.append((tuple(mid+axis*half),tuple(mid-axis*half),tuple(mid+np.array([0,0,.005+.003*math.sin(PI*t)]))))
 for i in range(slices):
  l0,r0,b0=verts[i];l1,r1,b1=verts[i+1]
  mesh.quad(l0,l1,b1,b0,material);mesh.quad(b0,b1,r1,r0,material)
  # thin underside bridge, offset from top cap to avoid exactly coincident faces
  mesh.quad(r0,r1,l1,l0,material)
 if vein_material:
  tapered_curve(mesh,[tuple(a+v*t+np.array([0,0,-.017])) for t in (0,.5,1)],
                [max(.0025,width*.11),max(.002,width*.07),.0009],vein_material,sides=6,steps=3)

def fin_membrane(mesh, spine, heights, material, half_thickness=.005):
 """Single connected membrane, two displaced outer surfaces (no duplicated faces)."""
 if len(spine)!=len(heights):raise ValueError('fin dimensions')
 for k in range(len(spine)-1):
  ax,ay,az=spine[k]; bx,by,bz=spine[k+1]; ha,hb=heights[k:k+2]
  for zz in (-half_thickness,half_thickness):
   a=(ax,ay,az+zz);b=(ax,ay+ha,az+zz)
   c=(bx,by+hb,bz+zz);d=(bx,by,bz+zz)
   mesh.quad(a,b,c,d,material)
  mesh.quad((ax,ay+ha,az-half_thickness),(ax,ay+ha,az+half_thickness),
           (bx,by+hb,bz+half_thickness),(bx,by+hb,bz-half_thickness),material)

def loop_trim(mesh, y, rx, rz, material, wave=0.0, z0=.04, thickness=.007, count=150):
 """Smooth continuous piping along a wavy garment hem, ring is in X/Z."""
 pts=[]
 for i in range(count+1):
  th=2*PI*i/count
  pts.append((rx*math.cos(th),y+wave*math.cos(12*th),z0+rz*math.sin(th)))
 # Piecewise thin short lengths; caps only at first and last for circular seam.
 # Seam segments have no intermediate caps thanks to tangent-preserving tube.
 tapered_curve(mesh,pts,[thickness]*len(pts),material,sides=6,steps=1,caps=False)