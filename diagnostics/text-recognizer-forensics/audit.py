"""Read-only Canvas package audit. Run from the repository root with Python 3.

Writes evidence only beneath this script's directory. Never edits app sources.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
TERMS = re.compile(r'TextRecognizer1|TextRecognizer|msdyn_aimodels|Predict|Results|Selected|FullText|BoundingBox|OnChange', re.I)


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def walk(value, path='$'):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk(child, path + '/' + key)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from walk(child, path + '/' + str(i))


def decode(value):
    if isinstance(value, dict):
        return {k: decode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [decode(v) for v in value]
    if isinstance(value, str) and value.lstrip().startswith(('{', '[')):
        try:
            return decode(json.loads(value))
        except ValueError:
            # Manifest resource Paths contain escaped embedded JSON objects.
            try:
                return decode(json.loads(json.loads('"' + value + '"')))
            except ValueError:
                pass
    return value


packages = list(ROOT.glob('*.msapp')) + list((ROOT / 'app-src').glob('*.msapr'))
for name in subprocess.check_output(['git', 'ls-tree', '-rz', '--name-only', 'HEAD'], cwd=ROOT).decode().split('\0'):
    if name.endswith(('.msapp', '.msapr')):
        target = OUT / 'extracted' / 'git-head-artifacts' / Path(name).name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT))
        packages.append(target)
packages += list((OUT / 'experiments').glob('*.msapp'))
manifest, refs, controls, bindings, checks, settings = [], [], [], [], [], []
for index, package in enumerate(packages):
    label = str(package.relative_to(ROOT))
    entries = []
    with zipfile.ZipFile(package) as archive:
        for entry in archive.namelist():
            data = archive.read(entry)
            entries.append({'entry': entry, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
            try:
                source = data.decode('utf-8-sig')
            except UnicodeError:
                continue
            try:
                obj = json.loads(source)
            except ValueError:
                obj = None
            normalized = json.dumps(obj, ensure_ascii=False, indent=2) if obj is not None else source
            dest = OUT / 'extracted' / str(index) / entry
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(normalized, encoding='utf-8')
            for line, text in enumerate(normalized.splitlines(), 1):
                for match in TERMS.finditer(text):
                    refs.append({'package': label, 'entry': entry, 'line': line, 'column': match.start() + 1,
                                 'term': match.group(), 'context': text[max(0, match.start()-100):match.end()+180]})
            if obj is None:
                continue
            if entry.endswith(('packed.json', 'msapr-header.json', 'Header.json')):
                settings.append({'package': label, 'entry': entry, 'value': obj})
            for pointer, node in walk(obj):
                if not isinstance(node, dict):
                    continue
                if node.get('Name') == 'TextRecognizer1' and 'Template' in node:
                    template = node['Template']
                    controls.append({'package': label, 'entry': entry, 'pointer': pointer,
                                     'template': {k: v for k, v in template.items() if k != 'DynamicControlDefinitionJson'},
                                     'definition_sha256': hashlib.sha256(template['DynamicControlDefinitionJson'].encode()).hexdigest(),
                                     'rules': node['Rules']})
                    save('decoded-control-definition.json', decode(template['DynamicControlDefinitionJson']))
                if node.get('EntitySetName') == 'msdyn_aimodels':
                    item = {k: v for k, v in node.items() if k != 'WadlMetadata'}
                    xml = ET.fromstring(node['WadlMetadata']['WadlXml'])
                    item['predict_contract'] = [ET.tostring(e, encoding='unicode') for e in xml.iter()
                        if e.attrib.get('name') in ('Microsoft_Dynamics_CRM_PredictResponse', 'Predict_param_body_def')
                        or e.attrib.get('path', '').endswith('/Microsoft.Dynamics.CRM.Predict')]
                    bindings.append({'package': label, 'entry': entry, 'pointer': pointer, 'value': item})
                if node.get('ruleId', '').startswith('app-'):
                    checks.append({'package': label, 'entry': entry, 'rule': node})
    manifest.append({'index': index, 'path': label, 'sha256': hashlib.sha256(package.read_bytes()).hexdigest(), 'entries': entries})
for source in (ROOT / 'app-src' / 'Src').glob('*.pa.yaml'):
    for line, text in enumerate(source.read_text(encoding='utf-8').splitlines(), 1):
        for match in TERMS.finditer(text):
            refs.append({'package': 'working-source', 'entry': str(source.relative_to(ROOT)), 'line': line,
                         'column': match.start()+1, 'term': match.group(), 'context': text})
for name, value in [('manifest.json', manifest), ('references.json', refs), ('control-comparison.json', controls),
                    ('bindings.json', bindings), ('checker-evidence.json', checks), ('package-settings.json', settings)]:
    save(name, value)
save('schema-evidence.json', [
    {'package': c['package'], 'entry': c['entry'], 'version': c['template']['Version'],
     'overrides': c['template']['OverridableProperties'],
     'dynamic_schemas': {k: json.loads(v['DynamicSchema']) for k, v in
                         c['template']['PCFDynamicSchemaForIRRetrieval'].items()}}
    for c in controls])
source_artifact = next(m for m in manifest if m['path'].startswith('app-src') and m['path'].endswith('.msapr'))
baseline = {e['entry'].removeprefix('msapp/'): e['sha256'] for e in source_artifact['entries']
            if e['entry'].startswith('msapp/')}
workflow = []
for package in manifest:
    if 'experiments' not in Path(package['path']).parts:
        continue
    with zipfile.ZipFile(ROOT / package['path']) as archive:
        workflow.append({'package': package['path'], 'baseline_msapr': source_artifact['path'],
                         'baseline_entries': len(baseline),
                         'byte_identical_entries': [e['entry'] for e in package['entries']
                                                    if baseline.get(e['entry']) == e['sha256']],
                         'packed': json.loads(archive.read('packed.json')),
                         'source_files': [n for n in archive.namelist() if n.startswith('Src/')],
                         'source_has_ocr': any(b'TextRecognizer' in archive.read(n)
                                               for n in archive.namelist() if n.startswith('Src/'))})
save('workflow-evidence.json', workflow)
print(f'Audited {len(packages)} packages; {len(controls)} OCR instances; {len(refs)} term occurrences.')
