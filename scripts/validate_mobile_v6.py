"""Validate the v6 flexible-height gallery and unchanged application behavior."""
import json
from pathlib import Path
import subprocess

from build_mobile_v6 import BASE, CARD_HEIGHT, OUT as PACKAGE, REPORT, ROOT, SPACER_Y, archive, walk


def load(path):
    members = archive(path)
    controls = {
        control["Name"]: control
        for name, data in members.items()
        if name.startswith("Controls/")
        for control in walk(json.loads(data))
        if "Name" in control and "Rules" in control
    }
    return members, controls


base_members, base = load(BASE)
members, controls = load(PACKAGE)
properties = {
    name: {rule["Property"]: rule["InvariantScript"] for rule in control["Rules"]}
    for name, control in controls.items()
}
get = lambda name, prop: properties[name][prop]

assert set(controls) == set(base) | {"shpProductTemplateBottom"}
for name, before in base.items():
    after_without_children = dict(controls[name], Children=[])
    before_without_children = dict(before, Children=[])
    assert after_without_children == before_without_children, name
    before_children = [child["Name"] for child in before["Children"]]
    after_children = [child["Name"] for child in controls[name]["Children"]]
    if name == "galProducts":
        assert after_children == before_children + ["shpProductTemplateBottom"]
    else:
        assert after_children == before_children, name

assert controls["galProducts"]["VariantName"] == "galleryVariableTemplateHeight"
assert get("galProducts", "Items") == "colProductGroups"
assert get("galProducts", "TemplateSize") == "76"
assert get("galProducts", "AutoHeight") == "true"
assert get("btnProductCard", "Height") == CARD_HEIGHT
assert get("galWarehouses", "Items") == "ThisItem.WarehouseRows"
assert get("galWarehouses", "TemplateSize") == "52"
base_warehouse_height = next(
    rule["InvariantScript"]
    for rule in base["galWarehouses"]["Rules"]
    if rule["Property"] == "Height"
)
assert get("galWarehouses", "Height") == base_warehouse_height
assert get("galWarehouses", "Visible") == next(
    rule["InvariantScript"]
    for rule in base["galWarehouses"]["Rules"]
    if rule["Property"] == "Visible"
)
assert get("shpProductTemplateBottom", "Y") == SPACER_Y
assert get("shpProductTemplateBottom", "Height") == "1"
assert get("shpProductTemplateBottom", "Fill") == "RGBA(0, 0, 0, 0)"

behavior = 0
for name, control in base.items():
    before_rules = {rule["Property"]: rule["InvariantScript"] for rule in control["Rules"]}
    for prop, formula in before_rules.items():
        if prop.startswith("On"):
            assert get(name, prop) == formula, (name, prop)
            behavior += 1
for name in ["App", "tmrLoadingFlow", "tmrLoadingVisual", "galWarehouses"]:
    assert controls[name] == base[name]

for name in ["Header.json", "References/DataSources.json", "References/Resources.json", "References/Themes.json"]:
    assert members[name] == base_members[name], name

package_properties = json.loads(members["Properties.json"])
settings = {
    name: package_properties[name]
    for name in [
        "DocumentLayoutWidth",
        "DocumentLayoutHeight",
        "DocumentLayoutOrientation",
        "DocumentLayoutScaleToFit",
        "DocumentLayoutMaintainAspectRatio",
        "DocumentLayoutLockOrientation",
        "DocumentAppType",
    ]
}
assert settings == {
    "DocumentLayoutWidth": 390,
    "DocumentLayoutHeight": 844,
    "DocumentLayoutOrientation": "portrait",
    "DocumentLayoutScaleToFit": False,
    "DocumentLayoutMaintainAspectRatio": False,
    "DocumentLayoutLockOrientation": False,
    "DocumentAppType": "Phone",
}

for screen in ["scrHome", "scrScan", "scrLoading", "scrResults", "scrError"]:
    assert get(screen, "Width") == "App.Width"
    assert get(screen, "Height") == "App.Height"
for container in ["conHome", "conSearch", "conLoading", "conResults", "conError"]:
    assert get(container, "Height") == "Parent.Height"
    assert "Parent.Width" in get(container, "Width")

rules = []
invalid_fonts = []
for name, control in controls.items():
    for prop, formula in properties[name].items():
        if "OpenSans" in formula or "Font.OpenSans" in formula:
            invalid_fonts.append((name, prop, formula))
        if prop == "Font":
            assert formula == "Font.'Open Sans'", name
        if formula:
            rules.append({"name": name + "." + prop, "formula": formula})
assert not invalid_fonts

source_text = (ROOT / "app-src-mobile-v6/Src/scrResults.pa.yaml").read_text(encoding="utf8")
assert "Variant: VariableHeight" in source_text
assert "shpProductTemplateBottom:" in source_text
assert "OpenSans" not in source_text
assert "Items: =colProductGroups" in source_text
assert "Items: =ThisItem.WarehouseRows" in source_text
for prop in ["X", "Y", "Width", "Height", "Fill", "Visible", "OnSelect", "ZIndex"]:
    expected_line = f"                  {prop}: =" + get("shpProductTemplateBottom", prop)
    assert expected_line in source_text, (prop, expected_line)

previous = json.loads((ROOT / "validation/mobile-v5/fx-input.json").read_text(encoding="utf8"))
tests = list(previous["tests"])


def test(name, formula, expected):
    tests.append({"name": name, "formula": formula, "expected": str(expected)})


for expanded, item_number, expected in [
    (False, "SKU", 76),
    (True, "OTHER", 76),
    (True, "SKU", 320),
]:
    bindings = (
        f"varProductExpanded:{str(expanded).lower()},"
        f'varExpandedItemNumber:"{item_number}",'
        'ThisItem:{ItemNumber:"SKU"},'
        "galWarehouses:{Y:100,Height:208},btnProductToggle:{Y:0,Height:76}"
    )
    test(
        f"product_template_bottom_{expanded}_{item_number}",
        "With({" + bindings + "},Text(" + SPACER_Y + " + 1))",
        expected,
    )

(REPORT / "fx-input.json").write_text(
    json.dumps({"rules": rules, "tests": tests}, ensure_ascii=False),
    encoding="utf8",
)

checker = ROOT / "build/font-tools/check/bin/Debug/net10.0/check.dll"
dotnet = ROOT / "build/font-tools/dotnet/dotnet.exe"
powerfx = subprocess.run(
    [str(dotnet), str(checker), str(REPORT / "fx-input.json")],
    cwd=ROOT,
    capture_output=True,
    text=True,
    encoding="utf8",
    errors="replace",
)
(REPORT / "powerfx-results.txt").write_text(
    powerfx.stdout + powerfx.stderr, encoding="utf8"
)
assert powerfx.returncode == 0, powerfx.stdout + powerfx.stderr
assert f"Parsed {len(rules)} runtime formulas; failures=0" in powerfx.stdout

embedded_sarif = json.loads(members["AppCheckerResult.sarif"])
embedded_formula_findings = [
    result
    for run in embedded_sarif.get("runs", [])
    for result in run.get("results", [])
    if str(result.get("ruleId", "")).startswith("app-Err")
]
summary = {
    "status": "PASS",
    "formula_count_prepared": len(rules),
    "executable_checks_prepared": len(tests),
    "local_powerfx_parse_failures": 0,
    "local_powerfx_executable_checks": "PASS",
    "existing_behavior_formulas_unchanged": behavior,
    "galProducts_variable_height_runtime": True,
    "template_bottom_spacer_runtime_and_yaml": True,
    "galWarehouses_unchanged": True,
    "responsive_manifest": settings,
    "root_screen_and_container_formulas": "PASS",
    "invalid_font_identifiers": 0,
    "embedded_historical_app_checker_formula_findings": len(embedded_formula_findings),
    "embedded_app_checker_preserved_from_v5": members["AppCheckerResult.sarif"]
    == base_members["AppCheckerResult.sarif"],
    "studio_app_checker": "NOT RUN",
    "physical_phone": "NOT TESTED",
}
(REPORT / "static-checks.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
)
print(
    f"PASS: {len(rules)} formulas prepared; {behavior} existing behavior formulas unchanged; "
    "flexible gallery and responsive manifest verified."
)
