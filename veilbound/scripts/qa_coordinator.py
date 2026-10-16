#!/usr/bin/env python3
"""VEILBOUND QA coordinator: evidence -> deterministic, reviewable worker task plan.

No network calls or repository writes. Tests define priority, not an LLM.
Visual guesses and software-emulator FPS are never reported as confirmed
physical-device failures.
"""
import argparse
import json
from pathlib import Path

PRIORITY = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
RECOMMENDATIONS = {
    "emulator-smoke": ("P0", "qa", "Android gameplay acceptance failed",
        "Inspect the failing emulator input/state transition; preserve screenshots and logcat.",
        "Rebuild APK, install on Android 15 emulator, rerun full touch gameplay."),
    "studio-orbit": ("P1", "studio", "Model Atelier orbit control not visibly responding",
        "Check real touch orbit gesture, GL draw readiness and studio camera framing.",
        "Repeat real ADB swipe 3 times and assert quantifiable scene pixel movement."),
    "studio-controls": ("P1", "studio", "Model Atelier model/material/lighting controls failed",
        "Verify Android touch zones, dispatch ordering, and GL state transitions for model selector, lights and material modes. Do not assume a renderer bug.",
        "On Moto G (2025) viewport run real ADB taps; assert distinct item/light/material log transitions and capture visible stage frames."),
    "studio-enter": ("P1", "studio", "Model Atelier entrance or mesh initialization failed",
        "Trace title-screen atelier touch routing, initialization barriers and GL load markers without bypassing input.",
        "Launch the APK on Moto G-sized Android 15 emulator, open Model Atelier by touch and assert the expected GL readiness markers."),
    "missing-qa": ("P1", "qa", "No machine-readable visual QA report",
        "Make sure qa_analyze.py executes after the emulator and always uploads reports.",
        "Run emulator workflow and confirm visual_quality_metrics.json is uploaded."),
    "missing-images": ("P1", "qa", "Missing or insufficient emulator screenshots",
        "Repair screenshot capture and system-overlay handling; do not invent frames.",
        "Verify title, studio, exploration, attack, and lock-on PNG captures."),
    "gl-error": ("P0", "renderer", "Nonzero OpenGL error during rendering",
        "Inspect GL call logs and bindings, correct cause; do not suppress telemetry.",
        "Full emulator pass with repeated error-code sampling."),
    "asset-comparison": ("P1", "models", "Two studio assets have nearly identical world-stage images",
        "Check studio asset switching, camera framing and registered geometry.",
        "Regenerate actual model-studio screenshots and compare cropped 3D stage."),
    "blank-render": ("P1", "renderer", "Screenshot may be blank or obscured",
        "Check screenshot framing, overlays, draw loop and shading.",
        "Capture unobscured Android render and compare color statistics."),
    "slow-emulator": ("P2", "performance", "Software emulator sampled very low FPS",
        "Profile draw count, geometry and overdraw; validate on Motorola G 2025 before setting a hardware FPS failure.",
        "Collect physical-device FPS and frame times plus GPU diagnostics."),
    "fps-missing": ("P2", "qa", "No retained FPS telemetry",
        "Fix logcat sampling or report collection without inventing FPS.",
        "Confirm FRAME_QA entries in captured logcat."),
    "lock-untested": ("P2", "combat", "Target-lock activation not confirmed by telemetry",
        "Check target acquisition near an encounter; strengthen test to assert a valid target ID.",
        "Move near a living enemy, tap LOCK, assert target ID >= 0 and capture reticle."),
    "unknown-warning": ("P3", "qa", "Unclassified QA warning requires inspection",
        "Read the raw QA warning and assign a concrete test before patching.",
        "Add a deterministic regression test for the confirmed condition."),
}

def load_json(path):
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, UnicodeError, ValueError):
        return None

def create_plan(emulator=None, visual=None, *, commit=None):
    emulator = emulator if isinstance(emulator, dict) else {}
    visual = visual if isinstance(visual, dict) else None
    tasks = {}
    def add(code, evidence, *, title=None):
        if code in tasks:
            if evidence not in tasks[code]["evidence"]:
                tasks[code]["evidence"].append(evidence[:450])
            return
        severity, owner, heading, fix, test = RECOMMENDATIONS[code]
        tasks[code] = {"id": "VB-" + code.upper().replace("_", "-"),
                       "priority": severity, "worker": owner,
                       "title": title or heading, "evidence": [evidence[:450]],
                       "repair_guidance": fix, "required_test": test,
                       "confidence": "measurement" if code not in ("unknown-warning", "slow-emulator", "lock-untested") else "needs-verification"}
    if emulator.get("status") != "passed":
        error = str(emulator.get("error", "not recorded"))[:240]
        failure = error.lower()
        if "studio orbit" in failure or "model studio orbit" in failure:
            add("studio-orbit", "emulator_report.status=failed; error=" + error)
        elif ("studio model/material/light" in failure or
              "studio model/material" in failure):
            add("studio-controls", "emulator_report.status=failed; error=" + error)
        elif ("atelier button did not open" in failure or
              "atelier gl high-poly" in failure or
              "atlas / sculpt initialization" in failure):
            add("studio-enter", "emulator_report.status=failed; error=" + error)
        else:
            add("emulator-smoke", "emulator_report.status=" + str(emulator.get("status", "missing")) +
                "; error=" + error)
    if visual is None:
        add("missing-qa", "visual_quality_metrics.json absent, invalid or not a JSON object")
    else:
        imgs = visual.get("screenshots", [])
        if not isinstance(imgs, list) or len(imgs) < 10:
            add("missing-images", "Screenshot metric count=" + str(len(imgs) if isinstance(imgs, list) else "invalid"))
        perf = visual.get("performance_samples", [])
        if not isinstance(perf, list):
            perf = []
        gl_errors = sorted({str(p.get("gl_error")) for p in perf
                            if isinstance(p, dict) and p.get("gl_error") not in (None, 0)})
        if gl_errors:
            add("gl-error", "Nonzero FRAME_QA GL codes: " + ", ".join(gl_errors))
        if not perf:
            add("fps-missing", "No valid performance sample entries")
        fps = [p["fps"] for p in perf if isinstance(p, dict)
               and isinstance(p.get("fps"), (int, float)) and not isinstance(p["fps"], bool)]
        if fps and min(fps) < 8:
            add("slow-emulator", "Software-emulator minimum FPS=" + str(round(min(fps), 2)))
        for entry in visual.get("world_asset_stage_comparisons", []):
            if isinstance(entry, dict):
                delta = entry.get("stage_mean_absolute_change")
                if isinstance(delta, (int, float)) and delta < 1.25:
                    add("asset-comparison", str(entry.get("asset", "unknown")) + " stage pixel delta=" + str(delta))
        warnings = visual.get("warnings", [])
        for warning in warnings if isinstance(warnings, list) else []:
            if not isinstance(warning, str):
                continue
            w = warning.lower()
            if "non-zero opengl" in w or "nonzero opengl" in w:
                add("gl-error", warning)
            elif "low variation" in w or "blank render" in w:
                add("blank-render", warning)
            elif "screenshot" in w and ("missing" in w or "no emulator" in w):
                add("missing-images", warning)
            elif "asset" in w and ("identical" in w or "nearly" in w):
                add("asset-comparison", warning)
            elif "slow software-emulator" in w:
                add("slow-emulator", warning)
            elif "fps samples" in w or "fps sample" in w:
                add("fps-missing", warning)
            elif "gameplay acceptance" in w:
                add("emulator-smoke", warning)
            else:
                add("unknown-warning", warning)
    target = emulator.get("lock_target_diagnostic")
    if emulator.get("status") == "passed" and emulator.get("lock_button_exercised") and (
            not isinstance(target, int) or isinstance(target, bool) or target < 0):
        add("lock-untested", "Lock button tapped but target diagnostic=" + repr(target))
    ordered = sorted(tasks.values(), key=lambda item: (PRIORITY[item["priority"]], item["id"]))
    blockers = [t["id"] for t in ordered if t["priority"] in ("P0", "P1")]
    return {"schema_version": 1, "project": "VEILBOUND",
            "source_commit": commit or "unknown",
            "emulator_status": emulator.get("status", "missing"),
            "release_gate": "blocked" if blockers else ("needs-review" if ordered else "clear"),
            "blocker_ids": blockers, "task_count": len(ordered), "tasks": ordered,
            "note": "Priorities describe test evidence, not verified game photorealism. "
                    "P2 emulator FPS is not phone hardware measurement."}

def markdown(plan):
    lines = ["# VEILBOUND — automatic QA repair queue", "",
             "Source commit: `" + str(plan["source_commit"]) + "`  ",
             "Emulator result: **" + str(plan["emulator_status"]) + "**  ",
             "Release gate: **" + plan["release_gate"] + "**", "",
             "| Priority | Worker | Finding |", "|---|---|---|"]
    for task in plan["tasks"]:
        lines.append("| " + task["priority"] + " | " + task["worker"] + " | " + task["title"].replace("|", "/") + " |")
    lines.extend(["", "## Evidence and acceptance steps", ""])
    if not plan["tasks"]:
        lines.append("No machine-detectable issues in supplied evidence. Visual review and physical-device QA still required.")
    for task in plan["tasks"]:
        lines.extend(["### " + task["id"] + " · " + task["title"], "",
                      "**Owner:** " + task["worker"] + " · **Severity:** " + task["priority"],
                      "**Evidence:** " + "; ".join(task["evidence"]),
                      "**Proposal:** " + task["repair_guidance"],
                      "**Verification:** " + task["required_test"], ""])
    return "\n".join(lines) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=Path("inspection_output/veilbound"))
    ap.add_argument("--output", type=Path)
    ap.add_argument("--commit", default="unknown")
    args = ap.parse_args()
    dest = args.output or args.input
    dest.mkdir(parents=True, exist_ok=True)
    plan = create_plan(load_json(args.input / "emulator_report.json"),
                       load_json(args.input / "visual_quality_metrics.json"), commit=args.commit)
    (dest / "task_plan.json").write_text(json.dumps(plan, indent=2) + "\n")
    (dest / "task_plan.md").write_text(markdown(plan))
    print(json.dumps({"release_gate": plan["release_gate"],
                      "task_count": plan["task_count"],
                      "tasks": [(x["id"], x["priority"]) for x in plan["tasks"]]}, indent=2))
    return 0  # coordinator never hides emulator/test exit codes

if __name__ == "__main__":
    raise SystemExit(main())
