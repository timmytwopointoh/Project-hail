#!/usr/bin/env python3
"""Android 15 test: actual APK install, launch, touchscreen interaction, PNG diagnostics."""
import json
import re
import struct
import subprocess
import time
from pathlib import Path
from io import BytesIO
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=Path('inspection_output/riftward')
APK=ROOT/'app/build/outputs/apk/debug/app-debug.apk'
PACKAGE='com.trioncompasitor.riftward'
ACTIVITY=PACKAGE+'/.MainActivity'
PNG=bytes.fromhex('89504e470d0a1a0a')

def adb(*args, timeout=35):
    p=subprocess.run(['adb',*map(str,args)],capture_output=True,check=True,timeout=timeout)
    return p.stdout

def screenshot(name, require_visible=False):
    error=''
    for _ in range(8 if require_visible else 2):
        try:
            data=adb('exec-out','screencap','-p',timeout=35)
            if not data.startswith(PNG):raise ValueError('Non-PNG screenshot')
            w,h=struct.unpack('>II',data[16:24]);assert w>250 and h>400
            if require_visible:
                # A dark Android transition frame is not a verified rendered menu.
                img=Image.open(BytesIO(data)).convert('RGB')
                img=img.crop((0,0,w,int(h*.89))).resize((64,110))
                lit=sum(1 for r,g,b in img.getdata() if r+g+b>360)
                if lit<22:raise ValueError(f'UI not drawn yet ({lit} lit samples)')
            (OUT/name).write_bytes(data)
            return {'file':name,'width':w,'height':h,'bytes':len(data)}
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired,AssertionError,ValueError) as e:
            error=str(e)
            time.sleep(1)
    raise RuntimeError('Could not capture screenshot: '+error)

def state():
    text=adb('logcat','-d','-s','RIFTWARD_STATE:I','*:S',timeout=18).decode('utf-8','replace')
    matches=re.findall(r'RIFTWARD_STATE:\s*(menu|playing|paused|upgrade|gameover|settings)',text)
    return matches[-1] if matches else None

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={'package':PACKAGE,'installed':False,'launched':False,'menu_state':None,
            'touch_started':False,'screenshots':[],'status':'failed'}
    try:
        assert APK.is_file(),f'APK missing at {APK}'
        report['install_output']=adb('install','-r',str(APK),timeout=120).decode('utf-8','replace').strip()
        report['installed']=True
        report['launch_output']=adb('shell','am','start','-W','-n',ACTIVITY,timeout=65).decode('utf-8','replace').strip()
        report['launched']=True
        time.sleep(5)
        for _ in range(5):
            report['menu_state']=state()
            if report['menu_state']=='menu':break
            time.sleep(1)
        if report['menu_state']!='menu':raise AssertionError('Missing menu-ready state: '+str(report['menu_state']))
        first=screenshot('01_menu.png',require_visible=True);report['screenshots'].append(first)
        for fraction in (.70,.72,.68,.75):
            x=first['width']//2;y=int(first['height']*fraction)
            adb('shell','input','tap',x,y,timeout=25)
            time.sleep(1)
            report['post_tap_state']=state()
            report['last_tap']=[x,y]
            if report['post_tap_state']=='playing':
                report['touch_started']=True
                break
        if not report['touch_started']:raise AssertionError('Touch did not enter gameplay: '+str(report.get('post_tap_state')))
        time.sleep(2)
        report['screenshots'].append(screenshot('02_playing.png'))
        report['status']='passed'
    except Exception as e:
        report['error']=str(e)
    finally:
        try:
            logs=adb('logcat','-d','-t','350',timeout=20).decode('utf-8','replace')
            (OUT/'recent_logcat.txt').write_text(logs)
        except Exception:pass
        (OUT/'emulator_report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(report,indent=2))
    return 0 if report['status']=='passed' else 1

if __name__=='__main__':raise SystemExit(main())
