"""Repair the supplied Studio snapshot without reloading YAML. No original edits."""
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent.parent
OUT = ROOT / 'Barkod-Uygulamasi-Phase2-FIXED-v2.msapp'
FIELDS = ('OverridableProperties', 'PCFDynamicSchemaForIRRetrieval')

def read(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(set(z.namelist()))
        return {n: z.read(n) for n in z.namelist()}

def walk(v):
    yield v
    if isinstance(v, dict):
        for x in v.values():
            yield from walk(x)
    elif isinstance(v, list):
        for x in v:
            yield from walk(x)

def find(files):
    matches = []
    for n, data in files.items():
        if n.endswith('.json'):
            for v in walk(json.loads(data)):
                if isinstance(v, dict) and v.get('Name') == 'TextRecognizer1' and 'Template' in v:
                    matches.append((n, v))
    assert len(matches) == 1
    return matches[0]

def run(name, args):
    p = subprocess.run(args, capture_output=True, text=True, encoding='utf8')
    (BASE / 'reports' / name).write_text(json.dumps({'command': subprocess.list2cmdline(args),
        'stdout': p.stdout, 'stderr': p.stderr, 'exit': p.returncode}, indent=2), encoding='utf8')
    print(p.stdout)
    assert p.returncode == 0

healthy = read(ROOT / 'forensics/textrecognizer-repair/healthy/input.msapp')
studio = read(BASE / 'inputs/studio.msapp')
old_fixed = read(ROOT / 'Barkod-Uygulamasi-Phase2-FIXED.msapp')
hn, hc = find(healthy)
sn, sc = find(studio)
_, oc = find(old_fixed)
assert {k:v for k,v in hc['Template'].items() if k not in FIELDS} == {k:v for k,v in sc['Template'].items() if k not in FIELDS}
assert sc['Template'][FIELDS[0]]['Results']['Type']['Kind'] == 'Record'
assert oc['Template'][FIELDS[0]]['Results']['Type']['Kind'] == 'Table'
assert next(r['InvariantScript'] for r in sc['Rules'] if r['Property']=='OnChange') == 'false'
evidence = {'healthy': {f:hc['Template'][f] for f in FIELDS},
            'previous_fixed': {f:oc['Template'][f] for f in FIELDS},
            'studio_export': {f:sc['Template'][f] for f in FIELDS},
            'same_control_definition': True, 'studio_onchange': 'false',
            'studio_control_id': sc['ControlUniqueId'], 'studio_parent': sc['Parent']}
(BASE/'reports/comparison.json').write_text(json.dumps(evidence,indent=2),encoding='utf8')
msapr = next((BASE/'source').glob('*.msapr'))
original = msapr.read_bytes()
files = read(msapr)
doc = json.loads(files['msapp/'+sn])
control = next(v for v in walk(doc) if isinstance(v,dict) and v.get('Name')=='TextRecognizer1' and 'Template' in v)
for f in FIELDS:
    control['Template'][f] = copy.deepcopy(hc['Template'][f])
assert not OUT.exists()
with zipfile.ZipFile(io.BytesIO(original)) as source, zipfile.ZipFile(msapr,'w') as target:
    target.comment = source.comment
    for entry in source.infolist():
        target.writestr(entry, json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode('utf8')
                        if entry.filename=='msapp/'+sn else source.read(entry.filename))
run('pack.json',['pac','canvas','pack','--sources',str(BASE/'source'),'--msapp',str(OUT),'--layout','SourceCode','--disable-load-from-yaml'])
run('reunpack.json',['pac','canvas','unpack','--msapp',str(OUT),'--sources',str(BASE/'roundtrip'),'--layout','SourceCode'])
fixed = read(OUT)
assert set(fixed) == set(studio)|{'packed.json'}
assert json.loads(fixed['packed.json'])['LoadConfiguration']['LoadFromYaml'] is False
assert all(fixed[n]==data for n,data in studio.items() if n!=sn)
expected_doc = json.loads(studio[sn])
expected_control = next(v for v in walk(expected_doc) if isinstance(v,dict) and v.get('Name')=='TextRecognizer1' and 'Template' in v)
for f in FIELDS:
    expected_control['Template'][f] = hc['Template'][f]
assert json.loads(fixed[sn]) == expected_doc
roundtrip = read(next((BASE/'roundtrip').glob('*.msapr')))
_, rc = find(roundtrip)
for f in FIELDS:
    assert rc['Template'][f] == hc['Template'][f]
for n,data in roundtrip.items():
    if n.startswith('msapp/'):
        assert data == fixed[n.removeprefix('msapp/')]
for label, representation in [('fixed',fixed),('roundtrip',roundtrip)]:
    _, instance = find(representation)
    assert instance['Template'][FIELDS[0]]['Results']['Type']['Kind']=='Table'
    assert json.loads(instance['Template'][FIELDS[1]]['Results']['DynamicSchema'])['type']=='array'
    assert next(r['InvariantScript'] for r in instance['Rules'] if r['Property']=='OnChange')=='false'
result={'package_validation':'PASS','runtime':'NOT EXECUTED',
        'output':str(OUT),'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'bytes':OUT.stat().st_size,
        'changed_entry':sn,'added_entry':'packed.json','LoadFromYaml':False,
        'all_other_studio_entries_byte_identical':True,'all_formula_values_unchanged':True,
        'healthy_schema_survives_reunpack':True}
(BASE/'reports/validation.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
