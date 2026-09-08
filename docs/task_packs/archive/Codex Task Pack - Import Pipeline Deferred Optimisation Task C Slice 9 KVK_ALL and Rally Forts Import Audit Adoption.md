# Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 9 KVK_ALL and Rally Forts Import Audit Adoption

> Archived 2026-06-30 after the combined KVK_ALL/Rally Forts scope was split into two
> implementation PRs. Slice 9 delivered KVK_ALL generic durable import audit adoption in mirror
> PR #190 and production PR #498, including smoke-tested `KVK.KVK_Scan` and
> `KVK.KVK_Ingest_Diagnostics` correlation. Rally Forts was promoted into Task C Slice 10 and
> later delivered in mirror PR #191 and production PR #499.

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task C Slice 9 - KVK_ALL and Rally Forts Import Audit Adoption`
- Date: `2026-06-30`
- Owner/context: `Chris Watts / K98 bot import architecture`
- Task type: `deferred optimisation batch | import audit adoption | KVK_ALL and Rally Forts upload routes`
- Depends on:
  - Task A, archived at `docs/task_packs/archive/Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md`
  - Task B, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md`
  - Task C Slice 1, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Import Architecture and Service DAL Wrappers.md`
  - Task C Slice 2, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 2 Durable Batch Audit Foundation.md`
  - Task C Slice 3, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3 Non-Fallback Audit Adoption.md`
  - Task C Slice 3A, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3A Import Audit Batch Counter Normalization.md`
  - Task C Slice 4, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 4 Honor Import Audit Adoption.md`
  - Task C Slice 5, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 5 PreKvK Import Audit Adoption.md`
  - Task C Slice 6, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 6 Weekly Activity Import Audit Adoption.md`
  - Task C Slice 7, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 7 MGE Results Import Audit Adoption.md`
  - Task C Slice 8, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 8 Inventory Import Audit Adoption.md`
- One-pass approved: `no`
- Status: `archived split-scope record; KVK_ALL delivered, Rally Forts moved to Task C Slice 10`

## 2. Objective

Adopt generic durable import audit for the KVK_ALL all-kingdom upload route and the Rally Forts
upload route, after inventory audit adoption was delivered and smoke tested in Task C Slice 8.

This slice must start with audit/scope only. Confirm the current KVK_ALL route, importer, DAL,
SQL ingest procedure, diagnostics, recompute/export scheduling, result embeds, tests, and smoke
expectations. Also confirm the current Rally Forts route, local file staging, daily/all-time
importers, SQL staging/current tables, `dbo.IngestionLog` behavior, log-backup scheduling, result
embeds, tests, and smoke expectations. Then propose a PR-sized implementation plan. If audit finds
that KVK_ALL and Rally Forts are too risky for one implementation PR, split the implementation
after the shared audit packet and preserve this task pack as the route-coverage map.

Important distinction: KVK_ALL and Rally Forts upload-route extraction is already complete. KVK_ALL
was extracted in upload-routing Phase 4 / PR 110, and Rally Forts was extracted in upload-routing
Phase 5C / PR 115. What remains is generic durable import audit adoption for those routes.

## 3. Delivered Baseline

Confirmed delivered import baseline:

- Task C Slice 2 added `dbo.ImportAuditBatch`, `dbo.ImportAuditPhase`, SQL-owned audit writer
  procedures, bot audit DAL/service wrappers, and fallback-first audit wiring correlated to
  `dbo.FallbackImportBatchControl`.
- Task C Slice 3 wired player-location generic audit for the auto `scan_1198.csv` route and
  `/location import` command merge path.
- Task C Slice 3A normalized batch-level `RowsInSource` through SQL-owned terminal writer
  procedures and bot wrappers.
- Task C Slice 4 adopted generic durable audit for Honor uploads.
- Task C Slice 5 adopted generic durable audit for PreKvK uploads.
- Task C Slice 6 adopted generic durable audit for weekly activity uploads.
- Task C Slice 7 adopted generic durable audit for MGE results uploads and manual/overwrite
  imports through the importer.
- Task C Slice 8 adopted generic durable audit for inventory image uploads, command-session
  imports, additional-material continuation, approval/reject/cancel/timeout/failure outcomes, and
  corrected aggregate material screenshot counting to `RowsInSource=3` for the three-image smoke.

Current KVK_ALL baseline to validate:

- `DL_bot.py` delegates to `upload_routes/kvk_all_route.py`.
- The route is gated by the configured Pro Kingdom channel and accepts `.xlsx`, `.xls`, and `.csv`
  attachments.
- The route reads attachments into memory, runs SQL headroom preflight, offloads
  `kvk_all_importer.ingest_kvk_all_excel`, renders existing success/warning/error embeds, builds
  the best-effort Google Sheet link button, and schedules auto-export when enabled.
- `kvk_all_importer.py` is a compatibility wrapper over `kvk.services.kvk_all_import_service` and
  `kvk.dal.kvk_all_import_dal`.
- SQL ingest uses `KVK.KVK_AllPlayers_Stage`, `KVK.sp_KVK_AllPlayers_Ingest`, `KVK.KVK_Scan`,
  `KVK.KVK_AllPlayers_Raw`, `KVK.KVK_Ingest_Negatives`, `KVK.sp_KVK_Recompute_Windows`, and
  optional `KVK.KVK_Ingest_Diagnostics` for rejected/failed diagnostic rows.
- Accepted imports return `kvk_no`, `scan_id`, `row_count`, `staged_rows`, negative count,
  timing details, sheet/schema metadata, and `success=True`.

Current Rally Forts baseline to validate:

- `DL_bot.py` delegates to `upload_routes/rally_forts_route.py`.
- The route is gated by `FORT_RALLY_CHANNEL_ID`, treats channel id `0` as disabled, accepts only
  `.xlsx` attachments, rejects path separators before save, stages local files under
  `LOG_DIR/downloads`, lazy-loads `forts_ingest` importers, runs SQL headroom preflight, offloads
  daily/all-time imports, aggregates per-file success/skip/error results, renders the existing
  final embed, and schedules best-effort log backup after successful imports.
- `forts_ingest.import_rally_daily_xlsx()` parses `Rally_data_DD-MM-YYYY.xlsx`, writes
  `dbo.stg_RallyDaily`, runs `dbo.sp_Import_Rally_Daily`, writes `dbo.IngestionLog`, and returns
  `status`, `rows`, and `as_of`.
- `forts_ingest.import_rally_alltime_xlsx()` parses all-time Rally filenames, writes
  `dbo.stg_RallyAllTime`, runs `dbo.sp_Import_Rally_AllTime`, writes `dbo.IngestionLog`, and
  returns `status` and `rows`.

## 4. Source Deferred Item Promoted Into This Pack

### Deferred Optimisation
- Area: `upload_routes/kvk_all_route.py`, `kvk_all_importer.py`, `kvk/dal/kvk_all_import_dal.py`, `upload_routes/rally_forts_route.py`, `forts_ingest.py`, `services/import_audit_service.py`, `stats/dal/import_audit_dal.py`, SQL repo KVK/Rally objects
- Type: consistency
- Description: KVK_ALL and Rally Forts upload routes were extracted from `DL_bot.py` during the earlier upload-routing programme, but they have not been adopted into the generic durable `ImportAuditBatch` / `ImportAuditPhase` model. Operators currently rely on route embeds, logs, KVK-specific diagnostic tables, `dbo.IngestionLog`, and downstream output tables rather than one shared import-audit surface for these route lifecycles.
- Suggested Fix: Adopt generic audit for KVK_ALL and Rally Forts using service/DAL-owned best-effort audit wrappers. Validate accepted KVK_ALL correlation to `KVK.KVK_Scan` with `ExternalBatchId=<KVK_NO>:<ScanID>`, validate rejected/failed KVK diagnostics correlation to `KVK.KVK_Ingest_Diagnostics` when a diagnostic id exists, and validate Rally Forts correlation to `dbo.IngestionLog` when a stable `IngestionID` can be returned or looked up without behavior changes. Preserve route UX, file handling, importer contracts, SQL table/procedure behavior, export/recompute scheduling, embeds, telemetry/logging, and user-facing behavior.
- Impact: medium
- Risk: medium
- Dependencies: Task C Slice 2 audit foundation; Task C Slice 3A terminal counter normalization; Task C Slice 8 inventory adoption closure; SQL validation against `C:\K98-bot-SQL-Server`; existing KVK_ALL and Rally Forts route tests.

## 5. Proposed Implementation Boundary

### In Scope

- Audit KVK_ALL state surfaces:
  - route channel gating and accepted extension filtering;
  - attachment read and SQL headroom preflight;
  - offload contract for `ingest_kvk_all_excel`;
  - schema validation failure, empty workbook, missing stage columns, KVK-details range rejection,
    ingest procedure failure, accepted ingest, negative corrections, recompute, auto-export, and
    per-attachment continuation;
  - existing `KVK.KVK_Ingest_Diagnostics` write and returned `diagnostic_id` for rejected/failed
    outcomes;
  - route embeds and sheet link button behavior;
  - KVK_ALL route/importer/DAL/service/schema/recompute tests.
- Audit Rally Forts state surfaces:
  - route channel gating, disabled-route behavior, `.xlsx` filtering, filename classification,
    unsafe filename rejection, local save, SQL headroom preflight, offload dispatch, result
    aggregation, final embed behavior, and log-backup scheduling;
  - daily vs all-time importer result contracts;
  - `dbo.IngestionLog` duplicate detection, success/error logging, and whether `IngestionID` can
    be returned or looked up safely;
  - Rally route tests and any missing importer/DAL tests needed to support generic audit adoption.
- Validate SQL objects against `C:\K98-bot-SQL-Server`.
- Reuse existing generic audit objects and bot wrappers from Task C Slice 2 / Slice 3A.
- Keep audit writes best-effort.
- Add import-kind-specific audit service helpers only if they keep route/importer code simple and
  match the existing Honor/PreKvK/weekly/MGE/inventory pattern.
- Preserve all user-facing route behavior, embed text, attachment handling, importer outputs,
  SQL table/procedure behavior, export/recompute/log-backup scheduling, and existing tests.
- Update tests and deferred documentation after delivery.

### Out Of Scope

- Discord route UX or embed text changes.
- Changing accepted filename/extension rules.
- Replacing KVK_ALL importer, Rally importer, or offload mechanics.
- Changing KVK_ALL workbook schema, Rally workbook format, SQL table schemas, stored procedure
  semantics, views, exports, report output, or Google Sheets behavior.
- New SQL schema objects or new generic audit objects unless audit finds a blocker and approval is
  granted.
- Historical production data backfill.
- `dbo.UPDATE_ALL2` wrapper/audit-output instrumentation.
- `dbo.IMPORT_STAGING_PROC` decomposition.
- `dbo.UPDATE_ALL2` decomposition.
- Residual `stats_module.py` cleanup.
- Legacy PreKvK SQL cleanup.
- Weekly cumulative view cleanup.
- Inventory view-orchestration extraction.

## 6. SQL Position To Validate

Known KVK_ALL candidates from current SQL validation:

- Accepted KVK_ALL imports create `KVK.KVK_Scan` rows keyed by `(KVK_NO, ScanID)`. Proposed
  external correlation: `ExternalBatchTable=KVK.KVK_Scan`,
  `ExternalBatchId=<KVK_NO>:<ScanID>`.
- Accepted raw rows land in `KVK.KVK_AllPlayers_Raw`; negative corrections in
  `KVK.KVK_Ingest_Negatives`; stage rows use `KVK.KVK_AllPlayers_Stage`.
- Rejected/failed diagnostic rows can be written to `KVK.KVK_Ingest_Diagnostics` with
  `DiagnosticID`. Proposed failed/rejected correlation when present:
  `ExternalBatchTable=KVK.KVK_Ingest_Diagnostics`, `ExternalBatchId=<DiagnosticID>`.
- Pre-parse/pre-diagnostic failures should remain uncorrelated unless implementation can attach a
  stable diagnostic id without changing behavior.

Known Rally Forts candidates from current SQL validation:

- `dbo.IngestionLog` has identity `IngestionID`, unique `(Source, FileName)`, `RowsIn`, `Status`,
  `ErrorMessage`, and `AsOfDate`.
- Current importers write `dbo.IngestionLog` but return only `status`, `rows`, and optional
  `as_of`; duplicate outcomes return before writing a new row.
- Proposed accepted/error correlation: `ExternalBatchTable=dbo.IngestionLog`,
  `ExternalBatchId=<IngestionID>` only if audit validates a safe small return/lookup helper.
- Duplicate/no-row/unrecognized/preflight failures should remain uncorrelated unless a stable
  existing `IngestionID` can be looked up without changing behavior.

## 7. Audit Taxonomy Proposal

KVK_ALL:

- `ImportKind`: `kvk_all`
- `SourceType`: `discord_upload_xlsx`, `discord_upload_xls`, or `discord_upload_csv`
- Likely phases:
  - `kvk_all_attachment_read`
  - `kvk_all_schema_parse`
  - `kvk_all_stage_insert`
  - `kvk_all_sql_ingest`
  - `kvk_all_recompute_windows`
  - `kvk_all_negative_check`
  - `kvk_all_auto_export_schedule`
- Terminal statuses:
  - accepted import: `completed`
  - schema/validation failure: `failed`
  - KVK-details range rejection: `skipped` unless audit confirms `failed` better matches current
    operator semantics
  - SQL preflight abort: `failed` or `skipped` only after validating current user-facing semantics
  - per-attachment exception: `failed`

Rally Forts:

- `ImportKind`: `rally_forts`
- `SourceType`: `discord_upload_xlsx`
- Likely phases:
  - `rally_forts_attachment_save`
  - `rally_forts_file_classify`
  - `rally_forts_sql_preflight`
  - `rally_forts_daily_ingest` or `rally_forts_alltime_ingest`
  - `rally_forts_log_backup_schedule`
- Terminal statuses:
  - successful daily/all-time import: `completed`
  - duplicate or no-row importer skip: `skipped`
  - unrecognized file: `skipped`
  - unsafe filename or importer/offload exception: `failed`
  - SQL preflight abort: `failed` or `skipped` only after validating current user-facing semantics

## 8. Remaining Slice Map To Preserve

Do not lose these later slices:

1. **Later SQL Slice - `dbo.UPDATE_ALL2` Wrapper/Audit Outputs**
   - Add non-invasive audit output around downstream rebuild phases before procedure decomposition.
2. **Later SQL Slice - `dbo.IMPORT_STAGING_PROC` Responsibility Split**
   - Split only after durable audit evidence and compatibility wrappers are stable.
3. **Later SQL Slice - `dbo.UPDATE_ALL2` Decomposition**
   - Prepare only after wrapper/audit-output evidence identifies phase boundaries and hotspots.
4. **Later Python Slice - Residual `stats_module.py` Import Cleanup**
   - Continue shrinking `stats_module.py` once audit and SQL instrumentation are stable.
5. **Later SQL Cleanup - Legacy PreKvK Phase Object Retirement**
   - `dbo.PreKvk_Phases` retirement remains separate after live dependency review.
6. **Later SQL Cleanup - `dbo.vAllianceActivity_WeeklyCumulative` Review**
   - Confirm downstream/manual usage before correcting or retiring the view.
7. **Later Python Slice - Inventory View Orchestration Extraction**
   - Inventory lifecycle coordination cleanup remains separate now that Slice 8 audit adoption is
     delivered and smoke tested.

## 9. Required Reading

Before audit work, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/deferred_optimisations.md`
- archived Task C Slice 2 through Slice 8 task packs
- `docs/task_packs/archive/DL_bot Upload Routing - Phase 4 KVK_ALL Upload Route Starter.md`
- `docs/task_packs/archive/DL_bot Upload Routing - Phase 5C Rally Forts Route Starter.md`

SQL references:

- generic import audit tables and writer procedures
- `C:\K98-bot-SQL-Server\sql_schema\KVK.KVK_Scan.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\KVK.KVK_AllPlayers_Stage.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\KVK.KVK_AllPlayers_Raw.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\KVK.KVK_Ingest_Diagnostics.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\KVK.KVK_Ingest_Negatives.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\KVK.sp_KVK_AllPlayers_Ingest.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.IngestionLog.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.stg_RallyDaily.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.stg_RallyAllTime.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.cur_RallyDaily.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.cur_RallyTotals_Base.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.sp_Import_Rally_Daily.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.sp_Import_Rally_AllTime.StoredProcedure.sql`

## 10. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Confirm route/importer/DAL/SQL boundaries before implementation. |
| `k98-sql-validation` | use | Validate KVK/Rally SQL objects, identity/correlation candidates, and writer compatibility. |
| `k98-test-selection` | use | Required before validation command selection. |
| `k98-deferred-optimisation-capture` | use | Required to update the remaining import-audit backlog after delivery. |
| `k98-pr-review` | use before PR handoff | Confirm architecture, SQL alignment, tests, deferred tracking, and promotion safety. |
| `k98-promotion-check` | use before production promotion | Required if SQL/config/deployment sequencing is involved. |
| `codex-security:security-diff-scan` | use or justify skip | File upload handling, SQL/data access, user-controlled workbook parsing, local file staging, and audit persistence are security-sensitive surfaces. |

## 11. Files And SQL Objects To Audit

Bot repo:

- `upload_routes/kvk_all_route.py`
- `kvk_all_importer.py`
- `kvk/services/kvk_all_import_service.py`
- `kvk/dal/kvk_all_import_dal.py`
- `kvk/schemas/kvk_all_schema.py`
- `upload_routes/rally_forts_route.py`
- `forts_ingest.py`
- `services/import_audit_service.py`
- `stats/dal/import_audit_dal.py`
- `tests/test_kvk_all_upload_route.py`
- `tests/test_kvk_all_importer.py`
- `tests/test_kvk_all_import_service.py`
- `tests/test_kvk_all_import_dal.py`
- `tests/test_kvk_all_schema.py`
- `tests/test_kvk_all_recompute_sql_contract.py`
- `tests/test_rally_forts_upload_route.py`
- `tests/test_import_audit_service.py`
- `tests/test_import_audit_dal.py`

SQL repo:

- generic import audit tables and writer procedures
- KVK_ALL scan/stage/raw/diagnostic/negative/recompute objects
- Rally staging/current/history/log/procedure objects used by `forts_ingest.py`

## 12. Required First Response

Use this shape and stop for approval before code or SQL changes:

```markdown
**Scope Summary**
<KVK_ALL and Rally Forts generic audit adoption objective, plus explicit route-extraction already complete / generic-audit not complete distinction>

**Current Route State**
<KVK_ALL route/importer/DAL/SQL flow and Rally route/importer/SQL flow>

**SQL Position**
<validated KVK.KVK_Scan, KVK.KVK_Ingest_Diagnostics, dbo.IngestionLog, and any ambiguous correlation decisions>

**Audit Taxonomy Proposal**
<ImportKind, SourceType, phase names, counters, details JSON, terminal status policy for both routes>

**Implementation Proposal**
<files to change, service/DAL ownership, best-effort behavior, route/importer contract preservation, split-if-needed decision>

**Remaining Slice Map**
<UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup, PreKvK legacy SQL cleanup, weekly cumulative view cleanup, inventory orchestration follow-up>

**Validation Plan**
<SQL validation, focused tests, broad checks, smoke tests, Codex Security review>

**Open Questions / Approval Needed**
<specific decisions for Chris>
```

## 13. Validation Plan

Baseline commands:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

Likely focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_all_upload_route.py tests\test_kvk_all_importer.py tests\test_kvk_all_import_service.py tests\test_kvk_all_import_dal.py tests\test_kvk_all_schema.py tests\test_kvk_all_recompute_sql_contract.py tests\test_rally_forts_upload_route.py tests\test_import_audit_service.py tests\test_import_audit_dal.py
```

Broad checks when shared audit helpers or upload behavior are touched:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

SQL validation if SQL assumptions are changed:

```powershell
cd C:\K98-bot-SQL-Server
.\deploy\Validate-SqlRepo.ps1
```

Manual smoke after deployment:

- Upload a valid KVK_ALL workbook where operationally safe and confirm existing success/warning
  embed, Google Sheet button, auto-export scheduling, and KVK output behavior remain unchanged.
- Confirm one completed `kvk_all` audit batch correlated to `KVK.KVK_Scan` with
  `ExternalBatchId=<KVK_NO>:<ScanID>`.
- Upload a valid Rally daily or all-time workbook where operationally safe and confirm existing
  final embed, SQL ingest behavior, and log-backup scheduling remain unchanged.
- Confirm one completed `rally_forts` audit batch correlated to `dbo.IngestionLog` only if the
  implementation safely exposes or looks up `IngestionID`; otherwise confirm the uncorrelated
  decision is documented.
- Cover invalid workbook, rejected timestamp, duplicate Rally filename, unsafe filename, and
  importer exceptions in tests unless an operator explicitly approves production negative-path
  smoke.

## 14. Acceptance Criteria

- [ ] KVK_ALL and Rally Forts route/importer/DAL/SQL state surfaces are audited before
  implementation.
- [ ] The first response clearly confirms route extraction is complete but generic durable audit
  adoption is not complete for KVK_ALL or Rally Forts.
- [ ] SQL object names, columns, statuses, constraints, indexes, and domain correlation candidates
  are validated against the SQL repo.
- [ ] First response stops for approval before code or SQL changes.
- [ ] Generic audit wiring is implemented only after approval.
- [ ] Existing route UX, file handling, importer contracts, SQL procedure/table behavior, embeds,
  exports/recompute/log-backup scheduling, telemetry/logging, and user-facing behavior are
  preserved.
- [ ] Audit writes remain best-effort.
- [ ] Batch-level counters use the normalized Slice 3A terminal writer contract where applicable.
- [ ] Focused KVK_ALL/Rally/import-audit tests pass.
- [ ] Remaining SQL/Python cleanup items remain documented.
