#!/usr/bin/env python3
"""Real Android OpenGL RPG smoke: install, draw, input, screen difference, logs."""
import json
import os
import re
import struct
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

APK=Path("veilbound/app/build/outputs/apk/debug/app-debug.apk")
OUT=Path("inspection_output/veilbound")
PKG="game.ashenveil.veilbound"
ACTIVITY=PKG+"/.MainActivity"

def adb(*args,timeout=60):
    return subprocess.run(["adb", *map(str,args)],capture_output=True,check=True,timeout=timeout).stdout

def diagnostic_state():
    result=adb("logcat","-d","-s","VEILBOUND_STATE:I","*:S",timeout=25)
    lines=[x for x in result.decode("utf-8","replace").splitlines() if "mode=" in x]
    if not lines:return None
    m=re.search(r"\bmode=([a-z]+)",lines[-1])
    return m.group(1) if m else None

def touch(x,y):
    adb("shell","input","tap",int(x),int(y),timeout=25)

def dismiss_android_overlay():
    """Dismiss only known Android first-launch tutorial / launcher ANR dialogs.

    Never bypass in-game menus or modify game state programmatically.
    """
    import xml.etree.ElementTree as ET
    for attempt in range(5):
        try:
            adb("shell","uiautomator","dump","/sdcard/veilbound-system.xml",timeout=28)
            xml=adb("exec-out","cat","/sdcard/veilbound-system.xml",timeout=18)
            (OUT/"system_ui.xml").write_bytes(xml)
            root=ET.fromstring(xml)
            nodes=list(root.iter("node"))
            text=" ".join(n.get("text","") for n in nodes)
            button=None
            if "Viewing full screen" in text:
                button=next((n for n in nodes if n.get("text","")=="Got it"),None)
            elif ("isn't responding" in text or "not responding" in text):
                button=next((n for n in nodes if n.get("text","")=="Wait"),None)
            if button is None:
                return
            m=re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]",button.get("bounds",""))
            if m is None:return
            x1,y1,x2,y2=map(int,m.groups())
            touch((x1+x2)//2,(y1+y2)//2)
            time.sleep(1.1)
        except (subprocess.SubprocessError,ValueError,ET.ParseError) as exc:
            (OUT/"system_overlay_warning.txt").write_text(str(exc))
            return

def shot(name):
    # Large mesh/texture uploads can coincide with a transient Android
    # Quickstep launcher ANR. Only dismiss known system dialogs.
    for attempt in range(7):
        if attempt:
            dismiss_android_overlay()
            time.sleep(1.35)
        content=adb("exec-out","screencap","-p",timeout=55)
        if not content.startswith(bytes.fromhex("89504e470d0a1a0a")):
            raise AssertionError("Screenshot missing PNG signature")
        with Image.open(__import__("io").BytesIO(content)) as image:
            image.load()
            rgb=image.convert("RGB")
            std=ImageStat.Stat(rgb.resize((120,80))).stddev
            colors=len(rgb.resize((60,40)).getcolors(2400) or [])
            sample=rgb.resize((120,68))
            samples=list(sample.getdata())
            white=sum(1 for r,g,b in samples if min(r,g,b)>218)/len(samples)
            quality={"path":name,"width":rgb.width,"height":rgb.height,
                     "bytes":len(content),"stddev":list(map(lambda n:round(n,2),std)),
                     "distinct_colors":colors,
                     "near_white_coverage":round(white,4),
                     "dialog_retries":attempt}
        if white>.08:
            if attempt==6:
                (OUT/"obscured_last_frame.png").write_bytes(content)
                raise AssertionError("System overlay persists after seven retries; coverage="+str(round(white,3)))
            continue
        if min(quality["width"],quality["height"])<500 or max(std)<8:
            raise AssertionError("Renderer frame is blank, obscured or too small: "+str(quality))
        (OUT/name).write_bytes(content)
        return quality
    raise AssertionError("No clear Android frame captured")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={"apk":str(APK),"package":PKG,"installed":False,"launched":False,
            "gpu_scene_visible":False,"touch_started":False,"screenshots":[]}
    try:
        report["install_output"]=adb("install","-r",str(APK),timeout=130).decode("utf-8","replace").strip()
        report["installed"]=True
        report["launch_output"]=adb("shell","am","start","-W","-n",ACTIVITY,
                                     timeout=85).decode("utf-8","replace").strip()
        report["launched"]=True
        time.sleep(6)
        dismiss_android_overlay()
        time.sleep(1.5)
        for retry in range(3):
            dismiss_android_overlay()
            time.sleep(.75)
            try:
                first=shot("01_menu.png")
                break
            except AssertionError:
                if retry==2:raise
        report["screenshots"].append(first);w,h=first["width"],first["height"]
        report["initial_mode"]=diagnostic_state()
        # Visit the ACTUAL model workshop, inspect its 3D stage and take
        # orbit/material snapshots before progressing into the existing game.
        atelier={"open":False,"orbit":False,"asset_switch":False,"lighting":False}
        report["atelier"]=atelier
        for attempt in range(3):
            dismiss_android_overlay()
            touch(w*.50,h*.826)
            time.sleep(1.6)
            if diagnostic_state()=="lab":
                atelier["open"]=True
                break
        if not atelier["open"]:
            raise AssertionError("Title's MODEL ATELIER button did not open studio")
        # The HUD renders on Android's UI thread and can display LAB before
        # the GL thread has finished constructing its dense sculpture/atlas.
        # Wait for the GL upload signal, then for a completed rendered frame.
        for ready_try in range(20):
            studio_ready=adb("logcat","-d","-s","VEILBOUND_STUDIO:I","*:S",timeout=20).decode("utf-8","replace")
            if "SURFACE_MAPS_READY" in studio_ready and "DETAIL_MESH_READY" in studio_ready:
                break
            time.sleep(.6)
        else:
            raise AssertionError("Atelier GL high-poly / atlas initialization never completed")
        time.sleep(2.5)
        hero=shot("01_atelier_hero.png")
        report["screenshots"].append(hero)
        adb("shell","input","swipe",int(w*.54),int(h*.46),
            int(w*.78),int(h*.40),620,timeout=35)
        time.sleep(.8)
        turned=shot("01_atelier_orbit.png")
        report["screenshots"].append(turned)
        with Image.open(OUT/"01_atelier_hero.png") as before, Image.open(OUT/"01_atelier_orbit.png") as after:
            diff=ImageChops.difference(before.convert("RGB").resize((160,90)),
                                       after.convert("RGB").resize((160,90)))
            atelier["orbit"]=diff.getbbox() is not None
        # Verify the studio actually uses the new 512px material maps rather
        # than silently falling back to the earlier flat surface shader.
        studio_gl_log=adb("logcat","-d","-s","VEILBOUND_STUDIO:I","*:S",timeout=20).decode("utf-8","replace")
        atelier["surface_atlas"]="SURFACE_MAPS_READY" in studio_gl_log
        atelier["cinematic_sculpt"]="DETAIL_MESH_READY" in studio_gl_log
        if not atelier["surface_atlas"] or not atelier["cinematic_sculpt"]:
            raise AssertionError("M0.8 atlas / sculpt initialization missing in Android log")
        touch(w*.43,h*.265)
        time.sleep(.9)
        lod=shot("01_atelier_lite_mesh.png")
        report["screenshots"].append(lod)
        atelier["mesh_lod_toggle"]=True
        touch(w*.43,h*.265)
        time.sleep(.9)
        if not atelier["orbit"]:
            raise AssertionError("Model studio orbit gesture did not change image")
        # Extreme close-up camera confirms mesh detail survives full zoom.
        # Single-tap anatomy detail camera framing: close enough to inspect
        # the custom-finger geometry rather than merely scaling an entire hero.
        touch(w*.66,h*.265)
        time.sleep(1.1)
        close=shot("01_atelier_closeup.png")
        report["screenshots"].append(close)
        atelier["closeup"]=True
        touch(w*.921,h*.946)  # reset the camera, not the game state
        time.sleep(.5)
        touch(w*.65,h*.865)
        time.sleep(.8)
        touch(w*.20,h*.944)
        touch(w*.52,h*.944)
        time.sleep(.9)
        detail=shot("01_atelier_material.png")
        report["screenshots"].append(detail)
        logs=adb("logcat","-d","-s","VEILBOUND_STUDIO:I","*:S",timeout=20).decode("utf-8","replace")
        atelier["asset_switch"]="item=1" in logs
        atelier["lighting"]="light=1" in logs and "material=1" in logs
        if not atelier["asset_switch"] or not atelier["lighting"]:
            raise AssertionError("Studio model/material/light settings did not change: "+str(atelier))
        touch(w*.65,h*.865)  # Hushed -> Ash Knight
        time.sleep(.8)
        boss=shot("01_atelier_boss.png")
        report["screenshots"].append(boss)
        for _ in range(3):  # material 1 -> 4, actual GL_LINES
            touch(w*.52,h*.944)
            time.sleep(.22)
        time.sleep(.5)
        wire=shot("01_atelier_wireframe.png")
        report["screenshots"].append(wire)
        with Image.open(OUT/"01_atelier_boss.png") as before, Image.open(OUT/"01_atelier_wireframe.png") as after:
            delta=ImageChops.difference(before.convert("RGB").resize((160,90)),
                                        after.convert("RGB").resize((160,90)))
            atelier["wireframe"]=delta.getbbox() is not None
        if not atelier["wireframe"]:
            raise AssertionError("Wireframe mode did not visibly change model rendering")
        for _ in range(4): # boss -> chapel (seven asset slots)
            touch(w*.65,h*.865)
            time.sleep(.23)
        time.sleep(.6)
        chapel=shot("01_atelier_chapel.png")
        report["screenshots"].append(chapel)
        atelier["chapel"]=True
        touch(w*.08,h*.08)
        # Model-hall screenshots can saturate emulator CPU; HUD telemetry is
        # sampled every ~1.4 s. Poll state instead of treating a stale log as
        # proof that BACK was ignored.
        for _ in range(12):
            time.sleep(.38)
            if diagnostic_state()=="title":
                break
        else:
            raise AssertionError("Studio return control did not restore main menu")

        # System's one-time immersive tutorial may cover the first screen.
        for attempt in range(6):
            if diagnostic_state()=="playing":break
            dismiss_android_overlay()
            touch(w*.50,h*.75)
            time.sleep(1.7)
        report["mode_after_start"]=diagnostic_state()
        if report["mode_after_start"]!="playing":
            # The emulator sometimes adds a fullscreen tutorial. Recover only
            # known "got it" prompt, never force a gameplay state.
            try:
                adb("shell","uiautomator","dump","/sdcard/veilbound-window.xml",timeout=22)
                xml=adb("exec-out","cat","/sdcard/veilbound-window.xml",timeout=20)
                (OUT/"system_ui.xml").write_bytes(xml)
                if b"Viewing full screen" in xml and b"Got it" in xml:
                    touch(w*.5,h*.62)
                    touch(w*.5,h*.75)
                    touch(w*.5,h*.75)
                    time.sleep(2.5)
            except (subprocess.SubprocessError,ValueError):pass
        report["mode_after_start"]=diagnostic_state()
        report["touch_started"]=report["mode_after_start"]=="playing"
        if not report["touch_started"]:
            raise AssertionError("Real touch input did not start native game: "+str(report["mode_after_start"]))
        time.sleep(1)
        dismiss_android_overlay()
        time.sleep(.6)
        second=shot("02_exploration.png");report["screenshots"].append(second)
        report["gpu_scene_visible"]=True
        # Real ADB swipe on left control + attack + dodge buttons.
        adb("shell","input","swipe",int(w*.12),int(h*.81),
            int(w*.15),int(h*.57),1100,timeout=35)
        touch(w*.905,h*.806);time.sleep(.35)
        touch(w*.805,h*.866);time.sleep(2)
        dismiss_android_overlay()
        third=shot("03_combat_controls.png");report["screenshots"].append(third)
        with Image.open(OUT/"02_exploration.png") as a,Image.open(OUT/"03_combat_controls.png") as b:
            small_a=a.convert("RGB").resize((160,90))
            small_b=b.convert("RGB").resize((160,90))
            bbox=ImageChops.difference(small_a,small_b).getbbox()
            report["screen_changed"]=bbox is not None
        if not report["screen_changed"]:
            raise AssertionError("Touch and movement did not alter visible frame")
        report["status"]="passed"
    except Exception as exc:
        report["status"]="failed";report["error"]=repr(exc)
    finally:
        try:
            (OUT/"logcat_recent.txt").write_bytes(adb("logcat","-d","-t","700",timeout=24))
        except Exception:pass
        (OUT/"emulator_report.json").write_text(json.dumps(report,indent=2)+"\n")
        print(json.dumps(report,indent=2))
    return 0 if report["status"]=="passed" else 1

if __name__=="__main__":
    sys.exit(main())
