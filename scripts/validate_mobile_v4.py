"""Validate the actual v4 package against the working v3.1 package."""
import json
from pathlib import Path
import zipfile
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'validation/mobile-v4'


def walk(v):
    if isinstance(v, dict):
        yield v
        for x in v.values(): yield from walk(x)
    elif isinstance(v, list):
        for x in v: yield from walk(x)


def load(version):
    with zipfile.ZipFile(ROOT / f'Barkod-Uygulamasi-Mobile-Light-{version}.msapp') as z:
        assert z.testzip() is None
        members = {n: z.read(n) for n in z.namelist()}
    cs = {c['Name']: c for n, b in members.items() if n.startswith('Controls/')
          for c in walk(json.loads(b)) if 'Name' in c and 'Rules' in c}
    return members, cs


baseline, old = load('v3-1')
members, cs = load('v4')
prop = lambda n, p: next(r['InvariantScript'] for r in cs[n]['Rules'] if r['Property'] == p)
assert len({c['ControlUniqueId'] for c in cs.values()}) == len(cs)
assert all(isinstance(c.get('Children'), list) for c in cs.values())
behavior_count = 0
for n, c in old.items():
    for r in c['Rules']:
        if r['Property'].startswith('On'):
            assert prop(n, r['Property']) == r['InvariantScript'], (n, r['Property'])
            behavior_count += 1
for n in members:
    if n.startswith('References/') or n == 'Header.json':
        assert members[n] == baseline[n], n
assert cs['TextRecognizer1']['Template'] == old['TextRecognizer1']['Template']
for p in ['Start', 'Reset', 'AutoStart', 'AutoPause', 'Repeat', 'Duration']:
    assert prop('tmrLoadingFlow', p) == next(r['InvariantScript'] for r in old['tmrLoadingFlow']['Rules'] if r['Property'] == p)
settings = json.loads(members['Properties.json'])
for p in ['DocumentLayoutScaleToFit', 'DocumentLayoutMaintainAspectRatio', 'DocumentLayoutLockOrientation']:
    assert settings[p] is False
assert prop('TextRecognizer1', 'Height') == prop('TextRecognizer1', 'ButtonHeight') == '48'
assert prop('galProducts', 'Items') == 'colProductGroups'
assert prop('galWarehouses', 'Items') == 'ThisItem.WarehouseRows'
assert prop('galProducts', 'AutoHeight') == 'true'
assert prop('galWarehouses', 'TemplatePadding') == '0'
assert 'Min(' not in prop('galWarehouses', 'Height')
for c in cs.values():
    if c['Template']['Name'] == 'groupContainer':
        assert [prop(child['Name'], 'ZIndex') for child in c['Children']] == [str(i) for i in range(1, len(c['Children'])+1)]
rules = [{'name': n+'.'+r['Property'], 'formula': r['InvariantScript']}
         for n, c in cs.items() for r in c['Rules'] if r['InvariantScript']]
assert sum('barcode_flow.Run(' in r['formula'] for r in rules) == 1
assert all('Reserve:' not in r['formula'] for r in rules)
# The previous executable fixtures are valid because every original behavior,
# all OCR metadata, and all flow timing rules above are byte-for-byte identical.
previous = json.loads((ROOT/'validation/mobile-v3-1/fx-input.json').read_text(encoding='utf8'))
tests = [t for t in previous['tests'] if not t['name'].startswith('layout_')]


def test(name, formula, expected):
    tests.append(dict(name=name, formula=formula, expected=expected))


for value, expected in [('"030"', '30'), ('"01"', '1'), ('0', '0'), ('30', '30'), ('1', '1'),
                        ('-12', '-12'), ('12.5', '12,5'), ('1234567', '1234567')]:
    test('quantity_'+value, 'With({ThisItem:{AvailableOnHandQuantity:'+value+'}},'+prop('lblWarehouseAvailable', 'Text')+')', expected)
for value, expected in [('Blank()', 'HIDDEN'), ('0', 'HIDDEN'), ('1', 'SHOWN'), ('30', 'SHOWN')]:
    test('reserved_'+value, 'With({ThisItem:{ReservedOnHandQuantity:'+value+'}},If('+prop('lblWarehouseReserved', 'Visible')+',"SHOWN","HIDDEN"))', expected)

# Evaluate real layout formulas. These checks do not emulate native text rendering.
viewports = [(320,480),(320,568),(360,640),(375,667),(390,844),(412,915),(430,932),(844,390),(390,240),(1024,768)]
for width, height in viewports:
    for root in ['conHome','conSearch','conLoading','conResults','conError']:
        expression = prop(root, 'Width').replace('Parent.Width', str(width))
        test(f'viewport_{width}_{height}_{root}', f'With({{w:{expression}}},If(w <= {width} && w >= 320,"FITS","FAIL"))', 'FITS')
        assert prop(root, 'Height') == 'Parent.Height'
        assert prop(cs[root]['Parent'], 'Height') == 'App.Height'
        assert prop(root, 'PaddingBottom') == '24'
for expanded in [False, True]:
    for count in [0,1,3,4,17,50]:
        rows = 'FirstN(Table('+','.join('{n:'+str(i)+'}' for i in range(50))+'),'+str(count)+')'
        bindings = f'varProductExpanded:{str(expanded).lower()},varExpandedItemNumber:"SKU",ThisItem:{{ItemNumber:"SKU",WarehouseRows:{rows}}}'
        test(f'warehouse_height_{expanded}_{count}', 'With({'+bindings+'},Text('+prop('galWarehouses','Height')+'))', str(count*64 if expanded else 0))

# Check that review YAML contains the same values and hierarchy as the runtime.
yaml_controls = {}
for path in (ROOT/'app-src-mobile-v4/Src').glob('*.pa.yaml'):
    doc = yaml.safe_load(path.read_text(encoding='utf8'))
    for v in walk(doc):
        for n, node in v.items():
            if n in cs and isinstance(node, dict) and 'Properties' in node:
                yaml_controls[n] = node
                for p, fx in node['Properties'].items():
                    assert fx == '='+prop(n,p), (n,p)
for n,c in cs.items():
    if c['Template']['Name'] not in ['galleryTemplate','hostControl','appinfo']:
        assert n in yaml_controls, n
        actual = [x['Name'] for x in c['Children'] if x['Template']['Name'] != 'galleryTemplate']
        if n != 'App':
            assert actual == [next(iter(x)) for x in yaml_controls[n].get('Children',[])], n

(OUT/'fx-input.json').write_text(json.dumps(dict(rules=rules, tests=tests),ensure_ascii=False),encoding='utf8')
(OUT/'static-checks.json').write_text(json.dumps(dict(
    original_behavior_formulas_unchanged=behavior_count, references_byte_identical=True,
    ocr_metadata_identical=True, yaml_runtime_parity=True, control_count=len(cs),
    formula_count=len(rules), executable_cases=len(tests), viewports=viewports,
    physical_phone='NOT TESTED', studio='NOT TESTED'),indent=2),encoding='utf8')
print(f'PASS: {behavior_count} original behavior formulas preserved; {len(rules)} formulas, {len(tests)} executable checks prepared.')
