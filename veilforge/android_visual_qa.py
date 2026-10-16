#!/usr/bin/env python3
"""Android emulator visual QA: real ADB screenshots of the built glTF scene APK.

Objective gates: installed APK checksum, GLES2 load/frame markers for each view,
nonblank pixel foreground, camera-change evidence, screenshots+per-asset hashes,
memory snapshot. Subjective photorealism is NOT certified by these checks.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import time
from vq_logcat_stream import LogcatStream
from vq_android_qa_sdk import frame_is_trusted

ANDROID_PACKAGE="game.veilforge.probe"
ACTIVITY=ANDROID_PACKAGE+"/.ViewerActivity"
VIEWS=[(yaw,15 if index%3==0 else 25 if index%3==1 else 42)
       for index,yaw in enumerate(range(0,350,25))][:14]
ROLES={
    "scene-world":("scene","rolling_terrain","ancient_gate_standard"),
    "nature-mobile":("ancient_tree","forest_tree_mobile","ancient_gate_mobile"),
    "props-equipment":("treasure_chest","ceremonial_sword","cargo_cart"),
    "characters":("human_repaired","bellwarden_full_anatomy_repaired"),
}
BACKGROUND=(17,21,29)

def adb(*args,timeout=50,binary=False):
    proc=subprocess.run(["adb",*args],check=True,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,timeout=timeout)
    return proc.stdout if binary else proc.stdout.decode("utf-8","replace")

def screenshot(path):
    from PIL import Image
    raw=adb("exec-out","screencap","-p",timeout=40,binary=True)
    if not raw.startswith(b"\x89PNG"):
        raise RuntimeError("ADB screenshot was not PNG data")
    path.write_bytes(raw)
    pic=Image.open(io.BytesIO(raw)).convert("RGB")
    if min(pic.size)<240 or max(pic.size)<450:
        raise RuntimeError("Screenshot resolution was too small")
    return pic

def dialog_overlay_fraction(image):
    """Conservative Android system-dialog detector using UI rectangle pixels.

    The characteristic large bright central modal is not 3-D geometry.
    This intentionally fails closed if a genuine scene fills the area white.
    """
    frame=image.convert("RGB").resize((160,90))
    values=[frame.getpixel((x,y)) for y in range(36,63) for x in range(32,128)]
    return sum(min(rgb)>210 and max(rgb)-min(rgb)<35 for rgb in values)/len(values)

def renderer_background_confirmed(image):
    """Require the GLES clear color at independent sky coordinates.

    A launcher or Android splash screen can contain high-contrast pixels,
    yet is not a legitimate rendered model. Sample the actual source image
    once, rather than repeatedly fetching emulator screenshot/logcat data.
    """
    frame=image.convert("RGB")
    probes=((.50,.08),(.30,.10),(.65,.12))
    return all(max(abs(int(frame.getpixel((int(frame.width*x),
                                           int(frame.height*y)))[k])-BACKGROUND[k])
                   for k in range(3))<=9 for x,y in probes)

def metrics(image):
    from PIL import ImageStat
    # Static GL background is uniform; require actual colored geometry,
    # sampled at low resolution to make the gate device-independent.
    small=image.resize((240,135))
    pixels=list(small.getdata())
    mask=sum(1 for r,g,b in pixels if max(
        abs(r-BACKGROUND[0]),abs(g-BACKGROUND[1]),abs(b-BACKGROUND[2]))>=23)
    frac=mask/len(pixels)
    stat=ImageStat.Stat(small)
    contrast=max(stat.stddev)
    return {"foreground_fraction":round(frac,5),"channel_stddev":round(contrast,3),
            "modal_overlay_fraction":round(dialog_overlay_fraction(image),5),
            "renderer_background_confirmed":renderer_background_confirmed(image),
            "dimensions":list(image.size)}

def capture_visible_frame(path, *, attempts=8, interval=.75, monitor=None):
    """Wait for the *presented* Android frame, not just the GL draw callback.

    A FRAME_OK log is emitted before the emulator compositor necessarily
    presents the buffer. SwiftShader can briefly return a uniform black
    screenshot while the surface is attaching. Retry that transient only;
    never accept a blank screenshot or fabricate an image.
    """
    if attempts < 1:
        raise ValueError("At least one real screenshot attempt is required")
    last = None
    for attempt in range(1, attempts + 1):
        if monitor is not None:
            monitor.assert_healthy()
        pic = screenshot(path)
        last = metrics(pic)
        if monitor is not None:
            monitor.assert_healthy()
        if last.get("modal_overlay_fraction",0) >= .70:
            # Save visual proof of a false-positive foreground (e.g. Android
            # Quickstep launcher ANR overlay), then tap its "Wait" row.
            # Neither the overlay nor its pixels may count towards an approved
            # Android screenshot, even if FRAME_OK appeared in logcat.
            evidence=path.parent/(path.stem+f"_blocked_modal_{attempt}.png")
            evidence.write_bytes(path.read_bytes())
            print(f"VEILFORGE_SYSTEM_MODAL_BLOCKED attempt={attempt} fraction={last['modal_overlay_fraction']}",flush=True)
            adb("shell","input","tap",str(round(pic.width*.31)),
                str(round(pic.height*.66)),timeout=20)
            if attempt<attempts:time.sleep(interval)
            continue
        if frame_is_trusted(last):
            return pic, last, attempt
        print(f"VEILFORGE_FRAME_NOT_READY attempt={attempt}/{attempts} "
              f"metrics={last}", flush=True)
        # Persistent renderer errors are not compositor settling problems.
        if monitor is None:
            # Standalone compatibility; factory capture uses one subscriber.
            log = adb("logcat", "-d", "-s", "VEILFORGE_PROBE:I", "*:S", timeout=15)
            if any(marker in log for marker in ("GL_ERROR", "LOAD_FAIL", "ASSET_NOT_FOUND")):
                raise RuntimeError("Android GL renderer failed while awaiting screenshot: "
                                   + log[-1800:])
        else:
            monitor.assert_healthy()
        if attempt < attempts:
            time.sleep(interval)
    raise RuntimeError(f"Blank, launcher/splash, system UI, or near-empty GLES frame after {attempts} "
                       f"real screenshot attempts: {last}")


def change_fraction(a,b):
    from PIL import ImageChops
    a=a.resize((240,135));b=b.resize((240,135))
    diff=ImageChops.difference(a,b)
    return sum(1 for px in diff.getdata() if max(px)>=12)/(240*135)

def wait_frame(asset, yaw, pitch, *, monitor, since, timeout=15):
    """Require a NEW GLES draw event after this specific camera launch."""
    marker = f"FRAME_OK asset={asset} "
    target = f" yaw={yaw} pitch={pitch}"
    try:
        return monitor.wait_for(
            lambda line: marker in line and target in line,
            since=since, timeout=timeout)
    except TimeoutError as error:
        raise RuntimeError(
            f"Timed out waiting for GLES frame asset={asset} view={yaw}/{pitch}"
        ) from error


def capture(role,apk,output,expected_apk_sha,source_sha):
    if role not in ROLES:raise ValueError("Unknown worker role")
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    apk=Path(apk)
    real_sha=hashlib.sha256(apk.read_bytes()).hexdigest()
    if real_sha!=expected_apk_sha:raise RuntimeError("APK integrity mismatch")
    observed_api=int(adb("shell","getprop","ro.build.version.sdk").strip())
    if observed_api!=35:raise RuntimeError(f"Unexpected Android API {observed_api}")
    adb("install","-r",str(apk),timeout=180)
    packages=adb("shell","pm","path",ANDROID_PACKAGE)
    if "package:" not in packages:raise RuntimeError("APK not installed")
    adb("logcat","-c")
    with LogcatStream(output/"device_logcat.txt", reject_wrong_pack=True) as monitor:
        collected=[]
        for asset in ROLES[role]:
            base=output/asset;base.mkdir(parents=True,exist_ok=True)
            shots=[];measurements=[]
            for index,(yaw,pitch) in enumerate(VIEWS):
                cursor=monitor.mark()
                adb("shell","am","start","--activity-single-top",
                    "-n",ACTIVITY,"--es","asset",asset,
                    "--ei","yaw",str(yaw),"--ei","pitch",str(pitch),timeout=40)
                wait_frame(asset,yaw,pitch,monitor=monitor,since=cursor)
                dest=base/f"{index:02d}_yaw{yaw}_pitch{pitch}.png"
                pic,result,attempts=capture_visible_frame(dest,monitor=monitor)
                result.update({"index":index,"yaw":yaw,"pitch":pitch,
                                "capture_attempts":attempts,
                                "sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),
                                "image":str(dest.relative_to(output))})
                shots.append(pic);measurements.append(result)
            changes=[round(change_fraction(shots[0],other),5) for other in shots[1:]]
            del shots
            if max(changes)<.0006:
                raise RuntimeError(f"Camera did not visibly orbit {asset}: max delta={max(changes)}")
            collected.append({"asset":asset,"views":measurements,"max_orbit_change":max(changes),
                              "min_foreground_fraction":min(x["foreground_fraction"] for x in measurements)})
        monitor.assert_healthy()
    log=(output/"device_logcat.txt").read_text(encoding="utf-8")
    if "GLTF_LOADED actual_scene=true" not in log or "GLES_READY renderer=" not in log:
        raise RuntimeError("No real GLES geometry-import/GPU evidence")
    texture_markers=re.findall(r"MATERIAL_MAPS_LOADED basecolor=(\d+) metallic_roughness=(\d+) unique_gpu_textures=(\d+)",log)
    if not texture_markers or max(int(a) for a,b,t in texture_markers)<8 or (
        max(int(b) for a,b,t in texture_markers)<8) or (
        max(int(t) for a,b,t in texture_markers)<16):
        raise RuntimeError("Android GLES did not import genuine albedo and metallic-roughness texture maps")
    mem=adb("shell","dumpsys","meminfo",ANDROID_PACKAGE,timeout=40)
    (output/"android_meminfo.txt").write_text(mem,encoding="utf-8")
    report={"schema_version":1,"role":role,"source_commit":source_sha,
        "apk_sha256":real_sha,"device_android_api":observed_api,
        "source_gltf_imported":True,"real_gles2_draws":True,
        "material_textures_uploaded":True,
        "screenshots_clear_of_modal_ui":True,
        "texture_counts":{"basecolor":max(int(a) for a,b,t in texture_markers),
                          "metallic_roughness":max(int(b) for a,b,t in texture_markers),
                          "unique_gpu_textures":max(int(t) for a,b,t in texture_markers)},
        "screenshot_count":sum(len(x["views"]) for x in collected),
        "assets":collected,"memory_snapshot_saved":True,
        "technical_visual_smoke_pass":True,"artistic_quality_approved":False,
        "physical_device_qa_pass":False,"photorealism_verified":False,
        "quality_limitations":["Emulator uses software GPU not phone hardware",
            "Screenshot heuristics detect blank and frozen renders, not aesthetics",
            "Static renderer; no rigged animation, normal-map tangent basis, physically accurate PBR BRDF, FPS or physical GPU VRAM claims"]}
    (output/"emulator_visual_qa.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--role",choices=sorted(ROLES),required=True)
    p.add_argument("--apk",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--apk-sha",required=True)
    p.add_argument("--source-sha",required=True)
    a=p.parse_args()
    try:
        result=capture(a.role,a.apk,a.output,a.apk_sha,a.source_sha)
        print("VEILFORGE_ANDROID_VISUAL_PASS",json.dumps({
            k:result[k] for k in ("role","device_android_api","screenshot_count",
                "technical_visual_smoke_pass")}))
    except Exception as error:
        a.output.mkdir(parents=True,exist_ok=True)
        try:
            (a.output/"device_logcat_failure.txt").write_text(
                adb("logcat","-d","-s","VEILFORGE_PROBE:I","*:S",timeout=20),
                encoding="utf-8")
        except Exception:
            pass
        (a.output/"emulator_failure.json").write_text(json.dumps(
            {"role":a.role,"error":repr(error),"passed":False},indent=2)+"\n")
        raise

if __name__=="__main__":
    main()
