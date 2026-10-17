#!/usr/bin/env python3
"""VQ Anatomy Milestone A1 — original continuous character surface construction.

This is a deterministic parametric geometry engine, NOT trained anatomical AI,
production retopology or reference-likeness validation. X right, Y up, -Z front.
Preserves VEILFORGE's Mesh + glTF export layer and review-before-promotion model.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import json,math,hashlib,sys
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage.measure import marching_cubes
from PIL import Image
from factory import Mesh,MATERIALS,export_gltf,export_obj
from vq_distal_anatomy import add_face, add_hand, add_foot

@dataclass(frozen=True)
class ShapeSpec:
    name: str
    species: str = 'human'
    height: float = 1.72
    head_ratio: float = .149         # head length / height
    shoulder_ratio: float = .133     # shoulder width / height (single shoulder extent)
    hip_ratio: float = .125
    leg_ratio: float = .495
    arm_ratio: float = .365
    face_width: float = 1.0
    jaw_strength: float = 1.0
    eye_scale: float = 1.0
    garment: str = 'tunic'
    palette: str = 'rose'
    seed: int = 19
    def validate(self):
        if self.species not in ('human','elf','orc','axolotl','feline','dwarf','automaton'):
            raise ValueError('Unsupported species without reviewed anatomy recipe')
        ranges={'height':(.85,2.5),'head_ratio':(.105,.245),'shoulder_ratio':(.105,.345),
                'hip_ratio':(.095,.25),'leg_ratio':(.36,.60),'arm_ratio':(.27,.52),
                'face_width':(.78,1.25),'jaw_strength':(.70,1.4),'eye_scale':(.65,1.65)}
        for n,(lo,hi) in ranges.items():
            v=getattr(self,n)
            if not isinstance(v,(float,int)) or not math.isfinite(v) or not lo<=v<=hi:
                raise ValueError(f'Invalid anatomy parameter {n}')
        if self.garment not in ('tunic','bodysuit','robes') or self.palette not in ('rose','earth','teal','metal'):
            raise ValueError('Unknown outfit/material')
        if not isinstance(self.seed,int) or not 0<=self.seed<2**31:raise ValueError('Invalid seed')
        if not self.name or not self.name.replace('_','').isalnum():raise ValueError('Unsafe name')
        return self

def parse_description(text,*,seed=19):
    """Explicit finite vocabulary, not a claim of unrestricted prompt comprehension.
    Unknown anatomy words are flagged as clarification needs for the later AI app.
    """
    s=' '.join(text.lower().replace('-',' ').split())
    species=next((f for f in ('axolotl','automaton','feline','orc','dwarf','elf','human') if f in s),'human')
    kw={'axolotl':(.212,.145,.128,.435),'dwarf':(.169,.156,.151,.415),
        'orc':(.142,.166,.146,.486),'elf':(.141,.124,.113,.523),
        'feline':(.158,.130,.122,.508),'automaton':(.144,.147,.129,.510),
        'human':(.149,.133,.125,.502)}
    hr,sr,hip,leg=kw[species]
    if 'chibi' in s:hr=min(.235,hr*1.38);leg=max(.37,leg*.84)
    if 'broad shoulder' in s or 'muscular' in s:sr=min(.34,sr*1.20)
    if 'slender' in s:sr*=.91;hip*=.93
    if 'long legs' in s:leg=min(.59,leg*1.08)
    if 'short legs' in s:leg=max(.36,leg*.87)
    if 'large eyes' in s:eyes=1.35
    else:eyes=1.0
    garment='robes' if 'robes' in s or 'robe' in s else ('bodysuit' if 'bodysuit' in s else 'tunic')
    palette='metal' if species=='automaton' else ('teal' if 'teal' in s else ('earth' if 'earth' in s else 'rose'))
    return ShapeSpec(name='vq_'+species+'_'+str(seed),species=species,head_ratio=hr,
      shoulder_ratio=sr,hip_ratio=hip,leg_ratio=leg,garment=garment,
      palette=palette,seed=seed,eye_scale=eyes).validate()

def _smooth_union(a,b,k):
    if k<=0:return np.minimum(a,b)
    h=np.clip(.5+.5*(b-a)/k,0.,1.)
    return b*(1-h)+a*h-k*h*(1-h)

def _ell(X,Y,Z,c,r):
    q=np.sqrt(((X-c[0])/r[0])**2+((Y-c[1])/r[1])**2+((Z-c[2])/r[2])**2)
    return (q-1)*min(r)

def _capsule(X,Y,Z,a,b,r0,r1):
    a=np.array(a);b=np.array(b); v=b-a
    t=np.clip(((X-a[0])*v[0]+(Y-a[1])*v[1]+(Z-a[2])*v[2])/sum(v*v),0.,1.)
    d=np.sqrt((X-(a[0]+v[0]*t))**2+(Y-(a[1]+v[1]*t))**2+(Z-(a[2]+v[2]*t))**2)
    return d-(r0+(r1-r0)*t)

def anatomy_anchors(spec):
    h=spec.height; leg=spec.leg_ratio*h; head_len=spec.head_ratio*h
    head_center=h-head_len*.51;neck=head_center-head_len*.90
    hip_y=leg*.94; shoulder_y=hip_y+(neck-hip_y)*.948
    shoulders=spec.shoulder_ratio*h;hips=spec.hip_ratio*h
    arm_len=spec.arm_ratio*h
    elbows=[(s*(shoulders+.37*arm_len),shoulder_y-.15*arm_len,0) for s in (-1,1)]
    wrists=[(s*(shoulders+.82*arm_len),shoulder_y-.26*arm_len,-.01*h) for s in (-1,1)]
    return {'height':h,'head_len':head_len,'head_center':head_center,'neck':neck,'hips':hips,
      'shoulders':shoulders,'shoulder_y':shoulder_y,'hip_y':hip_y,
      'knees':[(s*hips*.78,leg*.49,-.03*h) for s in (-1,1)],
      'ankles':[(s*hips*.82,.10*h,0) for s in (-1,1)],
      'elbows':elbows,'wrists':wrists,
      'eyes':[(s*head_len*.23,head_center+.08*head_len,-head_len*.39) for s in (-1,1)],
      'jaw':(0,head_center-.30*head_len,-head_len*.22),
      'mouth':(0,head_center-.28*head_len,-head_len*.435)}

def sdf_body(spec,voxel=.016):
    a=anatomy_anchors(spec);h=spec.height
    half=max(abs(v[0]) for v in a['wrists'])+.20*h
    xx=np.arange(-half,half+voxel*.5,voxel,dtype=np.float32)
    yy=np.arange(-.05*h,h+.07*h,voxel,dtype=np.float32)
    zz=np.arange(-.33*h,.28*h,voxel,dtype=np.float32)
    X=xx[:,None,None];Y=yy[None,:,None];Z=zz[None,None,:]
    field=np.full((len(xx),len(yy),len(zz)),5.0,dtype=np.float32)
    def add(f,k):
        nonlocal field
        field=_smooth_union(field,f,k).astype(np.float32,copy=False)
    shoulder=a['shoulders'];hips=a['hips']; hip_y=a['hip_y']; sy=a['shoulder_y'];yc=a['head_center'];r=a['head_len'];neck=a['neck']
    add(_ell(X,Y,Z,(0,(sy+hip_y)*.5,0),(shoulder*.96,(sy-hip_y)*.64,.097*h)),.035*h)
    add(_ell(X,Y,Z,(0,hip_y+.04*h,.013*h),(hips*.88,.125*h,.10*h)),.030*h)
    add(_capsule(X,Y,Z,(0,sy-.010*h,0),(0,yc-r*.31,0),.045*h,.045*h),.024*h)
    # Face, chin, cheek mass and nose are blended as a single continuous surface.
    add(_ell(X,Y,Z,(0,yc,.005*h),(r*.39*spec.face_width,r*.52,r*.38)),.017*h)
    add(_ell(X,Y,Z,(0,yc-r*.26,-r*.06),(r*.33*spec.face_width*spec.jaw_strength,r*.26,r*.30)),.016*h)
    for side in (-1,1):
        add(_ell(X,Y,Z,(side*r*.22,yc-r*.12,-r*.20),(r*.17,r*.13,r*.12)),.015*h)
    add(_ell(X,Y,Z,(0,yc-r*.17,-r*.36),(r*.083,r*.19,r*.11)),.009*h)
    # A3 anatomical planes: frontal brow, jaw, lips, ears and nose.
    add_face(lambda f,k: add(f,k),lambda c,r: _ell(X,Y,Z,c,r),h,r,yc,spec.face_width,spec.jaw_strength)
    distal={"hands":[],"feet":[]}
    # Sculpt joints out of one SDF so disconnected cylinder seams cannot occur.
    for i,s in enumerate((-1,1)):
        p=(s*shoulder*.46,sy-.055*h,0);el=a['elbows'][i];wr=a['wrists'][i]
        add(_ell(X,Y,Z,(s*shoulder*.40,sy-.065*h,0),(shoulder*.44,.092*h,.093*h)),.038*h)
        add(_capsule(X,Y,Z,p,el,.058*h,.043*h),.024*h)
        add(_capsule(X,Y,Z,el,wr,.043*h,.027*h),.018*h)
        distal['hands'].append(add_hand(add,lambda c,r: _ell(X,Y,Z,c,r),
            lambda a,b,r0,r1: _capsule(X,Y,Z,a,b,r0,r1), wr,s,h))
        top=(s*hips*.75,hip_y+.01*h,0); knee=a['knees'][i];ankle=a['ankles'][i]
        add(_capsule(X,Y,Z,top,knee,.079*h,.053*h),.024*h)
        add(_capsule(X,Y,Z,knee,ankle,.053*h,.029*h),.020*h)
        distal['feet'].append(add_foot(add,lambda c,r: _ell(X,Y,Z,c,r),
            lambda a,b,r0,r1: _capsule(X,Y,Z,a,b,r0,r1),ankle,s,h))
    # marching cubes isosurface, smooth enough to be seen from any camera.
    vertices,faces,normals,_=marching_cubes(field,level=0,spacing=(voxel,voxel,voxel),allow_degenerate=False)
    vertices+=np.array([xx[0],yy[0],zz[0]],np.float32)
    # Perturb only numerically collapsed marching-cubes slivers, preserving
    # connectivity instead of discarding faces and introducing T-junctions.
    # This is a bounded numerical repair, not a perceptual sculpting operation.
    for attempt in range(7):
        v0=vertices[faces[:,0]];v1=vertices[faces[:,1]];v2=vertices[faces[:,2]]
        area=np.linalg.norm(np.cross(v1-v0,v2-v0),axis=1)*.5
        tiny=np.flatnonzero(area<1e-11)
        if not len(tiny):break
        for fi in tiny:
            vi=int(faces[fi,2]);e1=vertices[faces[fi,1]]-vertices[faces[fi,0]]
            trial=np.cross(e1,np.array([.347,.813,.211],np.float32))
            trial=trial/(np.linalg.norm(trial)+1e-20)
            vertices[vi]+=trial*(.00018*(attempt+1))
    # Marching cubes can introduce tiny isolated islands at fingertip scale.
    # Discard only negligible <32-face closed islands, never disconnected limbs.
    import trimesh
    raw=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
    components=raw.split(only_watertight=False)
    islands=[m for m in components if len(m.faces)<32]
    if islands:
        kept=[m for m in components if len(m.faces)>=32]
        if not kept:raise ValueError('Anatomy surface contains only fragments')
        raw=trimesh.util.concatenate(kept)
    a['distal_landmarks']=distal
    a['discarded_island_faces']=int(sum(len(m.faces) for m in islands))
    a['discarded_island_count']=len(islands)
    return np.asarray(raw.vertices,np.float32),np.asarray(raw.faces,np.int32),normals,a

def _taper(mesh,p,rad,material,n=14):
    # Build via the engine's sweep geometry (VQ factory), not a reused asset.
    p0,p1,p2=p
    nvec=np.array(p2)-p0
    # curve lofting via existing VQ Mesh.sweep in vertical direction is inappropriate
    # for arbitrary tangents, so this calls the saved generic VQ R1 curve recipe.
    from vq_character_techniques import tapered_curve
    tapered_curve(mesh,p,rad,material,sides=n,steps=4,aspect=.85)

def _ellipsoid(mesh,center,rad,material,detail=14):
    # VQ's existing geometric construction API
    mesh.ellipsoid(tuple(center),tuple(rad),material,lat=detail,lon=detail*2,seed=13)

def build_accessories(mesh,spec,anchors):
    h=spec.height;r=anchors['head_len'];yc=anchors['head_center'];hip=anchors['hip_y'];sy=anchors['shoulder_y']
    # Face features: bony brow planes, flatter eye shapes and actual nose bridge.
    for side in (-1,1):
        x=side*r*.23
        ey=(yc+r*.07);fz=-r*.364
        _ellipsoid(mesh,(x,ey,fz),(r*.073*spec.eye_scale,r*.052*spec.eye_scale,r*.024),'sclera',16)
        _ellipsoid(mesh,(x,ey-.002*h,fz-r*.034),(r*.038*spec.eye_scale,r*.042*spec.eye_scale,r*.017),'iris',14)
        _ellipsoid(mesh,(x,ey-.002*h,fz-r*.05),(r*.020,r*.029,r*.008),'pupil',12)
        _taper(mesh,[(x-side*r*.125,ey+r*.14,fz+r*.044),(x,ey+r*.16,fz+r*.01),(x+side*r*.13,ey+r*.11,fz+r*.035)],[r*.012,r*.014,r*.006],'hair',8)
    _taper(mesh,[(-r*.14,yc-r*.285,-r*.385),(0,yc-r*.316,-r*.42),(r*.14,yc-r*.285,-r*.385)],[r*.007,r*.013,r*.007],'lip',10)
    # Salon: hair cap plus separate tapered large locks, not segmented cylinders.
    _ellipsoid(mesh,(0,yc+r*.34,r*.095),(r*.409,r*.20,r*.397),'hair',16)
    for j in range(9):
        x=(j-4)*r*.077
        _taper(mesh,[(x*.8,yc+r*.42,-r*.24),(x,yc+r*.24,-r*.372),(x+.007*h*math.sin(j),yc+r*(.055 if j%2 else .12),-r*.393)],
               [r*.045,r*.038,r*.005],'hair',10)
    # garment construction as free-form loft with actual curvature and trim
    ns=48
    if spec.garment=='robes':
        rings=[(0,hip-.23*h,.015*h,anchors['hips']*1.25,.118*h),(0,hip-.05*h,0,anchors['hips']*.92,.109*h),
               (0,sy-.11*h,0,anchors['shoulders']*.80,.115*h),(0,sy+.012*h,0,anchors['shoulders']*.62,.092*h)]
    else:
        rings=[(0,hip-.045*h,0,anchors['hips']*.91,.110*h),(0,hip+.085*h,0,anchors['hips']*.82,.104*h),
               (0,sy-.10*h,0,anchors['shoulders']*.82,.121*h),(0,sy+.012*h,0,anchors['shoulders']*.64,.091*h)]
    rings=[(cx,y,cz,rx*1.12,rz+.026*h) for cx,y,cz,rx,rz in rings]
    # A2 silhouette-guided garment: interpolate smoothly between designed rings.
    # The old 4-ring cloth was a strongly faceted box even at high triangle counts.
    from scipy.interpolate import PchipInterpolator
    control=np.asarray(rings,dtype=float)
    ygrid=np.linspace(control[0,1],control[-1,1],21)
    rings=[tuple(float(y) if k==1 else float(PchipInterpolator(control[:,1],control[:,k])(y))
            for k in range(5)) for y in ygrid]
    if spec.garment!='bodysuit':
        mesh.sweep(rings,'cloth',sides=ns,cap=True)
        mid=rings[0][1]
        pts=[(rings[0][3]*math.cos(2*math.pi*i/ns),mid+.010*h*math.cos(i*math.pi/3),
              rings[0][4]*math.sin(2*math.pi*i/ns)) for i in range(ns+1)]
        from vq_character_techniques import tapered_curve
        tapered_curve(mesh,pts,[.0055*h]*(ns+1),'trim',sides=6,steps=1,caps=False)
    else:
        mesh.sweep(rings,'cloth',sides=ns,cap=True)
    # species morphology: more meaningful outline changes rather than color variations.
    if spec.species in ('elf','feline','orc','axolotl'):
        for side in (-1,1):
            if spec.species=='elf':
                _taper(mesh,[(side*r*.35,yc+r*.06,0),(side*r*.57,yc+r*.12,0),(side*r*.82,yc+r*.40,.01*h)],
                        [r*.12,r*.08,r*.005],'appendage',12)
            elif spec.species=='feline':
                _taper(mesh,[(side*r*.25,yc+r*.48,0),(side*r*.35,yc+r*.97,0),(side*r*.60,yc+r*.67,0)],
                        [r*.16,r*.12,r*.006],'appendage',12)
                _taper(mesh,[(side*.04*h,hip-.04*h,.06*h),(side*.11*h,hip-.24*h,.18*h),(side*.27*h,hip-.38*h,.23*h)],
                        [.038*h,.031*h,.003*h],'appendage',12)
            elif spec.species=='orc':
                _taper(mesh,[(side*r*.14,yc-r*.31,-r*.33),(side*r*.18,yc-r*.08,-r*.40),(side*r*.26,yc+r*.035,-r*.38)],
                        [r*.09,r*.055,r*.005],'sclera',10)
            elif spec.species=='axolotl':
                for j in range(3):
                    by=yc+r*(.38-.32*j)
                    _taper(mesh,[(side*r*.34,by,.02*h),(side*r*.62,by+r*(.24-.12*j),.01*h),
                                 (side*r*.91,by+r*(.28-.18*j),0)],
                           [r*.08,r*.09,r*.005],'frill',12)
        if spec.species=='axolotl':
            _taper(mesh,[(0,hip-.05*h,.06*h),(.06*h,hip-.14*h,.19*h),(.15*h,hip-.27*h,.33*h)],
                   [.09*h,.065*h,.004*h],'frill',18)
    return mesh

PALETTES={
 'rose':{'skin':'#e2ad9e','sclera':'#ffeadc','iris':'#768e9f','pupil':'#251b29','hair':'#392d37','lip':'#a45d65','cloth':'#503747','trim':'#c78ca2','frill':'#e897aa','appendage':'#e2ad9e'},
 'earth':{'skin':'#b78869','sclera':'#fff4e8','iris':'#73846e','pupil':'#252325','hair':'#322821','lip':'#86494d','cloth':'#3b5142','trim':'#d9b78e','frill':'#ae9276','appendage':'#b78869'},
 'teal':{'skin':'#e7b3b6','sclera':'#fff4ec','iris':'#377c84','pupil':'#1e2831','hair':'#26363c','lip':'#a45d83','cloth':'#265769','trim':'#d6ad9b','frill':'#eea7ba','appendage':'#e7b3b6'},
 'metal':{'skin':'#9da8b5','sclera':'#dae5ef','iris':'#66dae0','pupil':'#11232b','hair':'#34404f','lip':'#536675','cloth':'#46515c','trim':'#c7a472','frill':'#c3d4dc','appendage':'#9da8b5'}}

def configure_materials(spec):
    for key,hx in PALETTES[spec.palette].items():
        c=[int(hx[i:i+2],16)/255 for i in (1,3,5)]
        metal=.80 if spec.species=='automaton' and key in ('skin','hair','trim') else (.45 if key=='trim' else 0.)
        rough=.39 if metal>.6 else (.52 if key in ('skin','lip') else .72)
        MATERIALS[key]={'base':c+[1.],'metallic':metal,'roughness':rough}

def bake_material_maps(spec,out,size=128):
    """M5-compatible deterministic tiling material maps, NOT photographic PBR baking."""
    rng=np.random.default_rng(spec.seed)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    maps={};reports={}
    for name in ('skin','sclera','iris','pupil','hair','lip','cloth','trim','frill','appendage'):
        d=out/name;d.mkdir(exist_ok=True)
        m=MATERIALS[name];base=np.array(m['base'][:3]);noise=rng.normal(0,.021,(size,size)).astype(np.float32)
        noise=(gaussian_filter(noise,1.15)+noise*.30)
        albedo=np.clip((base[None,None,:]+noise[:,:,None])*255,0,255).astype(np.uint8)
        mr=np.zeros((size,size,3),dtype=np.uint8);mr[:,:,0]=255
        mr[:,:,1]=np.clip(m['roughness']*255+noise*80,0,255).astype(np.uint8)
        mr[:,:,2]=int(round(m['metallic']*255))
        gy,gx=np.gradient(noise)
        bump=np.stack([-gx*2.3,-gy*2.3,np.ones_like(gx)],axis=-1)
        bump/=np.maximum(np.linalg.norm(bump,axis=2,keepdims=True),1e-8)
        normal=np.clip((bump*.5+.5)*255,0,255).astype(np.uint8)
        ao=np.full((size,size),244,np.uint8)
        for fn,arr in (('albedo.png',albedo),('metallic_roughness.png',mr),('normal.png',normal),('ao.png',ao)):
            Image.fromarray(arr).save(d/fn)
        maps[name]={kind:f'textures/{name}/{fn}' for kind,fn in
            (('albedo','albedo.png'),('metallic_roughness','metallic_roughness.png'),('normal','normal.png'),('ao','ao.png'))}
        reports[name]={kind:hashlib.sha256((d/fn).read_bytes()).hexdigest() for kind,fn in
            (('albedo','albedo.png'),('metallic_roughness','metallic_roughness.png'),('normal','normal.png'),('ao','ao.png'))}
    return maps,reports

def build(spec,root,voxel=.016,texture_size=128):
    spec.validate();root=Path(root);root.mkdir(parents=True,exist_ok=True)
    configure_materials(spec)
    vertices,faces,normals,anchors=sdf_body(spec,voxel)
    mesh=Mesh()
    for ids in faces:
        p=vertices[ids]
        # marching cubes emits a consistent facing winding; Mesh.tri recomputes normals
        mesh.tri(tuple(map(float,p[0])),tuple(map(float,p[1])),tuple(map(float,p[2])),'skin')
    build_accessories(mesh,spec,anchors)
    obj=root/(spec.name+'.obj');export_obj(mesh,obj)
    maps,baked=bake_material_maps(spec,root/'textures',texture_size)
    dst=root/(spec.name+'.gltf')
    document=export_gltf(mesh,dst,{'id':spec.name,'category':'characters','detail':'standard','seed':spec.seed},material_maps=maps)
    try:
        import trimesh
        scene=trimesh.load(dst,force='scene',process=False)
        # The legacy factory intentionally splits triangle corners on flat normals
        # and UV seams. Replace only the SDF body's split skin primitive with
        # its original indexed watertight isosurface; keep VQ-authored accessories.
        for key,geom in list(scene.geometry.items()):
            if getattr(getattr(geom.visual,'material',None),'name','')=='skin':
                scene.delete_geometry(key)
        # Smooth shading across contiguous garment/skin-like material regions.
        for part in scene.geometry.values():
            pname=getattr(getattr(part.visual,'material',None),'name','')
            if pname in ('cloth','hair','frill','appendage'):
                part.merge_vertices()
                _=part.vertex_normals
        continuous=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
        material=MATERIALS['skin']
        continuous.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
            name='skin',baseColorFactor=tuple(int(v*255) for v in material['base']),
            metallicFactor=material['metallic'],roughnessFactor=material['roughness']))
        scene.add_geometry(continuous,geom_name='continuous_skin_surface')
        blob=scene.export(file_type='glb')
        (root/(spec.name+'.glb')).write_bytes(blob)
        glb_check=trimesh.load(root/(spec.name+'.glb'),force='scene')
        tri_glb=sum(len(g.faces) for g in glb_check.geometry.values())
        assert tri_glb==mesh.triangle_count,(tri_glb,mesh.triangle_count)
    except Exception as e:
        raise RuntimeError('GLB export/reimport failed') from e
    return {'spec':asdict(spec),'mesh':mesh,'obj':str(obj),'gltf':str(dst),'glb':str(root/(spec.name+'.glb')),
            'triangle_count':mesh.triangle_count,'body_faces':len(faces),'source_vertices':len(vertices),
            'gltf_vertex_count':document['extras']['indexed_vertices'],
            'glb_faces_reimported':tri_glb,'anchors':anchors,'material_map_sha256':baked}