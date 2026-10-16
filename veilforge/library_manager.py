#!/usr/bin/env python3
"""VEILFORGE M3 asset library manager; read-only review and bounded CI matrix."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from factory import CATEGORIES, load_catalog

MAX_JOBS=24
VIEWS=("front","side","three_quarter","elevated")

def plan(catalog,out,github_output=None):
    specs=load_catalog(catalog)
    if len(specs)>MAX_JOBS:raise ValueError("More jobs requested than the audited maximum")
    matrix={"include":[{"id":key} for key in sorted(specs)]}
    result={"schema_version":1,"jobs":len(specs),"categories":sorted(
        {s["category"] for s in specs.values()}),"matrix":matrix,
        "approval":"review-only","auto_merge":False}
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/"library_plan.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    if github_output:
        with Path(github_output).open("a",encoding="utf-8") as f:
            f.write("matrix="+json.dumps(matrix,separators=(",",":"))+"\n")
    return result

def review(catalog,collected,out):
    specs=load_catalog(catalog)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    folders=list(Path(collected).rglob("asset_manifest.json"))
    problems=[]
    output={}
    for entry in folders:
        try:
            row=json.loads(entry.read_text(encoding="utf-8"))
            name=row["id"]
            if name in output or name not in specs:
                problems.append(f"Unexpected or duplicate asset: {name}");continue
            recipe=specs[name]
            if row["category"]!=recipe["category"] or row["detail"]!=recipe["detail"] or row["seed"]!=recipe["seed"]:
                problems.append(f"{name}: catalog metadata mismatch")
            if not isinstance(row["triangles"],int) or not 0<row["triangles"]<=row["budget"]:
                problems.append(f"{name}: invalid triangle budget")
            for stem in ("obj","gltf"):
                filename=row.get("source_obj" if stem=="obj" else "gltf")
                if filename!=name+"."+stem:
                    problems.append(f"{name}: unexpected {stem} filename");continue
                file=entry.parent/filename
                if not file.is_file():
                    problems.append(f"{name}: missing {stem} source/export");continue
                digest=hashlib.sha256(file.read_bytes()).hexdigest()
                if digest!=row[stem+"_sha256"]:
                    problems.append(f"{name}: altered {stem} bytes")
            gltfpath=entry.parent/(name+".gltf")
            if gltfpath.is_file():
                gltf=json.loads(gltfpath.read_text())
                if gltf.get("asset",{}).get("version")!="2.0":
                    problems.append(f"{name}: bad glTF version")
                if gltf.get("extras",{}).get("production_approved") is not False:
                    problems.append(f"{name}: prohibited automatic asset approval")
                buffers=gltf.get("buffers",[])
                if len(buffers)!=1 or buffers[0].get("uri")!=name+".bin":
                    problems.append(f"{name}: missing binary linkage")
                elif not (entry.parent/(name+".bin")).is_file() or (
                    (entry.parent/(name+".bin")).stat().st_size!=buffers[0]["byteLength"]):
                    problems.append(f"{name}: binary buffer length mismatch")
                if len(gltf.get("meshes",[{}])[0].get("primitives",[]))!=len(row.get("materials",[])):
                    problems.append(f"{name}: submesh/material mismatch")
            preview=entry.parent/"previews"
            for label in VIEWS:
                path=preview/("view_"+label+".png")
                if not path.is_file() or path.stat().st_size<1000:
                    problems.append(f"{name}: missing actual geometry preview {label}")
            if not (preview/"contact_sheet.png").is_file():
                problems.append(f"{name}: missing review sheet")
            corners=row.get("source_vertex_corners")
            indexed=row.get("indexed_vertices")
            saved=row.get("vertices_saved")
            bytes_size=row.get("gltf_binary_bytes")
            if (not all(isinstance(v,int) and not isinstance(v,bool)
                        for v in (corners,indexed,saved,bytes_size)) or
                corners!=row["triangles"]*3 or
                indexed<3 or indexed>corners or
                saved!=corners-indexed or bytes_size<32):
                problems.append(f"{name}: invalid indexed-mesh savings evidence")
            if gltfpath.is_file() and gltf.get("extras",{}).get("indexed_vertices")!=indexed:
                problems.append(f"{name}: indexed-mesh exporter/manifest mismatch")
            quality=row.get("mesh_quality",{})
            if quality.get("degenerate_triangles")!=0:
                problems.append(f"{name}: invalid degenerate geometry")
            if row.get("production_approved") is not False or row.get("manual_visual_review_required") is not True:
                problems.append(f"{name}: approval guard invalid")
            output[name]={"category":row["category"],"tier":row["detail"],
                "triangles":row["triangles"],"budget":row["budget"],
                "materials":len(row["materials"]),"boundaries":quality.get("boundary_edges"),
                "nonmanifold_edges":quality.get("nonmanifold_edges"),
                "vertex_corners":corners,"indexed_vertices":indexed,
                "vertices_saved":saved,"gltf_buffer_bytes":bytes_size,
                "review":"pending"}
        except (KeyError,ValueError,TypeError,OSError,IndexError) as error:
            problems.append(f"{entry}: invalid asset evidence: {error}")
    missing=sorted(set(specs)-set(output))
    for ident in missing:problems.append(f"Missing evidence: {ident}")
    categories={x["category"] for x in output.values()}
    missing_families=sorted(set(CATEGORIES)-categories)
    if missing_families:
        problems.append("Unexercised builder families: "+", ".join(missing_families))
    result={"schema_version":1,"engine":"VEILFORGE_M3","expected":len(specs),
        "complete":len(output),"categories_produced":sorted(categories),
        "assets":output,"evidence_passed":not problems,"problems":problems,
        "actual_game_integration_tested":False,"photorealism_approved":False,
        "production_approved":False,"future_families":"character/creatures, animation, VFX, audio, UI, physics, navmeshes, foliage systems",
        "note":"CPU geometry previews and source export are not physical-device acceptance."}
    (out/"library_review.json").write_text(json.dumps(result,indent=2)+"\n")
    md=["# VEILFORGE M3 — General-purpose asset factory","",
        f"**Evidence:** {len(output)}/{len(specs)} asset exports audited; {len(categories)}/{len(CATEGORIES)} producer families; structural gate {'PASS' if not problems else 'FAIL'}.",
        "","**All assets remain human-review only. No game files were edited.**","",
        "| Asset | Category | Tier | Triangles | Materials |",
        "|---|---|---|---:|---:|"]
    for ident,item in sorted(output.items()):
        md.append(f"| {ident} | {item['category']} | {item['tier']} | {item['triangles']} | {item['materials']} |")
    md+=["","Limitations: these are reproducible original procedural assets with scalar PBR materials and four diagnostic 3D views, not photorealistic sculptures or measured GPU benchmarks.","","Structural defects:"]
    md+=["- "+x for x in problems] if problems else ["- None in the tested production gates."]
    (out/"library_review.md").write_text("\n".join(md)+"\n")
    return result

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="mode",required=True)
    a=sub.add_parser("plan");a.add_argument("--catalog",type=Path,default=Path("veilforge/catalog.json"))
    a.add_argument("--out",type=Path,required=True);a.add_argument("--github-output",type=Path)
    a=sub.add_parser("review");a.add_argument("--catalog",type=Path,default=Path("veilforge/catalog.json"))
    a.add_argument("--collected",type=Path,required=True);a.add_argument("--out",type=Path,required=True)
    x=p.parse_args()
    if x.mode=="plan":
        data=plan(x.catalog,x.out,x.github_output)
        print("VEILFORGE_LIBRARY_PLAN",data["jobs"],"assets")
    else:
        data=review(x.catalog,x.collected,x.out)
        print("VEILFORGE_LIBRARY_REVIEW",data["complete"],"/",data["expected"],"passed=",data["evidence_passed"])
        if not data["evidence_passed"]:raise SystemExit(1)
if __name__=="__main__":
    main()
