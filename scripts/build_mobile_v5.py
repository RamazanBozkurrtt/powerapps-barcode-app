"""Build the composition revision from the accepted, font-fixed v4 package."""
import copy
from collections import Counter
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile
import yaml

from mobile_v5_composition import apply_composition

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'Barkod-Uygulamasi-Mobile-Light-v4.msapp'
SOURCE = ROOT / 'app-src-mobile-v5'
OUT = ROOT / 'Barkod-Uygulamasi-Mobile-Light-v5.msapp'
REPORT = ROOT / 'validation/mobile-v5'
TOOLS = ROOT / 'build/font-tools'


def archive(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        return {i.filename.replace('\\', '/'): z.read(i) for i in z.infolist()}


def walk(v):
    if isinstance(v, dict):
        yield v
        for x in v.values():
            yield from walk(x)
    elif isinstance(v, list):
        for x in v:
            yield from walk(x)


def pac(args, name):
    executable = shutil.which('pac')
    env = os.environ.copy()
    if executable:
        command = [executable]
    else:
        env['DOTNET_ROOT'] = str(TOOLS / 'dotnet')
        env['DOTNET_CLI_TELEMETRY_OPTOUT'] = '1'
        command = [str(TOOLS / 'dotnet/dotnet.exe'), str(TOOLS / 'pac-portable/pac.dll')]
    p = subprocess.run(command + args, cwd=ROOT, env=env, capture_output=True, text=True,
                       encoding='utf8', errors='replace')
    (REPORT / name).write_text(json.dumps(dict(command=['pac'] + args, exit=p.returncode,
        stdout=p.stdout, stderr=p.stderr), ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    assert p.returncode == 0, p.stdout + p.stderr


def main():
    REPORT.mkdir(parents=True, exist_ok=True)
    original = archive(BASE)
    docs = {n: json.loads(b) for n, b in original.items() if n.startswith('Controls/')}
    cs = {c['Name']: c for d in docs.values() for c in walk(d) if 'Name' in c and 'Rules' in c}
    baseline = copy.deepcopy(cs)
    changed = {}

    def get(n, p):
        return next(r['InvariantScript'] for r in cs[n]['Rules'] if r['Property'] == p)

    def setp(n, **props):
        c = cs[n]
        for p, value in props.items():
            rule = next((r for r in c['Rules'] if r['Property'] == p), None)
            if rule is None:
                rule = dict(Property=p, Category='Behavior' if p.startswith('On') else 'Design', RuleProviderType='Unknown')
                c['Rules'].append(rule)
                c['ControlPropertyState'].append(p)
            rule['InvariantScript'] = str(value)
            changed.setdefault(n, set()).add(p)

    apply_composition(cs, setp, get, changed)
    # Enforce UI-only scope before writing any artifact.
    protected = {'Items', 'Default', 'DisplayMode', 'Start', 'Reset', 'AutoStart', 'AutoPause',
                 'Repeat', 'Duration', 'StartScreen', 'OnStart', 'OnVisible', 'OnHidden'}
    behavior_count = 0
    for name, c in baseline.items():
        assert name in cs
        assert cs[name]['Template'] == c['Template'], name
        for rule in c['Rules']:
            p = rule['Property']
            if p.startswith('On') or p in protected:
                assert get(name, p) == rule['InvariantScript'], (name, p)
            if p.startswith('On'):
                behavior_count += 1
    assert cs['App'] == baseline['App']
    for n in ['tmrLoadingFlow', 'tmrLoadingVisual']:
        assert cs[n] == baseline[n], n
    assert len({c['ControlUniqueId'] for c in cs.values()}) == len(cs)
    assert all(isinstance(c['Children'], list) for c in cs.values())

    updated = dict(original)
    for n, doc in docs.items():
        updated[n] = json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode('utf8')
    templates = json.loads(original['References/Templates.json'])
    templates['UsedTemplates'].append(dict(Name='image', Version='2.2.0',
        Template=(ROOT / 'scripts/image_2.2.0.xml').read_text(encoding='utf8')))
    updated['References/Templates.json'] = json.dumps(templates, ensure_ascii=False, separators=(',', ':')).encode('utf8')
    properties = json.loads(original['Properties.json'])
    properties['ControlCount'] = dict(Counter(c['Template']['Name'] for c in cs.values()
        if c['Template']['Name'] not in ['appinfo', 'hostControl']))
    updated['Properties.json'] = json.dumps(properties, ensure_ascii=False, separators=(',', ':')).encode('utf8')

    class Dumper(yaml.SafeDumper):
        pass
    Dumper.add_representer(str, lambda d, s: d.represent_scalar('tag:yaml.org,2002:str', s, style='|' if '\n' in s else None))
    originals = {}
    for name, data in original.items():
        if name.endswith('.pa.yaml'):
            for v in walk(yaml.safe_load(data)):
                for key, value in v.items():
                    if key in cs and isinstance(value, dict) and 'Properties' in value:
                        originals[key] = value

    def render(c):
        name = c['Name']
        node = copy.deepcopy(originals.get(name, {}))
        node.pop('Children', None)
        rules = {r['Property']: r['InvariantScript'] for r in c['Rules']}
        keys = set(node.get('Properties', {})) | changed.get(name, set())
        kind = c['Template']['Name']
        if name not in originals:
            node['Control'] = {'label': 'Label@2.5.1', 'image': 'Image@2.2.0',
                'rectangle': 'Rectangle@2.3.0', 'groupContainer': 'GroupContainer@1.3.0'}[kind]
        if kind == 'groupContainer':
            node['Variant'] = 'AutoLayout'
        node['Properties'] = {p: '=' + rules[p] for p in sorted(keys) if p in rules and rules[p]}
        children = [x for x in c['Children'] if x['Template']['Name'] != 'galleryTemplate']
        if children and kind != 'appinfo':
            node['Children'] = [{x['Name']: render(x)} for x in children]
        return node

    for name, data in original.items():
        if name.endswith('.pa.yaml') and not name.endswith('_EditorState.pa.yaml'):
            doc = yaml.safe_load(data)
            if 'Screens' in doc:
                doc = {'Screens': {n: render(cs[n]) for n in doc['Screens']}}
            elif 'App' in doc:
                # No App logic or source changes in this layout revision.
                continue
            updated[name] = yaml.dump(doc, Dumper=Dumper, allow_unicode=True, sort_keys=False, width=110).encode('utf8')

    SOURCE.mkdir(parents=True, exist_ok=True)
    snapshot_base = next((ROOT / 'app-src-mobile-v4').glob('*.msapr'))
    payload = archive(snapshot_base)
    for n, data in updated.items():
        if 'msapp/' + n in payload:
            payload['msapp/' + n] = data
    with zipfile.ZipFile(SOURCE / snapshot_base.name, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, data in payload.items():
            z.writestr(n, data)
    for n, data in updated.items():
        if n.startswith('Src/'):
            path = SOURCE / n
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    pac(['canvas', 'pack', '--sources', str(SOURCE), '--msapp', str(OUT), '--layout',
         'SourceCode', '--disable-load-from-yaml', '--overwrite'], 'pack.json')
    actual = archive(OUT)
    for n, data in updated.items():
        if n != 'packed.json':
            assert actual[n] == data, n
    assert json.loads(actual['packed.json'])['LoadConfiguration']['LoadFromYaml'] is False
    with tempfile.TemporaryDirectory(prefix='v5-roundtrip-', dir=TOOLS) as temp:
        pac(['canvas', 'unpack', '--msapp', str(OUT), '--sources', temp, '--layout', 'SourceCode'], 'roundtrip.json')
        snapshot = archive(next(Path(temp).glob('*.msapr')))
        assert all(actual[n.removeprefix('msapp/')] == b for n, b in snapshot.items() if n.startswith('msapp/'))
    with tempfile.TemporaryDirectory(prefix='v5-loader-', dir=TOOLS) as temp:
        pac(['canvas', 'unpack', '--msapp', str(OUT), '--sources', temp, '--layout', 'Experimental'], 'document-load.json')
    report = dict(package='PASS', baseline_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),
        sha256=hashlib.sha256(OUT.read_bytes()).hexdigest(), behavior_formulas_unchanged=behavior_count,
        app_and_timers_unchanged=True, control_count=len(cs),
        changed_controls={n: sorted(v) for n, v in changed.items()},
        studio_app_checker='NOT RUN', physical_phone='NOT TESTED')
    (REPORT / 'build.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print('PASS: v5 pack, roundtrip, Microsoft document loader; existing business behavior unchanged.')


if __name__ == '__main__':
    main()
