"""Check v5 business invariants, source parity, and UI formula references."""
import json
from pathlib import Path
import re
import zipfile
import yaml
from build_mobile_v5 import archive, walk

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'validation/mobile-v5'


def load(version):
    members = archive(ROOT / f'Barkod-Uygulamasi-Mobile-Light-{version}.msapp')
    controls = {c['Name']: c for n, b in members.items() if n.startswith('Controls/')
                for c in walk(json.loads(b)) if 'Rules' in c and 'Name' in c}
    return members, controls


old_members, old = load('v4')
members, cs = load('v5')
props = {n: {r['Property']: r['InvariantScript'] for r in c['Rules']} for n, c in cs.items()}
get = lambda n, p: props[n][p]
assert len({c['ControlUniqueId'] for c in cs.values()}) == len(cs)
assert all(isinstance(c['Children'], list) for c in cs.values())
behavior = 0
protected = {'Items', 'Default', 'DisplayMode', 'Start', 'Reset', 'AutoStart', 'AutoPause', 'Repeat', 'Duration'}
for n, c in old.items():
    assert cs[n]['Template'] == c['Template'], n
    for r in c['Rules']:
        if r['Property'].startswith('On') or r['Property'] in protected:
            assert get(n, r['Property']) == r['InvariantScript'], (n, r['Property'])
        behavior += r['Property'].startswith('On')
for n in ['App', 'tmrLoadingFlow', 'tmrLoadingVisual']:
    assert cs[n] == old[n], n
for n, b in old_members.items():
    if n.startswith('References/') and n != 'References/Templates.json' or n == 'Header.json':
        assert members[n] == b, n
before_templates = json.loads(old_members['References/Templates.json'])
after_templates = json.loads(members['References/Templates.json'])
added_image = after_templates['UsedTemplates'].pop()
assert added_image['Name'] == 'image' and after_templates == before_templates

enums = {
    'Font': {"'Open Sans'"}, 'FontWeight': {'Normal', 'Semibold', 'Bold', 'Lighter'},
    'LayoutMode': {'Auto'}, 'LayoutDirection': {'Horizontal', 'Vertical'},
    'LayoutAlignItems': {'Start', 'End', 'Center', 'Stretch'},
    'LayoutJustifyContent': {'Start', 'End', 'Center', 'SpaceBetween'},
    'LayoutOverflow': {'Scroll', 'Hide'},
    'AlignInContainer': {'Start', 'End', 'Center', 'Stretch', 'SetByContainer'},
    'Align': {'Left', 'Right', 'Center', 'Justify'},
    'VerticalAlign': {'Top', 'Middle', 'Bottom'}, 'ImagePosition': {'Fit', 'Fill', 'Stretch', 'Center', 'Tile'},
}
references_checked = 0
rules = []
for n, c in cs.items():
    for p, fx in props[n].items():
        assert 'OpenSans' not in fx, (n, p)
        if p == 'Font':
            assert fx == "Font.'Open Sans'", n
        if fx:
            rules.append(dict(name=n + '.' + p, formula=fx))
        # Ignore quoted string literals when inspecting actual formula references.
        expression = re.sub(r'"(?:[^"]|"")*"', '""', fx)
        for prefix, member in re.findall(r"\b([A-Za-z_][A-Za-z_0-9]*)\.('[^']+'|[A-Za-z_][A-Za-z_0-9]*)", expression):
            if prefix in enums:
                assert member in enums[prefix], (n, p, prefix, member)
            target = n if prefix == 'Self' else c.get('Parent') if prefix == 'Parent' else prefix
            if target in props and (prefix in ['Self', 'Parent'] or prefix in cs):
                builtins = {'TemplateWidth', 'TemplateHeight', 'TemplateSize', 'AllItems', 'Selected'} if cs[target]['Template']['Name'] == 'gallery' else set()
                builtins |= {'Value'} if cs[target]['Template']['Name'] == 'timer' else set()
                builtins |= {'Text'} if cs[target]['Template']['Name'] == 'text' else set()
                builtins |= {'Width', 'Height', 'ActiveScreen', 'Theme'} if target == 'App' else set()
                builtins |= {'Results', 'OriginalImage'} if target == 'TextRecognizer1' else set()
                assert member in props[target] or member in builtins, (n, p, prefix, member)
                references_checked += 1

yaml_controls = {}
for path in (ROOT / 'app-src-mobile-v5/Src').glob('*.pa.yaml'):
    assert 'OpenSans' not in path.read_text(encoding='utf8')
    for v in walk(yaml.safe_load(path.read_bytes())):
        for n, node in v.items():
            if n in cs and isinstance(node, dict) and 'Properties' in node:
                yaml_controls[n] = node
                for p, fx in node['Properties'].items():
                    assert fx == '=' + get(n, p), (n, p)
for n, c in cs.items():
    if c['Template']['Name'] not in ['galleryTemplate', 'hostControl', 'appinfo']:
        assert n in yaml_controls
        assert [x['Name'] for x in c['Children'] if x['Template']['Name'] != 'galleryTemplate'] == [next(iter(x)) for x in yaml_controls[n].get('Children', [])], n
    if c['Template']['Name'] == 'groupContainer':
        assert [get(x['Name'], 'ZIndex') for x in c['Children']] == [str(i) for i in range(1, len(c['Children'])+1)], n

previous = json.loads((ROOT / 'validation/mobile-v4/fx-input.json').read_text(encoding='utf8'))
tests = [t for t in previous['tests'] if not t['name'].startswith(('layout_', 'viewport_', 'warehouse_height_'))]


def test(name, formula, expected):
    tests.append(dict(name=name, formula=formula, expected=str(expected)))


for width, height in [(320,480), (320,568), (360,640), (375,667), (390,844), (412,915), (430,932), (844,390), (390,240), (1024,768)]:
    for n in ['conHome', 'conSearch', 'conLoading', 'conResults', 'conError']:
        expression = get(n, 'Width').replace('Parent.Width', str(width))
        test(f'width_{width}_{height}_{n}', f'Text({expression})', min(width,560))
    for n, bindings in [
        ('conHome', 'conHomeIntro:{Height:224},conHomeAction:{Height:200},lblHomeFooter:{Height:48}'),
        ('conSearch', 'conSearchHeader:{Height:48},lblScanInstruction:{Height:48},conSearchForm:{Height:572}'),
        ('conError', 'conErrorCard:{Height:328}')]:
        expression = get(n, 'PaddingTop').replace('Parent.Height', str(height))
        test(f'bounded_padding_{width}_{height}_{n}', f'With({{{bindings}}},With({{p:{expression}}},If(p >= 16 && p <= 120,"PASS","FAIL")))', 'PASS')
for expanded in [False,True]:
    for count in [0,1,4,17,50]:
        rows = 'FirstN(Table('+','.join('{n:'+str(i)+'}' for i in range(50))+'),'+str(count)+')'
        bindings = f'varProductExpanded:{str(expanded).lower()},varExpandedItemNumber:"SKU",ThisItem:{{ItemNumber:"SKU",WarehouseRows:{rows}}}'
        test(f'warehouse_height_{expanded}_{count}', 'With({'+bindings+'},Text('+get('galWarehouses','Height')+'))', count*52 if expanded else 0)
test('collapsed_product_card', 'With({varProductExpanded:false,varExpandedItemNumber:"SKU",ThisItem:{ItemNumber:"SKU"},galWarehouses:{Y:100,Height:208},btnProductToggle:{Height:76}},Text('+get('btnProductCard','Height')+'))', 76)
for value in ['""','"   "','"57047"']:
    # Real button gating expression; local record substitutes the Canvas control.
    expected = 'disabled' if value in ['""','"   "'] else 'edit'
    expression = get('btnSearchProduct','DisplayMode').replace('App.ActiveScreen = scrScan', 'true')
    test('manual_button_'+value, 'With({txtProductName:{Text:'+value+'},varScanReady:true,varScanAccepted:false,varFlowCallStarted:false,DisplayMode:{Disabled:"disabled",Edit:"edit"}},'+expression+')', expected)
(OUT / 'fx-input.json').write_text(json.dumps(dict(rules=rules,tests=tests),ensure_ascii=False),encoding='utf8')
summary = dict(status='PASS', formula_count=len(rules), executable_checks=len(tests),
    original_behavior_formulas_unchanged=behavior, app_and_timers_identical=True,
    control_reference_checks=references_checked, invalid_font_identifiers=0,
    yaml_runtime_parity=True, backend_references_byte_identical=True,
    studio_app_checker='NOT RUN', physical_phone='NOT TESTED')
(OUT / 'static-checks.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
print(f'PASS: {len(rules)} formulas; {references_checked} control references; {behavior} unchanged behavior formulas; {len(tests)} executable cases prepared.')
