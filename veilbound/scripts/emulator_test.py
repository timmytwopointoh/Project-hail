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
            m=re.fullmatch(r"\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]",button.get("bounds",""))
            if m is None:return
            x1,y1,x2,y2=map(int,m.groups())
            touch((x1+x2)//2,(y1+y2)//2)
            time.sleep(1.1)
        except (subprocess.SubprocessError,ValueError,ET.ParseError) as exc:
            (OUT/"system_overlay_warning.txt").write_text(str(exc))
            return

def shot(name):
    content=adb("exec-out","screencap","-p",timeout=55)
    if not content.startswith(bytes.fromhex("89504e470d0a1a0a")):
        raise AssertionError("Screenshot missing PNG signature")
    p=OUT/name;p.write_bytes(content)
    with Image.open(p) as image:
        image.load()
        rgb=image.convert("RGB")
        std=ImageStat.Stat(rgb.resize((120,80))).stddev
        colors=len(rgb.resize((60,40)).getcolors(2400) or [])
        quality={"path":name,"width":rgb.width,"height":rgb.height,
                 "bytes":len(content),"stddev":list(map(lambda n:round(n,2),std)),
                 "distinct_colors":colors}
    if min(quality["width"],quality["height"])<500 or max(std)<8:
        raise AssertionError("Renderer frame is blank, obscured or too small: "+str(quality))
    return quality

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
        first=shot("01_menu.png")
        report["screenshots"].append(first);w,h=first["width"],first["height"]
        report["initial_mode"]=diagnostic_state()
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
        second=shot("02_exploration.png");report["screenshots"].append(second)
        report["gpu_scene_visible"]=True
        # Real ADB swipe on left control + attack + dodge buttons.
        adb("shell","input","swipe",int(w*.12),int(h*.81),
            int(w*.15),int(h*.57),1100,timeout=35)
        touch(w*.905,h*.806);time.sleep(.35)
        touch(w*.805,h*.866);time.sleep(2)
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
