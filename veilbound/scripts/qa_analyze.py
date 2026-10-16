#!/usr/bin/env python3
"""Compact automated visual/performance QA, run after each Android emulator test.

Inputs from the verified native emulator: PNGs, JSON report and recent logcat.
Outputs quantitative warnings and Markdown summary; human still reviews images.
"""
import argparse
import json
import re
from pathlib import Path

def analyze(folder):
    from PIL import Image, ImageFilter, ImageStat
    report_file=folder / "emulator_report.json"
    report=json.loads(report_file.read_text()) if report_file.is_file() else {}
    metrics=[]
    for path in sorted(folder.glob("*.png")):
        with Image.open(path) as img:
            rgb=img.convert("RGB")
            small=rgb.resize((240,135))
            stat=ImageStat.Stat(small)
            gray=small.convert("L")
            edge=gray.filter(ImageFilter.FIND_EDGES)
            # Sobel-like high frequency proxy, not subjective asset quality.
            mean_edge=ImageStat.Stat(edge).mean[0]
            metrics.append({
                "file":path.name,"size_bytes":path.stat().st_size,
                "resolution":[rgb.width,rgb.height],
                "mean_rgb":[round(v,1) for v in stat.mean],
                "std_rgb":[round(v,1) for v in stat.stddev],
                "edge_energy":round(mean_edge,2),
                "dark_coverage":round(
                    sum(v for k,v in enumerate(gray.histogram()[:35]))/(240*135),4)
            })
    logs=(folder/"logcat_recent.txt").read_text(errors="replace") if (folder/"logcat_recent.txt").is_file() else ""
    matches=re.findall(
        r"FRAME_QA fps=([\d.]+) draws=(\d+) static_vertices=(\d+) gl_error=(\d+)",
        logs)
    perf=[{"fps":float(f),"draw_calls":int(d),"static_vertices":int(v),
           "gl_error":int(e)} for f,d,v,e in matches]
    issue_codes=sorted(set(p["gl_error"] for p in perf if p["gl_error"]!=0))
    # Independent screenshots of each world asset. Compare central 3D stage,
    # not only text labels, to detect missing geometry and scene regressions.
    from PIL import ImageChops
    asset_names=("flagstone","cenotaph","reliquary","root_fan")
    asset_files=[folder/("01_world_asset_"+name+".png") for name in asset_names]
    asset_comparisons=[]
    if all(p.is_file() for p in asset_files):
        previous=None
        for name,path in zip(asset_names,asset_files):
            with Image.open(path) as im:
                rgb=im.convert("RGB")
                ww,hh=rgb.size
                stage=rgb.crop((int(ww*.29),int(hh*.23),
                                int(ww*.73),int(hh*.72))).resize((170,110))
                if previous is not None:
                    diff=ImageChops.difference(stage,previous)
                    delta=round(sum(ImageStat.Stat(diff).mean)/3,2)
                    asset_comparisons.append({
                        "asset":name,"stage_mean_absolute_change":delta})
                previous=stage
    warnings=[]
    if not metrics:warnings.append("No emulator PNG screenshots available")
    if any(not p.is_file() for p in asset_files):
        warnings.append("Studio asset screenshot(s) missing")
    if any(a["stage_mean_absolute_change"]<1.25 for a in asset_comparisons):
        warnings.append("Two distinct world assets look nearly identical in the studio")
    if report.get("status")!="passed":
        warnings.append("Android gameplay acceptance test did not pass")
    if issue_codes:warnings.append("Non-zero OpenGL error codes: "+str(issue_codes))
    if perf and min(x["fps"] for x in perf)<8:
        warnings.append("Slow software-emulator frame rate; measure on physical Android")
    # Startup splash intentionally starts on a near-flat dark gradient;
    # it is NOT an in-game black-frame failure. Inspect actual scene frames
    # instead. Never exclude Studio, traversal or combat evidence.
    scene_frames=[x for x in metrics if x["file"]!="00_startup_loading.png"]
    if not scene_frames:
        warnings.append("No gameplay scene screenshots available for blank-frame test")
    elif any(max(x["std_rgb"])<12 for x in scene_frames):
        warnings.append("Screenshot has low variation; inspect potential blank render")
    if len(perf)==0:warnings.append("No FPS samples in tail log; check renderer log retention")
    result={"emulator_test":report.get("status","missing"),
            "screenshots":metrics,"performance_samples":perf,
            "world_asset_stage_comparisons":asset_comparisons,
            "observed_fps_range":[round(min(x["fps"] for x in perf),1),
                                  round(max(x["fps"] for x in perf),1)] if perf else None,
            "warnings":warnings}
    (folder/"visual_quality_metrics.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# VEILBOUND QA — visual and renderer inspection","",
           "Emulator gameplay: **"+str(result["emulator_test"])+"**","",
           "| Screenshot | Brightness (RGB) | Detail proxy |", "|---|---|---|"]
    for image in metrics:
        lines.append("| "+image["file"]+" | "+", ".join(map(str,image["mean_rgb"]))+
                     " | "+str(image["edge_energy"])+" |")
    lines+=["","Frame samples: **"+str(len(perf))+"**", ""]
    lines+=["## World asset stage comparisons (pixel mean absolute delta)",""]
    for diff in asset_comparisons:
        lines.append("- "+diff["asset"]+": "+str(diff["stage_mean_absolute_change"]))
    lines.append("")
    if result["observed_fps_range"]:
        lines.append("Emulator FPS range: **"+str(result["observed_fps_range"])+"**")
    lines+=["","## Warnings"]+["- "+v for v in warnings]
    (folder/"visual_quality_summary.md").write_text("\n".join(lines)+"\n")
    print(json.dumps({"test":result["emulator_test"],"png_count":len(metrics),
                      "fps_samples":len(perf),"warnings":warnings},indent=2))
    # Fail only when a completed test exposed a real GL error.
    return 1 if issue_codes else 0

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,default=Path("inspection_output/veilbound"))
    args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    raise SystemExit(analyze(args.output))
