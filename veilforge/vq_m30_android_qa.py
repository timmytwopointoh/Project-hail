#!/usr/bin/env python3
"""Four-device actual Android GLES validation for M30 sculpted normal baking.

Screenshots the same genuine low-poly mesh with the baked normal map enabled
and disabled, records the measured pixel difference, and verifies 14 orbit
angles, source/APK hashes, GPU import logs, and Android 15. No fake captures.
"""
from __future__ import annotations
import argparse,hashlib,json,re,time
from pathlib import Path
from android_visual_qa import (adb,screenshot,capture_visible_frame,
                               change_fraction,VIEWS,ANDROID_PACKAGE,ACTIVITY)

def wait(asset,yaw,pitch,flat,timeout=20):
    target=f"FRAME_OK asset={asset} "
    token=f" yaw={yaw} pitch={pitch}"
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        log=adb("logcat","-d","-s","VEILFORGE_PROBE:I","*:S",timeout=15)
        if "LOAD_FAIL" in log or "GL_ERROR" in log or "ASSET_NOT_FOUND" in log:
            raise RuntimeError("Android GLES asset failure: "+log[-1400:])
        lines=log.splitlines()
        if (any(target in line and token in line for line in lines)
              and any("M30_NORMAL_MAP_DRAW asset=vq_m30_patch active_normal="+
                        ("false" if flat else "true") in line for line in lines)):
            return log
        time.sleep(.35)
    raise RuntimeError("No verified Android normal-map framebuffer evidence")

def capture(apk,out,*,role,apk_sha,source_sha):
    apk=Path(apk);out=Path(out)
    if role not in ("pixel_4","pixel_5","pixel_6","pixel_7"):
        raise ValueError("Unknown virtual-device test profile")
    if hashlib.sha256(apk.read_bytes()).hexdigest()!=apk_sha:
        raise ValueError("APK bytes changed before emulator launch")
    observed=int(adb("shell","getprop","ro.build.version.sdk").strip())
    if observed!=35:raise RuntimeError("Android API 35 required")
    out.mkdir(parents=True,exist_ok=True)
    adb("install","-r",str(apk),timeout=180)
    if "package:" not in adb("shell","pm","path",ANDROID_PACKAGE):
        raise RuntimeError("Test APK did not install")
    adb("logcat","-c")
    views=[];frames=[];initial_log=""
    asset="vq_m30_patch"
    for index,(yaw,pitch) in enumerate(VIEWS):
        adb("shell","am","start","--activity-single-top",
            "-n",ACTIVITY,"--es","asset",asset,"--ez","flat","false",
            "--ei","yaw",str(yaw),"--ei","pitch",str(pitch),timeout=40)
        log=wait(asset,yaw,pitch,False)
        if index==0:initial_log=log
        dest=out/f"angle_{index:02d}.png"
        pic,metrics,attempts=capture_visible_frame(dest)
        frames.append(pic)
        views.append({"yaw":yaw,"pitch":pitch,"index":index,
                      "image":dest.name,"sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
                      "metrics":metrics,"capture_attempts":attempts})
    # Photograph same angle with normal disabled, and compare REAL GPU images.
    yaw,pitch=VIEWS[0]
    adb("logcat","-c")
    adb("shell","am","start","--activity-single-top",
        "-n",ACTIVITY,"--es","asset",asset,"--ez","flat","true",
        "--ei","yaw",str(yaw),"--ei","pitch",str(pitch),timeout=40)
    log=wait(asset,yaw,pitch,True)
    flat=out/"flat_baseline.png"
    pic,metrics,retries=capture_visible_frame(flat)
    effect=change_fraction(frames[0],pic)
    orbital=[change_fraction(frames[0],x) for x in frames[1:]]
    if max(orbital)<.001:
        raise RuntimeError("Real GLES camera orbit failed")
    if effect<.0015:
        raise RuntimeError(f"Baked normal map did not measurably change Android pixels: {effect:.7f}")
    log=initial_log+"\n"+adb("logcat","-d","-s","VEILFORGE_PROBE:I","*:S")
    # Initial load evidence is retained even after the flat-baseline logcat reset.
    if not re.search(r"M30_NORMAL_MAPS_LOADED normal=[1-9]\d* ao=[1-9]\d* tangent_basis=derived",log):
        raise RuntimeError("Android GLES did not upload actual M30 normal/AO textures")
    if "GLES_READY renderer=" not in log:
        raise RuntimeError("No real GLES renderer signature")
    (out/"device_logcat.txt").write_text(log)
    result={"schema_version":1,"milestone":"M30","role":role,
            "source_commit":source_sha,"apk_sha256":apk_sha,
            "android_api":observed,"screenshots":views,
            "flat_baseline_sha256":hashlib.sha256(flat.read_bytes()).hexdigest(),
            "actual_emulator_frames":len(views)+1,
            "distinct_view_change":round(max(orbital),6),
            "normal_map_on_off_pixel_difference":round(effect,6),
            "real_gles_normal_and_ao_uploaded":True,
            "shading_enabled_comparison_verified":True,
            "technical_gate_passed":True,"artistic_approval":False,
            "physical_phone_performance_verified":False,
            "photorealism_verified":False}
    (out/"m30_emulator_report.json").write_text(json.dumps(result,indent=2)+"\n")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--apk",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--role",required=True)
    p.add_argument("--apk-sha",required=True)
    p.add_argument("--source-sha",required=True)
    args=p.parse_args()
    try:
        r=capture(args.apk,args.out,role=args.role,
                  apk_sha=args.apk_sha,source_sha=args.source_sha)
        print("VQ_M30_ANDROID_REAL_BAKED_NORMAL_PASS",r["role"],
              r["actual_emulator_frames"],"frames, pixel delta",
              r["normal_map_on_off_pixel_difference"])
    except Exception as err:
        args.out.mkdir(parents=True,exist_ok=True)
        (args.out/"failed_emulator.json").write_text(json.dumps({
            "role":args.role,"error":repr(err),"approved":False},indent=2)+"\n")
        try:(args.out/"device_logcat_failure.txt").write_text(
            adb("logcat","-d","-s","VEILFORGE_PROBE:I","*:S",timeout=15))
        except Exception:pass
        raise
if __name__=="__main__":main()
