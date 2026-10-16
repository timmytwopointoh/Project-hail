#!/usr/bin/env python3
"""Four useful diagnostic views of ACTUAL generated meshes, not concept art.

Pillow software raster preview for topology, shape and orientation. No PBR,
shadow-casting, photorealism, Android GPU, or reference likeness is claimed.
"""
from __future__ import annotations
import argparse
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from factory import MATERIALS, generate, load_catalog

VIEWS=[("front",0,10),("three_quarter",45,15),("side",90,10),("elevated",35,52)]

def render(mesh, out, *, yaw=0, pitch=10, label="front", size=640):
    az=math.radians(yaw);el=math.radians(pitch)
    right=(math.cos(az),0,-math.sin(az))
    up=(-math.sin(az)*math.sin(el),math.cos(el),-math.cos(az)*math.sin(el))
    depth=(math.sin(az)*math.cos(el),math.sin(el),math.cos(az)*math.cos(el))
    bound=mesh.bounds()
    center=tuple((bound[0][i]+bound[1][i])*.5 for i in range(3))
    def proj(p):
        d=tuple(p[i]-center[i] for i in range(3))
        return (sum(d[i]*right[i] for i in range(3)),
                sum(d[i]*up[i] for i in range(3)),
                sum(d[i]*depth[i] for i in range(3)))
    # Auto frame uniformly across every mesh, preventing cropped scene previews.
    points=[proj(p) for faces in mesh.parts.values() for f in faces for p in f[:3]]
    extent=max(max(q[0] for q in points)-min(q[0] for q in points),
               max(q[1] for q in points)-min(q[1] for q in points),.15)
    scale=size*.75/extent
    im=Image.new("RGB",(size,size),(21,25,31))
    draw=ImageDraw.Draw(im)
    draw.rectangle((0,0,size,size),fill=(26,30,36))
    for i in range(0,size,64):
        draw.line((i,0,i,size),fill=(36,40,46))
        draw.line((0,i,size,i),fill=(36,40,46))
    faces=[]
    light=(.42,.68,.55)
    for mat,tris in mesh.parts.items():
        base=MATERIALS[mat]["base"][:3]
        for a,b,c,n,uv,tint in tris:
            coords=[proj(p) for p in (a,b,c)]
            shade=.42+.53*max(0,sum(n[k]*light[k] for k in range(3))) + .08*abs(sum(n[k]*depth[k] for k in range(3)))
            color=tuple(max(0,min(255,round(255*channel*shade*tint[0]))) for channel in base)
            xy=[(size/2+u*scale,size/2-v*scale) for u,v,d in coords]
            faces.append((sum(t[2] for t in coords)/3,xy,color))
    faces.sort(key=lambda row:row[0])
    for _,xy,color in faces:
        draw.polygon(xy,fill=color)
    draw.text((17,16),"VEILFORGE / "+label.upper(),fill=(230,234,240))
    draw.text((17,size-32),"ACTUAL 3D SOURCE MESH | DIAGNOSTIC ONLY",fill=(205,211,218))
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    im.save(out)

def build_views(catalog,ident,out):
    recipes=load_catalog(catalog)
    if ident not in recipes:raise ValueError("Unknown catalog asset")
    mesh=generate(recipes[ident])
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    shots=[]
    for label,yaw,pitch in VIEWS:
        name=f"view_{label}.png"
        render(mesh,out/name,yaw=yaw,pitch=pitch,label=label)
        shots.append(Image.open(out/name).convert("RGB"))
    sheet=Image.new("RGB",(1280,1280))
    for i,pic in enumerate(shots):
        sheet.paste(pic,((i%2)*640,(i//2)*640))
        pic.close()
    sheet.save(out/"contact_sheet.png")

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--catalog",type=Path,default=Path("veilforge/catalog.json"))
    a.add_argument("--id",required=True)
    a.add_argument("--out",type=Path,required=True)
    x=a.parse_args()
    build_views(x.catalog,x.id,x.out)
    print("VEILFORGE_VIEWS_PASS",x.id,"four_views=4")
if __name__=="__main__":
    main()
