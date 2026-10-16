#!/usr/bin/env python3
"""Audits one 50-slot wave and creates a human-review-only shortlist."""
import json
from pathlib import Path
import sys

TEAMS={
    "front_silhouette","side_silhouette","head_cranium","jaw_profile",
    "shoulders","torso","pelvis","hands_forearms","thighs_calves","feet"
}

def main(root:Path):
    reports=[]
    for team in sorted(TEAMS):
        # GitHub's artifact downloader nests each team's root under its
        # artifact NAME, not under the original local team folder.
        matches=[]
        for candidate in root.rglob("manager_review.json"):
            report=json.loads(candidate.read_text())
            if report.get("team")==team:matches.append((candidate,report))
        if len(matches)!=1:
            raise ValueError("Expected one independently produced manager report for "+team+
                             " got "+str(len(matches)))
        r=matches[0][1]
        if (r.get("team")!=team or r.get("micro_edits_evaluated")!=320 or
            r.get("workers_reviewed")!=5 or
            r.get("accepted_for_game") is not False or
            r.get("human_visual_approval_required") is not True):
            raise ValueError("Incomplete or nonreviewable manager evidence")
        reports.append(r)
    ranks=sorted(reports,key=lambda x:x["proxy_score"])
    result={
        "wave":"M20 reference anatomy",
        "number_of_anatomy_teams":10,
        "number_of_independent_worker_slots":50,
        "parameter_mutations_evaluated":sum(r["micro_edits_evaluated"] for r in reports),
        "manual_visual_signoff":False,
        "automatic_source_changes":0,
        "accepted_for_game":False,
        "reference_pixel_similarity_measured":False,
        "next_review_priority":ranks[:5],
        "all_teams":ranks
    }
    out=Path("inspection_output/wave-ranking")
    out.mkdir(parents=True,exist_ok=True)
    (out/"wave_leaderboard.json").write_text(json.dumps(result,indent=2)+"\n")
    summary=[
        "# VEILBOUND M20 — 50-worker human geometry wave",
        "",
        "Produced by 10 independent teams × 5 bounded numeric candidates × 64 "+
        "small measured mutations = **3,200 evaluated micro-mutations**.",
        "",
        "**NOT 3,200 committed edits. NOT 50 trained AI coding models.** "+
        "Outputs are unmerged proportions and actual original 3D four-angle renders.",
        "",
        "**None is declared photorealistic**; approximate landmark errors "+
        "cannot establish likeness to the user's reference photograph.",
        "",
        "| Review priority | Anatomy team | Proportion score (lower=better) |",
        "|---:|---|---:|"
    ]
    summary += [f"| {i+1} | {r['team']} | {r['proxy_score']:.3f} |"
                for i,r in enumerate(ranks)]
    summary.extend(["","Inspect each team's `front.png`, `side.png`, "+
        "`back.png`, and `three_quarter.png` before promoting any geometry.",
        "Perform topology/weighted-bone tests and four Android emulators on the "+
        "chosen **reviewed** model only; never silently merge parameter suggestions."])
    (out/"manager_human_review.md").write_text("\n".join(summary)+"\n")
    print(json.dumps({k:result[k] for k in [
        "number_of_anatomy_teams","number_of_independent_worker_slots",
        "parameter_mutations_evaluated","accepted_for_game"]}))

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("Usage: human_wave_manager.py <downloaded artifacts root>")
    main(Path(sys.argv[1]))
