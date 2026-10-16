#!/usr/bin/env python3
"""Deterministic 50-slot anatomy exploration; NO image intelligence claims.

Ten manager teams operate five workers each, 64 parameter micro-candidates per
worker (= 3,200 evaluated proportion edits per wave). A score based on manually
extracted, approximate human landmarks is a search PRIOR, not a verdict that
the model resembles the user's reference sheet. Never edits Android source.
All candidates remain manual-review-only until screenshots, topology, joints,
and device QA are approved.
"""
import argparse
import hashlib
import json
import math
import random
from pathlib import Path

TEAMS = {
    "front_silhouette": (0, 1, 2, 4),
    "side_silhouette": (3, 6, 7, 9),
    "head_cranium": (6, 7, 9),
    "jaw_profile": (6, 7, 9),
    "shoulders": (0, 1, 3),
    "torso": (2, 3, 4),
    "pelvis": (2, 4, 5),
    "hands_forearms": (0, 1, 10),
    "thighs_calves": (4, 5, 8),
    "feet": (5, 8, 11),
}
LABELS = ["shoulder_span", "deltoid", "waist", "ribcage", "pelvis",
          "quadriceps", "cranium", "jaw", "calves", "nose", "forearms", "feet"]
STEPS = 64  # 10 teams x 5 workers x 64 candidate edits = 3200 actual evaluations


def landmarks(c):
    shoulder = 2 * (.445 * c[0] + .161 * c[1])
    head = .354 * c[6]
    waist = .552 * c[2]
    hip = 2 * (.207 * c[4] + .175 * c[5])
    return {
        "shoulder_head_width": shoulder / head,
        "waist_shoulder": waist / shoulder,
        "hip_shoulder": hip / shoulder,
        "rib_waist": (.71 * c[3]) / waist,
        "jaw_head": (.264 * c[7]) / head,
        "calf_thigh": (.112 * c[8]) / (.161 * c[5]),
        "upper_forearm": (.128 * c[1]) / (.094 * c[10]),
        "foot_head": (.50 * c[11]) / head,
        "nose_head": (.06 * c[9]) / head,
    }


# Approximate anatomy targets derived manually from the approved character
# sheet. No false claim of automated pixel/image similarity optimization.
TARGETS = {
    "shoulder_head_width": (3.42, .18),
    "waist_shoulder": (.475, .055),
    "hip_shoulder": (.608, .065),
    "rib_waist": (1.30, .09),
    "jaw_head": (.765, .055),
    "calf_thigh": (.705, .055),
    "upper_forearm": (1.40, .12),
    "foot_head": (1.38, .11),
    "nose_head": (.175, .036),
}


def score(values):
    m = landmarks(values)
    errors = {name: ((m[name] - goal) / tolerance) ** 2
              for name, (goal, tolerance) in TARGETS.items()}
    # Bias toward minimal plausible anatomy edits, not extreme body shapes.
    regularization = sum(((v - 1) / .14)**2 * .22 for v in values)
    return sum(errors.values()) + regularization


def run_worker(team, slot, out):
    out.mkdir(parents=True, exist_ok=True)
    seed=int.from_bytes(hashlib.sha256(
        (team + ":" + str(slot) + ":m20").encode()).digest()[:8], "big")
    rng=random.Random(seed)
    controls=[1.0]*12
    current=score(controls)
    best=controls[:]
    best_value=current
    mutations=[]
    fields=TEAMS[team]
    for i in range(STEPS):
        idx=rng.choice(fields)
        trial=controls[:]
        variance=.016 * (1 - .62 * i/STEPS)
        change=rng.uniform(-variance, variance)
        trial[idx]=max(.83,min(1.17,round(trial[idx]+change,6)))
        value=score(trial)
        # Conservative small-step simulated annealing, but record only
        # tried proposals, not imaginary successfully accepted source edits.
        temp=.16*(1-i/STEPS)
        accepted=value<current or rng.random()<math.exp(
            max(-100, min(0,(current-value)/max(.00001,temp))))
        if accepted:
            controls=trial
            current=value
        if value<best_value:
            best=trial
            best_value=value
        mutations.append({"step":i+1,"parameter":LABELS[idx],
            "before":round(controls[idx]-change if accepted else controls[idx],6),
            "proposed":trial[idx],"proxy_score":round(value,6),
            "accepted":accepted,"best_proxy_score":round(best_value,6)})
    manifest={
        "team":team,"worker_slot":slot,"source":"bounded_numeric_anatomy_optimizer",
        "micro_edits_evaluated":len(mutations),
        "reference_pixel_analysis":False,
        "visually_approved":False,
        "promotable_without_human_review":False,
        "model_status":"unreviewed_geometry_candidate",
        "best_proxy_score":round(best_value,7),
        "parameters":best,
        "approximate_proportions":landmarks(best),
    }
    (out/"worker_result.json").write_text(json.dumps(manifest,indent=2)+"\n")
    with (out/"micro_edit_journal.jsonl").open("w") as f:
        for record in mutations:
            f.write(json.dumps(record)+"\n")
    print(json.dumps({"team":team,"slot":slot,"score":best_value,
                      "mutations_evaluated":STEPS}))


def select_team(team, root):
    valid=[]
    for slot in range(5):
        item=json.loads((root/str(slot)/"worker_result.json").read_text())
        if item.get("team")!=team or item.get("micro_edits_evaluated")!=STEPS:
            raise ValueError("Worker evidence absent or cross-team output")
        valid.append(item)
    winner=min(valid,key=lambda x:(x["best_proxy_score"],x["worker_slot"]))
    output={"team":team,"human_visual_approval_required":True,
        "accepted_for_game":False,"workers_reviewed":5,
        "micro_edits_evaluated":STEPS*5,
        "winner_slot":winner["worker_slot"],
        "proxy_score":winner["best_proxy_score"],
        "parameters":winner["parameters"],
        "approximate_proportions":winner["approximate_proportions"]}
    (root/"manager_review.json").write_text(json.dumps(output,indent=2)+"\n")
    print(",".join(str(n) for n in winner["parameters"]))


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--team",choices=TEAMS,required=True)
    p.add_argument("--slot",type=int)
    p.add_argument("--select",action="store_true")
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.select:
        select_team(args.team,args.out)
    else:
        if args.slot is None or not 0<=args.slot<5:
            p.error("Slot must be 0-4")
        run_worker(args.team,args.slot,args.out/str(args.slot))


if __name__=="__main__":
    main()
