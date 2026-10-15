#!/usr/bin/env python3
"""Evidence-driven mobile visual and controls QA for RIFTWARD."""
import json
import traceback
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'app/src/main/assets'
HTML=(ASSETS/'index.html').read_text()
HTML=HTML.replace('<link rel="stylesheet" href="style.css">','<style>'+ (ASSETS/'style.css').read_text() +'</style>')
HTML=HTML.replace('<script src="game.js"></script>','<script>' + (ASSETS/'game.js').read_text() +'</script>')
OUT=ROOT/'qa'
SIZES=[(320,640),(390,844),(430,932)]

def main():
    OUT.mkdir(exist_ok=True)
    report={'product':'RIFTWARD: ECLIPSE','viewports':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,**({'executable_path':shutil.which('chromium')} if shutil.which('chromium') else {}),args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader'])
        try:
            for w,h in SIZES:
                result={'viewport':f'{w}x{h}','screenshots':[],'errors':[]}
                report['viewports'].append(result)
                context=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=1,has_touch=True,is_mobile=True)
                page=context.new_page()
                page.on('pageerror',lambda e,r=result:r['errors'].append(str(e)))
                try:
                    page.set_content(HTML,wait_until='load')
                    page.wait_for_function("window.Riftward && window.Riftward.status().state === 'menu'",timeout=9000)
                    page.set_default_timeout(9000)
                    def shot(name):
                        filename=f'{name}_{w}x{h}.png'
                        page.screenshot(path=str(OUT/filename),animations='disabled')
                        result['screenshots'].append(filename)
                    def state():return page.evaluate('window.Riftward.status()')
                    rect=page.locator('#playBtn').bounding_box()
                    assert rect and rect['width']>=200 and rect['height']>=48 and rect['y']>0 and rect['y']+rect['height']<h,f'Start clipped: {rect}'
                    shot('menu')
                    page.locator('#menuSettings').click()
                    assert state()['state']=='settings','Settings not open'
                    page.locator('#toggleEffects').click()
                    assert state()['settings']['effects'] is False,'Effects switch failed'
                    page.locator('#toggleEffects').click()
                    page.locator('#toggleFps').click()
                    assert state()['settings']['fps'] is True
                    shot('settings')
                    page.locator('#closeSettings').click()
                    assert state()['state']=='menu'
                    page.locator('#playBtn').click()
                    assert state()['state']=='playing','Start failed'
                    # A wave should contain enemies, then shots after 2 seconds.
                    page.wait_for_timeout(2600)
                    current=state()
                    assert current['enemies']>=1, f'No enemies after 2.6s: {current}'
                    shot('combat')
                    rect=page.locator('#joyArea').bounding_box()
                    page.mouse.move(rect['x']+rect['width']*.5,rect['y']+rect['height']*.5)
                    page.mouse.down()
                    page.mouse.move(rect['x']+rect['width']*.8,rect['y']+rect['height']*.5,steps=3)
                    page.wait_for_timeout(400)
                    page.mouse.up()
                    page.locator('#novaBtn').click()
                    assert 'NOVA' in page.locator('#novaLabel').text_content() or 'SEC' in page.locator('#novaLabel').text_content()
                    shot('nova')
                    page.locator('#pauseBtn').click()
                    assert state()['state']=='paused'
                    assert page.locator('#pause').is_visible(), 'Pause overlay is not visible'
                    shot('pause')
                    page.locator('#resumeBtn').click()
                    assert state()['state']=='playing'
                    page.locator('#pauseBtn').click()
                    page.locator('#quitBtn').click()
                    assert state()['state']=='menu'
                    assert not result['errors'],f'Browser exceptions: {result["errors"]}'
                    result['status']='passed'
                    result['combat_enemies']=current['enemies']
                    result['fps_estimate']=current['fps']
                except Exception as e:
                    result['status']='failed';result['error']=str(e)
                    try:shot('failure')
                    except Exception:pass
                finally:context.close()
        finally:browser.close()
    report['passed']=sum(r['status']=='passed' for r in report['viewports']); report['total']=len(report['viewports'])
    (OUT/'browser_qa.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    return 0 if report['passed']==report['total'] else 1
if __name__=='__main__':raise SystemExit(main())
