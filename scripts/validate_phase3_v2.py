"""Extract current package formulas and regression cases for the Power Fx interpreter."""
import itertools
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():yield from walk(x)
    elif isinstance(v,list):
        for x in v:yield from walk(x)

with zipfile.ZipFile(ROOT/'Barkod-Uygulamasi-Phase3-Orange-v2.msapp') as z:
    cs={c['Name']:c for n in z.namelist() if n.startswith('Controls/')
        for c in walk(json.loads(z.read(n))) if 'Rules' in c}
    templates=json.loads(z.read('References/Templates.json'))['UsedTemplates']
rules=[{'name':c['Name']+'.'+r['Property'],'formula':r['InvariantScript']}
    for c in cs.values() for r in c['Rules'] if r['InvariantScript']]
def prop(n,p):return next(r['InvariantScript'] for r in cs[n]['Rules'] if r['Property']==p)
tests=json.loads((ROOT/'validation/phase3/fx-input.json').read_text(encoding='utf8'))['tests']
# Reuse only OCR fixtures: prove their extracted sort formula still matches this package.
ocr=prop('TextRecognizer1','OnChange')
sort=ocr[ocr.index('SortByColumns('):ocr.index('\n            },')].strip()
assert all(sort in t['formula'] for t in tests)
def test(name,formula,expected):tests.append({'name':name,'formula':formula,'expected':expected})
def boolfx(value):return 'true' if value else 'false'

guard=prop('tmrLoadingFlow','Start').replace('App.ActiveScreen = scrLoading','isLoading')
for loading,accepted,text,started,executed in itertools.product([False,True],repeat=5):
    bindings=f'isLoading:{boolfx(loading)},varScanAccepted:{boolfx(accepted)},varAcceptedText:{json.dumps("SKU" if text else "")},varFlowCallStarted:{boolfx(started)},varLoadingExecutionStarted:{boolfx(executed)}'
    expected='RUN' if loading and accepted and text and not started and not executed else 'STOP'
    test('dispatch_'+''.join(str(int(x)) for x in [loading,accepted,text,started,executed]),
         f'With({{{bindings}}},If({guard},"RUN","STOP"))',expected)

accept=ocr[ocr.index('varScanReady && App.ActiveScreen = scrScan && !varScanAccepted'):ocr.index(',\n    IfError(')]
accept=accept.replace('App.ActiveScreen = scrScan','isScan').replace('TextRecognizer1.OriginalImage','image')
for name,ready,is_scan,image,baseline,accepted,started,expected in [
    ('entry_empty',True,True,'','',False,False,'STOP'),
    ('reset_in_progress',False,True,'old','old',False,False,'STOP'),
    ('stale_on_entry',True,True,'old','old',False,False,'STOP'),
    ('fresh_image',True,True,'new','old',False,False,'ACCEPT'),
    ('duplicate_ocr',True,True,'new','old',True,False,'STOP'),
    ('off_screen',True,False,'new','old',False,False,'STOP'),
    ('same_file_after_empty_reset',True,True,'same','',False,False,'ACCEPT')]:
    bindings=f'varScanReady:{boolfx(ready)},isScan:{boolfx(is_scan)},image:{json.dumps(image)},varScanEntryImage:{json.dumps(baseline)},varScanAccepted:{boolfx(accepted)},varFlowCallStarted:{boolfx(started)}'
    test(name,f'With({{{bindings}}},If({accept},"ACCEPT","STOP"))',expected)

products='''Table(
{ItemNumber:"A",ProductName:"Alpha",HasNameConflict:false,WarehouseRows:Table(
{InventoryWarehouseId:"02",AvailableOnHandQuantity:2,ReservedOnHandQuantity:1},
{InventoryWarehouseId:"05",AvailableOnHandQuantity:8,ReservedOnHandQuantity:0})},
{ItemNumber:"B",ProductName:"Beta",HasNameConflict:false,WarehouseRows:Table(
{InventoryWarehouseId:"BODIST-AND",AvailableOnHandQuantity:3,ReservedOnHandQuantity:5})})'''
for name,opened,item,expected in [('closed',False,'','A|B|'),('open_a',True,'A','A|02|05|B|'),
    ('open_b',True,'B','A|B|BODIST-AND|'),('close_a',False,'A','A|B|')]:
    test('accordion_'+name,f'With({{colProductGroups:{products},varProductExpanded:{boolfx(opened)},varExpandedItemNumber:"{item}"}},Concat({prop("galProducts","Items")},If(IsProduct,ItemNumber,InventoryWarehouseId),"|"))',expected)
for product,qty,reserved,expected in [(False,2,1,'SHOW'),(False,3,1,'HIDE'),(False,2,0,'HIDE'),(True,2,1,'HIDE')]:
    test(f'reserve_{product}_{qty}_{reserved}',
      f'With({{ThisItem:{{IsProduct:{boolfx(product)},AvailableOnHandQuantity:{qty},ReservedOnHandQuantity:{reserved}}}}},If({prop("lblWarehouseReserved","Visible")},"SHOW","HIDE"))',expected)

# Catch the specific hierarchy, overlap, and missing-template mistakes packaging alone misses.
gal=cs['galProducts']
assert prop('galProducts','TemplateSize')=='112' and prop('galProducts','AutoHeight')=='false'
assert len([c for c in cs.values() if c['Template']['Name']=='gallery'])==1
assert all(not c.get('Children') for c in gal['Children'] if c['Template']['Name']=='galleryTemplate')
assert all(c['Parent']=='galProducts' for c in gal['Children'])
assert prop('btnProductToggle','DisplayMode')=='DisplayMode.Edit'
assert int(prop('btnProductToggle','ZIndex')) > max(int(prop(c['Name'],'ZIndex')) for c in gal['Children'] if c['Name']!='btnProductToggle' and c['Template']['Name']!='galleryTemplate')
for c in gal['Children']:
    if c['Template']['Name']=='galleryTemplate':continue
    assert float(prop(c['Name'],'Y'))+float(prop(c['Name'],'Height'))<=112,c['Name']
assert any(t['Name']=='button' and t['Version']=='2.2.0' for t in templates)
assert len({c['ControlUniqueId'] for c in cs.values()})==len(cs)
assert prop('tmrLoadingFlow','AutoStart')=='false'
assert prop('TextRecognizer1','ImageDisplayed')=='false'
assert all(prop(n,'Fill')=='RGBA(255, 255, 255, 1)' for n,c in cs.items() if c['Template']['Name']=='screen')
assert not any(c['Template']['Name']=='PowerApps_CoreControls_ButtonCanvas' for c in cs.values())
# Canvas supports Ungroup, but the standalone interpreter explicitly does not.
# Keep those cases in the report for Studio execution; do not silently substitute an implementation.
runtime_only=[t for t in tests if t['name'].startswith('accordion_')]
tests=[t for t in tests if not t['name'].startswith('accordion_')]
(ROOT/'validation/phase3-v2/fx-input.json').write_text(json.dumps({'rules':rules,'tests':tests,
    'studio_cases':runtime_only,'studio_reason':'Standalone Microsoft Power Fx interpreter does not support Ungroup.'},ensure_ascii=False),encoding='utf8')
print(f'Hierarchy, hit target, fixed row bounds, template and white-surface checks PASS. {len(tests)} executable Power Fx cases; {len(runtime_only)} accordion cases require Studio.')
