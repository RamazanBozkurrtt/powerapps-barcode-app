"""Evidence-constrained schema transplant. Run from any directory.

inspect: compare frozen inputs and unpacked snapshots without mutation.
repair: copy broken unpacked source to a new directory, transplant only the two
        schema containers from the healthy instance, then PAC pack/unpack.
verify: assert schemas survived and every unrelated Phase2 entry is unchanged.
"""
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent.parent
REPORTS = BASE / 'reports'
OUTPUT = ROOT / 'Barkod-Uygulamasi-Phase2-FIXED.msapp'
FIELDS = ('OverridableProperties', 'PCFDynamicSchemaForIRRetrieval')
PRIORITY = re.compile(r'TextRecognizer|Results|Selected|AIBuilder|AI Builder|RecognizeText|Type|Kind|Schema|Dynamic|Record|Table|array|object', re.I)


def dump(name, data):
    (REPORTS / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def decode(value):
    if isinstance(value, dict):
        return {k: decode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [decode(v) for v in value]
    if isinstance(value, str) and value.startswith(('{', '[')):
        try:
            return decode(json.loads(value))
        except ValueError:
            pass
    return value


def archive(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(set(z.namelist())), 'Duplicate ZIP members'
        return {n: z.read(n) for n in z.namelist()}


def walk(value, path='$'):
    yield path, value
    if isinstance(value, dict):
        for k, v in value.items():
            yield from walk(v, path + '/' + k)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, path + '/' + str(i))


def ocr(files):
    found = []
    for name, data in files.items():
        if not name.endswith('.json'):
            continue
        for path, node in walk(json.loads(data)):
            if isinstance(node, dict) and node.get('Name') == 'TextRecognizer1' and 'Template' in node:
                found.append((name, path, node))
    assert len(found) == 1, f'Expected one OCR instance, found {len(found)}'
    return found[0]


def differences(a, b, path='$'):
    if a == b:
        return []
    if isinstance(a, dict) and isinstance(b, dict):
        result = []
        for key in sorted(a.keys() | b.keys()):
            if key not in a or key not in b:
                result.append({'path': path + '/' + key, 'healthy': a.get(key), 'broken': b.get(key),
                               'healthy_present': key in a, 'broken_present': key in b})
            else:
                result += differences(a[key], b[key], path + '/' + key)
        return result
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in differences(x, y, path + '/' + str(i))]
    # Store large data compactly; raw files remain in frozen copies.
    def summarize(x):
        text = json.dumps(x, ensure_ascii=False)
        return x if len(text) < 2000 else {'length': len(text), 'sha256': sha(text.encode()), 'preview': text[:300]}
    return [{'path': path, 'healthy': summarize(a), 'broken': summarize(b)}]


def inputs():
    values = [archive(BASE / label / 'input.msapp') for label in ('healthy', 'broken')]
    frozen = json.loads((REPORTS / 'inputs.json').read_text(encoding='utf-8'))
    for info in frozen:
        original = Path(info['path'])
        assert original.stat().st_size == info['bytes']
        assert sha(original.read_bytes()) == info['sha256'], 'Original input changed'
        assert sha((BASE / info['label'] / 'input.msapp').read_bytes()) == info['sha256']
    return values


def compatible(healthy, broken):
    h, b = ocr(healthy), ocr(broken)
    ht, bt = h[2]['Template'], b[2]['Template']
    assert {k: v for k, v in ht.items() if k not in FIELDS} == {k: v for k, v in bt.items() if k not in FIELDS}
    assert ht['Version'] == bt['Version'] == '1.0.112'
    assert set(ht[FIELDS[0]]) == set(bt[FIELDS[0]]) == {'Results', 'Selected'}
    assert ht[FIELDS[0]]['Results']['Type']['Kind'] == 'Table'
    assert bt[FIELDS[0]]['Results']['Type'] == {'Name': 'Root', 'Kind': 'Record', 'EnumString': '', 'Type': []}
    assert bt[FIELDS[1]] == {}
    for prop, kind in [('Results', 'array'), ('Selected', 'object')]:
        schema = json.loads(ht[FIELDS[1]][prop]['DynamicSchema'])
        assert schema['type'] == kind
        assert not any(k in ('$ref', '$id', 'ControlUniqueId', 'Parent', 'Id', 'ID')
                       for _, node in walk(schema) if isinstance(node, dict) for k in node)
        assert ht[FIELDS[0]][prop]['Version'] == bt[FIELDS[0]][prop]['Version']
    for f in FIELDS:
        for _, node in walk(ht[f]):
            if isinstance(node, dict):
                assert not set(node).intersection({'ControlUniqueId', 'Parent', 'ControlId', 'ModelId', 'ConnectionId'})
    hp, bp = json.loads(healthy['Properties.json']), json.loads(broken['Properties.json'])
    assert hp['LocalDatabaseReferences'] == bp['LocalDatabaseReferences']
    ai = [next(v for v in json.loads(files['References/DataSources.json'])['DataSources']
               if v.get('EntitySetName') == 'msdyn_aimodels') for files in (healthy, broken)]
    for field in ('Name', 'Type', 'DatasetName', 'EntitySetName', 'LogicalName', 'ApiId', 'WadlMetadata', 'CdsActionInfo'):
        assert ai[0][field] == ai[1][field], f'AI binding mismatch: {field}'
    return h, b


def inspect():
    healthy, broken = inputs()
    h, b = compatible(healthy, broken)
    inventory, diff, matches = [], [], []
    for label, files in [('healthy', healthy), ('broken', broken)]:
        for name, data in files.items():
            inventory.append({'package': label, 'entry': name, 'bytes': len(data), 'sha256': sha(data)})
            try:
                text = data.decode('utf-8-sig')
            except UnicodeError:
                continue
            counts = {}
            for m in PRIORITY.finditer(text):
                counts[m.group()] = counts.get(m.group(), 0) + 1
            if counts:
                matches.append({'package': label, 'entry': name, 'term_counts': counts})
        snapshot = archive(next((BASE / label / 'unpacked').glob('*.msapr')))
        for name, data in snapshot.items():
            inventory.append({'package': label + '-msapr', 'entry': name, 'bytes': len(data), 'sha256': sha(data)})
            if name.startswith('msapp/'):
                assert data == files[name.removeprefix('msapp/')], 'Unpack changed serialized snapshot'
        for p in (BASE / label / 'unpacked').rglob('*'):
            if p.is_file():
                inventory.append({'package': label + '-unpacked', 'entry': str(p.relative_to(BASE / label / 'unpacked')),
                                  'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())})
    for name in sorted(healthy.keys() | broken.keys()):
        if name not in healthy or name not in broken:
            diff.append({'entry': name, 'status': 'healthy-only' if name in healthy else 'broken-only'})
        elif healthy[name] != broken[name]:
            try:
                details = differences(json.loads(healthy[name]), json.loads(broken[name]))
            except ValueError:
                details = [{'healthy_sha256': sha(healthy[name]), 'broken_sha256': sha(broken[name])}]
            diff.append({'entry': name, 'status': 'changed', 'differences': details})
        else:
            diff.append({'entry': name, 'status': 'identical'})
    dump('recursive-comparison.json', diff)
    dump('inventory.json', inventory)
    dump('priority-references.json', matches)
    dump('schema-evidence.json', {
        'healthy': {'entry': h[0], 'path': h[1], 'identity': h[2]['ControlUniqueId'], 'parent': h[2]['Parent'],
                    'metadata': {f: h[2]['Template'][f] for f in FIELDS}},
        'broken': {'entry': b[0], 'path': b[1], 'identity': b[2]['ControlUniqueId'], 'parent': b[2]['Parent'],
                   'metadata': {f: b[2]['Template'][f] for f in FIELDS}},
        'all_other_template_fields_identical': True,
        'definition_sha256': sha(h[2]['Template']['DynamicControlDefinitionJson'].encode()),
        'template_differences': differences(h[2]['Template'], b[2]['Template'])})
    print('FORENSICS: schema mismatch and transplant compatibility verified.')


def command(name, args):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    dump(name, {'command': subprocess.list2cmdline(args), 'exit_code': result.returncode,
                'stdout': result.stdout, 'stderr': result.stderr})
    print(result.stdout)
    assert result.returncode == 0, result.stderr


def repair():
    healthy, broken = inputs()
    h, b = compatible(healthy, broken)
    target = BASE / 'repaired'
    assert not target.exists() and not OUTPUT.exists(), 'Refusing to overwrite existing build'
    shutil.copytree(BASE / 'broken' / 'unpacked', target)
    path = next(target.glob('*.msapr'))
    contents = archive(path)
    entry = 'msapp/' + b[0]
    document = json.loads(contents[entry])
    instance = next(node for _, node in walk(document)
                    if isinstance(node, dict) and node.get('Name') == 'TextRecognizer1' and 'Template' in node)
    for field in FIELDS:
        instance['Template'][field] = copy.deepcopy(h[2]['Template'][field])
    new_data = json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    # Preserve original ZIP member attributes, archive comment, and every other payload.
    before = path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(before)) as source, zipfile.ZipFile(path, 'w') as dest:
        dest.comment = source.comment
        for info in source.infolist():
            dest.writestr(info, new_data if info.filename == entry else source.read(info.filename))
    changes = [{k.replace('healthy', 'before').replace('broken', 'after'): v for k, v in d.items()}
               for d in differences(json.loads(contents[entry]), json.loads(new_data))]
    dump('repair-changes.json', {'entry': entry, 'changed_containers': [b[1] + '/Template/' + f for f in FIELDS],
                                 'leaf_differences': changes})
    command('pack.json', ['pac', 'canvas', 'pack', '--sources', str(target), '--msapp', str(OUTPUT), '--layout', 'SourceCode'])
    command('fixed-unpack.json', ['pac', 'canvas', 'unpack', '--msapp', str(OUTPUT), '--sources', str(BASE / 'roundtrip'), '--layout', 'SourceCode'])
    verify()


def verify():
    healthy, broken = inputs()
    fixed = archive(OUTPUT)
    h, b = compatible(healthy, broken)
    f = ocr(fixed)
    assert f[:2] == b[:2]
    wanted = copy.deepcopy(b[2])
    for field in FIELDS:
        wanted['Template'][field] = h[2]['Template'][field]
    assert f[2] == wanted, 'Unexpected control-instance change'
    assert fixed.keys() == broken.keys(), 'Package members changed'
    changed = [n for n in fixed if fixed[n] != broken[n]]
    assert set(changed) == {b[0], 'packed.json'}, changed
    before_doc, after_doc = json.loads(broken[b[0]]), json.loads(fixed[b[0]])
    node = next(v for _, v in walk(before_doc) if isinstance(v, dict) and v.get('Name') == 'TextRecognizer1' and 'Template' in v)
    for field in FIELDS:
        node['Template'][field] = h[2]['Template'][field]
    assert before_doc == after_doc, 'Other scan controls or formulas changed'
    old_packed, new_packed = json.loads(broken['packed.json']), json.loads(fixed['packed.json'])
    assert {k: v for k, v in old_packed.items() if k != 'LastPackedDateTimeUtc'} == {k: v for k, v in new_packed.items() if k != 'LastPackedDateTimeUtc'}
    repaired = archive(next((BASE / 'repaired').glob('*.msapr')))
    roundtrip = archive(next((BASE / 'roundtrip').glob('*.msapr')))
    assert repaired.keys() == roundtrip.keys()
    assert all(repaired[k] == roundtrip[k] for k in repaired if k != 'msapp/packed.json'), 'Re-unpack changed repaired snapshot'
    assert json.loads(roundtrip['msapp/packed.json']) == new_packed
    assert json.loads(repaired['msapp/packed.json']) == old_packed
    for n, data in repaired.items():
        if n.startswith('msapp/') and n != 'msapp/packed.json':
            assert fixed[n.removeprefix('msapp/')] == data
    scans = []
    for label, files in [('fixed', fixed), ('repaired-msapr', repaired), ('roundtrip-msapr', roundtrip)]:
        count = 0
        for name, data in files.items():
            if not name.endswith(('.json', '.sarif')):
                continue
            for pointer, node in walk(json.loads(data)):
                if isinstance(node, dict) and 'OverridableProperties' in node:
                    overrides = node['OverridableProperties']
                    if 'Results' in overrides:
                        assert overrides['Results']['Type']['Kind'] == 'Table', (name, pointer)
                        assert overrides == h[2]['Template'][FIELDS[0]]
                        assert node[FIELDS[1]] == h[2]['Template'][FIELDS[1]]
                        count += 1
                # Inspect embedded dynamic schema strings too; manifest Object is generic, not a record override.
                if isinstance(node, dict) and 'PCFDynamicSchemaForIRRetrieval' in node and node.get('Name') == 'TextRecognizer':
                    assert json.loads(node[FIELDS[1]]['Results']['DynamicSchema'])['type'] == 'array'
                    assert json.loads(node[FIELDS[1]]['Selected']['DynamicSchema'])['type'] == 'object'
        assert count == 1, (label, count)
        scans.append({'representation': label, 'Results_Table_instances': count, 'Results_Record_instances': 0})
    screens = ['scrHome', 'scrScan', 'scrLoading', 'scrResults', 'scrError']
    for screen in screens:
        n = f'Src/{screen}.pa.yaml'
        assert fixed[n] == broken[n]
    for p in (BASE / 'repaired' / 'Src').rglob('*'):
        if p.is_file():
            assert p.read_bytes() == (BASE / 'roundtrip' / 'Src' / p.relative_to(BASE / 'repaired' / 'Src')).read_bytes()
    acceptance_path = REPORTS / 'runtime-acceptance.json'
    acceptance = json.loads(acceptance_path.read_text(encoding='utf-8')) if acceptance_path.exists() else None
    dump('validation.json', {'package_validation': 'PASS', 'runtime': acceptance['status'] if acceptance else 'REQUIRES POWER APPS STUDIO',
          'runtime_acceptance': acceptance,
          'runtime_reason': 'Computer-use inventory returned apps=[] and browsers=[]; getBrowser for https://make.powerapps.com/ returned No browser is available. No player session was executed.',
          'output': str(OUTPUT), 'bytes': OUTPUT.stat().st_size, 'sha256': sha(OUTPUT.read_bytes()),
          'changed_package_entries': changed, 'schema_scans': scans,
          'unchanged_phase2_screens': screens, 'all_yaml_byte_identical': True,
          'variables_preserved': sorted(set(re.findall(r'\bvar[A-Za-z0-9_]+', '\n'.join(
              data.decode('utf-8') for name, data in fixed.items() if name.endswith('.pa.yaml'))))),
          'all_formulas_and_instance_ids_preserved': True, 'repaired_msapr_equals_reunpacked_msapr_except_pack_timestamp': True,
          'original_input_hashes_unchanged': True,
          'retained_historical_checker_report': 'AppCheckerResult.sarif is unchanged historical analysis, not an executable schema or a fresh validation.'})
    print('PACKAGE VALIDATION: PASS. ' + ('User-reported runtime: ' + acceptance['status'] if acceptance else 'Runtime was not executed.'))


if __name__ == '__main__':
    {'inspect': inspect, 'repair': repair, 'verify': verify}[sys.argv[1]]()
