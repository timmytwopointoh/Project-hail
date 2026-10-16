#!/usr/bin/env python3
"""VEILFORGE M3: reusable original game-asset factory.

Deterministic, bounded geometric builders for six asset families. The factory
produces actual 3D source meshes, multi-material glTF 2.0 and inspectable OBJ.
No generated asset is approved for a game, scanned, rigged, or photorealistic.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import random
import re
import struct

MATERIALS = {
    "stone": {"base":[.42,.45,.47,1], "metallic":0, "roughness":.92},
    "stone_trim": {"base":[.62,.59,.51,1], "metallic":0, "roughness":.78},
    "earth": {"base":[.32,.29,.24,1], "metallic":0, "roughness":1},
    "grass": {"base":[.23,.38,.20,1], "metallic":0, "roughness":.96},
    "bark": {"base":[.33,.23,.15,1], "metallic":0, "roughness":.94},
    "leaf": {"base":[.22,.43,.19,1], "metallic":0, "roughness":.9},
    "wood": {"base":[.40,.27,.17,1], "metallic":0, "roughness":.78},
    "dark_wood": {"base":[.22,.15,.11,1], "metallic":0, "roughness":.85},
    "steel": {"base":[.59,.65,.70,1], "metallic":.92, "roughness":.36},
    "iron": {"base":[.26,.31,.35,1], "metallic":.88, "roughness":.53},
    "bronze": {"base":[.63,.43,.23,1], "metallic":.84, "roughness":.49},
    "leather": {"base":[.30,.18,.10,1], "metallic":0, "roughness":.82},
}
CATEGORIES = ("architecture","terrain","vegetation","props","weapons","vehicles")
TIERS = {"mobile": 5500, "standard": 18000, "cinematic": 55000}
MAX_TRIANGLES = 55000

class AssetError(ValueError):
    pass

def _vec(a,b):
    return tuple(b[i]-a[i] for i in range(3))

def _cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

def _norm(v):
    m=math.sqrt(sum(x*x for x in v))
    if not math.isfinite(m) or m<1e-12:
        raise AssetError("Degenerate face")
    return tuple(x/m for x in v)

class Mesh:
    def __init__(self):
        self.parts=defaultdict(list)
    def tri(self,a,b,c,material,uv=((0,0),(1,0),(0,1)),variation=1):
        if material not in MATERIALS:
            raise AssetError("Unsupported material "+str(material))
        if not all(len(v)==3 and all(math.isfinite(x) and abs(x)<=1000 for x in v)
                   for v in (a,b,c)):
            raise AssetError("Bad triangle coordinates")
        n=_norm(_cross(_vec(a,b),_vec(a,c)))
        if len(self.parts[material])>=MAX_TRIANGLES:
            raise AssetError("Asset exceeds maximum triangles")
        color=(variation,variation,variation,1.)
        self.parts[material].append((tuple(a),tuple(b),tuple(c),n,uv,color))
    def quad(self,a,b,c,d,material,variation=1):
        # Consistent planar UV orientation and predictable physical texel
        # scale, with continuous mapping across both triangles of a quad.
        # Dedicated seam unwrap/atlas packing remains a separate milestone.
        du=max(.01,math.dist(a,b)/.85)
        dv=max(.01,math.dist(a,d)/.85)
        self.tri(a,b,c,material,((0,0),(du,0),(du,dv)),variation)
        self.tri(a,c,d,material,((0,0),(du,dv),(0,dv)),variation)
    def box(self,c,s,mat):
        x,y,z=c
        hx,hy,hz=(t/2 for t in s)
        if min(hx,hy,hz)<=.00001:
            raise AssetError("Invalid box dimensions")
        corners=[
            (x-hx,y-hy,z-hz),(x+hx,y-hy,z-hz),
            (x+hx,y+hy,z-hz),(x-hx,y+hy,z-hz),
            (x-hx,y-hy,z+hz),(x+hx,y-hy,z+hz),
            (x+hx,y+hy,z+hz),(x-hx,y+hy,z+hz)]
        for a,b,c,d in ((4,5,6,7),(1,0,3,2),(0,4,7,3),
                        (5,1,2,6),(3,7,6,2),(0,1,5,4)):
            self.quad(corners[a],corners[b],corners[c],corners[d],mat)
    def sweep(self,rings,mat,sides=12,cap=True,noise=None):
        if len(rings)<2 or sides<3 or sides>64:
            raise AssetError("Unsupported loft")
        vertices=[]
        for r,(cx,y,cz,rx,rz) in enumerate(rings):
            if rx<=0 or rz<=0:
                raise AssetError("Nonpositive loft radius")
            row=[]
            for i in range(sides):
                theta=2*math.pi*i/sides
                wobble=1 if noise is None else noise(r,i)
                row.append((cx+rx*math.cos(theta)*wobble,y,
                            cz+rz*math.sin(theta)*wobble))
            vertices.append(row)
        for j in range(len(vertices)-1):
            for i in range(sides):
                a,b=vertices[j][i],vertices[j][(i+1)%sides]
                c,d=vertices[j+1][(i+1)%sides],vertices[j+1][i]
                self.quad(a,b,c,d,mat)
        if cap:
            start=tuple(sum(p[k] for p in vertices[0])/sides for k in range(3))
            end=tuple(sum(p[k] for p in vertices[-1])/sides for k in range(3))
            for i in range(sides):
                self.tri(start,vertices[0][(i+1)%sides],vertices[0][i],mat)
                self.tri(end,vertices[-1][i],vertices[-1][(i+1)%sides],mat)
    def tube(self,a,b,ra,rb,mat,sides=10):
        direction=_norm(_vec(a,b))
        helper=(0,0,1) if abs(direction[2])<.8 else (1,0,0)
        right=_norm(_cross(direction,helper))
        front=_cross(direction,right)
        aa=[];bb=[]
        for i in range(sides):
            theta=2*math.pi*i/sides
            normal=[math.cos(theta)*right[k]+math.sin(theta)*front[k] for k in range(3)]
            aa.append(tuple(a[k]+ra*normal[k] for k in range(3)))
            bb.append(tuple(b[k]+rb*normal[k] for k in range(3)))
        for i in range(sides):
            j=(i+1)%sides
            self.quad(aa[i],aa[j],bb[j],bb[i],mat)
            self.tri(a,aa[j],aa[i],mat)
            self.tri(b,bb[i],bb[j],mat)
    def ellipsoid(self,c,r,mat,lat=8,lon=12,seed=0):
        cx,cy,cz=c
        rng=random.Random(seed)
        phases=[rng.uniform(-1,1) for _ in range(lon)]
        poles=[(cx,cy-r[1],cz),(cx,cy+r[1],cz)]
        rings=[]
        for j in range(1,lat):
            theta=math.pi*j/lat
            row=[]
            for i in range(lon):
                phi=2*math.pi*i/lon
                f=1+.035*phases[i]
                row.append((cx+r[0]*math.sin(theta)*math.cos(phi)*f,
                            cy-r[1]*math.cos(theta),
                            cz+r[2]*math.sin(theta)*math.sin(phi)*f))
            rings.append(row)
        for i in range(lon):
            j=(i+1)%lon
            self.tri(poles[0],rings[0][i],rings[0][j],mat)
            self.tri(poles[1],rings[-1][j],rings[-1][i],mat)
        for k in range(len(rings)-1):
            for i in range(lon):
                j=(i+1)%lon
                self.quad(rings[k][i],rings[k+1][i],rings[k+1][j],rings[k][j],mat)
    @property
    def triangle_count(self):
        return sum(len(v) for v in self.parts.values())
    def bounds(self):
        pts=[p for faces in self.parts.values() for f in faces for p in f[:3]]
        return [[round(min(p[i] for p in pts),5) for i in range(3)],
                [round(max(p[i] for p in pts),5) for i in range(3)]]

def build_architecture(m,rng,detail):
    m.box((0,-.12,0),(4.6,.24,1.4),"stone")
    # Freestanding ruin gate: columns, fluting, capitals and concentric arch.
    for side in (-1,1):
        x=side*1.42
        m.box((x,1.1,0),(.72,2.2,.90),"stone")
        m.box((x,2.24,0),(1.04,.22,1.08),"stone_trim")
        m.box((x,.20,0),(1.0,.3,1.06),"stone_trim")
        for k in range(-2,3):
            if detail!="mobile" or k%2==0:
                m.sweep([(x+k*.12,.30,.52,.032,.028),
                         (x+k*.12,2.08,.52,.028,.028)],
                         "stone_trim",6,cap=True)
        for y in (.56,1.10,1.64):
            m.box((x,y,.48),(.68,.032,.045),"stone_trim")
    # An arched voussoir ring with real inner opening and recessed depth.
    steps=14 if detail=="mobile" else 28
    for i in range(steps):
        t0=math.pi*i/steps
        t1=math.pi*(i+1)/steps
        ri,ro=.98,1.53
        cy=2.26
        zf,zb=.48,-.48
        def point(rad,t,z):return (rad*math.cos(t),cy+rad*math.sin(t),z)
        inner0=point(ri,t0,zf);outer0=point(ro,t0,zf)
        inner1=point(ri,t1,zf);outer1=point(ro,t1,zf)
        bi0=point(ri,t0,zb);bo0=point(ro,t0,zb)
        bi1=point(ri,t1,zb);bo1=point(ro,t1,zb)
        mat="stone_trim" if i%4==0 else "stone"
        for quad in ((inner0,inner1,outer1,outer0),(bo0,bo1,bi1,bi0),
                     (inner0,bi0,bi1,inner1),(outer1,bo1,bo0,outer0),
                     (inner0,outer0,bo0,bi0),(inner1,bi1,bo1,outer1)):
            m.quad(*quad,mat)
    # Engraved crown accents
    m.box((0,3.88,0),(3.95,.18,1.14),"stone_trim")
    m.box((0,4.00,.47),(2.84,.08,.09),"bronze")

def build_terrain(m,rng,detail):
    n={"mobile":20,"standard":40,"cinematic":64}[detail]
    span=12.
    phases=[rng.uniform(-math.pi,math.pi) for _ in range(4)]
    grid=[]
    for j in range(n+1):
        row=[]
        for i in range(n+1):
            x=span*(i/n-.5);z=span*(j/n-.5)
            y=(.37*math.sin(x*.62+phases[0])*math.cos(z*.54+phases[1])
                +.18*math.sin(x*1.32+z*.71+phases[2])
                +.07*math.cos(x*2.25-z*1.72+phases[3]))
            row.append((x,y,z))
        grid.append(row)
    for j in range(n):
        for i in range(n):
            mat="earth" if (i+j)%7==0 else "grass"
            m.quad(grid[j][i],grid[j+1][i],
                   grid[j+1][i+1],grid[j][i+1],mat)
    for k in range(6 if detail=="mobile" else 14):
        x=rng.uniform(-4.8,4.8);z=rng.uniform(-4.8,4.8)
        m.ellipsoid((x,-.12,z),(.15+rng.random()*.23,.11,.20),
                    "stone",lat=4,lon=6,seed=k)

def build_vegetation(m,rng,detail):
    bark="bark";leaf="leaf"
    height=3.9
    m.sweep([(0,0,0,.30,.29),(.08,.45,0,.26,.24),
             (-.04,1.2,.02,.21,.20),(.11,2.2,.03,.15,.15),
             (.06,3.65,.01,.05,.06)],bark,10 if detail=="mobile" else 16)
    for i in range(7 if detail=="mobile" else 14):
        y=1.25+(i%7)*.32
        theta=2*math.pi*i/2.618
        reach=.85+rng.random()*.7
        a=(.08,y,.02)
        b=(math.cos(theta)*reach, y+.25+rng.random()*.42,
           math.sin(theta)*reach)
        m.tube(a,b,.095,.045,bark,6 if detail=="mobile" else 10)
        m.ellipsoid((b[0],b[1]+.22,b[2]),(.48,.62,.40),leaf,
                    lat=5 if detail=="mobile" else 8,
                    lon=8 if detail=="mobile" else 12,seed=i)
    for side in range(4):
        t=side*math.pi/2
        m.tube((0,.24,0),(.62*math.cos(t),.03,.62*math.sin(t)),.13,.03,bark,6)

def build_props(m,rng,detail):
    m.box((0,.46,0),(1.48,.68,.78),"wood")
    m.box((0,.87,0),(1.6,.17,.87),"dark_wood")
    m.box((0,.96,0),(1.62,.07,.90),"wood")
    for x in (-.57,.57):
        m.box((x,.51,0),(.09,.75,.83),"iron")
        m.box((x,.94,0),(.10,.16,.97),"iron")
    for z in (-.29,.29):
        m.box((0,.48,z),(1.55,.075,.095),"bronze")
    m.box((0,.69,.435),(.22,.25,.058),"bronze")
    m.box((0,.69,.483),(.075,.12,.04),"iron")
    for x in (-.56,.56):
        for z in (-.30,.30):
            m.box((x,.065,z),(.22,.13,.20),"dark_wood")
    if detail!="mobile":
        for i in range(8):
            x=-.61+i*.175
            m.box((x,.96,.43),(.022,.055,.045),"bronze")
            m.box((x,.96,-.43),(.022,.055,.045),"bronze")

def build_weapons(m,rng,detail):
    # Original sword, actual 3-D diamond cross section rather than a plane.
    m.sweep([(0,-.90,0,.095,.09),(0,-.65,0,.12,.12)],
            "bronze",10,cap=True)
    m.sweep([(0,-.64,0,.055,.052),(0,.11,0,.052,.047)],
            "leather",12)
    for j in range(10 if detail=="mobile" else 18):
        y=-.58+j*.038
        m.sweep([(0,y,0,.061,.058),(0,y+.011,0,.061,.058)],
                "bronze",8)
    m.box((0,.16,0),(1.04,.13,.16),"bronze")
    for side in (-1,1):
        m.sweep([(side*.47,.16,0,.092,.072),(side*.49,.34,0,.062,.053)],
                "steel",8)
    # blade facets taper to true tip; rings are elliptical diamond-like sections.
    m.sweep([(0,.24,0,.20,.064),(0,.43,0,.225,.060),
             (0,1.85,0,.155,.050),(0,2.55,0,.065,.020),
             (0,2.78,0,.004,.004)],"steel",4)
    # Integral shallow fuller ridge for closeup light breakup.
    m.box((0,1.04,.065),(.037,1.09,.011),"stone_trim")

def build_vehicles(m,rng,detail):
    m.box((0,.86,0),(2.30,.18,1.12),"wood")
    m.box((0,1.06,-.46),(2.48,.31,.12),"dark_wood")
    m.box((0,1.06,.46),(2.48,.31,.12),"dark_wood")
    for x in (-.92,.92):
        m.box((x,1.07,0),(.11,.36,1.15),"iron")
    m.box((1.25,.84,0),(1.08,.12,.12),"wood")
    for x in (-.77,.77):
        for z in (-.67,.67):
            # Wheels revolve around the Z axle.
            center=(x,.60,z)
            sides=12 if detail=="mobile" else 24
            radius=.57
            rings=[]
            for dz in (-.11,.11):
                row=[(x+radius*math.cos(2*math.pi*i/sides),
                      .60+radius*math.sin(2*math.pi*i/sides),
                      z+dz) for i in range(sides)]
                rings.append(row)
            for i in range(sides):
                k=(i+1)%sides
                m.quad(rings[0][i],rings[0][k],rings[1][k],rings[1][i],"dark_wood")
                m.tri((x,.60,z-.11),rings[0][k],rings[0][i],"wood")
                m.tri((x,.60,z+.11),rings[1][i],rings[1][k],"wood")
            m.tube((x,.60,z-.16),(x,.60,z+.16),.10,.10,"iron",8)
    m.box((0,1.24,0),(2.10,.045,.85),"bronze")

BUILDERS = {"architecture":build_architecture,"terrain":build_terrain,
            "vegetation":build_vegetation,"props":build_props,
            "weapons":build_weapons,"vehicles":build_vehicles}

def load_catalog(path):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data,dict) or data.get("schema_version")!=1 or not isinstance(data.get("assets"),list):
        raise AssetError("Expected a schema-versioned asset catalog")
    result={}
    for spec in data["assets"]:
        required={"id","category","detail","seed"}
        allowed=required|{"scale","tags","sculpt_layers"}
        if not isinstance(spec,dict) or not required.issubset(spec) or set(spec)-allowed:
            raise AssetError("Asset recipe must have id, category, detail and seed")
        ident=spec["id"]
        if not isinstance(ident,str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{1,63}",ident):
            raise AssetError("Invalid asset identifier")
        if ident in result or spec["category"] not in CATEGORIES or spec["detail"] not in TIERS:
            raise AssetError("Duplicate or unknown asset family/quality tier")
        seed=spec["seed"]
        if isinstance(seed,bool) or not isinstance(seed,int) or not 0<=seed<=2147483647:
            raise AssetError("Seed must be a nonnegative bounded integer")
        scale=spec.get("scale",1)
        if isinstance(scale,bool) or not isinstance(scale,(int,float)) or not math.isfinite(scale) or not .1<=scale<=10:
            raise AssetError("Scale must be a bounded finite positive number")
        tags=spec.get("tags",[])
        if not isinstance(tags,list) or len(tags)>16 or any(
            not isinstance(tag,str) or not re.fullmatch(r"[a-z0-9_-]{2,32}",tag)
            for tag in tags):
            raise AssetError("Tags must be an array of short identifiers")
        if "sculpt_layers" in spec:
            from sculpt_layers import validate_layers
            validate_layers(spec["sculpt_layers"],MATERIALS)
        result[ident]=spec
    if not result:
        raise AssetError("Empty asset catalog")
    return result

def generate(spec):
    if spec["category"] not in BUILDERS:
        raise AssetError("Unsupported asset builder")
    m=Mesh()
    BUILDERS[spec["category"]](m,random.Random(spec["seed"]),spec["detail"])
    scale=spec.get("scale",1)
    if scale!=1:
        for mat,faces in list(m.parts.items()):
            m.parts[mat]=[
                (tuple(x*scale for x in a),tuple(x*scale for x in b),
                 tuple(x*scale for x in c),n,uv,tint)
                for a,b,c,n,uv,tint in faces]
    if "sculpt_layers" in spec:
        from sculpt_layers import apply_layers
        m, m.sculpt_report=apply_layers(
            m,spec["sculpt_layers"],spec["seed"],
            triangle_budget=TIERS[spec["detail"]])
    if not 0<m.triangle_count<=TIERS[spec["detail"]]:
        raise AssetError(f"{spec['id']}: triangle budget exceeded ({m.triangle_count} > {TIERS[spec['detail']]})")
    return m

def export_obj(mesh,dest):
    dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
    lines=["# VEILFORGE original multi-material procedural source", "# Y-up, meters, right-handed"]
    index=1
    for material,faces in sorted(mesh.parts.items()):
        lines.append("usemtl "+material)
        for a,b,c,normal,uv,color in faces:
            for p in (a,b,c):
                lines.append("v "+" ".join(f"{v:.7f}" for v in p)+" "+
                             " ".join(f"{t:.5f}" for t in color[:3]))
            for _ in range(3):
                lines.append("vn "+" ".join(f"{v:.7f}" for v in normal))
            for coord in uv:
                lines.append("vt "+" ".join(f"{v:.6f}" for v in coord))
            lines.append(f"f {index}/{index}/{index} {index+1}/{index+1}/{index+1} {index+2}/{index+2}/{index+2}")
            index+=3
    dest.write_text("\n".join(lines)+"\n",encoding="utf-8")

def export_gltf(mesh,dest,spec,*,material_maps=None):
    dest=Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
    output=bytearray();views=[];accessors=[];primitives=[];materials=[]
    images=[];textures=[]
    sampler={"magFilter":9729,"minFilter":9729,"wrapS":10497,"wrapT":10497}
    def texture(uri):
        if not uri.startswith("textures/") or ".." in uri:
            raise AssetError("Unsafe material texture path")
        idx=len(images)
        images.append({"uri":uri,"mimeType":"image/png"})
        textures.append({"source":idx,"sampler":0})
        return len(textures)-1
    def add(values,arity,fmt,ctype,target,bounds=False):
        while len(output)%4:output.append(0)
        offset=len(output)
        output.extend(struct.pack("<"+fmt*len(values),*values))
        view=len(views)
        views.append({"buffer":0,"byteOffset":offset,"byteLength":len(output)-offset,"target":target})
        accessor={"bufferView":view,"componentType":ctype,"count":len(values)//arity,
                  "type":{1:"SCALAR",2:"VEC2",3:"VEC3",4:"VEC4"}[arity]}
        if bounds:
            accessor["min"]=[min(values[i::arity]) for i in range(arity)]
            accessor["max"]=[max(values[i::arity]) for i in range(arity)]
        accessors.append(accessor)
        return len(accessors)-1
    total_source_corners=0
    total_indexed_vertices=0
    for material,faces in sorted(mesh.parts.items()):
        pos=[];normal=[];uv=[];color=[];indices=[]
        # Exact corner-attribute welding, not spatial-only vertex welding:
        # preserve UV seams, hard surface normals, colors and material boundaries.
        # Each equivalent vertex occurs only once per PBR material primitive.
        corner_index={}
        for a,b,c,n,coords,tint in faces:
            for p,tc in zip((a,b,c),coords):
                total_source_corners+=1
                key=(tuple(p),tuple(n),tuple(tc),tuple(tint))
                index=corner_index.get(key)
                if index is None:
                    index=len(pos)//3
                    corner_index[key]=index
                    pos.extend(p)
                    normal.extend(n)
                    uv.extend(tc)
                    color.extend(tint)
                indices.append(index)
        total_indexed_vertices+=len(pos)//3
        attributes={
            "POSITION":add(pos,3,"f",5126,34962,True),
            "NORMAL":add(normal,3,"f",5126,34962),
            "TEXCOORD_0":add(uv,2,"f",5126,34962),
            "COLOR_0":add(color,4,"f",5126,34962)}
        idx=add(indices,1,"I",5125,34963)
        defn=MATERIALS[material]
        mat={"name":material,"doubleSided":material in ("leaf","grass"),
             "pbrMetallicRoughness":{
                 "baseColorFactor":defn["base"],
                 "metallicFactor":defn["metallic"],
                 "roughnessFactor":defn["roughness"]}}
        if material_maps is not None:
            maps=material_maps[material]
            # The albedo texture is authored at the intended material color:
            # don't multiply the palette color twice.
            mat["pbrMetallicRoughness"]["baseColorFactor"]=[1,1,1,1]
            mat["pbrMetallicRoughness"]["metallicFactor"]=1
            mat["pbrMetallicRoughness"]["roughnessFactor"]=1
            mat["pbrMetallicRoughness"]["baseColorTexture"]={
                "index":texture(maps["albedo"])}
            mat["pbrMetallicRoughness"]["metallicRoughnessTexture"]={
                "index":texture(maps["metallic_roughness"])}
            mat["normalTexture"]={"index":texture(maps["normal"])}
            mat["occlusionTexture"]={"index":texture(maps["ao"])}
        materials.append(mat)
        primitives.append({"attributes":attributes,"indices":idx,
                           "mode":4,"material":len(materials)-1})
    doc={"asset":{"version":"2.0","generator":"VEILFORGE M3 asset factory"},
         "scene":0,"scenes":[{"nodes":[0]}],
         "nodes":[{"name":spec["id"],"mesh":0}],
         "meshes":[{"name":spec["id"],"primitives":primitives}],
         "materials":materials,"buffers":[{"uri":dest.stem+".bin","byteLength":len(output)}],
         "bufferViews":views,"accessors":accessors,
         "extras":{"asset_id":spec["id"],"category":spec["category"],
                   "tier":spec["detail"],"seed":spec["seed"],
                   "triangles":mesh.triangle_count,
                   "original_vertex_corners":total_source_corners,
                   "indexed_vertices":total_indexed_vertices,
                   "vertices_saved":total_source_corners-total_indexed_vertices,
                   "vertex_indexing":"exact-position-normal-uv-color-within-material",
                   "rigged":False,"production_approved":False,
                   "non_destructive_sculpt_layers":[row["id"] for row in spec.get("sculpt_layers",[])]}}
    if images:
        doc["images"]=images
        doc["textures"]=textures
        doc["samplers"]=[sampler]
        doc["extras"]["material_maps_authored"]=True
        doc["extras"]["tangent_vectors_authored"]=False
    dest.write_text(json.dumps(doc,indent=2)+"\n",encoding="utf-8")
    (dest.parent/(dest.stem+".bin")).write_bytes(output)
    return doc

def build_asset(catalog,ident,dest):
    recipes=load_catalog(catalog)
    if ident not in recipes:raise AssetError("Unknown asset id")
    spec=recipes[ident]
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=True)
    mesh=generate(spec)
    obj=dest/(ident+".obj");gltf=dest/(ident+".gltf")
    export_obj(mesh,obj)
    from material_baker import bake
    maps={}
    bakes={}
    texture_size=128 if spec["detail"]!="cinematic" else 256
    for mat in sorted(mesh.parts):
        folder=dest/"textures"/mat
        result=bake(mat,folder,size=texture_size,seed=spec["seed"]+len(mat)*19)
        bakes[mat]=result
        maps[mat]={name:"textures/"+mat+"/"+meta["file"]
                   for name,meta in result["maps"].items()}
    doc=export_gltf(mesh,gltf,spec,material_maps=maps)
    from engine import inspect_obj
    metrics=inspect_obj(obj)
    if metrics["degenerate_triangles"]!=0 or metrics["triangles"]!=mesh.triangle_count:
        raise AssetError("Source geometry failed degenerate/triangle-count QA")
    manifest={
        "schema_version":1,"id":ident,"category":spec["category"],
        "detail":spec["detail"],"seed":spec["seed"],
        "scale":spec.get("scale",1),"tags":spec.get("tags",[]),
        "sculpt_quality":getattr(mesh,"sculpt_report",None),
        "sculpt_layer_recipe":spec.get("sculpt_layers",[]),
        "source_obj":obj.name,"gltf":gltf.name,"triangles":mesh.triangle_count,
        "source_vertex_corners":doc["extras"]["original_vertex_corners"],
        "indexed_vertices":doc["extras"]["indexed_vertices"],
        "vertices_saved":doc["extras"]["vertices_saved"],
        "gltf_binary_bytes":(dest/(ident+".bin")).stat().st_size,
        "budget":TIERS[spec["detail"]],"materials":sorted(mesh.parts),
        "bounds":mesh.bounds(),"obj_sha256":hashlib.sha256(obj.read_bytes()).hexdigest(),
        "gltf_sha256":hashlib.sha256(gltf.read_bytes()).hexdigest(),
        "mesh_quality":{"degenerate_triangles":metrics["degenerate_triangles"],
                        "boundary_edges":metrics["boundary_edges"],
                        "nonmanifold_edges":metrics["nonmanifold_edges"]},
        "topology_note":"Open architectural/terrain/vegetation surfaces may be intentional; component-aware approval needed.",
        "texture_maps":bakes,
        "render_level":"procedural geometry and textured PBR inputs; not cinematic BRDF or photoreal",
        "production_approved":False,"manual_visual_review_required":True
    }
    (dest/"asset_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    return manifest

def main():
    p=argparse.ArgumentParser(description="Create a fully reproducible catalogued game asset")
    p.add_argument("--catalog",type=Path,default=Path("veilforge/catalog.json"))
    p.add_argument("--id",required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    m=build_asset(args.catalog,args.id,args.out)
    print("VEILFORGE_FACTORY_PASS",json.dumps({
        k:m[k] for k in ("id","category","detail","triangles","materials")}))
if __name__=="__main__":
    main()
