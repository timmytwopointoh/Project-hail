#!/usr/bin/env python3
"""Evidence-based APK acceptance report. Does not claim real-phone certification."""
import argparse
import json
from pathlib import Path

def assess(out):
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    def load(name):
        try: return json.loads((out/name).read_text())
        except (OSError, ValueError): return {}
    def read(name):
        try: return (out/name).read_text(errors="replace")
        except OSError: return ""
    game=load("gameplay_report.json")
    visuals=load("visual_comparison.json")
    shots=game.get("screenshots",[])
    checks={
        "android_package": "com.trioncompasitor.matrixflap" in read("apk_badging.txt"),
        "zip_alignment": "Verification successful" in read("apk_alignment.txt"),
        "v2_signature": "Verified using v2 scheme (APK Signature Scheme v2): true" in read("apk_signature.txt"),
        "apk_installed": game.get("installed") is True,
        "activity_launched": game.get("launched") is True,
        "ready_state": game.get("initial_state") == "ready",
        "tap_starts_flight": game.get("touch_start_verified") is True and game.get("post_tap_state") in ("playing","over"),
        "screenshots_captured": len(shots)>=2 and all((out/s.get("name","")).is_file() and s.get("width",0)>=320 and s.get("height",0)>=640 for s in shots[:2]),
        "screen_visibly_changed": visuals.get("status")=="ok" and visuals.get("changed_fraction",0)>=0.005,
    }
    result={
        "game":"Matrix Flap","version":"1.1","result":"PASS" if all(checks.values()) else "FAIL",
        "checks":checks,"passed":sum(checks.values()),"total":len(checks),
        "changed_fraction":visuals.get("changed_fraction"),
        "optional_capture_warning":game.get("optional_extra_capture_warning"),
        "real_device_remaining":["Screen-size / cutout check","Audio and haptic feedback","Long-play performance and gameplay feel","Release signing and update-path verification"]
    }
    (out/"quality_gate.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# Matrix Flap v1.1 Emulator Quality Gate","",
           "**"+result["result"]+" — "+str(result["passed"])+"/"+str(result["total"])+" checks**","","## Automated"]
    lines += ["- "+("PASS" if v else "FAIL")+": "+k.replace("_"," ") for k,v in checks.items()]
    lines += ["","## Still requires a physical device"]
    lines += ["- "+s for s in result["real_device_remaining"]]
    if result["optional_capture_warning"]:
        lines += ["","Optional screenshot warning: "+result["optional_capture_warning"]]
    (out/"quality_gate.md").write_text("\n".join(lines)+"\n")
    print(json.dumps(result,indent=2))
    return result

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--output",type=Path,default=Path("inspection_output/matrix_flap"))
    x=a.parse_args()
    report=assess(x.output)
    raise SystemExit(0 if report["result"]=="PASS" else 1)
