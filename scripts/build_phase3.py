"""Build from the repaired serialized app; keep review YAML and runtime rules aligned.

Requires Python + PyYAML and PAC. Never reload YAML: that previously lost OCR schema.
"""
import copy
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile
import yaml

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'Barkod-Uygulamasi-Phase2-FIXED-v2.msapp'
SOURCE = ROOT / 'app-src-phase3'
REPORT = ROOT / 'validation/phase3'
OUTPUT = ROOT / 'Barkod-Uygulamasi-Phase3-Orange.msapp'
REPORT.mkdir(parents=True, exist_ok=True)
base_source = ROOT/'build/phase3-base'
if not base_source.exists():
    subprocess.run(['pac','canvas','unpack','--msapp',str(BASE),'--sources',str(base_source),
                    '--layout','SourceCode'],check=True,cwd=ROOT)

def archive(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        return {n: z.read(n) for n in z.namelist()}

def walk(v):
    if isinstance(v, dict):
        yield v
        for x in v.values():
            yield from walk(x)
    elif isinstance(v, list):
        for x in v:
            yield from walk(x)

original = archive(BASE)
docs = {n: json.loads(b) for n,b in original.items() if n.startswith('Controls/')}
controls = {v['Name']: v for d in docs.values() for v in walk(d) if 'Rules' in v and 'Name' in v}
changed = {}

def get(name, prop):
    return next(r['InvariantScript'] for r in controls[name]['Rules'] if r['Property'] == prop)

def setp(name, **props):
    c = controls[name]
    for p, value in props.items():
        value = str(value)
        r = next((r for r in c['Rules'] if r['Property'] == p), None)
        if r is None:
            r = {'Property': p, 'Category': 'Behavior' if p.startswith('On') else 'Design', 'RuleProviderType': 'Unknown'}
            c['Rules'].append(r)
            c['ControlPropertyState'].append(p)
        r['InvariantScript'] = value
        changed.setdefault(name, set()).add(p)

orange = 'RGBA(194, 65, 12, 1)'
soft = 'RGBA(255, 247, 237, 1)'
white = 'RGBA(255, 255, 255, 1)'
for name, c in controls.items():
    for r in list(c['Rules']):
        value = r['InvariantScript']
        for old,new in [('RGBA(37, 99, 235, 1)',orange), ('RGBA(247, 249, 252, 1)',white),
                        ('RGBA(245, 248, 255, 1)',soft), ('RGBA(191, 205, 232, 1)','RGBA(254, 215, 170, 1)')]:
            value = value.replace(old,new)
        if value != r['InvariantScript']:
            setp(name, **{r['Property']:value})
    if c['Template']['Name'] == 'PowerApps_CoreControls_ButtonCanvas':
        setp(name, BasePaletteColor=orange)
        if get(name,'DisplayMode') == 'DisplayMode.Disabled':
            setp(name, Appearance='"Secondary"')

setp('App', OnStart=get('App','OnStart') + ';\nSet(varExpandedItemNumber, Blank())')
setp('scrScan', OnVisible='''Set(varScanAccepted, false);
Set(varFlowCallStarted, false);
Set(varLoadingExecutionStarted, false);
Set(varOcrEmpty, false);
Set(varAcceptedText, "");
Set(varErrorMessage, "");
Set(varResultJson, "");
Reset(TextRecognizer1)''')
setp('TextRecognizer1', ShowBoundingBoxes='false', OnChange='''If(
    App.ActiveScreen = scrScan && !varScanAccepted && !varFlowCallStarted,
    IfError(
        With(
            {
                candidates: SortByColumns(
                    AddColumns(
                        Filter(
                            TextRecognizer1.Results,
                            !IsBlank(TrimEnds(Text)) &&
                            !IsBlank(BoundingBox.Top) && BoundingBox.Top >= 0
                        ),
                        OcrTop, BoundingBox.Top,
                        OcrLeft, Coalesce(BoundingBox.Left, 0),
                        OcrPage, Coalesce(PageNumber, 1)
                    ),
                    "OcrTop", SortOrder.Ascending,
                    "OcrPage", SortOrder.Ascending,
                    "OcrLeft", SortOrder.Ascending,
                    "Text", SortOrder.Ascending
                )
            },
            If(
                IsEmpty(candidates),
                Set(varAcceptedText, "");
                Set(varOcrEmpty, true);
                Notify("Okunabilir bir ürün adı bulunamadı. Etiketi netleştirip yeniden tarayın.", NotificationType.Warning),
                Set(varAcceptedText, TrimEnds(First(candidates).Text));
                Set(varOcrEmpty, false);
                Set(varScanAccepted, true);
                Navigate(scrLoading, ScreenTransition.Fade)
            )
        ),
        Set(varAcceptedText, "");
        Set(varOcrEmpty, true);
        Notify("Görüntüdeki metin okunamadı. Lütfen yeniden tarayın.", NotificationType.Warning)
    )
)''')
# Remove the manual action from the runtime tree, not merely hide it.
for d in docs.values():
    for v in walk(d):
        if 'Children' in v:
            v['Children'] = [c for c in v['Children'] if c.get('Name') != 'btnContinueWithSelectedProduct']
controls.pop('btnContinueWithSelectedProduct')
setp('lblScanInstruction', Text='"Etiketi çekin veya bir görsel seçin. En üstteki metin ürün adı olarak otomatik alınır."')
setp('lblScanHint', Text='"Seçim yapmanız gerekmez. Metin okunduğunda stok sorgusu otomatik başlar."')
# Preserve the existing flow invocation, parse/coalesce logic, grouping and error paths.
flow_before = get('tmrLoadingFlow','OnTimerEnd')
flow_after = flow_before.replace('!varLoadingExecutionStarted,',
    'varScanAccepted && !IsBlank(varAcceptedText) && !varFlowCallStarted && !varLoadingExecutionStarted,',1)
flow_after = flow_after.replace('Set(varLoadingExecutionStarted, true);',
    'Set(varLoadingExecutionStarted, true);\n    Set(varFlowCallStarted, true);',1)
setp('scrLoading', OnVisible='false')
setp('tmrLoadingFlow', OnTimerEnd=flow_after)
setp('scrResults', OnVisible='Set(varExpandedItemNumber, Blank())')
setp('lblResultsEyebrow', Text='"STOK ASİSTANI"', Y='24')
setp('lblResultsTitle', Text='"Depo Stokları"', Y='62', Width='Parent.Width - 64')
setp('lblResultsCount', Y='112', Width='Parent.Width - 64')
setp('btnResultsScanAgain', X='32', Y='162', Width='Parent.Width - 64', Height='56', FontSize='18')
setp('galProducts', AutoHeight='true', TemplateSize='1', TemplatePadding='12',
     DelayItemLoading='false', Y='242', Height='Parent.Height - Self.Y - 24',
     AccessibleLabel='"Ürünler. Ambar stoklarını görmek için ürün kartını açın."')
# AutoHeight is the serialized gallery switch used for a flexible-height gallery.
controls['galProducts']['VariantName'] = 'galleryVariableTemplateHeight'
expanded = 'varExpandedItemNumber = ThisItem.ItemNumber'
toggle = 'Set(varExpandedItemNumber, If(varExpandedItemNumber = ThisItem.ItemNumber, Blank(), ThisItem.ItemNumber))'
setp('btnProductCard', DisplayMode='DisplayMode.Edit', Appearance='"Secondary"',
     BorderColor='RGBA(229, 231, 235, 1)', OnSelect=toggle,
     Height='galWarehouses.Y + galWarehouses.Height + 16',
     AccessibleLabel='Coalesce(ThisItem.ProductName, ThisItem.ItemNumber) & If(varExpandedItemNumber = ThisItem.ItemNumber, ", açık. Kapat", ", kapalı. Ambarları göster")')
setp('lblProductName', Text='Coalesce(ThisItem.ProductName, ThisItem.ItemNumber, "Ürün")',
     X='24', Y='18', Width='Parent.TemplateWidth - 104', Height='32', AutoHeight='true',
     Size='18', OnSelect='Select(btnProductCard)')
setp('lblProductNumber', X='24', Y='lblProductName.Y + lblProductName.Height + 6',
     Width='Parent.TemplateWidth - 48', Height='28', Color='RGBA(107, 114, 128, 1)',
     Text='ThisItem.ItemNumber & "  •  " & CountRows(Distinct(ThisItem.WarehouseRows, InventoryWarehouseId)) & " ambar"',
     OnSelect='Select(btnProductCard)')
setp('lblProductConflict', X='24', Y='lblProductNumber.Y + lblProductNumber.Height + 8',
     Visible=f'{expanded} && ThisItem.HasNameConflict', Height=f'If({expanded} && ThisItem.HasNameConflict, 40, 0)',
     Width='Parent.TemplateWidth - 48')
setp('galWarehouses', X='24', Y='lblProductConflict.Y + lblProductConflict.Height',
     Width='Parent.TemplateWidth - 48', Visible=expanded,
     Height=f'If({expanded}, Min(CountRows(ThisItem.WarehouseRows) * 80, 400), 0)',
     TemplateSize='80', ShowScrollbar='true', AccessibleLabel='"Ambar ve stok miktarları"')
setp('lblWarehouseName', X='0', Y='12', Height='32', Width='Parent.TemplateWidth * 0.57', Size='15',
     Tooltip='ThisItem.InventoryWarehouseId')
setp('lblWarehouseAvailable', X='Parent.TemplateWidth * 0.61', Y='12', Height='48',
     Width='Parent.TemplateWidth * 0.39', Size='22')
setp('lblWarehouseAvailableCaption', Visible='false', Height='0', Y='0')
setp('lblWarehouseReserved', X='0', Y='46', Height='26', Width='Parent.TemplateWidth * 0.57',
     Fill=soft, Color=orange, PaddingLeft='8', Size='11',
     Text='"Reserve: " & Text(ThisItem.ReservedOnHandQuantity, "[$-tr-TR]0.##")',
     Visible='ThisItem.AvailableOnHandQuantity < 3 && ThisItem.ReservedOnHandQuantity <> 0')
for name in ['btnResultsEmptyCard','btnResultsEmptyMark','lblResultsEmptyTitle','lblResultsEmptyBody']:
    setp(name,Y=f'({get(name,"Y")}) + 64')

# A visible open/close affordance, cloned from a supported label instance.
chevron = copy.deepcopy(controls['lblProductNumber'])
chevron.update(Name='lblProductChevron', ControlUniqueId='2001', PublishOrderIndex=2001)
controls['lblProductChevron'] = chevron
template = next(v for v in walk(controls['galProducts']) if v.get('Template',{}).get('Name')=='galleryTemplate')
template['Children'].append(chevron)
setp('lblProductChevron', Text=f'If({expanded}, "−", "+")', X='Parent.TemplateWidth - 72',
     Y='16', Width='48', Height='48', Align='Align.Center', Size='24', Color=orange,
     ZIndex='10', OnSelect='Select(btnProductCard)')

class Dumper(yaml.SafeDumper):
    pass
def represent_string(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str',data,style='|' if '\n' in data else None)
Dumper.add_representer(str,represent_string)

updated = dict(original)
properties = json.loads(original['Properties.json'])
counts = Counter(c['Template']['Name'] for c in controls.values())
properties['ControlCount'] = {name: counts[name] for name in properties['ControlCount']}
updated['Properties.json'] = json.dumps(properties,ensure_ascii=False,separators=(',',':')).encode('utf8')
for n,d in docs.items():
    updated[n] = json.dumps(d,ensure_ascii=False,separators=(',',':')).encode('utf8')
for n,b in original.items():
    if not n.endswith('.pa.yaml') or n.endswith('_EditorState.pa.yaml'):
        continue
    doc = yaml.safe_load(b)
    def sync(name, node):
        if name in controls:
            props = node.setdefault('Properties',{})
            rules = {r['Property']:r['InvariantScript'] for r in controls[name]['Rules']}
            for p in sorted(set(props) | changed.get(name,set())):
                if p in rules and rules[p]: props[p] = '=' + rules[p]
            if name=='galProducts': node['Variant']='VariableHeight'
        if 'Children' in node:
            node['Children'] = [c for c in node['Children'] if 'btnContinueWithSelectedProduct' not in c]
            if name=='galProducts':
                source = next(c['lblProductNumber'] for c in node['Children'] if 'lblProductNumber' in c)
                node['Children'].append({'lblProductChevron':copy.deepcopy(source)})
            for child in node['Children']:
                for cn, cv in child.items(): sync(cn,cv)
    for key, value in doc.items():
        if key=='Screens':
            for name,node in value.items(): sync(name,node)
        elif key=='App': sync('App',value)
    updated[n] = yaml.dump(doc,Dumper=Dumper,allow_unicode=True,sort_keys=False,width=110).encode('utf8')

# Keep the existing worktree intact; deliver an independent, complete source tree.
if not SOURCE.exists():
    shutil.copytree(ROOT/'build/phase3-base', SOURCE)
snapshot = next(SOURCE.glob('*.msapr'))
payload = archive(next((ROOT/'build/phase3-base').glob('*.msapr')))
for n,b in updated.items():
    if 'msapp/'+n in payload:
        payload['msapp/'+n] = b
with zipfile.ZipFile(snapshot,'w',zipfile.ZIP_DEFLATED) as z:
    for n,b in payload.items(): z.writestr(n,b)
for n,b in updated.items():
    if n.startswith('Src/'):
        path = SOURCE/n
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(b)

def run(name,args):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf8',errors='replace')
    (REPORT/name).write_text(json.dumps({'command':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2),encoding='utf8')
    assert p.returncode==0,p.stdout+p.stderr

run('pack.json',['pac','canvas','pack','--sources',str(SOURCE),'--msapp',str(OUTPUT),'--layout','SourceCode','--disable-load-from-yaml','--overwrite'])
result=archive(OUTPUT)
assert json.loads(result['packed.json'])['LoadConfiguration']['LoadFromYaml'] is False
assert all(result[n]==b for n,b in updated.items() if n!='packed.json')
assert controls['TextRecognizer1']['Template']==next(v for v in walk(json.loads(original['Controls/15.json'])) if v.get('Name')=='TextRecognizer1')['Template']
assert all(result[n]==b for n,b in original.items() if n.startswith('References/') or n=='Header.json')
assert {k:v for k,v in properties.items() if k!='ControlCount'} == {k:v for k,v in json.loads(original['Properties.json']).items() if k!='ControlCount'}
rules='\n'.join(r['InvariantScript'] for c in controls.values() for r in c['Rules'])
assert rules.count('barcode_flow.Run(')==1
assert 'TextRecognizer1.Selected' not in rules
assert flow_before[flow_before.index('    IfError('):] == flow_after[flow_after.index('    IfError('):]
with tempfile.TemporaryDirectory(prefix='phase3-roundtrip-',dir=ROOT/'build') as temp:
    run('roundtrip.json',['pac','canvas','unpack','--msapp',str(OUTPUT),'--sources',temp,'--layout','SourceCode'])
    roundtrip=archive(next(Path(temp).glob('*.msapr')))
    assert all(result[n.removeprefix('msapp/')]==b for n,b in roundtrip.items() if n.startswith('msapp/'))
(REPORT/'validation.json').write_text(json.dumps({
    'package':'PASS','runtime':'NOT EXECUTED: no connected apps or browsers',
    'sha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),'bytes':OUTPUT.stat().st_size,
    'ocr_metadata_unchanged':True,'backend_references_unchanged':True,'flow_parse_group_error_logic_unchanged':True,
    'flow_call_sites':1,'manual_selection_references':0,'roundtrip_byte_identical':True,
    'changed_controls':{k:sorted(v) for k,v in changed.items()},
    'changed_package_entries':[n for n,b in result.items() if original.get(n)!=b]
},ensure_ascii=False,indent=2),encoding='utf8')
print('Pack and roundtrip PASS:',OUTPUT)
