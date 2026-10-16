#!/usr/bin/env python3
"""VQ Studio bounded reviewed parametric corrections.

A Trion correction is a new immutable source recipe, not an in-place
mutation of a running job. Arbitrary prompt text never executes as code.
"""
import argparse
import json
import math
from pathlib import Path

RATIOS={"original":1.0,"smaller":0.85,"larger":1.15}


def write_adjusted(catalog:Path,asset_id:str,adjustment:str,out:Path)->dict:
    if adjustment not in RATIOS:raise ValueError("Unsupported VQ geometry adjustment")
    data=json.loads(catalog.read_text(encoding="utf-8"))
    if data.get("schema_version")!=1 or not isinstance(data.get("assets"),list):
        raise ValueError("Unknown catalog schema")
    options=[x for x in data["assets"] if x.get("id")==asset_id]
    if len(options)!=1:raise ValueError("Asset is missing or ambiguous")
    spec=options[0]
    original=spec.get("scale",1)
    if not isinstance(original,(int,float)) or isinstance(original,bool):
        raise ValueError("Invalid source scale")
    if not math.isfinite(float(original)):
        raise ValueError("Source scale is not finite")
    final=round(float(original)*RATIOS[adjustment],6)
    if not 0.25<=final<=3:
        raise ValueError("Adjusted model scale exceeds tested boundaries")
    spec["scale"]=final
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
    return {"id":asset_id,"scale_factor":RATIOS[adjustment],
            "original_scale":original,"source_scale":final,
            "adjustment":adjustment,
            "artistic_quality_approved":False,"production_approved":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--catalog",type=Path,required=True)
    p.add_argument("--id",required=True)
    p.add_argument("--adjustment",choices=sorted(RATIOS),required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result=write_adjusted(a.catalog,a.id,a.adjustment,a.out)
    print("VQ_REVIEWED_GEOMETRY_ADJUSTMENT",json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
