#!/usr/bin/env python3
"""VQ M29 bounded multi-tool quality experiment on a real OBJ asset.

Runs non-destructive sculpt/smooth/stamp -> conforming adaptive subdivision ->
real glTF *single-material diagnostic preview* -> fourteen VQ OBJ inspection
views. Produces independent hashes and a rejectable quality-evidence pack.
This stage intentionally does not claim cinematic rendering, material baking,
multi-material finished glTF or Android import completion.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
from engine import inspect_obj
from vq_brushes import apply_brushes
from vq_adaptive_remesh import refine
from vq_model_tools import inspect
from gltf_export import export

def workflow(source,brush_recipe,refine_recipe,out,*,profile="stone",render_faces=4200):
    source=Path(source)
    out=Path(out)
    if not source.is_file():
        raise ValueError("A real readable OBJ source mesh is required")
    if source.resolve().is_relative_to(out.resolve()):
        raise ValueError("Refinement output cannot contain/overwrite original source")
    out.mkdir(parents=True,exist_ok=True)
    brush_out=out/"stage1_brushed.obj"
    sculpt_report=apply_brushes(
        source,json.loads(Path(brush_recipe).read_text(encoding="utf-8")),
        brush_out)
    refined=out/"stage2_refined.obj"
    remesh_report=refine(
        brush_out,json.loads(Path(refine_recipe).read_text(encoding="utf-8")),
        refined)
    preview_gltf=out/"stage2_single_material_diagnostic.gltf"
    gltf=export(refined,preview_gltf,profile=profile)
    vision=inspect(refined,out/"inspector",gltf=preview_gltf,
                   render_faces=render_faces)
    start=inspect_obj(source)
    final=inspect_obj(refined)
    keys=("boundary_edges","nonmanifold_edges","degenerate_triangles",
          "duplicate_triangles")
    unexpected=[key for key in keys if start[key]!=final[key]]
    if unexpected or not vision["technical_geometry_smoke_passed"]:
        raise ValueError("Combined refinement failed geometry or UV inspection: "+str(unexpected))
    report={
        "schema_version":1,"engine":"VEYLQUORIN","milestone":"M29",
        "workflow":["source","sculpt_smooth_stamp","conforming_adaptive_subdivision",
                    "single_material_diagnostic_gltf","14_real_obj_view_diagnostics"],
        "source_obj_sha256":sha256(source.read_bytes()).hexdigest(),
        "brushed_sha256":sculpt_report["candidate_sha256"],
        "remeshed_sha256":remesh_report["candidate_sha256"],
        "source_triangles":start["triangles"],
        "brushed_triangles":sculpt_report["candidate_triangles"],
        "remeshed_triangles":final["triangles"],
        "adaptive_interior_edges":remesh_report["edges_selected"],
        "material_source_ids":["original OBJ usemtl assignments preserved in OBJ"],
        "multi_material_finished_gltf":False,
        "gltf_single_material_diagnostic_only":True,
        "source_topology_metrics":{k:start[k] for k in keys},
        "refined_topology_metrics":{k:final[k] for k in keys},
        "checked_angles":len(vision["visual"]["views"]),
        "gltf_diagnostic_integrity_passed":vision["gltf"]["structural_smoke_passed"],
        "uv_collapsed_faces":vision["uv"]["collapsed_uv_faces"],
        "brush_and_refine_technical_gates_passed":True,
        "android_render_verified":False,
        "rigged_animation_verified":False,
        "reference_likeness_verified":False,
        "artist_approval":False,"game_ready":False,
        "next_review":"Evaluate actual before/after details in 14 angles, then build a true multi-material glTF candidate and test with the Android emulators."}
    (out/"refinement_evidence.json").write_text(json.dumps(report,indent=2)+"\n")
    text=["# VQ multi-stage quality experiment","",
          "This is a real geometry editing/export/inspection trial, not game approval.","",
          f"Original triangles: {report['source_triangles']}",
          f"After region brushes: {report['brushed_triangles']}",
          f"After adaptive subdivision: {report['remeshed_triangles']}",
          f"Conforming edges split: {report['adaptive_interior_edges']}",
          f"Real source diagnostic views: {report['checked_angles']}",
          f"Topology regressions: {len(unexpected)}",
          "Material warning: the preview glTF intentionally collapses materials and is NOT a production package.",
          "Android validation and aesthetic approval remain open."]
    (out/"refinement_evidence.md").write_text("\n".join(text)+"\n")
    return report

def main():
    p=argparse.ArgumentParser(description="Replay real VQ sculpt, remesh, glTF preview and inspect")
    p.add_argument("--obj",type=Path,required=True)
    p.add_argument("--brush",type=Path,required=True)
    p.add_argument("--refine",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    r=workflow(a.obj,a.brush,a.refine,a.out)
    print("VQ_M29_END_TO_END_REFINEMENT_PASS",
          json.dumps({"stages":len(r["workflow"]),"views":r["checked_angles"],
                      "original_faces":r["source_triangles"],
                      "refined_faces":r["remeshed_triangles"],
                      "android_approved":r["android_render_verified"]}))
if __name__=="__main__":main()
