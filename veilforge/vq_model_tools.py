#!/usr/bin/env python3
"""VEYLQUORIN (VQ): inspect any real triangulated OBJ, never invent render QA.

Produces measurable mesh/UV evidence, optional glTF byte-integrity checks,
14 source-mesh diagnostic angles and optional human-supplied silhouette-mask IoU.
The lightweight views use Pillow software rasterization, NOT a PBR renderer,
camera calibration, photorealism verification, or artist acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

from engine import inspect_obj, read_obj

ANGLES=[(i*25, (15,25,42)[i%3]) for i in range(14)]
MAX_RENDER_FACES=4500
MAX_TEX_PIXELS=8192*8192

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as inp:
        for buf in iter(lambda:inp.read(1<<20),b""):
            h.update(buf)
    return h.hexdigest()

def quantile(values, ratio):
    ordered=sorted(values)
    return ordered[int(round((len(ordered)-1)*ratio))] if ordered else 0.0

def uv_evidence(vertices, uvs, faces):
    """Measures UV completeness and per-face local area distortion, not unwrap quality."""
    with_uv=0; collapsed=0; total=0
    log_ratios=[]
    for face in faces:
        if not all(c[1] is not None for c in face):
            continue
        with_uv+=1
        a,b,c=(uvs[item[1]] for item in face)
        uv_area=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))*.5
        a,b,c=(vertices[item[0]] for item in face)
        u=[b[i]-a[i] for i in range(3)]
        v=[c[i]-a[i] for i in range(3)]
        cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        geo_area=math.sqrt(sum(x*x for x in cross))*.5
        if uv_area<1e-12:
            collapsed+=1
        elif geo_area>1e-12:
            total+=1
            log_ratios.append(math.log(uv_area/geo_area))
    median=statistics.median(log_ratios) if log_ratios else 0
    deviations=[abs(v-median) for v in log_ratios]
    return {"uv_faces":with_uv,
            "uv_coverage":round(with_uv/len(faces),6) if faces else 0,
            "collapsed_uv_faces":collapsed,
            "evaluated_uv_area_faces":total,
            "p90_relative_uv_area_scale_variation":round(math.exp(quantile(deviations,.9)),4)
                if deviations else None,
            "does_not_measure_texture_seam_continuity":True}

def inside(root:Path, uri:str) -> Path:
    if not isinstance(uri,str) or not uri or uri.startswith(("http:","https:","data:")):
        raise ValueError("External/data URI is not a verified portable input")
    path=(root/uri).resolve()
    if not path.is_relative_to(root.resolve()) or path.is_symlink():
        raise ValueError("Path escapes the source asset folder")
    return path

def check_gltf(path:Path):
    """Validate bounds/linkage of authored glTF buffers and texture files.

    This is intentionally a small validated subset, not the official glTF
    conformance suite or a production material/render compatibility guarantee.
    """
    root=path.parent
    doc=json.loads(path.read_text(encoding="utf-8"))
    errors=[]
    sources={}
    if doc.get("asset",{}).get("version")!="2.0":
        errors.append("Missing glTF 2.0 asset version")
    for i,b in enumerate(doc.get("buffers",[])):
        try:
            p=inside(root,b["uri"])
            if not p.is_file() or p.stat().st_size!=b["byteLength"]:
                raise ValueError("missing binary or incorrect declared byte length")
            sources[i]=p
        except (KeyError,ValueError,OSError) as e:
            errors.append("buffer "+str(i)+": "+str(e))
    for i,view in enumerate(doc.get("bufferViews",[])):
        try:
            src=sources[view["buffer"]]
            off=view.get("byteOffset",0);length=view["byteLength"]
            if type(off)!=int or type(length)!=int or off<0 or length<0 or off+length>src.stat().st_size:
                raise ValueError("buffer view exceeds file")
        except (KeyError,IndexError,TypeError,ValueError) as e:
            errors.append("bufferView "+str(i)+": "+str(e))
    for i,a in enumerate(doc.get("accessors",[])):
        try:
            view=doc["bufferViews"][a["bufferView"]]
            comp={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}[a["componentType"]]
            count={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4,"MAT4":16}[a["type"]]
            length=a["count"];offset=a.get("byteOffset",0)
            stride=view.get("byteStride",comp*count)
            if not (type(length)==int and length>0 and type(offset)==int and offset>=0
                and type(stride)==int and stride>=comp*count and
                offset+(length-1)*stride+comp*count<=view["byteLength"]):
                raise ValueError("accessor exceeds referenced buffer view")
        except (KeyError,IndexError,TypeError,ValueError) as e:
            errors.append("accessor "+str(i)+": "+str(e))
    verified_images=0
    for i,img in enumerate(doc.get("images",[])):
        if "uri" not in img:
            errors.append("image "+str(i)+": embedded bufferView needs separate inspection")
            continue
        try:
            p=inside(root,img["uri"])
            if not p.is_file() or p.stat().st_size<30:
                raise ValueError("missing or empty texture")
            verified_images+=1
        except (ValueError,OSError) as e:
            errors.append("image "+str(i)+": "+str(e))
    if doc.get("extras",{}).get("production_approved") is True:
        errors.append("Upstream asset claims production approval without this reviewer")
    return {"path":path.name,"sha256":sha(path),"buffers":len(sources),
        "images_verified":verified_images,
        "errors":errors,"structural_smoke_passed":not errors,
        "full_gltf_validator_passed":False}

def projected_frames(vertices,faces,out:Path, *, limit=MAX_RENDER_FACES,size=480):
    from PIL import Image,ImageDraw
    out.mkdir(parents=True,exist_ok=True)
    p3=[v[:3] for v in vertices]
    bounds=([(min(p[i] for p in p3),max(p[i] for p in p3)) for i in range(3)])
    center=[(lo+hi)*.5 for lo,hi in bounds]
    maximum=max(max(hi-lo for lo,hi in bounds),1e-4)
    stride=max(1,math.ceil(len(faces)/limit))
    chosen=faces[::stride]
    data=[]
    sheet=Image.new("RGB",(size*7,size*2),(21,25,31))
    masks=[]
    for i,(yaw,pitch) in enumerate(ANGLES):
        az=math.radians(yaw);el=math.radians(pitch)
        right=(math.cos(az),0,-math.sin(az))
        up=(-math.sin(az)*math.sin(el),math.cos(el),-math.cos(az)*math.sin(el))
        depth=(math.sin(az)*math.cos(el),math.sin(el),math.cos(az)*math.cos(el))
        def project(pt):
            d=[pt[k]-center[k] for k in range(3)]
            return (sum(d[k]*right[k] for k in range(3)),
                    sum(d[k]*up[k] for k in range(3)),
                    sum(d[k]*depth[k] for k in range(3)))
        scale=size*.72/maximum
        image=Image.new("RGB",(size,size),(21,25,31))
        mask=Image.new("L",(size,size),0)
        draw=ImageDraw.Draw(image)
        stencil=ImageDraw.Draw(mask)
        polys=[]
        for tri in chosen:
            points=[p3[item[0]] for item in tri]
            coords=[project(p) for p in points]
            xy=[(round(size/2+a*scale),round(size/2-b*scale)) for a,b,_ in coords]
            u=[points[1][k]-points[0][k] for k in range(3)]
            v=[points[2][k]-points[0][k] for k in range(3)]
            normal=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],
                    u[0]*v[1]-u[1]*v[0])
            magnitude=math.sqrt(sum(t*t for t in normal))
            shading=.35+.5*abs(normal[0]*.5+normal[1]*.7+normal[2]*.45)/magnitude if magnitude>1e-12 else .4
            color=(int(96*shading),int(162*shading),int(206*shading))
            polys.append((sum(c[2] for c in coords)/3,xy,color))
        polys.sort(key=lambda a:a[0])
        for _,points,color in polys:
            draw.polygon(points,fill=color)
            stencil.polygon(points,fill=255)
        draw.text((12,10),f"VQ / REAL OBJ / yaw {yaw:03d} pitch {pitch:02d}",fill=(234,234,240))
        draw.text((12,size-22),"DIAGNOSTIC ONLY - NOT PBR",fill=(220,220,224))
        filename=f"orbit_{i:02d}_yaw_{yaw:03d}.png"
        maskname=f"mask_{i:02d}.png"
        image.save(out/filename)
        mask.save(out/maskname)
        sheet.paste(image,((i%7)*size,(i//7)*size))
        masks.append(maskname)
        data.append({"view_index":i,"yaw":yaw,"pitch":pitch,
                     "image":filename,"image_sha256":sha(out/filename),
                     "mask":maskname,"mask_sha256":sha(out/maskname)})
    sheet.save(out/"contact_sheet.png")
    return {"views":data,"source_faces":len(faces),
            "faces_rendered_per_view":len(chosen),
            "sampling_used":len(chosen)<len(faces),
            "contact_sheet_sha256":sha(out/"contact_sheet.png"),
            "actual_obj_diagnostic_render":True,
            "gpu_renderer_or_photorealism_test":False}

def compare_mask(candidate:Path,reference:Path):
    """Compare manually prepared binary mask (white subject/black background).

    This compares masks after stretching to shared 256x256, so it is strictly
    a silhouette heuristic, NOT a shape ground truth for uncropped photos.
    """
    from PIL import Image
    with Image.open(candidate) as generated, Image.open(reference) as actual:
        cand=generated.convert("L").resize((256,256))
        ref=actual.convert("L").resize((256,256))
        if ref.getextrema()[0]>30 or ref.getextrema()[1]<225:
            raise ValueError("Reference must be a binary black/white subject mask")
        a=[x>=128 for x in cand.getdata()]
        b=[x>=128 for x in ref.getdata()]
    overlap=sum(x and y for x,y in zip(a,b))
    union=sum(x or y for x,y in zip(a,b))
    return {"mask_reference_sha256":sha(reference),
            "source_mask_sha256":sha(candidate),
            "silhouette_iou":round(overlap/union,6) if union else 0,
            "silhouette_only_not_reference_likeness":True,
            "artist_acceptance":False}

def inspect(src:Path,out:Path, *, gltf:Path|None=None, reference_mask:Path|None=None,
            render_faces:int=MAX_RENDER_FACES):
    if src.suffix.lower()!=".obj" or not src.is_file():
        raise ValueError("A real, existing, triangulated .obj source is required")
    if not 1<=render_faces<=10000:
        raise ValueError("Face sampling budget must be between 1 and 10000")
    out.mkdir(parents=True,exist_ok=True)
    vertices,uvs,normals,faces=read_obj(src)
    quality=inspect_obj(src)
    uv=uv_evidence(vertices,uvs,faces)
    visual=projected_frames(vertices,faces,out/"views",limit=render_faces)
    structural=check_gltf(gltf) if gltf else None
    comparisons=compare_mask(out/"views/mask_00.png",reference_mask) if reference_mask else None
    defects=[]
    if quality["degenerate_triangles"]:
        defects.append("Degenerate source OBJ triangles: "+str(quality["degenerate_triangles"]))
    if quality["duplicate_triangles"]:
        defects.append("Duplicate source OBJ triangles: "+str(quality["duplicate_triangles"]))
    if uv["collapsed_uv_faces"]:
        defects.append("Collapsed UV triangle mapping: "+str(uv["collapsed_uv_faces"]))
    if structural and structural["errors"]:
        defects.extend("glTF: "+e for e in structural["errors"])
    warnings=[]
    if uv["uv_coverage"]<.999:
        warnings.append("UV coordinates missing on some triangles; author UVs before PBR production")
    if quality["nonmanifold_edges"]:
        warnings.append("Non-manifold welded topology; artist must review if deliberately open")
    if quality["boundary_edges"]:
        warnings.append("Boundary edges detected; may be intentional on cloth, terrain or vegetation")
    if not comparisons:
        warnings.append("No human reference mask supplied; likeness cannot be evaluated")
    result={"schema_version":1,"engine":"VEYLQUORIN",
            "short_name":"VQ","legacy_pipeline":"veilforge",
            "source_obj":src.name,"source_sha256":sha(src),
            "geometry":quality,"uv":uv,"gltf":structural,
            "visual":visual,"reference_comparison":comparisons,
            "blocking_technical_findings":defects,"manual_review_warnings":warnings,
            "technical_geometry_smoke_passed":not defects,
            "artistic_quality_approved":False,"reference_likeness_verified":False,
            "photorealism_verified":False,"physical_device_tested":False,
            "production_approved":False,"human_review_required":True}
    (out/"vq_model_report.json").write_text(json.dumps(result,indent=2)+"\n")
    (out/"vq_model_report.md").write_text(
        "# VQ model technical inspection\n\n"
        f"- Source OBJ: {src.name}, {len(faces)} triangles\n"
        f"- UV coverage: {uv['uv_coverage']:.1%}; collapsed UV faces: {uv['collapsed_uv_faces']}\n"
        f"- Real source diagnostic views: {len(visual['views'])}, face sampling: {visual['sampling_used']}\n"
        f"- Technical defects: {len(defects)}; reviewer warnings: {len(warnings)}\n"
        f"- Optional mask IoU: {comparisons['silhouette_iou'] if comparisons else 'not supplied'}\n"
        "- NOT approval for artistic likeness, PBR realism or importing into a game.\n\n"
        +"\n".join("- BLOCKER: "+d for d in defects)
        +"\n"+"\n".join("- REVIEW: "+w for w in warnings)+"\n")
    return result

def main():
    p=argparse.ArgumentParser(description="VQ inspect an actual exported triangulated OBJ")
    p.add_argument("--obj",required=True,type=Path)
    p.add_argument("--gltf",type=Path)
    p.add_argument("--reference-mask",type=Path,
                   help="Optional manually segmented black/white reference PNG, not an ordinary photo")
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--render-faces",type=int,default=MAX_RENDER_FACES)
    args=p.parse_args()
    r=inspect(args.obj,args.out,gltf=args.gltf,
              reference_mask=args.reference_mask,render_faces=args.render_faces)
    print("VQ_MODEL_INSPECT",r["technical_geometry_smoke_passed"],
          "source",r["source_obj"],"angles",len(r["visual"]["views"]))
    if not r["technical_geometry_smoke_passed"]:
        raise SystemExit(1)

if __name__=="__main__":
    main()
