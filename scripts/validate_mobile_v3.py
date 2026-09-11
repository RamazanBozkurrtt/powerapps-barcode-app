"""Regression fixtures use formulas extracted from the deliverable, not rewritten logic."""
import itertools
import json
from pathlib import Path
import re
import zipfile
import sys
from mobile_v3_fixes import OCR_SELECTION, OCR_GUARD, MANUAL_GUARD

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'validation/mobile-v3'
PACKAGE = ROOT / 'Barkod-Uygulamasi-Mobile-Light-v3.msapp'
if '--mobile-v3-1' in sys.argv:
    OUT = ROOT / 'validation/mobile-v3-1'
    PACKAGE = ROOT / 'Barkod-Uygulamasi-Mobile-Light-v3-1.msapp'


def walk(v):
    if isinstance(v, dict):
        yield v
        for x in v.values():
            yield from walk(x)
    elif isinstance(v, list):
        for x in v:
            yield from walk(x)


with zipfile.ZipFile(PACKAGE) as z:
    cs = {c['Name']: c for n in z.namelist() if n.startswith('Controls/')
          for c in walk(json.loads(z.read(n))) if 'Rules' in c}
    props = json.loads(z.read('Properties.json'))
    templates = json.loads(z.read('References/Templates.json'))['UsedTemplates']
    assert json.loads(z.read('packed.json'))['LoadConfiguration']['LoadFromYaml'] is False


def prop(n, p):
    return next(r['InvariantScript'] for r in cs[n]['Rules'] if r['Property'] == p)


rules = [{'name': n + '.' + r['Property'], 'formula': r['InvariantScript']}
         for n, c in cs.items() for r in c['Rules'] if r['InvariantScript']]
tests = []


def test(name, formula, expected):
    tests.append(dict(name=name, formula=formula, expected=expected))


assert OCR_SELECTION in prop('TextRecognizer1', 'OnChange')
assert OCR_GUARD in prop('TextRecognizer1', 'OnChange')
assert MANUAL_GUARD in prop('btnSearchProduct', 'OnSelect')
assert 'Notify(' not in prop('TextRecognizer1', 'OnChange')
assert 'IsEmpty' not in prop('TextRecognizer1', 'OnChange').split('chosenText:')[0]
assert 'Reset(txtProductName)' in prop('scrScan', 'OnVisible')
assert props['DocumentLayoutScaleToFit'] is False
assert props['DocumentLayoutMaintainAspectRatio'] is False
assert prop('App', 'MinScreenWidth') == '320'
assert prop('App', 'MinScreenHeight') == '480'
assert len({c['ControlUniqueId'] for c in cs.values()}) == len(cs)
assert all(isinstance(c.get('Children'), list) for c in cs.values()), 'Every ControlInfo needs Children, including leaves'
assert sum('barcode_flow.Run(' in r['formula'] for r in rules) == 1
assert cs['TextRecognizer1']['Template']['OverridableProperties']['Results']['Type']['Kind'] == 'Table'
assert any(t['Name'] == 'text' and t['Version'] == '2.3.2' for t in templates)
assert all(prop(n, 'Fill') == 'RGBA(255, 255, 255, 1)' for n, c in cs.items() if c['Template']['Name'] == 'screen')
assert not any(c['Template']['Name'].startswith('PowerApps_CoreControls') for c in cs.values())


def line(text, top=10, left=10, width=40, height=20, page=1):
    def num(v):
        return 'Blank()' if v is None else str(v)
    return '{Text:' + json.dumps(text, ensure_ascii=False) + ',BoundingBox:{Top:' + num(top) + ',Left:' + num(left) + ',Width:' + num(width) + ',Height:' + num(height) + '},PageNumber:' + num(page) + '}'


cases = [
    ('top_right', [line('LEFT'), line('RIGHT', left=200), line('LOWER', top=70, left=300)], 'RIGHT'),
    ('skewed_row', [line('LEFT'), line('RIGHT', top=15, left=200)], 'RIGHT'),
    ('lower_row_not_selected', [line('TOP'), line('LOWER', top=25, left=200)], 'TOP'),
    ('right_edge', [line('WIDE', left=100, width=150), line('NARROW', left=190, width=10)], 'WIDE'),
    ('first_page', [line('PAGE2', top=0, page=2), line('PAGE1', page=1)], 'PAGE1'),
    ('missing_coordinates', [line('  10120 MX  ', top=None, left=None)], '10120 MX'),
    ('negative_coordinates_fallback', [line('READABLE', top=-1)], 'READABLE'),
    ('missing_height', [line('LEFT', height=None), line('RIGHT', left=200, height=None)], 'RIGHT'),
    ('missing_width', [line('LEFT', width=None), line('RIGHT', left=200, width=None)], 'RIGHT'),
    ('positioned_preferred', [line('UNKNOWN', top=None), line('KNOWN')], 'KNOWN'),
    ('blank_text', [line('   '), line('PRODUCT', top=60)], 'PRODUCT'),
    ('numeric_code', [line('  2032  ')], '2032'),
    ('turkish_text', [line('  Şişe Ürün İçi  ')], 'Şişe Ürün İçi'),
    ('no_text', [line('   ')], 'EMPTY'),
    ('stable_tie', [line('B'), line('A')], 'A'),
    ('normalised_coordinates', [line('LEFT', .1, .1, .2, .04), line('RIGHT', .11, .7, .2, .04)], 'RIGHT'),
    ('pixel_coordinates', [line('LEFT', 100, 100, 200, 40), line('RIGHT', 110, 700, 200, 40)], 'RIGHT'),
]
for name, lines, expected in cases:
    test('ocr_' + name, 'With({TextRecognizer1:{Results:Table(' + ','.join(lines) + ')}},Coalesce(' + OCR_SELECTION + ',"EMPTY"))', expected)
empty = 'Filter(Table(' + line('seed') + '), false)'
test('ocr_empty_initial_or_pending', 'With({TextRecognizer1:{Results:' + empty + '}},Coalesce(' + OCR_SELECTION + ',"EMPTY"))', 'EMPTY')
# Order independence for geometrically distinct lines.
for i, lines in enumerate(itertools.permutations(cases[0][1])):
    test(f'ocr_input_order_{i}', 'With({TextRecognizer1:{Results:Table(' + ','.join(lines) + ')}},Coalesce(' + OCR_SELECTION + ',"EMPTY"))', 'RIGHT')


def boolfx(v):
    return str(v).lower()


guard = prop('tmrLoadingFlow', 'Start').replace('App.ActiveScreen = scrLoading', 'isLoading')
for loading, accepted, text, started, executed in itertools.product([False, True], repeat=5):
    bindings = f'isLoading:{boolfx(loading)},varScanAccepted:{boolfx(accepted)},varAcceptedText:{json.dumps("SKU" if text else "")},varFlowCallStarted:{boolfx(started)},varLoadingExecutionStarted:{boolfx(executed)}'
    test('dispatch_' + ''.join(str(int(v)) for v in [loading, accepted, text, started, executed]),
         f'With({{{bindings}}},If({guard},"RUN","STOP"))',
         'RUN' if loading and accepted and text and not started and not executed else 'STOP')

for manual in [False, True]:
    guard = MANUAL_GUARD if manual else OCR_GUARD
    guard = guard.replace('App.ActiveScreen = scrScan', 'isScan')
    for ready, screen, accepted, started, typed in itertools.product([False, True], repeat=5):
        bindings = f'varScanReady:{boolfx(ready)},isScan:{boolfx(screen)},varScanAccepted:{boolfx(accepted)},varFlowCallStarted:{boolfx(started)},txtProductName:{{Text:{json.dumps(" Ürün " if typed else "   ")}}},TextRecognizer1:{{OriginalImage:"new"}},varScanEntryImage:"old"'
        expected = ready and screen and not accepted and not started and (typed if manual else not typed)
        test(('manual_' if manual else 'automatic_') + ''.join(str(int(v)) for v in [ready, screen, accepted, started, typed]),
             f'With({{{bindings}}},If({guard},"ACCEPT","STOP"))', 'ACCEPT' if expected else 'STOP')
for name, image, baseline, expected in [('empty', '', '', 'STOP'), ('stale', 'old', 'old', 'STOP'), ('same_file_after_reset', 'same', '', 'ACCEPT')]:
    bindings = 'varScanReady:true,isScan:true,varScanAccepted:false,varFlowCallStarted:false,txtProductName:{Text:""},TextRecognizer1:{OriginalImage:' + json.dumps(image) + '},varScanEntryImage:' + json.dumps(baseline)
    test('image_' + name, f'With({{{bindings}}},If({OCR_GUARD.replace("App.ActiveScreen = scrScan", "isScan")},"ACCEPT","STOP"))', expected)

# Resolve actual layout expressions recursively, and let Microsoft's engine
# evaluate them at common phone viewports. This is geometry QA, not a UI render.
def dimension(name, p, width, height, stack=()):
    key = (name, p)
    assert key not in stack, f'Circular layout reference: {key}'
    if name == 'App':
        return str({'Width': width, 'Height': height, 'MinScreenWidth': 320, 'MinScreenHeight': 480}[p])
    value = prop(name, p)
    def substitute(m):
        target, attr = m.groups()
        if target == 'Self':
            target = name
        if target == 'Parent':
            target = cs[name]['Parent']
        return '(' + dimension(target, attr, width, height, stack + (key,)) + ')'
    return re.sub(r'\b(\w+)\.(Width|Height|X|Y|MinScreenWidth|MinScreenHeight)\b', substitute, value)


viewports = [(320, 480), (320, 568), (360, 640), (375, 667), (390, 844), (412, 915), (430, 932), (844, 390), (390, 300)]
for width, height in viewports:
    for name, c in cs.items():
        if c.get('Parent') not in ['scrHome', 'scrScan', 'scrResults', 'scrLoading', 'scrError']:
            continue
        if prop(name, 'Visible') == 'false':
            continue
        x, y, w, h = [dimension(name, p, width, height) for p in ['X', 'Y', 'Width', 'Height']]
        formula = f'With({{x:{x},y:{y},w:{w},h:{h}}},If(x >= 0 && y >= 0 && w > 0 && h > 0 && x+w <= {max(width,320)} && y+h <= {max(height,480)},"FITS","CLIPPED"))'
        test(f'layout_{width}x{height}_{name}', formula, 'FITS')

# Contrast against the explicit light backgrounds (WCAG normal text >= 4.5).
def luminance(rgb):
    channels = [v/255 for v in rgb]
    return sum(weight * (v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4)
               for weight, v in zip([.2126, .7152, .0722], channels))


contrasts = {}
for name, fg, bg in [('body', (31,41,55), (255,255,255)), ('muted', (75,85,99), (255,255,255)),
                     ('button', (255,255,255), (194,65,12)), ('disabled', (75,85,99), (243,244,246)),
                     ('reserve', (194,65,12), (255,247,237))]:
    a, b = sorted([luminance(fg), luminance(bg)])
    contrasts[name] = round((b+.05)/(a+.05), 2)
    assert contrasts[name] >= 4.5
(OUT / 'fx-input.json').write_text(json.dumps(dict(rules=rules, tests=tests), ensure_ascii=False), encoding='utf8')
(OUT / 'static-checks.json').write_text(json.dumps(dict(package_structure='PASS', contrast=contrasts,
    viewport_sizes=viewports, formula_count=len(rules), executable_cases=len(tests),
    runtime='NOT EXECUTED: browser inventory returned no browsers/apps'), indent=2), encoding='utf8')
print(f'Structure/contrast PASS; {len(rules)} formulas and {len(tests)} executable cases ready.')
