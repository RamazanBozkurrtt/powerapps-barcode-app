"""Build the flexible-product-gallery revision without changing application logic."""
import copy
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "versions/Barkod-Uygulamasi-Mobile-Light-v5.msapp"
BASE_SOURCE = ROOT / "app-src-mobile-v5"
SOURCE = ROOT / "app-src-mobile-v6"
OUT = ROOT / "versions/Barkod-Uygulamasi-Mobile-Light-v6.msapp"
REPORT = ROOT / "validation/mobile-v6"
TOOLS = ROOT / "build/font-tools"
SNAPSHOT_NAME = "Barkod-Uygulamasi-Phase2-FIXED-v2.msapr"

EXPANDED = "varProductExpanded && varExpandedItemNumber = ThisItem.ItemNumber"
CARD_HEIGHT = (
    f"If({EXPANDED}, galWarehouses.Y + galWarehouses.Height + 12, "
    "btnProductToggle.Height)"
)
SPACER_Y = (
    f"If({EXPANDED}, galWarehouses.Y + galWarehouses.Height + 11, "
    "btnProductToggle.Y + btnProductToggle.Height - 1)"
)


def archive(path):
    with zipfile.ZipFile(path) as package:
        assert package.testzip() is None
        return {
            item.filename.replace("\\", "/"): package.read(item)
            for item in package.infolist()
        }


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def pac(args, report_name):
    executable = shutil.which("pac")
    environment = os.environ.copy()
    if executable:
        command = [executable]
    else:
        environment["DOTNET_ROOT"] = str(TOOLS / "dotnet")
        environment["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1"
        command = [
            str(TOOLS / "dotnet/dotnet.exe"),
            str(TOOLS / "pac-portable/pac.dll"),
        ]
    process = subprocess.run(
        command + args,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf8",
        errors="replace",
    )
    (REPORT / report_name).write_text(
        json.dumps(
            {
                "command": ["pac"] + args,
                "exit": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf8",
    )
    assert process.returncode == 0, process.stdout + process.stderr


def main():
    assert BASE.is_file(), BASE
    assert (BASE_SOURCE / "Src/scrResults.pa.yaml").is_file(), BASE_SOURCE
    REPORT.mkdir(parents=True, exist_ok=True)
    SOURCE.mkdir(parents=True, exist_ok=True)
    shutil.copytree(BASE_SOURCE / "Src", SOURCE / "Src", dirs_exist_ok=True)

    base_hash = hashlib.sha256(BASE.read_bytes()).hexdigest()
    original = archive(BASE)
    documents = {
        name: json.loads(data)
        for name, data in original.items()
        if name.startswith("Controls/")
    }
    controls = {
        control["Name"]: control
        for document in documents.values()
        for control in walk(document)
        if "Name" in control and "Rules" in control
    }
    baseline = copy.deepcopy(controls)

    def get(name, prop):
        return next(
            rule["InvariantScript"]
            for rule in controls[name]["Rules"]
            if rule["Property"] == prop
        )

    def set_existing(name, **properties):
        control = controls[name]
        for prop, value in properties.items():
            rule = next(
                (item for item in control["Rules"] if item["Property"] == prop),
                None,
            )
            assert rule is not None, (name, prop)
            rule["InvariantScript"] = str(value)

    # Runtime schema names are taken from the already Studio-generated v5 package.
    # Explicitly asserting and assigning them makes the source build independent of
    # an inherited/default Vertical gallery variant.
    gal_products = controls["galProducts"]
    assert gal_products["Template"]["Name"] == "gallery"
    assert gal_products["Template"]["Version"] == "2.15.0"
    gal_products["VariantName"] = "galleryVariableTemplateHeight"
    set_existing("galProducts", AutoHeight="true", TemplateSize="76")
    set_existing("btnProductCard", Height=CARD_HEIGHT)

    assert "shpProductTemplateBottom" not in controls
    spacer = copy.deepcopy(controls["shpWarehouseDivider"])
    next_uid = max(int(control["ControlUniqueId"]) for control in controls.values()) + 1
    spacer.update(
        Name="shpProductTemplateBottom",
        Parent="galProducts",
        ControlUniqueId=str(next_uid),
        PublishOrderIndex=next_uid,
        Children=[],
        VariantName="",
    )
    controls[spacer["Name"]] = spacer
    gal_products["Children"].append(spacer)
    set_existing(
        spacer["Name"],
        AccessibleLabel='""',
        Tooltip='""',
        X="0",
        Y=SPACER_Y,
        Width="1",
        Height="1",
        Fill="RGBA(0, 0, 0, 0)",
        DisabledFill="RGBA(0, 0, 0, 0)",
        PressedFill="RGBA(0, 0, 0, 0)",
        HoverFill="RGBA(0, 0, 0, 0)",
        BorderThickness="0",
        Visible="true",
        DisplayMode="DisplayMode.View",
        TabIndex="-1",
        OnSelect="false",
        ZIndex="10",
    )

    # No existing behavior, data binding, navigation, timer, App, or child-gallery
    # formula is allowed to change in this revision.
    protected = {
        "Items",
        "Default",
        "DisplayMode",
        "Start",
        "Reset",
        "AutoStart",
        "AutoPause",
        "Repeat",
        "Duration",
        "StartScreen",
        "OnStart",
        "OnVisible",
        "OnHidden",
    }
    behavior_count = 0
    for name, before in baseline.items():
        assert name in controls
        assert controls[name]["Template"] == before["Template"], name
        for rule in before["Rules"]:
            prop = rule["Property"]
            if prop.startswith("On") or prop in protected:
                assert get(name, prop) == rule["InvariantScript"], (name, prop)
            if prop.startswith("On"):
                behavior_count += 1
    for name in ["App", "tmrLoadingFlow", "tmrLoadingVisual", "galWarehouses"]:
        assert controls[name] == baseline[name], name
    assert get("galProducts", "Items") == "colProductGroups"
    assert get("galWarehouses", "Items") == "ThisItem.WarehouseRows"
    assert get("galWarehouses", "TemplateSize") == "52"
    assert get("galWarehouses", "Height") == baseline["galWarehouses"]["Rules"][
        next(
            index
            for index, rule in enumerate(baseline["galWarehouses"]["Rules"])
            if rule["Property"] == "Height"
        )
    ]["InvariantScript"]
    assert len({control["ControlUniqueId"] for control in controls.values()}) == len(
        controls
    )

    updated = dict(original)
    for name, document in documents.items():
        updated[name] = json.dumps(
            document, ensure_ascii=False, separators=(",", ":")
        ).encode("utf8")

    properties = json.loads(original["Properties.json"])
    properties["ControlCount"] = dict(
        Counter(
            control["Template"]["Name"]
            for control in controls.values()
            if control["Template"]["Name"] not in ["appinfo", "hostControl"]
        )
    )
    updated["Properties.json"] = json.dumps(
        properties, ensure_ascii=False, separators=(",", ":")
    ).encode("utf8")

    # Keep the readable YAML source in parity with the runtime snapshot. The
    # variable-height spelling and Rectangle schema come from the v5 Studio source.
    yaml_path = SOURCE / "Src/scrResults.pa.yaml"
    yaml_text = yaml_path.read_text(encoding="utf8")
    assert yaml_text.count("            Variant: VariableHeight") == 1
    assert "shpProductTemplateBottom:" not in yaml_text
    spacer_properties = {
        rule["Property"]: "=" + rule["InvariantScript"]
        for rule in spacer["Rules"]
        if rule["InvariantScript"]
    }
    snippet_lines = [
        "            - shpProductTemplateBottom:",
        "                Control: Rectangle@2.3.0",
        "                Properties:",
    ]
    snippet_lines.extend(
        f"                  {prop}: {formula}"
        for prop, formula in spacer_properties.items()
    )
    snippet = "\n".join(snippet_lines) + "\n"
    marker = "        - lblResultsEmptyTitle:"
    assert yaml_text.count(marker) == 1
    yaml_text = yaml_text.replace(marker, snippet + marker)
    yaml_path.write_text(yaml_text, encoding="utf8", newline="")
    updated["Src/scrResults.pa.yaml"] = yaml_path.read_bytes()

    snapshot_base = BASE_SOURCE / SNAPSHOT_NAME
    snapshot = archive(snapshot_base)
    for name, data in updated.items():
        embedded_name = "msapp/" + name
        if embedded_name in snapshot:
            snapshot[embedded_name] = data
    snapshot_out = SOURCE / SNAPSHOT_NAME
    with zipfile.ZipFile(snapshot_out, "w", zipfile.ZIP_DEFLATED) as package:
        for name, data in snapshot.items():
            package.writestr(name, data)

    assert OUT.resolve() != BASE.resolve()
    pac(
        [
            "canvas",
            "pack",
            "--sources",
            str(SOURCE),
            "--msapp",
            str(OUT),
            "--layout",
            "SourceCode",
            "--disable-load-from-yaml",
            "--overwrite",
        ],
        "pack.json",
    )
    actual = archive(OUT)
    for name, data in updated.items():
        if name != "packed.json":
            assert actual[name] == data, name
    assert json.loads(actual["packed.json"])["LoadConfiguration"]["LoadFromYaml"] is False

    with tempfile.TemporaryDirectory(prefix="v6-roundtrip-", dir=TOOLS) as temp:
        pac(
            [
                "canvas",
                "unpack",
                "--msapp",
                str(OUT),
                "--sources",
                temp,
                "--layout",
                "SourceCode",
            ],
            "roundtrip.json",
        )
        roundtrip = archive(next(Path(temp).glob("*.msapr")))
        assert all(
            actual[name.removeprefix("msapp/")] == data
            for name, data in roundtrip.items()
            if name.startswith("msapp/")
        )
    with tempfile.TemporaryDirectory(prefix="v6-loader-", dir=TOOLS) as temp:
        pac(
            [
                "canvas",
                "unpack",
                "--msapp",
                str(OUT),
                "--sources",
                temp,
                "--layout",
                "Experimental",
            ],
            "document-load.json",
        )

    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == base_hash
    package_hash = hashlib.sha256(OUT.read_bytes()).hexdigest()
    (REPORT / "build.json").write_text(
        json.dumps(
            {
                "status": "PASS",
                "base_package": str(BASE.relative_to(ROOT)),
                "base_sha256_before_and_after": base_hash,
                "base_package_preserved": True,
                "package": str(OUT.relative_to(ROOT)),
                "sha256": package_hash,
                "behavior_formulas_unchanged": behavior_count,
                "app_timers_and_nested_gallery_unchanged": True,
                "added_control": spacer["Name"],
                "galProducts_variant": gal_products["VariantName"],
                "studio_app_checker": "NOT RUN",
                "physical_phone": "NOT TESTED",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf8",
    )
    print(f"PASS: built {OUT.name}; v5 preserved at {BASE}")


if __name__ == "__main__":
    main()
