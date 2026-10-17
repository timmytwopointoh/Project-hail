#!/usr/bin/env python3
"""Non-destructive source health/compatibility audit for VQ/VF engine modules.

No speculative dead-code deletion: other GitHub branches and app consumers
may rely on modules not imported by this particular workflow.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path

REQUIRED=[
"engine.py","factory.py","vq_brushes.py","vq_adaptive_remesh.py",
"vq_multimaterial_export.py","vq_refinement_pipeline.py",
"vq_mesh_baker.py","vq_uv_atlas.py","vq_uv_transfer.py","vq_sculpt_detail_patch.py","vq_model_tools.py",
"vq_quality_plan.py","vq_emulator_efficiency.py","vq_android_repair_handoff.py","provenance.py","vq_engine_health.py"]
def audit(root,out):
    root=Path(root).resolve()
    directory=root/"veilforge"
    issues=[];rows=[]
    if not (root/".github/workflows/vq-model-tools.yml").is_file():
        issues.append("Existing automated VQ tool workflow missing")
    for name in REQUIRED:
        p=directory/name
        if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(root):
            issues.append("Missing or unsafe engine module "+name);continue
        data=p.read_bytes()
        try:tree=ast.parse(data.decode("utf-8"),filename=name)
        except (SyntaxError,UnicodeDecodeError) as err:
            issues.append(f"{name}: unparseable Python source: {err}");continue
        funcs={}
        for node in tree.body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                funcs.setdefault(node.name,[]).append(node.lineno)
        for symbol,places in funcs.items():
            if len(places)>1:issues.append(f"{name}: shadowed/duplicate module symbol {symbol}: {places}")
        # A source module that accidentally checks out generated binary files
        # at its own path would be caught by strict UTF-8 and AST parsing.
        rows.append({"module":name,"sha256":hashlib.sha256(data).hexdigest(),
                     "bytes":len(data),"top_level_symbols":len(funcs)})
    # Scanning unrelated game/older branches for "unused" imports would
    # incorrectly flag external plug-ins, scripts and connector entrypoints.
    status={"schema_version":1,"engine":"VEYLQUORIN",
            "scope":"only explicitly required engine entrypoints",
            "modules_checked":len(rows),"required_modules":len(REQUIRED),
            "problems":issues,"technical_cleanup_gate_passed":not issues,
            "redundant_single_material_export_when_source_gltf_available":False,
            "unverified_orphan_code_deleted":False,
            "existing_game_modules_deleted":False,
            "other_worktrees_modified":False,
            "release_approved":False}
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"status":status,"modules":rows},indent=2)+"\n",encoding="utf-8")
    return status
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    row=audit(a.root,a.out)
    print("VQ_ENGINE_HEALTH",row["modules_checked"],"modules,",
          "passed=",row["technical_cleanup_gate_passed"])
    if row["problems"]:raise SystemExit(1)
if __name__=="__main__":main()
