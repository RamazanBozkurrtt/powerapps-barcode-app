TextRecognizer forensic repair

**SUPERSEDING RUNTIME RESULT — FAIL (user-reported).** The delivered repair still produces the same JSON error during navigation. The earlier package PASS below means only that the requested metadata transplant survived local serialization. It is not a successful application repair. The former exact-runtime-root-cause conclusion is withdrawn: classification **F — unknown; more evidence required**, with a proven historical schema discrepancy. The original report is retained below as the record of that attempted repair.

The supplied Monitor session reports errors at 15:23:22.113, 15:23:28.083, 15:23:33.190, and 15:23:36.396; getRows and invokeAction succeeded between them. Error controlName, propertyName, nodeId, functionName, and context are null and formula script is empty. This does not identify Results, Selected, a specific connector, or an application formula as the failing boundary. Successful network operations do not prove that output conversion succeeded.

The local delivered artifact was re-inspected and still has Results Table/array and populated Selected fields, with SHA-256 `13be94e0e451bcb6232d9f3fb42299df8534a91e74ca6f05a403171ef62195a9`. It also retains LoadFromYaml=true and the previously documented source/snapshot formula discrepancy. No package exported AFTER the failing Studio load is available. Therefore whether Studio replaced or disregarded the transplanted schema is untested. Merely disabling YAML loading could activate the stale snapshot OnChange formula (automatic navigation and flow call); it is not a justified production fix.

Required next evidence: save a separate copy of the failing Studio app, download its current `.msapp`, and export the complete Monitor session with the getRows/invokeAction details. Compare that actual post-load package against the delivered local artifact before another repair. No original file or runtime formula was changed in response to this failure. Runtime evidence is recorded in [runtime-acceptance.json](../forensics/textrecognizer-repair/reports/runtime-acceptance.json).

The fixed artifact is `C:\Users\ramaz\source\repos\powerapps-barcode-app\Barkod-Uygulamasi-Phase2-FIXED.msapp`. Package validation passed after independent PAC re-unpack. Runtime Home → Scan requires Power Apps Studio; no runtime PASS is claimed.

1. Input hashes

Both original inputs were hashed before modification, copied to independent directories, and checked again after repair. Neither original was modified.

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| `Barkod Uygulaması V2.msapp` — healthy ground truth supplied by user | 111022 | `25ecb30774cde9350a8384f676e1f63a5d4cc74c1bcb83f70ab3f55fc5cfdc97` |
| `Barkod-Uygulamasi-Phase2.msapp` — broken | 247950 | `5e6a2af3c7e6d5f1e962e966a56e975ee23e84ba904dd3fedc1dc9dac3fd5bea` |
| `Barkod-Uygulamasi-Phase2-FIXED.msapp` — repaired output | 247142 | `13be94e0e451bcb6232d9f3fb42299df8534a91e74ca6f05a403171ef62195a9` |

Inputs are frozen under `forensics/textrecognizer-repair/healthy/input.msapp` and `broken/input.msapp`. Separate `unpacked/`, `repaired/`, and `roundtrip/` directories hold each stage. The working `app-src` tree and earlier diagnostic experiments were not used as repair inputs.

2. Tool versions and commands

Power Platform CLI: **2.11.2+g47bc199**, running on **.NET 10.0.10**. Python standard-library `zipfile`, `json`, and `hashlib` perform inspection, the targeted transplant, and verification. The exact Python version and complete CLI help output are recorded in [tool-version.txt](../forensics/textrecognizer-repair/reports/tool-version.txt).

Commands below ran from the repository root. Each command has a JSON log containing the exact command line, exit code, stdout, and stderr.

```powershell
pac canvas unpack --msapp forensics/textrecognizer-repair/healthy/input.msapp --sources forensics/textrecognizer-repair/healthy/unpacked --layout SourceCode
pac canvas unpack --msapp forensics/textrecognizer-repair/broken/input.msapp --sources forensics/textrecognizer-repair/broken/unpacked --layout SourceCode
python forensics/textrecognizer-repair/repair.py inspect
python forensics/textrecognizer-repair/repair.py repair
```

The repair script invoked these final commands with absolute paths:

```powershell
pac canvas pack --sources C:\Users\ramaz\source\repos\powerapps-barcode-app\forensics\textrecognizer-repair\repaired --msapp C:\Users\ramaz\source\repos\powerapps-barcode-app\Barkod-Uygulamasi-Phase2-FIXED.msapp --layout SourceCode
pac canvas unpack --msapp C:\Users\ramaz\source\repos\powerapps-barcode-app\Barkod-Uygulamasi-Phase2-FIXED.msapp --sources C:\Users\ramaz\source\repos\powerapps-barcode-app\forensics\textrecognizer-repair\roundtrip --layout SourceCode
```

All four PAC operations exited 0. PAC explicitly states that a SourceCode-packed app needs Studio validation. Logs: [healthy unpack](../forensics/textrecognizer-repair/reports/healthy-unpack.json), [broken unpack](../forensics/textrecognizer-repair/reports/broken-unpack.json), [pack](../forensics/textrecognizer-repair/reports/pack.json), [fixed unpack](../forensics/textrecognizer-repair/reports/fixed-unpack.json).

3. Exact root cause

**C — generated control schema corruption**, retained by the local packing workflow. The broken TextRecognizer instance has `Template.OverridableProperties.Results.Type.Kind = Record` and an empty field list, although the healthy instance of the exact same control version defines a Table/array of OCR lines. The broken instance also has an empty `PCFDynamicSchemaForIRRetrieval` map. Selected retains its Record kind but loses its fields and dynamic schema.

The incorrect expectation is physically stored in broken `Controls/15.json`, at `$/TopParent/Children/6/Template/OverridableProperties/Results/Type/Kind`. PAC unpack retains the same bytes in `input.msapr!msapp/Controls/15.json`. Thus the corruption is not inferred from a formula or from the error wording alone.

This establishes the package's object-versus-array contract defect. It explains an array being rejected at the Results output boundary; the user reports the runtime failure occurs during control initialization before image selection. This environment did not capture that initialization payload or execute the player. Which historical edit/save operation originally discarded the schemas is not recorded in these two packages and is not claimed as proven.

4. Healthy versus broken evidence

Healthy control path H = `Controls/4.json → $/TopParent/Children/0/Template`.
Broken control path B = `Controls/15.json → $/TopParent/Children/6/Template`.
Each has the same corresponding location inside its independently unpacked `.msapr`, prefixed by `msapp/`.

| Artifact/file | Field/path | Healthy value | Broken value | Runtime relevance | Repair decision |
| --- | --- | --- | --- | --- | --- |
| H / B | `OverridableProperties.Results.Type.Kind` | `Table` | `Record` | Wrong top-level output contract | Copy healthy value |
| H / B | `OverridableProperties.Results.Type.Type` | BoundingBox, PageNumber, Text fields | `[]` | OCR line fields absent | Copy healthy field tree |
| H / B | `OverridableProperties.Selected.Type.Kind` | `Record` | `Record` | Single selected line | Preserve Record |
| H / B | `OverridableProperties.Selected.Type.Type` | BoundingBox, PageNumber, Text fields | `[]` | Selected line fields absent | Copy healthy field tree |
| H / B | `PCFDynamicSchemaForIRRetrieval.Results` | JSON schema `type: array`, object items; `PCFSkipValidation: false` | Missing | Dynamic Results schema lost | Copy complete healthy entry |
| H / B | `PCFDynamicSchemaForIRRetrieval.Selected` | JSON schema `type: object`; `PCFSkipValidation: false` | Missing | Dynamic Selected schema lost | Copy complete healthy entry |
| H / B | `Id`, `Name`, `Version` | TextRecognizer / `1.0.112` | Identical | Same implementation and contract | Preserve Phase2 |
| H / B | `DynamicControlDefinitionJson` | SHA-256 `c4cd6080dfca98ee5287d5bdff1398be0e9bdcf1a0d88f0186950f8b7bb3f27c` | Identical bytes | Same output definitions and LoadSchema dependencies | Preserve Phase2 |
| Parent control object | `ControlUniqueId`, `Parent` | `5`, `Screen1` | `21`, `scrScan` | Instance ownership and navigation identity | Preserve `21`, `scrScan` |
| `References/DataSources.json` | AI model source identity and WADL | Hidden `43b0dc67-68af-47ae-9a9c-9e69d396ba3e`, `default.cds`, `msdyn_aimodels`, Predict contract | Identical relevant binding fields/WADL | Same AI service contract | Preserve all Phase2 references |
| `Properties.json` | `LocalDatabaseReferences` | Configured Dataverse mapping | Byte-identical string | Same database binding | Preserve |
| Broken `AppCheckerResult.sarif` | `.Results` diagnostic | Healthy schema is Table | Saved `expected Table / provided Record` error | Independent historical corroboration | Retain historical report; do not mislabel it as a current check |
| `Src/scrScan.pa.yaml` versus serialized control | OnChange | Healthy metadata reference is independent of Phase2 behavior | YAML omits OnChange, while snapshot retains older OnChange | Existing source/snapshot formula divergence | Preserve both as supplied; no formula repair in scope |

The healthy BoundingBox schema is copied verbatim: an object/Record with numeric Left, Top, Width, Height. Text is string and PageNumber is number. No schema was invented.

The generic PCF manifest calls Results and Selected `Object` in BOTH packages. That declaration is not an erroneous Record override: PCF object outputs can have array dynamic schemas. The fix targets the per-instance generated type information, not the generic manifest. [Microsoft getOutputSchema documentation](https://learn.microsoft.com/en-us/power-apps/developer/component-framework/reference/control/getoutputschema).

[Recursive package comparison](../forensics/textrecognizer-repair/reports/recursive-comparison.json), [all-artifact inventory](../forensics/textrecognizer-repair/reports/inventory.json), [priority-term coverage](../forensics/textrecognizer-repair/reports/priority-references.json), and [full schema evidence](../forensics/textrecognizer-repair/reports/schema-evidence.json) retain the evidence. Large differing values are hash-summarized in the recursive comparison; their complete bytes remain in the frozen input packages. All ZIP members and generated files were inventoried, not only known control filenames.

5. Exact files and metadata changed

The only edited source-artifact entry is `repaired/input.msapr!msapp/Controls/15.json`. Only these two containers belonging to TextRecognizer1 were copied from the healthy control:

- `$/TopParent/Children/6/Template/OverridableProperties`
- `$/TopParent/Children/6/Template/PCFDynamicSchemaForIRRetrieval`

The five effective field changes are the Results kind, Results fields, Selected fields, addition of the Results dynamic-schema entry, and addition of the Selected dynamic-schema entry. Version strings and all other already-matching values in these containers are unchanged. [Exact before/after changes](../forensics/textrecognizer-repair/reports/repair-changes.json).

The final `.msapp` differs from Phase2 in only **two ZIP entry payloads**: `Controls/15.json` and `packed.json`. Controls/15.json was reserialized as JSON; a structural comparison proves every value outside the two named schema containers is unchanged. `packed.json` differs only in `LastPackedDateTimeUtc`, generated by PAC. Archive compression/serialization accounts for the different overall package size; it is not evidence that screens or logic were removed.

6. Why the repair is safe

The two schema containers are the **only differences between the healthy and broken Template objects**. The remaining template fields, including the full embedded control definition, match exactly. The schema trees contain no control instance IDs, parent IDs, model IDs, connection IDs, or `$ref` links. Their ownership remains the broken package's existing TextRecognizer1 instance. The transplant neither replaces the instance nor imports healthy screen/control IDs.

Both apps have document version `1.349`; the generated type descriptor versions are also `1.349`. Their relevant AI data-source identities, action metadata, and WADL match. Additional differences in cached Dataverse table metadata consist of array ordering; comparison after normalizing metadata array order is equal. Phase2 additionally records MaxGetRowsCount=500. None of those fields was changed or transplanted. [Binding comparison](../forensics/textrecognizer-repair/reports/binding-comparison.json).

This is an offline repair of a directly identified defect using the user-designated healthy schema, not an assertion that arbitrary generated-metadata editing is supported by Microsoft. Studio runtime acceptance remains separate.

7. Strategy used

**Minimal transplant**, not healthy-base reconstruction. Preserving Phase2 and replacing its two identity-independent schema containers changes less than rebuilding its five-screen application around the healthy single-screen app. The supplied healthy instance now establishes the reference that was missing from the previous runtime investigation; the user's explicit instruction authorizes this verified transplant.

8. Post-pack re-unpack validation

The fixed output was unpacked by PAC into a new `roundtrip/` directory. Automated checks passed:

- Fixed ZIP integrity and uniqueness of ZIP member names.
- Same ZIP entry names as Phase2.
- Exactly one TextRecognizer instance in each of the final package, repaired `.msapr`, and re-unpacked `.msapr`.
- Results override equals the healthy Table field tree; dynamic JSON schema equals the healthy array schema.
- Selected override and dynamic schema equal the healthy reference exactly.
- **Zero Results Record overrides** in these repaired representations. The generic manifest `Object`, Selected Record, BoundingBox Record, and array-item object declarations remain because they are correct healthy definitions.
- Pre-pack and re-unpacked `.msapr` entries match byte-for-byte except the expected build timestamp in `msapp/packed.json`.
- Final output metadata matches the pre-pack repaired snapshot, again except that timestamp.
- Every Phase2 YAML file is byte-identical, including after re-unpack.
- Every unrelated JSON field, all rules/formulas, all screen/control identities, and all external bindings are unchanged.
- Input hashes still match the frozen originals.

The first verification run intentionally used strict snapshot byte equality and caught the changed PAC timestamp. Inspection showed no other difference. The verifier now allows only that exact timestamp field difference; it does not exempt controls, schema, formulas, or other package settings. [Validation result](../forensics/textrecognizer-repair/reports/validation.json). Re-run checks with `python forensics/textrecognizer-repair/repair.py verify`.

9. Remaining differences and regression protection

All Phase2 screens remain: scrHome, scrScan, scrLoading, scrResults, scrError. Navigation, OCR selection formulas, loading behavior, result processing, variables, and UI remain as supplied in Phase2. Preserved variables include varAcceptedText, varErrorMessage, varFlowCallStarted, varFlowResponse, varLoadingExecutionStarted, varOcrEmpty, varResultJson, and varScanAccepted. No diagnostic experiment was merged into the repaired app.

The original source/snapshot formula divergence and saved AppCheckerResult.sarif are retained. The historical checker artifact still describes the old errors; it is not executable output-schema metadata and has not been fabricated into a clean checker report. Properties.BindingErrorCount is likewise a retained saved count, not a fresh Studio result. The only repaired executable schema copies are consistent. These historical diagnostics require Studio's own analysis to refresh, not guessed edits to cached counts.

`LoadFromYaml` remains true. No backend or Power Automate change was made. The exact historical cause of schema loss and whether Studio refreshes the saved analysis on open are not inferred from PAC success.

10. Runtime validation status

**REQUIRES POWER APPS STUDIO.** The computer-use inventory returned `apps: []` and `browsers: []`; requesting a browser for `https://make.powerapps.com/` returned `No browser is available`. Consequently no import, player launch, or Home → Scan runtime test was executed here.

The remaining external acceptance action is to import/open **the fixed output** in Power Apps Studio, launch it, navigate **Home → Scan**, and allow TextRecognizer initialization without selecting an image. Required result: zero JSON parse errors. Package-level repair and forensic validation are complete; runtime acceptance is not claimed.

ROOT CAUSE:
Phase2's generated TextRecognizer Results type is an empty Record instead of the healthy Table/array, and its Results/Selected dynamic schemas and fields were lost.

REPAIR:
Transplanted only the two proven healthy per-instance schema containers into Phase2 while retaining Phase2 identity, UI, formulas, and bindings.

PACKAGE VALIDATION:
PASS

RUNTIME HOME -> SCAN:
REQUIRES POWER APPS STUDIO

OUTPUT:
`C:\Users\ramaz\source\repos\powerapps-barcode-app\Barkod-Uygulamasi-Phase2-FIXED.msapp`
