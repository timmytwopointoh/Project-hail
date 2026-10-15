#!/usr/bin/env python3
"""Accelerated *real game loop* test: waves, upgrades and a boss appear without stubs."""
import json
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'app/src/main/assets'
HTML=(ASSETS/'index.html').read_text().replace('<link rel="stylesheet" href="style.css">','<style>'+(ASSETS/'style.css').read_text()+'</style>').replace('<script src="game.js"></script>','<script>'+(ASSETS/'game.js').read_text()+'</script>')
OUT=ROOT/'qa'

def main():
    OUT.mkdir(exist_ok=True)
    report={'wave_survival':False,'upgrades_selected':0,'boss_seen':False,'snapshots':[],'errors':[]}
    with sync_playwright() as p:
        opts={'executable_path':shutil.which('chromium')} if shutil.which('chromium') else {}
        browser=p.chromium.launch(headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--enable-unsafe-swiftshader'],**opts)
        page=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
        page.clock.install()
        page.on('pageerror',lambda exc:report['errors'].append(str(exc)))
        try:
            page.set_content(HTML)
            page.locator('#playBtn').click()
            # Real movement input driven by the browser's own clock, not a
            # hidden game-state setter. Circles the arena continuously.
            page.evaluate("""() => {
                const dirs=['ArrowRight','ArrowDown','ArrowLeft','ArrowUp'];
                let n=0;let current=dirs[0];
                window.dispatchEvent(new KeyboardEvent('keydown',{key:current,bubbles:true}));
                window.__qaPilot=setInterval(()=>{
                    window.dispatchEvent(new KeyboardEvent('keyup',{key:current,bubbles:true}));
                    n=(n+1)%4;current=dirs[n];
                    window.dispatchEvent(new KeyboardEvent('keydown',{key:current,bubbles:true}));
                },3300);
            }""")
            for stage in range(4):
                for chunk in range(6):
                    page.clock.run_for(5000)
                    s=page.evaluate('window.Riftward.status()')
                    if s['boss']=='alive' and not report['boss_seen']:
                        report['boss_seen']=True
                        name='boss_encounter.png';page.screenshot(path=str(OUT/name),animations='disabled');report['snapshots'].append(name)
                    if s['state'] in ('upgrade','gameover'):break
                if s['state']=='gameover':
                    report['gameover_stage']=stage
                    break
                if s['state']=='upgrade':
                    if stage==0:
                        report['wave_survival']=True
                        name='wave_upgrade.png';page.screenshot(path=str(OUT/name),animations='disabled');report['snapshots'].append(name)
                    assert page.locator('#upgradeCards .upgradeCard').count()==3, 'Expected three upgrades'
                    # Prefer protection for a reproducible, skill-based boss probe.
                    cards=page.locator('#upgradeCards .upgradeCard')
                    labels=[cards.nth(i).inner_text().upper() for i in range(3)]
                    priority=('AETHER ARMOR','PHOENIX SEAL','STARSHIELD','RAPID CONVERGENCE','SOLAR LANCE')
                    choice=next((i for label in priority for i,text in enumerate(labels) if label in text),0)
                    cards.nth(choice).click()
                    report['upgrades_selected']+=1
                    assert page.evaluate('window.Riftward.status().state')=='playing'
            report['last_state']=page.evaluate('window.Riftward.status()')
            report['passed']=report['wave_survival'] and report['upgrades_selected']>=3 and report['boss_seen'] and not report['errors']
        except Exception as e:
            report['passed']=False;report['error']=str(e)
        finally:
            (OUT/'wave_probe.json').write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps(report,indent=2))
            browser.close()
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
