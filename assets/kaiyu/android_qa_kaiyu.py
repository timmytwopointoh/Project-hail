"""Isolated real Android 15 GLES2 Kaiyu screenshot worker.
Checks the model actually renders, 14 camera poses, no blank or modal screens;
does not claim motion playback, reference likeness, or physical-device FPS.
"""
import sys, argparse, json, hashlib, re, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from veilforge import android_visual_qa as qa

def wait_kaiyu_frame(yaw, pitch, timeout=210):
 """Kaiyu-only frame gate: do not use unrelated courtyard mesh-count sentinel.

 Require the exact static Kaiyu source triangle count and a per-pose draw marker.
 This checks OpenGL draw callbacks only; screenshot validity is checked separately.
 """
 deadline=time.monotonic()+timeout
 loaded=False
 while time.monotonic()<deadline:
  log=qa.adb('logcat','-d','-s','VEILFORGE_PROBE:I','VEILFORGE_PROBE:E','*:S',timeout=25)
  if 'LOAD_FAIL' in log or 'GL_ERROR' in log or 'ASSET_NOT_FOUND' in log:
   raise RuntimeError('Kaiyu GLES failure: '+log[-4000:])
  for entry in log.splitlines():
   if 'GLTF_LOADED actual_scene=true' in entry:
    count=re.search(r'models=(\\d+) nodes=(\\d+) source_triangles=(\\d+)',entry)
    if not count or tuple(map(int,count.groups()))!=(90,90,133584):
     raise RuntimeError('Kaiyu scene counts differ from reviewed source: '+entry)
    loaded=True
   if loaded and 'FRAME_OK asset=kaiyu ' in entry and (' yaw='+str(yaw)+' pitch='+str(pitch)+' ') in entry:
    return log
  time.sleep(.6)
 raise RuntimeError('Kaiyu frame callback timeout at yaw='+str(yaw)+' pitch='+str(pitch)+' (loaded='+str(loaded)+')')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apk',required=True);ap.add_argument('--out',required=True)
 a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 apk=Path(a.apk);digest=hashlib.sha256(apk.read_bytes()).hexdigest()
 sdk=int(qa.adb('shell','getprop','ro.build.version.sdk').strip());assert sdk==35, sdk
 qa.adb('install','-r',str(apk),timeout=180)
 qa.adb('logcat','-G','16M',timeout=35)
 qa.adb('logcat','-c')
 qa.adb('shell','wm','size','720x1280',timeout=35)
 frames=[];shots=[]
 for i,(yaw,pitch) in enumerate(qa.VIEWS):
  qa.adb('shell','am','start','--activity-single-top','-n',qa.ACTIVITY,'--es','asset','kaiyu','--ei','yaw',str(yaw),'--ei','pitch',str(pitch),timeout=35)
  try:
   log=wait_kaiyu_frame(yaw,pitch,timeout=210)
  except Exception as exc:
   # Preserve real device evidence on a first-frame failure, never invent a PASS.
   (out/'android_first_frame_failure.txt').write_text(
    str(exc)+'\n'+qa.adb('logcat','-d',timeout=40)[-120000:],encoding='utf-8')
   try:
    (out/'android_activity_dump.txt').write_text(
     qa.adb('shell','dumpsys','activity','activities',timeout=30),encoding='utf-8')
   except Exception: pass
   try:
    (out/'kaiyu_tagged_logcat.txt').write_text(qa.adb('logcat','-d','-s','VEILFORGE_PROBE:V','AndroidRuntime:E','ActivityManager:E','*:S',timeout=40))
   except Exception: pass
   try: qa.screenshot(out/'android_first_frame_failure.png')
   except Exception: pass
   raise
  dest=out/f'kaiyu_android_{i:02d}.png'
  image,metrics,attempts=qa.capture_visible_frame(dest,attempts=12)
  assert metrics['foreground_fraction']>.003 and metrics['channel_stddev']>3
  assert metrics['modal_overlay_fraction']<.70
  metrics.update({'image':dest.name,'yaw':yaw,'pitch':pitch,'attempts':attempts,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
  shots.append(image);frames.append(metrics)
 changes=[qa.change_fraction(shots[0],s) for s in shots[1:]]
 assert max(changes)>.001, max(changes)
 log=qa.adb('logcat','-d','-s','VEILFORGE_PROBE:I','*:S',timeout=35)
 assert 'GLTF_LOADED actual_scene=true' in log and 'GLES_READY renderer=' in log
 markers=re.findall(r'MATERIAL_MAPS_LOADED basecolor=(\d+) metallic_roughness=(\d+) unique_gpu_textures=(\d+)',log)
 assert markers and max(int(x[0]) for x in markers)>=1,markers
 report={'milestone':'Kaiyu M4 actual Android 15 static 3D rendering','apk_sha256':digest,'android_api':sdk,'model':'Kaiyu', 'screenshots':len(frames),'views':frames,'max_orbit_change':round(max(changes),5),'material_albedo_uploaded':True,'real_gles2_scene_draw':True,'screenshots_real_adb':True,'skinned_motion_android_verified':False,'reference_likeness_approved':False,'physical_phone_fps_verified':False,'production_ready':False}
 (out/'kaiyu_android_report.json').write_text(json.dumps(report,indent=2)+'\n')
 (out/'device_logcat.txt').write_text(log)
 print('KAIYU_ANDROID_STATIC_14_VIEW_PASS',len(frames), 'MAX_ORBIT_CHANGE',max(changes))
if __name__=='__main__':main()