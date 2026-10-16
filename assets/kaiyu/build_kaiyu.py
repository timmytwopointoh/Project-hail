"""Kaiyu / axolotl girl — reference-guided layered game character.
Generates a 3D GLB with named transform joints & looping secondary motion.
Requirements: numpy, trimesh, scipy, vtk(optional for preview). Python 3.11+.
Source reference: 1021.jpg supplied by the user. Y-forward = -Y, Z-up.
Model is an iterative procedural prototype, NOT a 1:1 production sculpt.
"""
import os,json,math,struct,collections,zipfile,copy
import numpy as np
import trimesh
from PIL import Image,ImageDraw,ImageFont
from scipy.spatial.transform import Rotation as R
OUT=os.path.dirname(__file__)
# These material colors are visually estimated from the Kaiyu turnaround sheet.
C={
 'skin':'#F9C2C6','blush':'#F39BAE','skin_shade':'#D98A9D','hair':'#3A232C','hair_shadow':'#25161F',
 'hair_highlight':'#6C3A48','hair_pink':'#E98CA6','gill':'#F4A0B5','gill_light':'#FFD4E0',
 'gill_tip':'#ED91AB','gill_vein':'#D96385','white':'#FFF0EA','eye_black':'#26151E',
 'eye_rose':'#B63860','eye_pink':'#F36B91','eye_shine':'#FFFFFF',
 'black':'#251A23','ink':'#171017','burgundy':'#702238','burgundy_light':'#9D3C58',
 'lace':'#E48AA0','pink':'#F58BA7','hotpink':'#F65B93','rose':'#D65981',
 'gold':'#F4D5B5','boots':'#281B25','bootshine':'#5A3949','tail':'#F6BACA','tail_spot':'#E786A3',
 'tail_fin':'#F0A1B9','tail_fin_light':'#FFE0E6','flower':'#F69CB4',
}
def rgba(s,a=255):return tuple(bytes.fromhex(s.lstrip('#')))+(a,)
COL={k:np.array(rgba(v),dtype=np.uint8) for k,v in C.items()}
# material-key,transform-node => list of local meshes
GROUP=collections.defaultdict(list); NODE={}; METADATA=[]
def node(name,parent='Kaiyu_Root',pos=(0,0,0)):
 NODE[name]={'parent':parent,'pos':list(map(float,pos))}
node('Kaiyu_Root',parent=None)
node('Torso',pos=(0,0,.90))
node('Head',parent='Torso',pos=(0,0,.58))
node('Arm_L',parent='Torso',pos=(-.235,-.025,.175))
node('Arm_R',parent='Torso',pos=(.235,-.025,.175))
node('Leg_L',pos=(-.135,-.005,.73))
node('Leg_R',pos=(.135,-.005,.73))
node('Tail_01',pos=(0,.20,.78))
node('Tail_02',parent='Tail_01',pos=(.06,.20,-.08))
node('Tail_03',parent='Tail_02',pos=(.105,.26,-.105))
node('Tail_04',parent='Tail_03',pos=(.13,.28,-.04))
for side in ['L','R']:
 for j in range(3):
  node(f'Gill_{side}_{j+1}_Root',parent='Head',pos=((-1 if side=='L' else 1)*.292,.018,.13+(.12-j*.11)))
  node(f'Gill_{side}_{j+1}_Tip',parent=f'Gill_{side}_{j+1}_Root',pos=((-1 if side=='L' else 1)*.17,.007, (.10-j*.095)))
for side in ['L','R']:
 for j in range(3):node(f'Hair_{side}_{j+1}',parent='Head',pos=((-1 if side=='L' else 1)*(.17+.055*j),.05,-.17-.04*j))

def emit(mesh,mat,parent='Torso'):
 if mesh is None:return
 mesh=mesh.copy()
 GROUP[(parent,mat)].append(mesh)
def ell(pos,sc,mat,parent='Torso',seg=20,rings=14):
 # sphere normals smooth when importing
 m=trimesh.creation.uv_sphere(radius=1,count=[seg,rings]);m.vertices=m.vertices*np.array(sc)+np.array(pos)
 emit(m,mat,parent)
def tube(points,radii,mat,parent='Torso',sides=12):
 pts=np.asarray(points,float);rads=np.asarray(radii,float)
 if len(pts)<2:return
 out=[]
 for i,p in enumerate(pts):
  t=pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)];t=t/(np.linalg.norm(t)+1e-9)
  ref=np.array([0,0,1.]) if abs(t[2])<.94 else np.array([0,1.,0])
  u=np.cross(t,ref);u=u/(np.linalg.norm(u)+1e-9);v=np.cross(t,u)
  for j in range(sides):out.append(p+rads[i]*(u*math.cos(j*2*math.pi/sides)+v*math.sin(j*2*math.pi/sides)))
 faces=[]
 for i in range(len(pts)-1):
  for k in range(sides):
   a=i*sides+k;b=i*sides+(k+1)%sides;c=(i+1)*sides+(k+1)%sides;d=(i+1)*sides+k
   faces.extend([(a,b,c),(a,c,d)])
 for k in range(1,sides-1): faces.extend([(0,k+1,k),((len(pts)-1)*sides,(len(pts)-1)*sides+k,(len(pts)-1)*sides+k+1)])
 emit(trimesh.Trimesh(vertices=np.array(out),faces=faces,process=False),mat,parent)
def line(points,r,mat,parent='Torso',sides=7):
 arr=np.array(points,dtype=float)
 tube(arr,np.asarray([r*(1-.4*i/max(1,len(arr)-1)) for i in range(len(arr))]),mat,parent,sides)
def heart(x,y,z,s=.035,mat='rose',parent='Torso',direction=1):
 # Heart points triangulated with raised center for dimension; face front is negative Y
 contour=[]
 for t in np.linspace(0,2*math.pi,32,endpoint=False):
  vx=16*math.sin(t)**3/17
  vz=(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))/17
  contour.append([x+s*vx, y,z+s*vz])
 verts=[[x,y+.009,z]]+contour+[[x,y-.012,z]]
 faces=[]
 for j in range(32):faces.append((0,j+1,((j+1)%32)+1));faces.append((33,((j+1)%32)+1,j+1))
 emit(trimesh.Trimesh(vertices=verts,faces=faces,process=False),mat,parent)
def flower(x,y,z,s=.035,parent='Head',normal=-1):
 for k in range(5):
  a=2*math.pi*k/5
  ell((x+math.sin(a)*s*.58,y+normal*.004,z+math.cos(a)*s*.58),(.012+s*.22,.009,s*.50),'flower',parent,12,8)
 ell((x,y+normal*.012,z),(.010,.010,.010),'gold',parent,12,8)
def bow(x,y,z,s=.055,parent='Head',mat='burgundy'):
 for sign in (-1,1):
  ell((x+sign*s*.6,y,z),(.046*s/.055,.017*s/.055,.023*s/.055),mat,parent,14,10)
 ell((x,y-.013,z),(.015*s/.055,.012,.018*s/.055),'rose',parent)
 for sign in (-1,1):
  tube([(x+sign*.005,y,z),(x+sign*s*.22,y,z-s*.5),(x+sign*s*.45,y,z-s*1.18)],[s*.16,s*.12,s*.09],mat,parent,8)
def leaf(center,length,width,rot,mat,parent,depth=.010):
 # two sided curved tapered leaf geometry (used for gills and ruffles)
 x,y,z=center;pts=[];faces=[]
 for i in range(9):
  t=i/8.;axis=np.array([math.cos(rot),0,math.sin(rot)]);perp=np.array([-math.sin(rot),0,math.cos(rot)])
  p=np.array([x,y,z])+axis*(length*t)
  w=width*math.sin(math.pi*t)**.8
  for q in (-1,1):
   pp=p+q*perp*w+np.array([0,-depth*math.sin(math.pi*t),0]);pts.append(pp)
 for i in range(8):
  a=2*i;faces.extend([(a,a+2,a+1),(a+1,a+2,a+3),(a+1,a+2,a),(a+3,a+2,a+1)])
 emit(trimesh.Trimesh(vertices=pts,faces=faces,process=False),mat,parent)
# Body, hands and structural shapes: chibi stylized, rounded rather than photorealistic
ell((0,.005,-.035),(.20,.125,.235),'skin','Torso',28,20)
ell((0,-.005,-.235),(.204,.13,.11),'skin','Torso',24,14)
ell((0,-.005,.27),(.075,.07,.10),'skin','Torso')
# Face and detailed hair cap
ell((0,0,0),(.354,.306,.355),'skin','Head',48,32)
ell((0,.035,.092),(.366,.326,.35),'hair','Head',40,24)
# hair cap area covering back (hair scalp) deliberately in front? visible face via skin geometry occlusion
# Hair ring on sides and back, wavy bob layered with front fringe
for s in (-1,1):
 for j in range(8):
  t=j/7
  xx=s*(.215+.085*math.sin(t*math.pi))
  y=.005+.15*t
  z=.14-.45*t+.02*math.cos(j*1.8)
  ell((xx,y,z),(.09-.01*t,.077,.155-.018*t),'hair' if j%3 else 'hair_highlight','Head',18,12)
# scalp bangs: segmented swoop, keeping eyes clear
for j in range(13):
 x=-.285+j*.048
 z=.26-.085*math.exp(-((x-.055)/.12)**2)+.022*math.sin(j*1.8)
 y=-.255+.045*(abs(x)/.29)
 tube([(x,y+.02,.305),(x+.019,y-.024,z+.043),(x+.024,y-.043,z-.057)], [.049,.045,.004], 'hair_pink' if j in (6,7) else ('hair_highlight' if j%4==0 else 'hair'),'Head',9)
# Curving back hair-lock panels create layered chibi-bob silhouette in every orbit.
for k in range(18):
 a=(k+.35)/18*math.pi
 x=.295*math.cos(a)
 y=.105+.20*math.sin(a)
 length=.19+.082*(k%4)/3
 z=.245
 points=[(x*.62,y*.42,z),(x*.95,y*.82,z-.07),(x*1.06,y+.042,z-.19),(x*1.11+math.sin(k*2.1)*.024,y+.040,z-.28-length*.28)]
 tube(points,[.037,.053,.042,.004], 'hair' if k%5 else 'hair_highlight','Head',11)
for k in range(10):
 a=(k+.6)/10*math.pi
 x=.275*math.cos(a); y=.09+.24*math.sin(a)
 line([(x*.8,y*.83,.23),(x*1.04,y+.013,.08),(x*.96,y+.058,-.13)],.006,'hair_highlight','Head')
# crown ahoge loose strand
line([(.02,-.015,.341),(.045,-.015,.425),(.005,-.015,.478),(-.06,-.012,.468)],.023,'hair_highlight','Head')
# subtle separate hair ringlets
for s in (-1,1):
 for j in range(6):
  xx=s*(.245+.032*(j%3))
  yy=-.04+.046*(j//3)
  line([(xx,yy,-.02),(xx+s*.032,yy,-.12),(xx+s*.016,yy,-.23),(xx+s*.042,yy,-.30)], .024,'hair','Head',7)
# fringe thin lines
for x in [-.21,-.13,-.04,.075,.17,.25]:
 line([(x,-.300,.285),(x+.019,-.314,.205),(x+.02,-.302,.16)],.0055,'hair_highlight','Head',6)
# enormous glossy eyes: cream sclera, colored iris, darker pupil, catchlights and eyelashes
for s in (-1,1):
 x=s*.147
 ell((x,-.270,.034),(.084,.010,.090),'white','Head',24,16)
 ell((x,-.283,.032),(.071,.009,.080),'eye_black','Head',24,16)
 ell((x,-.294,.032),(.062,.009,.073),'eye_rose','Head',24,16)
 ell((x,-.304,.005),(.051,.007,.057),'eye_pink','Head',20,12)
 ell((x,-.310,.044),(.032,.006,.043),'eye_black','Head',18,12)
 ell((x-s*.027,-.316,.066),(.017,.008,.023),'eye_shine','Head',12,8)
 ell((x+s*.027,-.315,.013),(.010,.005,.013),'eye_shine','Head',12,8)
 line([(x-s*.095,-.284,.087),(x,-.296,.118),(x+s*.093,-.282,.082)],.012,'eye_black','Head')
 for j in range(3):
  xx=x+s*(.071+.014*j)
  line([(xx,-.283,.09),(xx+s*.028,-.285,.12+j*.007)],.009,'eye_black','Head',7)
 line([(x-s*.075,-.286,-.085),(x,-.299,-.103),(x+s*.072,-.286,-.084)],.006,'skin_shade','Head')
 ell((s*.242,-.257,-.066),(.077,.011,.049),'blush','Head',15,10)
 for j in range(3):
  ell((s*(.205+j*.019),-.272,-.046-j*.003),(.008,.005,.005),'flower','Head',9,6)
 # expressive eyebrow
 line([(x-s*.07,-.283,.191),(x,-.299,.203),(x+s*.07,-.286,.193)],.008,'hair_shadow','Head')
# smiling mouth and slight nose
ell((0,-.303,-.077),(.014,.012,.009),'skin_shade','Head',12,8)
line([(-.045,-.294,-.149),(-.024,-.305,-.175),(0,-.31,-.185),(.024,-.305,-.175),(.045,-.294,-.149)],.008,'burgundy','Head')
ell((0,-.308,-.172),(.023,.006,.009),'eye_pink','Head',12,8)
# gills: 3 feather branches on each side, individually animated root + tip
for s,side in [(-1,'L'),(1,'R')]:
 for j in range(3):
  root=f'Gill_{side}_{j+1}_Root';tip=f'Gill_{side}_{j+1}_Tip';vz=.10-j*.095
  tube([(0,0,0),(s*.09,-.005,vz*.55),(s*.179,.007,vz)],[.018,.015,.010],'gill_vein',root,12)
  ell((s*.04,-.012,0),(.058,.018,.040),'gill_light',root,20,14)
  # membrane panels and scalloped petals on root
  for i in range(14):
   t=(i+.15)/14
   dx=s*(.03+t*.135);zz=vz*t
   ang=(.65 if j==0 else (-.46 if j==2 else .04))+(.12*i)
   leaf((dx,-.022,zz),.172+.015*(i%2),.047, (math.pi if s==-1 else 0)+ang, 'gill' if i%2 else 'gill_light',root)
  # tip is a child bone: fine branching feathery lamellae
  tube([(0,0,0),(s*.068,.002,.02),(s*.115,.003,.021)], [.016,.012,.001],'gill_vein',tip,10)
  for i in range(11):
   xx=s*(.012+i*.010)
   zz=.018*math.sin(i*.54)
   length=.15*(1-(i/15))
   angle=(.45 if i%2==0 else -.65)+(0 if s==1 else math.pi)
   leaf((xx,-.027,zz),length,.038,angle,'gill_light' if i%3==0 else 'gill_tip',tip,.02)
  flower(s*(.29+.05*(j%2)),-.09,.18-.11*j,.028,'Head')
# Pink cherry blossoms, dangling beads and side bows, near gill bases
for s in (-1,1):
 flower(s*.288,-.09,.265,.042,'Head')
 flower(s*.323,-.074,.135,.035,'Head')
 bow(s*.33,-.067,.145,.041,'Head','burgundy')
 for j in range(4):
  line([(s*(.29+j*.017),-.018,.15),(s*(.32+j*.020),-.017,.07),(s*(.31+j*.025),-.020,-.06-j*.012)],.003,'gold','Head')
  ell((s*(.31+j*.025),-.021,-.06-j*.012),(.008,.008,.011),'lace','Head',10,7)
# Minimal but detailed everyday gothic-kawaii outfit
# black and burgundy fitted crop top, straps and tiny front center heart
ell((0,-.015,.075),(.206,.139,.124),'black','Torso',26,16)
ell((0,-.114,.08),(.135,.030,.090),'burgundy','Torso')
for s in (-1,1):
 tube([(s*.05,-.125,.145),(s*.115,-.08,.218),(s*.18,-.005,.250)],[.012,.014,.012],'ink','Torso',9)
 tube([(s*.055,-.126,.098),(s*.125,-.119,.018)],[.007,.009],'lace','Torso')
for j in range(9):
 x=-.16+j*.04
 leaf((x,-.132,-.013),.045,.014,-math.pi/2,'lace' if j%2 else 'burgundy_light','Torso')
heart(0,-.15,.119,.038,'hotpink','Torso')
heart(0,-.155,-.01,.022,'gold','Torso')
# Waist belt and dual frilled skirt layers; scalloped hem
tube([(-.17,-.05,-.103),(0,-.16,-.12),(.17,-.05,-.103)],[.025,.022,.025],'ink','Torso')
for layer in range(2):
 ztop=-.13-layer*.08;zbot=-.26-layer*.085
 verts=[];faces=[];steps=80
 for i in range(steps):
  a=2*math.pi*i/steps; w=.015*math.sin(12*a+layer)
  for rr,zz in [(.165,ztop),(.292+layer*.025+w,zbot+.025*math.cos(10*a))]:
   verts.append((rr*math.cos(a),.91*rr*math.sin(a),zz))
 for i in range(steps):
  j=(i+1)%steps;faces.extend([(i*2,i*2+1,j*2),(i*2+1,j*2+1,j*2)])
 emit(trimesh.Trimesh(vertices=verts,faces=faces,process=False),'burgundy' if layer==0 else 'black','Torso')
 for i in range(26):
  a=2*math.pi*i/26
  rx=(.27+layer*.028)*math.cos(a);ry=(.27+layer*.028)*.91*math.sin(a)
  ell((rx,ry,zbot-.015),(.039,.018,.018),'lace' if i%3 else 'burgundy_light','Torso',10,7)
# bow at lower back
bow(0,.185,-.115,.068,'Torso','burgundy')
# Sleeves/arms: arm root parent Torso, local from clavicle y 0 to hand
for side,s in [('L',-1),('R',1)]:
 a=f'Arm_{side}'
 ell((s*.055,-.0,-.058),(.073,.080,.106),'skin',a)
 tube([(s*.055,0,-.070),(s*.092,-.02,-.17),(s*.115,-.065,-.29)],[.068,.056,.043],'skin',a,16)
 ell((s*.115,-.064,-.312),(.050,.044,.065),'skin',a)
 for k in range(4):
  xf=s*(.080+k*.024)
  tube([(xf,-.095,-.342),(xf+s*.010,-.098,-.378)], [.012,.009],'skin',a,8)
 # detached layered lace cuffs and lace-up gothic sleeves
 tube([(s*.075,-.025,-.145),(s*.094,-.04,-.20),(s*.116,-.058,-.262)],[.07,.080,.078],'black',a,16)
 ell((s*.114,-.068,-.268),(.087,.07,.028),'burgundy',a,18,10)
 for jj in range(10):
  ang=jj*2*math.pi/10
  ell((s*.115+.082*math.cos(ang),-.067+.065*math.sin(ang),-.283),(.021,.014,.027),'lace' if jj%2 else 'black',a,10,7)
 for z in (-.17,-.22):
  heart(s*.115,-.121,z,.016,'rose',a)
# short legs, black high socks, garter straps, decorated chunky boots
for side,s in [('L',-1),('R',1)]:
 name=f'Leg_{side}'
 ell((0,0,-.052),(.106,.105,.130),'skin',name)
 tube([(0,0,-.145),(0,-.012,-.26),(0,-.026,-.416)],[.083,.077,.064],'skin',name,16)
 # thigh garter strips visible between skirt and boot
 for z in (-.155,-.225):
  ell((0,0,z),(.090,.082,.017),'black',name,16,9)
  ell((0,-.083,z),(.027,.012,.013),'rose',name,10,8)
 tube([(0,-.015,-.275),(0,-.025,-.41),(0,-.035,-.55)],[.075,.072,.070],'boots',name,16)
 ell((0,-.046,-.552),(.092,.127,.106),'boots',name,20,12)
 ell((0,-.13,-.585),(.109,.151,.060),'boots',name,20,12)
 ell((0,-.132,-.625),(.113,.156,.031),'ink',name,20,10)
 for z in (-.33,-.39,-.45,-.51):
  ell((0,-.10,z),(.081,.009,.013),'bootshine',name,16,8)
  for sign in (-1,1):
   ell((sign*.036,-.105,z),(.014,.009,.013),'gold',name,8,6)
 # tiny knee adornment
 heart(0,-.094,-.17,.02,'lace',name)
# M2 seamless swimming tail: one continuous body with skin-weighted joints.
# All positions below are local to Tail_01; the rig converts the whole surface to
# a deformable single mesh. Surface spots are painted flat into the UV atlas.
path=np.array([(0,0,0),(.06,.20,-.08),(.165,.46,-.185),(.295,.74,-.225),(.445,.945,-.135)],float)
# Use piecewise Catmull-Rom interpolation: C1 continuous axial center-line.
def path_sample(t):
 u=min(3.9999,max(0,float(t)*4));k=int(u);v=u-k
 p0=path[max(0,k-1)];p1=path[k];p2=path[k+1];p3=path[min(4,k+2)]
 return .5*((2*p1)+(-p0+p2)*v+(2*p0-5*p1+4*p2-p3)*v*v+(-p0+3*p1-3*p2+p3)*v*v*v)
segments=76;sides=40;verts=[];faces=[];uv=[];fin=[];finuv=[];finfaces=[]
# Tail begins inside the hips, then widens to the fin-body section, tapering
# to a soft point. No separate circular end caps or visible segment cuts.
for i in range(segments+1):
 t=i/segments
 c=path_sample(t); tangent=path_sample(min(1,t+.002))-path_sample(max(0,t-.002));tangent/=np.linalg.norm(tangent)+1e-9
 side=np.cross(tangent,[0,0,1.]);side/=np.linalg.norm(side)+1e-9;up=np.cross(side,tangent)
 radius=(.139+.030*math.sin(t*math.pi))*(1-t**2)**.57+.005
 for k in range(sides+1):
  a=k*math.pi*2/sides
  point=c+side*(radius*math.cos(a))+up*(radius*.72*math.sin(a))
  verts.append(point);uv.append((t,k/sides))
 # Flexible translucent dorsal fin follows the whole body and tapers naturally.
 rise=(.030+.19*math.sin(math.pi*t)**1.2)*(1-.65*t)
 fin.append(c+up*radius*.71);fin.append(c+up*(radius*.71+rise)+side*(.012*math.sin(t*8*math.pi)))
 finuv.extend([(t,0),(t,1)])
for i in range(segments):
 for k in range(sides):
  a=i*(sides+1)+k;b=(i+1)*(sides+1)+k
  faces.extend([(a,b,a+1),(a+1,b,b+1)])
 i2=i*2;finfaces.extend([(i2,i2+2,i2+1),(i2+1,i2+2,i2+3)])
tail=trimesh.Trimesh(vertices=np.array(verts),faces=faces,process=False)
# Albedo texture is a real image: mottling, round axolotl spots, and delicate
# fin-scale freckles baked into a consistent UV surface, not raised balls.
from PIL import Image as PilImage,ImageDraw as PilDraw,ImageFilter as PilFilter
rng=np.random.default_rng(15491);tex=PilImage.new('RGB',(1024,512),(247,184,199));td=PilDraw.Draw(tex,'RGBA')
for i in range(190):
 u=float(rng.uniform(.025,.975));v=float(rng.uniform(.06,.94))
 radius=float(rng.uniform(2.8,11.5))*(.9 if u<.75 else .55)
 x=u*1024;y=v*512
 td.ellipse((x-radius*1.4,y-radius*.8,x+radius*1.4,y+radius*.8),fill=(208,97,142,int(rng.uniform(28,98))))
for i in range(80):
 u=float(rng.uniform(.04,.95));v=float(rng.uniform(.12,.88));r=rng.uniform(1.5,4)
 x=u*1024;y=v*512;td.ellipse((x-r,y-r,x+r,y+r),fill=(255,233,239,85))
tex=tex.filter(PilFilter.GaussianBlur(.9))
# Keep tail texture on material exported as baseColorTexture (PNG embedded in GLB).
TAIL_TEX=tex
emit(tail,'tail','Tail_01')
finmesh=trimesh.Trimesh(vertices=np.array(fin),faces=finfaces,process=False)
emit(finmesh,'tail_fin','Tail_01')
TAIL_UVS=np.asarray(uv,float)
TAIL_FIN_UVS=np.asarray(finuv,float)
# mesh grouping and node hierarchy
MAT={}
for name,col in C.items():
 mat=trimesh.visual.material.PBRMaterial(name=name,baseColorFactor=rgba(col),metallicFactor=.02,
      roughnessFactor=.57 if name!='eye_shine' else .10,doubleSided=True)
 MAT[name]=mat
scene=trimesh.Scene()
# Ensure graph has all transform nodes first, and preserve chain hierarchy.
for name,rec in NODE.items():
 if name=='Kaiyu_Root':scene.graph.update(frame_to=name,frame_from='world',matrix=np.eye(4));continue
 tr=np.eye(4);tr[:3,3]=rec['pos'];scene.graph.update(frame_to=name,frame_from=rec['parent'],matrix=tr)
for (parent,mat),ms in GROUP.items():
 m=trimesh.util.concatenate(ms) if len(ms)>1 else ms[0]
 m.visual=trimesh.visual.TextureVisuals(material=MAT[mat])
 if parent=='Tail_01' and mat=='tail':
  from PIL import Image as PilImage
  m.visual=trimesh.visual.TextureVisuals(uv=TAIL_UVS,material=trimesh.visual.material.PBRMaterial(name='axolotl_spotted_tail',baseColorTexture=TAIL_TEX,metallicFactor=.0,roughnessFactor=.52,doubleSided=True))
 elif parent=='Tail_01' and mat=='tail_fin':
  m.visual=trimesh.visual.TextureVisuals(uv=TAIL_FIN_UVS,material=trimesh.visual.material.PBRMaterial(name='semi_translucent_dorsal_fin',baseColorFactor=(255,162,190,178),alphaMode='BLEND',metallicFactor=.0,roughnessFactor=.42,doubleSided=True))
 scene.add_geometry(m,geom_name=f'{parent}_{mat}',node_name=f'{parent}_{mat}_Geometry',parent_node_name=parent)
# Save source mesh GLB and embed looping procedural transform animations in GLB JSON/BIN.
raw=scene.export(file_type='glb')

def unpack_glb(blob):
 magic,version,total=struct.unpack_from('<4sII',blob,0)
 assert magic==b'glTF' and version==2 and total==len(blob)
 chunks=[];p=12
 while p<len(blob):
  n,tag=struct.unpack_from('<I4s',blob,p);p+=8;chunks.append((tag,blob[p:p+n]));p+=n
 dic=json.loads(next(c for tag,c in chunks if tag==b'JSON').decode());binbuf=next((c for tag,c in chunks if tag==b'BIN\x00'),b'')
 return dic,bytearray(binbuf)
def write_glb(j,b):
 jb=json.dumps(j,ensure_ascii=False,separators=(',',':')).encode();jb+=b' ' *((4-len(jb)%4)%4)
 bb=bytes(b);bb+=b'\x00'*((4-len(bb)%4)%4)
 return struct.pack('<4sII',b'glTF',2,12+8+len(jb)+8+len(bb))+struct.pack('<I4s',len(jb),b'JSON')+jb+struct.pack('<I4s',len(bb),b'BIN\x00')+bb
j,b=unpack_glb(raw);i_by_name={n.get('name',''):i for i,n in enumerate(j['nodes'])}
animated={n:k for n,k in NODE.items() if n in i_by_name and (n.startswith('Tail_') or n.startswith('Gill_') or n.startswith('Hair_'))}
# User-visible metadata with exact names for a game engine to drive spring bones.
RIG={'units':'meters','up':'Z','forward':'-Y','version':'0.1.0-prototype','name':'Kaiyu','species':'Axolotl humanoid',
     'source':'1021.jpg turnaround reference','joint_nodes':list(animated.keys()),
     'animation':'idle_secondary_motion','notes':'Transform-joint rig (no skin weights yet). For skinning, transfer to Blender armature and retopologize. All accessory meshes are separated into material geometry nodes.',
     'suggested_springs':{'gills':{'frequency_hz':3.2,'damping_ratio':.35,'limit_degrees':16},'tail':{'frequency_hz':1.5,'damping_ratio':.40,'limit_degrees':25},'hair':{'frequency_hz':2.6,'damping_ratio':.46,'limit_degrees':13}},
     'reference_match_features':['chibi face and oversized eyes','short dark-brown bob with pink fringe','three bilateral pink external axolotl gill structures','thick spotted pink finned tail','gothic-kawaii layered outfit','flowers, bows, hearts, platform boots','individual tail/gill/hair pivots']}
# Add one animation that affects node rotations. Preserve rest translation on nodes.
# glTF animation requires TRS instead of matrix for each animated node.
frames=49;dur=2.4;ticks=np.linspace(0,dur,frames,dtype='<f4')
# Append tightly packed binary buffers with accessors/bufferViews

def append_accessor(data,typ,components,comp_type=5126):
 global b
 arr=np.asarray(data,dtype='<f4')
 while len(b)%4:b.append(0)
 offset=len(b);buf=arr.tobytes();b.extend(buf)
 view=len(j.setdefault('bufferViews',[]));j['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(buf)})
 acc=len(j.setdefault('accessors',[]));q={'bufferView':view,'componentType':comp_type,'count':len(arr),'type':typ}
 if typ=='SCALAR':q.update(min=[float(arr.min())],max=[float(arr.max())])
 j['accessors'].append(q);return acc
input_acc=append_accessor(ticks,'SCALAR',1)
channels=[];samplers=[]
for name in animated:
 idx=i_by_name[name];nd=j['nodes'][idx]
 if 'matrix' in nd:
  m=np.array(nd.pop('matrix')).reshape((4,4),order='F')
  nd['translation']=[float(v) for v in m[:3,3]]
  nd['rotation']=[float(v) for v in R.from_matrix(m[:3,:3]).as_quat()]
  nd['scale']=[1,1,1]
 orig=R.from_quat(nd.get('rotation',[0,0,0,1]))
 v=[]
 for t in ticks:
  phase=float(t)/dur*2*math.pi
  if name.startswith('Tail_'):
   depth=int(name[-2:]);amp=.06+.024*depth
   rot=R.from_euler('zy',[amp*math.sin(phase-depth*.55),.03*math.sin(phase*2-depth*.42)])
  elif name.startswith('Gill_'):
   key=int(name.split('_')[2])-1
   sign=(-1 if '_L_' in name else 1);tip='Tip' in name
   rot=R.from_euler('y',sign*(.045+.018*key)*(1.9 if tip else 1)*math.sin(phase*2.0+key*.45))
  else:
   sign=-1 if '_L_' in name else 1
   rot=R.from_euler('x',.065*math.sin(phase*2+sign+.3*int(name[-1])))
  v.append((orig*rot).as_quat())
 acc=append_accessor(np.array(v,dtype='<f4'),'VEC4',4)
 si=len(samplers);samplers.append({'input':input_acc,'output':acc,'interpolation':'LINEAR'})
 channels.append({'sampler':si,'target':{'node':idx,'path':'rotation'}})
j['animations']=[{'name':'Kaiyu_Idle_Bouncy_Gills_Tail_Hair','samplers':samplers,'channels':channels}]
j['buffers'][0]['byteLength']=len(b)
j.setdefault('asset',{}).setdefault('extras',{}).update({'character':'Kaiyu','iteration':'0.1.0','reference':'1021.jpg'})
model=write_glb(j,b)
glbpath=os.path.join(OUT,'kaiyu_axolotl_prototype.glb')
open(glbpath,'wb').write(model)
with open(os.path.join(OUT,'kaiyu_rig.json'),'w') as f:json.dump(RIG,f,indent=2)
# QA structural validations
jx,bx=unpack_glb(model)
assert len(jx['animations'][0]['channels'])==len(animated)
assert len(jx['animations'][0]['channels'])>=20
for anim in jx['animations']:
 for c in anim['channels']:
  assert c['target']['path']=='rotation'
assert all(x['bufferView']<len(jx['bufferViews']) for x in jx['accessors'] if 'bufferView' in x)
print('GLB',len(model),'meshes',len(jx.get('meshes',[])),'nodes',len(jx['nodes']), 'animation channels',len(channels), 'triangles',sum(len(m.faces) for ms in GROUP.values() for m in ms))
# Use VTK to create tri-view preview from local source mesh (not claimed a gameplay screenshot).
try:
 if os.environ.get('KAIYU_ENABLE_VTK_PREVIEW','')!='1':
  raise RuntimeError('headless preview disabled; use VQ inspection views')
 import vtk
 from vtk.util.numpy_support import numpy_to_vtk
 from PIL import Image as PILImage
 views=[('FRONT',(1.0,-5.65,2.58)),('SIDE',(5.7,-.15,2.50)),('BACK',(.05,5.65,2.48))]
 imgs=[]
 for label,pos in views:
  ren=vtk.vtkRenderer();ren.SetBackground(.090,.071,.10)
  rw=vtk.vtkRenderWindow();rw.SetOffScreenRendering(1);rw.SetSize(520,650);rw.AddRenderer(ren);rw.SetMultiSamples(4)
  for (parent,mat),ms in GROUP.items():
   m=trimesh.util.concatenate(ms) if len(ms)>1 else ms[0]
   T=scene.graph.get(parent)[0];xyz=trimesh.transform_points(m.vertices,T)
   poly=vtk.vtkPolyData();points=vtk.vtkPoints();points.SetData(numpy_to_vtk(np.ascontiguousarray(xyz),deep=True))
   poly.SetPoints(points)
   cells=vtk.vtkCellArray()
   for face in m.faces:
    tri=vtk.vtkTriangle()
    for k in range(3):tri.GetPointIds().SetId(k,int(face[k]))
    cells.InsertNextCell(tri)
   poly.SetPolys(cells)
   norm=vtk.vtkPolyDataNormals();norm.SetInputData(poly);norm.SetSplitting(False);norm.ConsistencyOn();norm.AutoOrientNormalsOff();norm.Update()
   mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(norm.GetOutputPort())
   actor=vtk.vtkActor();actor.SetMapper(mapper);hexcol=C[mat].lstrip('#');r,g,bv=[int(hexcol[i:i+2],16)/255 for i in (0,2,4)]
   actor.GetProperty().SetColor(r,g,bv);actor.GetProperty().SetInterpolationToPhong();actor.GetProperty().SetAmbient(.40);actor.GetProperty().SetDiffuse(.68);actor.GetProperty().SetSpecular(.13)
   ren.AddActor(actor)
  ren.SetUseFXAA(False)
  light=vtk.vtkLight();light.SetPosition(-3,-7,8);light.SetIntensity(1.0);ren.AddLight(light)
  fill=vtk.vtkLight();fill.SetPosition(3,5,6);fill.SetIntensity(.72);ren.AddLight(fill)
  camera=ren.GetActiveCamera();camera.SetPosition(*pos);camera.SetFocalPoint(0,.26,.92);camera.SetViewUp(0,0,1);camera.SetViewAngle(24);ren.ResetCameraClippingRange()
  rw.Render();win=vtk.vtkWindowToImageFilter();win.SetInput(rw);win.SetInputBufferTypeToRGB();win.ReadFrontBufferOff();win.Update()
  writer=vtk.vtkPNGWriter();writer.SetInputConnection(win.GetOutputPort());path=os.path.join(OUT,'kaiyu_'+label.lower()+'.png');writer.SetFileName(path);writer.Write()
  img=PILImage.open(path).convert('RGB');imgs.append(img)
 sheet=PILImage.new('RGB',(520*3,690),(23,17,27));d=ImageDraw.Draw(sheet)
 for i,im in enumerate(imgs):sheet.paste(im,(520*i,36));d.text((520*i+15,10),f'{views[i][0]} — Kaiyu v0.1 3D prototype',fill='#FFC0D0')
 sheet.save(os.path.join(OUT,'kaiyu_three_view.png'))
 print('PREVIEWS_OK',os.path.join(OUT,'kaiyu_three_view.png'))
except Exception as ex:print('PREVIEW_ERROR',type(ex).__name__,str(ex)[:300])