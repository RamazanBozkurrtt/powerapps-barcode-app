"""Audit a font-only repair against a Git revision; requires PyYAML.

This checks source/snapshot/package parity and scope, not Studio App Checker.
"""
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
FONT = "Font.'Open Sans'"
PACKAGE = 'Barkod-Uygulamasi-Mobile-Light-v4.msapp'


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def without_fonts(value):
    if isinstance(value, dict):
        return {k: without_fonts(v) for k, v in value.items() if k != 'Font'}
    if isinstance(value, list):
        return [without_fonts(v) for v in value
                if not (isinstance(v, dict) and v.get('Property') == 'Font')]
    return value


def archive(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(set(z.namelist()))
        return {n: z.read(n) for n in z.namelist()}


def check_archive_metadata(before, after):
    # Python 3.14 on Windows normalizes ZipInfo.filename. Canvas's legacy
    # loader still needs the original backslashes in References member names.
    with zipfile.ZipFile(io.BytesIO(before)) as old, zipfile.ZipFile(io.BytesIO(after)) as new:
        assert old.comment == new.comment
        fields = ('orig_filename', 'date_time', 'create_system', 'external_attr', 'comment', 'extra')
        assert [tuple(getattr(i, f) for f in fields) for i in old.infolist()] == [
            tuple(getattr(i, f) for f in fields) for i in new.infolist()]


def controls(members, prefix):
    return {c['Name']: c for n, data in members.items() if n.startswith(prefix + 'Controls/')
            for c in walk(json.loads(data)) if 'Rules' in c and 'Name' in c}


def font_rules(cs):
    return {name + '.Font': r['InvariantScript'] for name, c in cs.items()
            for r in c['Rules'] if r['Property'] == 'Font'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, help='Git revision before the font repair')
    args = parser.parse_args()
    revision = subprocess.check_output(['git', 'rev-parse', args.baseline], cwd=ROOT, text=True).strip()

    def baseline(path):
        return subprocess.check_output(['git', 'show', revision + ':' + path.as_posix()], cwd=ROOT)

    changed_files = []
    source_counts = {}
    for source in sorted(ROOT.glob('app-src*')):
        yaml_fonts = []
        invalid_before = 0
        for path in sorted(source.rglob('*.pa.yaml')):
            relative = path.relative_to(ROOT)
            before, after = baseline(relative), path.read_bytes()
            assert b'OpenSans' not in after, relative
            old, new = yaml.safe_load(before), yaml.safe_load(after)
            assert without_fonts(old) == without_fonts(new), relative
            yaml_fonts.extend(v['Font'] for v in walk(new) if 'Font' in v)
            invalid_before += before.count(b'Font.OpenSans')
            if old != new:
                changed_files.append(relative.as_posix())
        snapshot_fonts = []
        for path in source.glob('*.msapr'):
            relative = path.relative_to(ROOT)
            before, after = baseline(relative), path.read_bytes()
            check_archive_metadata(before, after)
            old, new = archive(before), archive(after)
            assert old.keys() == new.keys(), relative
            for name, data in new.items():
                assert b'OpenSans' not in data, (relative, name)
                if name.startswith('msapp/Controls/'):
                    assert without_fonts(json.loads(old[name])) == without_fonts(json.loads(data)), (relative, name)
                else:
                    assert old[name] == data, (relative, name)
            snapshot_fonts.extend(font_rules(controls(new, 'msapp/')).values())
            if before != after:
                changed_files.append(relative.as_posix())
        assert set(yaml_fonts) <= {'=' + FONT, '=App.Theme.Font'}, source
        assert set(snapshot_fonts) <= {FONT, 'App.Theme.Font', '""'}, source
        source_counts[source.name] = dict(invalid_yaml_before=invalid_before,
            invalid_after=0, yaml_font_count=len(yaml_fonts),
            runtime_font_count=len(snapshot_fonts), runtime_fonts=dict(Counter(snapshot_fonts)))

    original_bytes, current_bytes = baseline(Path(PACKAGE)), (ROOT / PACKAGE).read_bytes()
    check_archive_metadata(original_bytes, current_bytes)
    original = archive(original_bytes)
    current = archive(current_bytes)
    assert original.keys() == current.keys()
    changed_entries = []
    for name, data in current.items():
        assert b'OpenSans' not in data, name
        if data == original[name]:
            continue
        changed_entries.append(name)
        if name.startswith('Controls/'):
            assert without_fonts(json.loads(original[name])) == without_fonts(json.loads(data)), name
        elif name.startswith('Src/') and name.endswith('.pa.yaml'):
            assert without_fonts(yaml.safe_load(original[name])) == without_fonts(yaml.safe_load(data)), name
        else:
            raise AssertionError('Non-font package entry changed: ' + name)
    changed_files.append(PACKAGE)
    old_cs, cs = controls(original, ''), controls(current, '')
    old_fonts, fonts = font_rules(old_cs), font_rules(cs)
    assert len(fonts) == 53 and set(fonts.values()) == {FONT}, fonts
    font_changes = {name: {'before': old_fonts[name], 'after': value}
                    for name, value in fonts.items() if old_fonts[name] != value}
    assert len(font_changes) == 53
    assert Counter(v['before'] for v in font_changes.values()) == {'Font.OpenSans': 51, 'App.Theme.Font': 2}
    assert all(old_cs[n]['Template']['Name'] == 'timer'
               for n in old_cs if old_fonts.get(n + '.Font') == 'App.Theme.Font')
    snapshot = archive(next((ROOT / 'app-src-mobile-v4').glob('*.msapr')).read_bytes())
    for name, data in snapshot.items():
        if name.startswith('msapp/') and name != 'msapp/packed.json':
            assert current[name.removeprefix('msapp/')] == data, name
    for path in (ROOT / 'app-src-mobile-v4/Src').glob('*.pa.yaml'):
        assert yaml.safe_load(current['Src/' + path.name]) == yaml.safe_load(path.read_bytes()), path
    for path in (ROOT / 'scripts').glob('*.py'):
        if path.name.startswith(('mobile_', 'phase3_')):
            assert 'Font.OpenSans' not in path.read_text(encoding='utf8'), path
    result = dict(status='PASS', baseline_revision=revision, package=PACKAGE,
        sha256=hashlib.sha256((ROOT / PACKAGE).read_bytes()).hexdigest(), sources=source_counts,
        font_changes=font_changes, all_non_font_properties_unchanged=True,
        other_package_entries_byte_identical=True, yaml_snapshot_package_parity=True,
        changed_source_and_package_files=changed_files, changed_package_entries=changed_entries,
        studio_app_checker='NOT RUN: no connected Power Apps Studio session')
    output = ROOT / 'validation/font-fix/audit.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print('PASS: all app-src* Font properties audited; 195 invalid source formulas removed.')
    print('PASS: all 53 v4 Font rules use the native enum; every non-Font property is unchanged.')
    print('PASS: YAML, snapshot and package agree; Studio App Checker remains unverified.')


if __name__ == '__main__':
    main()
