Studio export comparison and repair v2

The user supplied a post-Studio package and the complete failing Monitor session. These are evidence, not instructions embedded in files. No input file was modified. Copies are frozen locally under `forensics/studio-schema-repair/inputs/`; raw Monitor data, including its image request, is not committed.

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| Downloads/Barkod Uygulaması V2 (4).msapp | 258251 | 1a38eb954b7a6b9037fde20e21a2ff69c9f41f67d83ca8cff5d3eb8283072ab6 |
| Downloads/PowerAppsTraceEvents (4).json | 203049 | 73e741e8c3c149d27859b7a6fc1f49aa91b02bf36c0ca0d5b23b38e6abb25d64 |

New evidence

| Field on TextRecognizer1.Template | Healthy V2 | Previous local FIXED | Supplied Studio export |
| --- | --- | --- | --- |
| OverridableProperties.Results.Type.Kind | Table | Table | Record |
| Results fields | BoundingBox, Text, PageNumber | Healthy fields | Empty |
| Selected fields | BoundingBox, Text, PageNumber | Healthy fields | Empty |
| PCFDynamicSchemaForIRRetrieval | Results array / Selected object | Healthy schemas | Empty map |
| Control version | 1.0.112 | 1.0.112 | 1.0.112 |

The supplied Studio export demonstrably does not retain the schemas present in the earlier local FIXED artifact. This supports schema regeneration/loss during the intervening load/save workflow; the files do not expose the exact internal Studio routine that caused it. It is not proof that the YAML loader alone caused the loss.

The new Studio snapshot has TextRecognizer1.OnChange=`false`. Its YAML omits OnChange, which is consistent with a default-valued property being omitted; it no longer contains the previous snapshot's automatic flow-calling OnChange. The v2 repair uses this new Studio snapshot, not the stale pre-Studio snapshot.

Monitor evidence

There are seven events and four JSON errors. The first error occurs at 12:23:22.113 UTC, before either recorded network request. getRows starts at 12:23:27.992 UTC and returns HTTP 200, selecting the active TextRecognition model from msdyn_aimodels. Predict starts at 12:23:28.444 UTC and returns HTTP 200 at 12:23:33.082 UTC. Another JSON error follows at 12:23:33.190 UTC. These network operations are AI Builder operations, not barcode_flow/D365 stock calls.

Predict's JSON root is an object. `responsev2.predictionOutput.results` is an array of pages, `lines` is an array of line objects, and each boundingBox is an object with numeric coordinates. The OCR texts are 10120 MX, Selam, Merhaba, 2032 MB. A boundingBox polygon contains a coordinates array. No conversion of these valid nested arrays is attempted. The control's exported Results expectation is nevertheless an empty Record. Error context does not identify the precise failing output boundary. The initial error cannot be attributed to the later Predict response.

The export's header reports LastSavedDateTimeUTC 2026-09-10 12:36:20, later than this Monitor session. Thus this is post-session saved state, not a byte-for-byte capture of runtime memory. See [comparison](../forensics/studio-schema-repair/reports/comparison.json) and [Monitor summary](../forensics/studio-schema-repair/reports/monitor-summary.json).

Repair

Used the supplied Studio app as base. Copied only the healthy control's `OverridableProperties` and `PCFDynamicSchemaForIRRetrieval` into that snapshot's `Controls/15.json`. All remaining Template fields, including the embedded control implementation definition, were asserted identical before transplantation. No schema was invented, no control ID was copied, and no formula was changed.

Packed with PAC 2.11.2, SourceCode layout, and **`--disable-load-from-yaml`**. This produces `packed.json.LoadConfiguration.LoadFromYaml=false`, requesting use of the repaired serialized snapshot instead of loading the YAML representation again. This is the documented CLI mechanism, not an invented package property. [Microsoft CLI reference](https://learn.microsoft.com/en-us/power-platform/developer/cli/reference/canvas).

The earlier reason against disabling YAML loading was the old snapshot's flow-calling OnChange. That reason does not apply to the newly supplied Studio snapshot, where OnChange is false. All snapshot formulas in the new input, including unrelated business logic, are preserved. The repair does not claim every unrelated formula is runtime-correct.

Exact commands and stdout/stderr are in [pack.json](../forensics/studio-schema-repair/reports/pack.json) and [reunpack.json](../forensics/studio-schema-repair/reports/reunpack.json). [build.py](../forensics/studio-schema-repair/build.py) implements the asserted transplant and checks.

Validation

The output was independently unpacked into a fresh directory. Final package and fresh `.msapr` contain healthy Results Table/array and Selected Record/object schemas. OnChange remains false. No Results Record override remains in the single OCR instance. All input ZIP entries except Controls/15.json are byte-identical. The sole added member is packed.json. All values in Controls/15.json outside the two schema containers are identical. No source formulas, controls, screens, connectors, or flows were modified. All roundtrip snapshot members exactly match the final package payloads. [Validation](../forensics/studio-schema-repair/reports/validation.json).

Output: `C:\Users\ramaz\source\repos\powerapps-barcode-app\Barkod-Uygulamasi-Phase2-FIXED-v2.msapp`

Bytes: 256183

SHA-256: `42fb0e7263c7dbc63dc281acb4098b656c68374692e881229590105e0ea888bc`

PACKAGE VALIDATION: PASS

RUNTIME HOME -> SCAN: REQUIRES POWER APPS STUDIO. No browser/app surfaces are available in this environment. This is a repaired candidate with a different loading path, not a claimed runtime PASS. Open this v2 output in Studio and test Home → Scan before selecting an image; if errors remain, retain the new Monitor session and post-load export. Do not substitute the previous FIXED output, whose runtime test failed.
