# S11 G4 calculation-chain parser correction — 2026-10-01

The approved local parser correction is implemented and retested. Excel calculation-chain references are now distinguished from worksheet cells using exact SpreadsheetML namespace, root and direct-child depth. Worksheet validation and package-wide XML/ZIP safety checks remain in place. No file normalization, workbook save, import, SQL/provider call, credential/ACL change, deployment or activation was performed.

## Input decision and results

Use the retained `C:\Users\cwatt\Downloads\KVK_16_Baseline.xlsx` as B0, following the operator's agreement to the original-baseline recommendation. The CSV remains preserved; it is a different snapshot, not an equivalent re-export or accepted XLSX source.

|Input|Parsed player rows|Formula cells retained as unavailable|
|---|---:|---:|
|Original B0|5,806|9|
|Pass 4 start|5,729|6|
|Pass 4 end|5,720|6|

All three hash-bound historical originals passed full offline parsing, with original bytes unchanged. The start/end copies under `Downloads\KVK16` changed after the initial analysis. The bound retest stopped on hash mismatch; retained originals directly under Downloads still matched. Separate read-only comparison found zero changed typed cell values across the Scan grids. Both current KVK16 copies also passed full parsing and have exactly the same semantic digests as their respective originals. Cause of the external file change has been asked, not inferred.

Baseline SHA256: `d28d58b3505eac2cfaffc144130ce8816f270496dee439842c49fc06064fe147`.

Original start/end SHA256: `512e0268ab5ca524b1bc1a94971a27299e67bb5a5e2cdc1da9b61f3394cfdfe1` / `eae10b1cf83ee00332857333fbb26bda8e0a43078c4c3db8bc191adbbe8ac974`.

Current KVK16 start/end SHA256: `450c128f3aea7a510cb5c9f72f6ac7cc568d63b15a66f1135ee44aab8cdf37e4` / `718e9b1dc4e4d7e1952d9097667a0279704961c72479af916096973902e0cbdd`.

Historical contract times are used only in offline diagnostic metadata; diagnostic kingdom scope comes from retained input analysis. This is not intake approval or runtime configuration. Pass 4 uses end minus start, with the original B0 roster. Missing endpoints stay unavailable. Kingdom/Camp aggregate inputs and actual DKP/config bindings are not supplied by this parser exercise.

## Validation and security disposition

The new positive regression reproduced `cell_order` before correction. After correction, parser/metadata/digest tests: **180 passed**. Ruff, architecture, deferred-item, security-routing and command-registration validators passed. Five new negative cases retain refusal of malformed/foreign/nested cell structures. Existing tests cover renamed XML parts, entities, numeric evidence, duplicate values and bounds.

The test selector recommends the full suite whenever tests change. Full suite and broad smoke imports were skipped: the correction is confined to the pure offline parser, the focused suites exercise its consumers directly, and this turn does not authorize broad runtime observation or gated fixtures. No SQL source changed, so a new SQL review is not applicable.

Security routing selected Changes review, Deep off. Independent review of the exact copied-before/current two-file delta found no plausible security candidate. **Native Changes-scan completion remains unavailable for this copied-file baseline**; current security artifact rules prohibit fabricating terminal canonical output. The managed standalone assessment is supporting evidence, not a completed native scan. Old Bot/SQL reviews remain bound to their old snapshots; do not claim they cover this correction.

Reviewed parser SHA256: `1d6ff76a3a8c0d738a1d8ee1ccb0303a745918d5545b68123982012e732c68af`.
Reviewed tests SHA256: `e5321a268f0d3a71c4ba0c8961a8c1e760d9fff482afd583a20d6419a9f60f85`.

Evidence directory: `.codex_artifacts/s11-calcchain-parser-20261001/`. Includes before/after source copies, focused test output, validator results, command-registration output, original/current parser results, typed-value comparison, failed diagnostic attempt qualifications, standalone security review copy, and a separate seal. Old implementation, readiness, SQL and input-review seals remain unchanged.

## Remaining readiness boundary

RDY-H01 completed only the approved local owner/DACL/reparse observation. It did not authorize or perform permission changes. Existing broad inherited grants require a concrete correction plan covering protected paths and parents, with recovery boundaries, before any change. User's key-holder statement remains prod/local only; do not ask again.

The readiness packet's remaining seven typed proof requirements, exact runtime installation, writer/reference closure, registration and real two-export demonstration remain open. No source test or historical capture establishes their acceptance. Keep DB22 read-only/restricted/Broker-disabled with its 119 media files, retain DB23 and prior failed/completed evidence, and preserve S6/S8, uncertain outputs, shared-account amendment and withdrawn collector. Production remains hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`; rollout/G5 require their own operator decisions.
