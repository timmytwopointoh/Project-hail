#!/usr/bin/env python3
"""Bounded, copy-on-write VQ model rewrite proposals from real Android QA.

Auto-generates ONE allowlisted sword thickness candidate from immutable model
evidence. The proposal is NOT inserted into the Android scene/game; only a
later separately approved build+Android screenshot comparison can accept it.
No model/scene/review source file is ever overwritten.
"""
from __future__ import annotations
import argparse,hashlib,json,math
from pathlib import Path
from engine import read_obj,inspect_obj
from vq_brushes import _face_materials
from vq_model_tools import inspect as inspect_source

ALLOWED={"ceremonial_sword":"view_visibility"}
MAX_TASKS=25
MAX_RELATIVE_SHIFT=.008
MAX_AXIS_GAIN=1.08

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def specialist_approval(tasks_file, task_pack, selected, approval_file, source_sha):
    """A REVIEW ticket is not a model-edit authorization."""
    if approval_file is None:
        return None
    if len(selected)!=1:
        raise ValueError("No single reviewed geometry issue")
    task=selected[0]
    frames=task.get("camera_view_evidence")
    if task.get("screenshot_provenance_verified") is not True or not isinstance(frames,list) or len(frames)!=14:
        raise ValueError("Missing SHA-verified Android screenshot evidence")
    hashes=[row.get("sha256") for row in frames if isinstance(row,dict)]
    if len(hashes)!=14 or len(set(hashes))!=14 or any(
        not isinstance(h,str) or len(h)!=64 or any(c not in "0123456789abcdef" for c in h)
        for h in hashes):
        raise ValueError("Invalid Android screenshot hashes")
    path=Path(approval_file)
    if not path.is_file() or path.resolve()==tasks_file.resolve():
        raise ValueError("Separate specialist review file required")
    review=json.loads(path.read_text())
    views=review.get("non_edge_on_view_indices")
    if not isinstance(views,list) or len(views)<2 or len(set(views))!=len(views) or any(
        type(i)!=int or i<0 or i>=14 for i in views):
        raise ValueError("Specialist must identify multiple non-edge-on views")
    if (review.get("decision")!="confirmed_geometry_defect" or
        review.get("asset")!=task["asset"] or review.get("task_id")!=task["id"] or
        review.get("source_commit")!=source_sha or
        review.get("run_id")!=task_pack.get("github_actions_run_id") or
        review.get("handoff_sha256")!=sha(tasks_file) or
        review.get("frame_sha256")!=hashes or
        not isinstance(review.get("reason"),str) or len(review["reason"].strip())<30):
        raise ValueError("Specialist review does not match original Android evidence")
    return sha(path)

def rewrite(tasks_file,source_dir,out,*,source_sha,review_approval=None):
    tasks_file=Path(tasks_file);source_dir=Path(source_dir);out=Path(out)
    task_pack=json.loads(tasks_file.read_text())
    if not isinstance(source_sha,str) or len(source_sha)!=40 or any(c not in "0123456789abcdef" for c in source_sha):
        raise ValueError("Invalid source Git commit")
    if task_pack.get("source_commit")!=source_sha or task_pack.get("all_semantic_warnings_accounted_for") is not True or task_pack.get("ready_for_automated_model_rewrite") is not False:
        raise ValueError("Unverified or stale actual emulator handoff")
    tasks=task_pack.get("tasks")
    if not isinstance(tasks,list) or len(tasks)>MAX_TASKS:
        raise ValueError("Too many or malformed feedback tickets")
    selected=[t for t in tasks if isinstance(t,dict) and
              t.get("asset") in ALLOWED and
              t.get("diagnostic")==ALLOWED[t["asset"]] and
              t.get("emulator_role")=="props-equipment" and
              t.get("source_commit")==source_sha and
              t.get("screenshots_in_evidence")==14 and
              t.get("automatic_model_edit") is False and
              t.get("auto_promote") is False and
              t.get("minimum_foreground_coverage",1)<.006]
    if len(selected)>1:
        raise ValueError("Duplicate eligible model-rewrite tickets")
    heuristic_count=len(selected)
    approval_sha=specialist_approval(tasks_file,task_pack,selected,review_approval,source_sha)
    if approval_sha is None:
        selected=[]
    out.mkdir(parents=True,exist_ok=True)
    result={"schema_version":1,"milestone":"VQ-auto-rewrite-v1","source_commit":source_sha,
            "feedback_sha256":sha(tasks_file),"tickets_received":len(tasks),
            "heuristic_tickets":heuristic_count,"eligible_tickets":len(selected),
            "review_approval_sha256":approval_sha,"specialist_review_required":True,
            "candidates":[],
            "protected_original_source":True,"auto_promotion":False,
            "android_candidate_visual_qa_passed":False,"artistic_acceptance":False}
    if selected:
        ticket=selected[0];ident=ticket["asset"]
        src=source_dir/(ident+".obj")
        manifest_file=source_dir/"asset_manifest.json"
        if not src.is_file() or src.is_symlink() or not manifest_file.is_file():
            raise ValueError("Missing original verified asset source")
        manifest=json.loads(manifest_file.read_text())
        if (manifest.get("id")!=ident or manifest.get("source_obj")!=src.name or
            manifest.get("obj_sha256")!=sha(src) or
            manifest.get("production_approved") is not False or
            manifest.get("manual_visual_review_required") is not True):
            raise ValueError("Asset source manifest hash or nonapproval mismatch")
        vertices,uvs,normals,faces=read_obj(src)
        if any(not all(math.isfinite(v) for v in row[:3]) for row in vertices):
            raise ValueError("Source has invalid coordinates")
        # Only widen the thinner X/Z dimension; never adjust the sword's
        # vertical length. Nonuniform transform has positive determinant.
        extents=[max(v[k] for v in vertices)-min(v[k] for v in vertices) for k in range(3)]
        major=max(extents)
        axis=0 if extents[0]<=extents[2] else 2
        if major<=1e-8 or extents[axis]<=1e-8:
            raise ValueError("Sword has invalid/nonrevisable source proportions")
        mids=[(max(v[k] for v in vertices)+min(v[k] for v in vertices))/2 for k in range(3)]
        gain=min(MAX_AXIS_GAIN,1+2*major*MAX_RELATIVE_SHIFT/extents[axis])
        if gain<=1 or gain>MAX_AXIS_GAIN:
            raise ValueError("Unbounded rewrite")
        src_text=src.read_text(encoding="utf-8")
        lines=[];max_shift=0.;nv=nn=0
        for line in src_text.splitlines(keepends=True):
            chunks=line.partition("#")[0].strip().split()
            if chunks and chunks[0]=="v":
                p=list(map(float,chunks[1:4]))
                new=p[axis]+(p[axis]-mids[axis])*(gain-1)
                max_shift=max(max_shift,abs(new-p[axis]))
                p[axis]=new
                lines.append("v "+" ".join(f"{x:.10g}" for x in p)+
                             (" "+" ".join(chunks[4:]) if len(chunks)>4 else "")+"\n")
                nv+=1
            elif chunks and chunks[0]=="vn":
                n=list(map(float,chunks[1:4]))
                n[axis]/=gain # inverse transpose for nonuniform scaling
                norm=math.sqrt(sum(x*x for x in n))
                if norm<1e-12:
                    raise ValueError("Invalid source vertex normal")
                n=[x/norm for x in n]
                lines.append("vn "+" ".join(f"{x:.10g}" for x in n)+"\n")
                nn+=1
            else:lines.append(line)
        if nv!=len(vertices) or nn!=len(normals):
            raise ValueError("OBJ rewritten out of alignment")
        if not 0<max_shift<=major*MAX_RELATIVE_SHIFT+1e-7:
            raise ValueError("Rewrite exceeded displacement budget")
        dest=out/(ident+"_candidate.obj")
        if dest.resolve()==src.resolve() or dest.exists():
            raise ValueError("Refuse source overwrite or candidate collision")
        dest.write_text("".join(lines),encoding="utf-8")
        try:
            after=inspect_obj(dest);before=inspect_obj(src)
            protected=["triangles","vertices_raw","boundary_edges","nonmanifold_edges",
                       "degenerate_triangles","duplicate_triangles","uvs","normals"]
            if any(before[k]!=after[k] for k in protected):
                raise ValueError("Automatic rewrite altered source topology/attributes")
            if _face_materials(src,len(faces))!=_face_materials(dest,len(faces)):
                raise ValueError("Automatic rewrite altered material assignments")
            if read_obj(src)[3]!=read_obj(dest)[3]:
                raise ValueError("Automatic rewrite changed face reference layout")
            # Render source and candidate from real OBJ triangles at all 14
            # cameras, but do NOT mistake this software check for Android QA.
            baseline=inspect_source(src,out/"original_review",render_faces=1200)
            candidate=inspect_source(dest,out/"candidate_review",render_faces=1200)
            if not (baseline["technical_geometry_smoke_passed"] and
                    candidate["technical_geometry_smoke_passed"]):
                raise ValueError("Model source 14-angle technical QA failed")
            if not (len(baseline["visual"]["views"])==len(candidate["visual"]["views"])==14):
                raise ValueError("Missing real-source camera views")
        except Exception:
            dest.unlink(missing_ok=True)
            raise
        result["candidates"].append({
            "asset":ident,"ticket_id":ticket["id"],
            "operation":"small_horizontal_minor_axis_thickness_adjustment",
            "axis":"x" if axis==0 else "z","gain":round(gain,6),
            "max_displacement":round(max_shift,8),
            "relative_displacement_limit":MAX_RELATIVE_SHIFT,
            "source_obj_sha256":sha(src),"candidate_obj_sha256":sha(dest),
            "source_mesh_faces":before["triangles"],"candidate_mesh_faces":after["triangles"],
            "original_14_views":14,"candidate_14_views":14,
            "source_manifest_sha256":sha(manifest_file),
            "source_file_modified":False,"next_stage":"separate Android on/off candidate comparison",
            "approval":"pending_android_and_artist_review"})
    (out/"auto_rewrite_candidates.json").write_text(json.dumps(result,indent=2)+"\n")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--tasks",required=True,type=Path)
    p.add_argument("--source-dir",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--source-sha",required=True)
    p.add_argument("--review-approval",type=Path,default=None)
    a=p.parse_args()
    row=rewrite(a.tasks,a.source_dir,a.out,source_sha=a.source_sha,
                review_approval=a.review_approval)
    print("VQ_AUTO_REWRITE_CANDIDATES",len(row["candidates"]),"from",
          row["tickets_received"],"emulator warning tasks")
if __name__=="__main__":main()
