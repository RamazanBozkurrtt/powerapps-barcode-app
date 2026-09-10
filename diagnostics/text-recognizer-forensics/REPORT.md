Power Apps Text Recognizer forensic report — 2026-09-10

Most likely classification: **C — stale/generated control metadata defect**. **D — local pack/unpack/source-code workflow defect** is an evidenced contributing limitation: this pack operation preserves the suspect metadata without regenerating it. Runtime causation remains unconfirmed; the Home → Scan success criterion has NOT been demonstrated. No production fix has been made.

1. **Most likely root cause.** TextRecognizer1's generated output schemas were lost between the earlier single-screen package and the later five-screen package. The later package describes Results as an empty Record instead of a Table. An array arriving at that record boundary fits the reported message, including at initialization. The initialization output value itself was not captured here; an empty-array initialization remains an inference, not an observed payload.

2. **Supporting evidence.** The earlier on-disk `Barkod Uygulaması V2.msapp` has a Table Results override and explicit array JSON schema. `Barkod Uygulaması V2 3.msapp`, Phase 2, both supplied diagnostic packages, and the current `.msapr` instead have an empty Record Results override and no PCF dynamic schemas. Their saved checker report independently flags `.Results` with expected `Table`, provided `Record`. See [schema evidence](schema-evidence.json), [control comparison](control-comparison.json), and [checker evidence](checker-evidence.json).

3. **Evidence against alternatives.** The user's observed isolated runtime sequence excludes the flow, D365 stock response, result_json processing, nested startup collections, and polling logic for this reproduction. Those runtime observations were supplied by the user, not rerun here. Identical TextRecognizer version and definition bytes across the earlier and later packages argue against a control-template version change. Old OnChange formulas do survive in serialized files, but the user's Monitor trace proves the simplified OnChange executed in the tested session; surviving old text alone does not prove it executed. A platform initialization or binding defect is not yet excluded.

4. **Does the error occur with TextRecognizer completely absent?** Unknown. No genuine OCR-free runtime test is available. A local YAML removal probe packed successfully but retained the entire OCR control and bindings in serialized metadata. It is deliberately named `source-removal-probe-NOT-ISOLATED.msapp` and is not Build 1 or a release candidate. The Git HEAD artifacts contain no TextRecognizer control, but they are the initial blank app, not a tested Home/Scan isolation build.

5. **Exact mismatch.** In the earlier package, `Controls/4.json`, TextRecognizer1 → Template → OverridableProperties → Results → Type → Kind is `Table`. In the later package and current `.msapr`, the corresponding `Controls/15.json` value is `Record`, with `Type: []`. The earlier PCFDynamicSchemaForIRRetrieval.Results.DynamicSchema has `type: array`, with object items containing BoundingBox, Text, and PageNumber. The later PCFDynamicSchemaForIRRetrieval is `{}`. This is a proven serialized type discrepancy; the precise runtime error-producing boundary still needs confirmation.

6. **Do YAML and the `.msapr` disagree?** Yes, for formulas. Current `app-src/Src/scrScan.pa.yaml` sets OnChange to only `Trace("DIAG_TEXT_RECOGNIZER_ONCHANGE", TraceSeverity.Information)`. The `.msapr` retains an OnChange rule that reads and sorts Self.Results, navigates to loading, and invokes barcode_flow.Run. It also retains older screen/app rules. YAML does not contain the generated output schema, so there is no YAML schema declaration to compare against the Record override. Absence of schema in YAML is not itself a conflicting declaration.

7. **Does stale TextRecognizer metadata exist?** Yes: stale serialized formulas and the retained suspect output schemas. All inspected OCR instances have version `1.0.112`. Their DynamicControlDefinitionJson SHA-256 is `c4cd6080dfca98ee5287d5bdff1398be0e9bdcf1a0d88f0186950f8b7bb3f27c`. No claim is made that every retained generated field is invalid.

8. **Must Studio regenerate the control?** Studio is required for the safe next diagnostic step. Do not transplant the older schemas, change Record to Table manually, invent output properties, or splice serialized controls between packages. The older control is useful comparative evidence, but its successful runtime operation and safe transplantability are unproven. A fresh Studio-created Text Recognizer is required for Build 2. Whether regeneration fixes the reported error must then be tested.

9. **Is local pack/unpack contributing?** It demonstrably preserves stale metadata. The `.msapr` ZIP holds `msapr-header.json` plus 15 `msapp/` entries, including all six Controls JSON files, data sources, templates, properties, and checker output. These are a retained serialized app snapshot; no independent compiled bytecode/IR artifact was identified, so “compiled fallback snapshot” should not be treated as a proven execution model. Fresh packing copied all 15 entries byte-for-byte. The no-OCR YAML probe did the same. Both outputs set `packed.json → LoadConfiguration → LoadFromYaml: true`. The flag enables YAML loading; it does not demonstrate that PCF schemas were regenerated. Do not disable it as a fix: that requests non-YAML loading and risks using old formulas. Which retained fields Studio consumes or regenerates requires Studio observation.

10. **Smallest safe next action.** Produce and runtime-test the Studio-only Build 1 below, then create Build 2 from it using Insert. Export both packages and Monitor logs for comparison. Stop after the navigation path is proven clean; do not restore application behavior.

Exact schema comparison

| Representation | Results override | Selected override | Dynamic schemas |
| --- | --- | --- | --- |
| Earlier on-disk V2 package; Phase1-Fixed | Table with BoundingBox/Text/PageNumber | Record with BoundingBox/Text/PageNumber | Results array; Selected object |
| V2 3; Phase2; Diagnostic 1; Diagnostic 2; current msapr | Empty Record | Empty Record | Empty map |
| Fresh unchanged repack; source-removal probe | Empty Record retained | Empty Record retained | Empty map retained |

Selected's top-level Record kind is consistent, but its field schema is lost. BoundingBox in the earlier schema is an object/Record containing numeric Height, Left, Top, Width. No corresponding field schema remains in the later instance override. The observed OCR `boundingBox.top = 0.270625` is compatible with a numeric coordinate, but the raw Monitor export is absent (`test.json` is empty). There is insufficient evidence to reconstruct or compare the complete live AI Builder response contract.

The generic PCF manifest declares both Results and Selected as `Object`. **That is not the defect by itself.** Microsoft's getOutputSchema documentation explicitly supports an array schema for a manifest object output. The concrete difference is in the per-instance override and missing dynamic schema. FullText is present in the manifest (`Multiple`, dynamic property Type 12); no Results-like override exists for it. Numeric internal type IDs are reported as serialized, not assigned invented meanings. LoadSchema defaults to true, and the generated PropertyDependencies declare it necessary for the schemas of Results and Selected. OcrObjects is a hidden Object input. No custom OcrObjects rule was found. See [decoded definition](decoded-control-definition.json).

Control and AI Builder binding

- Template ID: `http://microsoft.com/appmagic/powercontrol/TextRecognizer`; version `1.0.112`.
- Namespace/constructor: `Intelligence.TextRecognizerControl.TextRecognizer`; first-party virtual PCF control.
- References/Templates.json declares TextRecognizer `1.0.112`; its recorded conversion adds FullText from `1.0.106` to `1.0.107`. No conflicting TextRecognizer version was found.
- Hidden data-source name: `43b0dc67-68af-47ae-9a9c-9e69d396ba3e`; Type `NativeCDSDataSourceInfo`; DatasetName `default.cds`; EntitySetName `msdyn_aimodels`; LogicalName `msdyn_aimodel`; ApiId `/msdyn_aimodel`; CdsActionInfo.IsUnboundAction `false`.
- Properties.LocalDatabaseReferences maps that source to `https://org81ed1142.crm4.dynamics.com/`, API `v9.0`.
- Serialized WADL exposes POST `/msdyn_aimodels({msdyn_aimodelid})/Microsoft.Dynamics.CRM.Predict`. Request fields are version/string, request/string, requestv2/untypedObject, and source/string. PredictResponse is an object with string fields response, overrideHttpStatusCode, overrideLocation, overrideRetryAfter.
- This is the saved action envelope, not a typed OCR line-output contract. No direct TextRecognizer1 Power Fx Predict formula or explicit instance-to-model-ID assignment was found. The hidden source's GUID is not asserted to be the prediction model ID. Internal runtime binding details cannot be recovered from these declarations alone. Full extracted binding evidence is in [bindings.json](bindings.json).

Local workflow experiments

CLI: `2.11.2+g47bc199`, .NET `10.0.10`. Commands used:

```powershell
pac canvas pack --sources app-src --msapp diagnostics/text-recognizer-forensics/experiments/unchanged-repack.msapp --layout SourceCode
pac canvas pack --sources diagnostics/text-recognizer-forensics/experiments/source-removal-probe --msapp diagnostics/text-recognizer-forensics/experiments/source-removal-probe-NOT-ISOLATED.msapp --layout SourceCode
```

The first attempt lacked the output directory and exited with DirectoryNotFoundException. After creating that directory, packing succeeded. This filesystem error is unrelated to the runtime issue. Both successful packs emitted an explicit instruction to validate by opening the app for editing in Studio. Neither was run in the player. [Workflow evidence](workflow-evidence.json) lists the preserved entries and load settings.

The removal probe contains only App, Home, and Scan YAML, two navigation buttons, and the copied source artifact. It has no OCR, flow, parsing, stock, or timer formula in YAML. Yet the packed JSON contains the original five screens, OCR control, old flow-calling formula, bindings, and checker output. Removing those generated structures by hand would cross the user's boundary against emulating Studio metadata. Therefore no locally fabricated Build 1 or Build 2 is presented as true binary isolation.

Microsoft's current YAML documentation says exported pa.yaml is for reviewing Studio changes and limits supported external editing to Power Platform Git Integration. The CLI reference marks pack/unpack deprecated but still documents SourceCode loading options; the installed CLI supports them and requires Studio validation. These sources should not be flattened into a claim that this CLI ignores all YAML: the user's trace is evidence that edited YAML can take effect. The narrower proven limitation here is **packing does not regenerate the suspect PCF metadata**. The available packages do not establish which earlier operation originally lost the schemas.

Manual Studio procedure — separate diagnostic apps

1. Preserve the existing Phase 2 app. In the same environment, create a **new blank Canvas app** with phone layout named `OCR-Isolation-Build1-NoOCR`. This avoids carrying hidden bindings from the suspect package.
2. Rename the first blank screen `scrHome`; insert another blank screen named `scrScan`. Add a button to Home with Text `"Scan"` and OnSelect `Navigate(scrScan, ScreenTransition.None)`. Add a button to Scan with Text `"Home"` and OnSelect `Navigate(scrHome, ScreenTransition.None)`. Use the Studio locale's argument separator if it displays semicolons.
3. Set App.StartScreen to `scrHome`. Leave App.OnStart and both screen OnVisible properties blank. Add no other controls, data sources, flows, timers, formulas, or AI Builder components.
4. Save Build 1, close the editor, and reopen it. Start Live monitor from the app's menu/Studio, open the diagnostic app for playback, clear the log, and navigate Home → Scan → Home → Scan without selecting an image. Export the Monitor log, including all errors. Download the saved `.msapp` using the Save menu's Download a copy option (in interfaces using File, Save as → This computer).
5. Save a **separate copy** of Build 1 named `OCR-Isolation-Build2-FreshOCR`. On scrScan use Studio **Insert → AI Builder → Text recognizer** (or search Insert for Text recognizer). Let Studio initialize its generated binding. Do not paste/copy the old control or source metadata.
6. Leave the new control's OnChange at its Studio-created default. Do not add Results, Selected, FullText, or OcrObjects formulas anywhere. Keep both screens and navigation unchanged. Save, close Studio, reopen Build 2, and repeat the same monitored navigation **before selecting an image**.
7. Download Build 2 and export its Monitor log. Record the new control's name/version, Studio session version if shown, app version, test time, environment, and whether each navigation produced the JSON error. Stop; do not reconnect the flow or restore OCR selection/stock logic.

Provide afterward: `OCR-Isolation-Build1-NoOCR.msapp`, `OCR-Isolation-Build2-FreshOCR.msapp`, both exported Live monitor logs, and a fresh download of the exact currently failing diagnostic app (with trace-only OnChange) named `OCR-Failing-TraceOnly-Studio.msapp`. Local Phase 2 and the current source do not themselves prove the contents of that last Studio session.

I will inspect all package entries for OCR references in Build 1, compare Build 2's generated Results/Selected schemas and bindings, and correlate runtime logs. A clean Build 1 and failing Build 2 localize the problem to adding the control/binding, but do not alone distinguish component code from environment/schema behavior. If both are clean and the regenerated schema is correct, perform the following repair experiment only in another copy of the failing app: delete TextRecognizer1 and formulas referring to it; save; close/reopen; add a fresh Text recognizer through Insert; leave default behavior; save; close/reopen; test navigation and download. Do not attempt this replacement in production before reviewing the isolation result.

Evidence coverage and preservation

The audit reads six original on-disk msapp packages, the working msapr, both historical Git HEAD artifacts, and two local probes. It scans every textual ZIP entry and every working pa.yaml for every occurrence of the nine requested terms. [references.json](references.json) stores file, normalized line, column, and context for all 4,735 occurrences; [manifest.json](manifest.json) records package and entry hashes. Expanded files are local under `extracted/`; experiments are local under `experiments/`. Both directories are ignored by this diagnostic folder's gitignore. [audit.py](audit.py) regenerates the main inventory without editing source packages. Schema and workflow summaries are captured separately.

All pre-existing app sources and packages were preserved. The Power Automate flow was neither called nor changed. Only a diagnostic commit is appropriate; no fix commit is warranted without a validated repair.

Primary documentation consulted

- [Text recognizer component properties](https://learn.microsoft.com/en-us/ai-builder/prebuilt-text-recognizer-component-in-powerapps): Results is a list of lines; Selected describes one selected line.
- [PCF getOutputSchema](https://learn.microsoft.com/en-us/power-apps/developer/component-framework/reference/control/getoutputschema): dynamic schemas for object outputs, including array schemas.
- [Object output component sample](https://learn.microsoft.com/en-us/power-apps/developer/component-framework/sample-controls/object-output): platform obtains output schema before component initialization.
- [Canvas source-code files](https://learn.microsoft.com/en-us/power-apps/maker/canvas-apps/power-apps-yaml): exported-source limitations and supported Git integration.
- [CLI canvas reference](https://learn.microsoft.com/en-us/power-platform/developer/cli/reference/canvas): deprecation, SourceCode options, and disable-load-from-yaml semantics.
