"""Render package-derived phone layout simulations, never claim native device proof."""
import json
from pathlib import Path
import shutil
import urllib.request
from playwright.sync_api import sync_playwright
from build_mobile_v5 import archive, walk

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'validation/mobile-v5/preview'
OUT.mkdir(parents=True, exist_ok=True)
members = archive(ROOT / 'Barkod-Uygulamasi-Mobile-Light-v5.msapp')
cs = {c['Name']: c for n, b in members.items() if n.startswith('Controls/')
      for c in walk(json.loads(b)) if 'Rules' in c and 'Name' in c}
(OUT / 'controls.js').write_text('window.controls='+json.dumps(cs,ensure_ascii=False)+';',encoding='utf8')
shutil.copyfile(ROOT / 'scripts/mobile_v5_preview.html', OUT / 'index.html')
shutil.copyfile(ROOT / 'scripts/mobile_v5_preview.js', OUT / 'preview.js')
font = OUT / 'OpenSans.ttf'
if not font.exists():
    font.write_bytes(urllib.request.urlopen('https://raw.githubusercontent.com/google/fonts/main/ofl/opensans/OpenSans%5Bwdth,wght%5D.ttf').read())
    (OUT / 'OFL.txt').write_bytes(urllib.request.urlopen('https://raw.githubusercontent.com/google/fonts/main/ofl/opensans/OFL.txt').read())
results=[]
interaction_checks=[]
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport=dict(width=1200,height=1400),device_scale_factor=1)
    page.goto((OUT / 'index.html').as_uri())
    page.wait_for_function('window.preview !== undefined')
    for width,height in [(320,568),(360,640),(390,844),(430,932),(844,390),(390,240)]:
        for screen in ['scrHome','scrScan','scrResults','scrLoading','scrError']:
            for variant in (['default','expanded','long'] if screen=='scrResults' else ['default']):
                page.evaluate('(o)=>preview.set(o)',dict(width=width,height=height,screen=screen,expanded=variant!='default',long=variant=='long',input=''))
                errors=page.evaluate('previewErrors')
                assert not errors,(width,height,screen,errors)
                boxes=page.locator('#phone').evaluate('''root=>{const r=root.getBoundingClientRect();return [...root.querySelectorAll('[data-name]')].map(e=>{const b=e.getBoundingClientRect();return {name:e.dataset.name,x:b.x-r.x,y:b.y-r.y,w:b.width,h:b.height,scrollHeight:e.scrollHeight,clientHeight:e.clientHeight}})}''')
                # Horizontal clipping is always a layout defect; vertical scrolling is intentional.
                offenders=[b for b in boxes if b['w']>0 and (b['x'] < -1 or b['x']+b['w'] > width+1)]
                assert not offenders,(width,height,screen,offenders[:3])
                name=f'{screen}-{width}x{height}-{variant}.png'
                page.locator('#phone').screenshot(path=str(OUT/name))
                results.append(dict(width=width,height=height,screen=screen,variant=variant,screenshot=name,boxes=boxes))
        # Test reachability after scrolling at each viewport, including keyboard height.
        page.evaluate('(o)=>preview.set(o)',dict(width=width,height=height,screen='scrScan',input=''))
        field=page.locator('[data-name=txtProductName]')
        button=page.locator('[data-name=btnSearchProduct]')
        assert button.is_disabled()
        field.fill('   ')
        assert button.is_disabled()
        field.fill('57047')
        assert button.is_enabled()
        button.scroll_into_view_if_needed()
        b=button.bounding_box()
        phone=page.locator('#phone').bounding_box()
        assert b['y'] >= phone['y'] and b['y']+b['height'] <= phone['y']+height+1
        page.locator('#phone').screenshot(path=str(OUT/f'scrScan-{width}x{height}-manual-ready.png'))
        page.evaluate('(o)=>preview.set(o)',dict(width=width,height=height,screen='scrHome'))
        home=page.locator('[data-name=btnScan]')
        home.scroll_into_view_if_needed()
        assert home.is_visible()
        interaction_checks.append(dict(width=width,height=height,blank_disabled=True,whitespace_disabled=True,
            text_enables_button=True,manual_button_reachable=True,home_action_reachable=True))
    browser.close()
(OUT / 'layout-checks.json').write_text(json.dumps(dict(type='SIMULATED: not native Canvas or physical phone',cases=len(results),horizontal_overflow=0,interaction_checks=interaction_checks,results=results),ensure_ascii=False,indent=2),encoding='utf8')
print(f'PASS: {len(results)} package-derived layout simulations; screenshots saved. Native phone acceptance is unverified.')
