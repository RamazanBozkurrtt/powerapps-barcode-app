"""Prove v3.1 only restores required leaf child arrays; reproduce v3 load failure."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'validation/mobile-v3-1'
OLD = ROOT / 'Barkod-Uygulamasi-Mobile-Light-v3.msapp'
NEW = ROOT / 'Barkod-Uygulamasi-Mobile-Light-v3-1.msapp'
NAMES = {'lblManualProductName', 'txtProductName', 'btnSearchProduct'}


def read(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(set(z.namelist()))
        return {n: z.read(n) for n in z.namelist()}


def walk(v):
    if isinstance(v, dict):
        yield v
        for x in v.values():
            yield from walk(x)
    elif isinstance(v, list):
        for x in v:
            yield from walk(x)


old, new = read(OLD), read(NEW)
assert set(old) == set(new)
changes = [n for n in old if old[n] != new[n]]
assert set(changes) == {'Controls/15.json', 'packed.json'}, changes
old_pack, new_pack = [json.loads(d['packed.json']) for d in [old, new]]
old_pack.pop('LastPackedDateTimeUtc')
new_pack.pop('LastPackedDateTimeUtc')
assert old_pack == new_pack, 'Only the packing timestamp may change'
expected = copy.deepcopy(json.loads(old['Controls/15.json']))
repaired = []
for c in walk(expected):
    if c.get('Name') in NAMES and 'Rules' in c:
        assert 'Children' not in c
        c['Children'] = []
        repaired.append(c['Name'])
assert set(repaired) == NAMES
assert json.loads(new['Controls/15.json']) == expected


def load(label, path):
    with tempfile.TemporaryDirectory(prefix='v31-audit-', dir=ROOT/'build') as temp:
        command = ['pac', 'canvas', 'unpack', '--msapp', str(path),
                   '--sources', temp, '--layout', 'Experimental']
        p = subprocess.run(command, capture_output=True, encoding='utf8', errors='replace')
        result = dict(command=command, exit=p.returncode, stdout=p.stdout, stderr=p.stderr)
        (REPORT / (label + '-loader.json')).write_text(json.dumps(result, indent=2), encoding='utf8')
        return result


broken = load('broken', OLD)
fixed = load('final', NEW)
assert broken['exit'] != 0 and 'NullReferenceException' in broken['stdout']
assert fixed['exit'] == 0

result = dict(
    repair='PASS', user_session_id='c559ed20-5925-40b6-abcb-3d0b7097cc1f',
    changed_package_entries=changes, restored_empty_children=repaired,
    packed_json_change='LastPackedDateTimeUtc only',
    all_other_package_entries_byte_identical=True,
    all_formulas_layout_theme_ocr_and_connector_data_unchanged=True,
    original_loader='FAIL: NullReferenceException', repaired_loader='PASS',
    sha256=hashlib.sha256(NEW.read_bytes()).hexdigest(), bytes=NEW.stat().st_size,
    studio_runtime='NOT EXECUTED; PAC document load is not a Studio/player session',
)
(REPORT / 'repair.json').write_text(json.dumps(result, indent=2), encoding='utf8')
print('Minimal repair PASS: only three Children arrays restored; old load FAIL, v3.1 load PASS.')
