# Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 5 PreKvK Import Audit Adoption

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task C Slice 5 - PreKvK Import Audit Adoption`
- Date: `2026-06-29`
- Owner/context: `Chris Watts / K98 bot import architecture`
- Task type: `deferred optimisation batch | import audit adoption | PreKvK ingestion`
- Depends on:
  - Task A, archived at `docs/task_packs/archive/Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md`
  - Task B, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md`
  - Task C Slice 1, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Import Architecture and Service DAL Wrappers.md`
  - Task C Slice 2, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 2 Durable Batch Audit Foundation.md`
  - Task C Slice 3, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3 Non-Fallback Audit Adoption.md`
  - Task C Slice 3A, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3A Import Audit Batch Counter Normalization.md`
  - Task C Slice 4, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 4 Honor Import Audit Adoption.md`
- One-pass approved: `no`
- Status: `delivered and archived after production smoke completion`

## 2. Objective

Adopt the generic durable import audit model for the PreKvK upload/import path after Honor adoption
was delivered and smoke tested in Task C Slice 4.

This slice must start with audit/scope only. Confirm the current PreKvK route, workbook parser,
importer, SQL domain tables/history objects, ranking refresh, telemetry, duplicate/rejection
semantics, and tests before proposing implementation. The expected implementation is a small,
behavior-preserving PreKvK audit wiring slice that reuses the existing generic audit DAL/service
wrappers and SQL-owned audit writer procedures.

## 2A. Delivered Closeout

Task C Slice 5 was delivered in mirror PR #186 and production PR #494. It adopted generic durable
audit for the PreKvK upload/import path only, added `services/prekvk_import_audit_service.py`,
extended `prekvk_importer.py` with opt-in structured metadata while preserving the default
`(ok, note, rows)` contract, and wired `upload_routes/prekvk_route.py` through
`prekvk_xlsx_parse`, `prekvk_sql_ingest`, and `prekvk_post_import_refresh` phases.

Accepted imports correlate to `dbo.PreKvk_Scan` as
`ExternalBatchId = <KVK_NO>:<ScanID>`. Duplicate, rejected, and failed outcomes correlate to
`dbo.PreKvk_ImportHistory.HistoryID` when the existing diagnostics hook returns it. A review
follow-up changed post-import refresh failures to use `fail_audit_batch` so batch-level
`ErrorType` / `ErrorText` are preserved.

No SQL schema changes, command changes, historical backfill, PreKvK import-history replacement, or
legacy PreKvK SQL cleanup were made.

Production smoke testing on 2026-06-29 confirmed:

- Accepted batch 8 completed with `ImportKind=prekvk`, `SourceType=discord_upload_xlsx`,
  `ExternalBatchTable=dbo.PreKvk_Scan`, `ExternalBatchId=15:1095`, `RowsInSource=1`,
  `RowsStaged=1`, `RowsWritten=1`, `RowsSkipped=0`, and completed parse, ingest, and refresh
  phases.
- Duplicate batch 9 completed with `Status=duplicate`,
  `ExternalBatchTable=dbo.PreKvk_ImportHistory`, `ExternalBatchId=17`, `RowsInSource=1`,
  `RowsWritten=0`, `RowsSkipped=1`, completed parse phase, and duplicate ingest phase.
- Rejected batch 10 failed with `ExternalBatchTable=dbo.PreKvk_ImportHistory`,
  `ExternalBatchId=18`, `ErrorType=MissingColumns`, `RowsInSource=0`, and failed parse phase.

Automated validation included focused PreKvK/import-audit tests, full pytest, architecture and
deferred validators, selected-test review, smoke imports, command registration, Pyright, whitespace
checks, pytest log-noise validation, and Codex Security diff scan with zero findings.

## 3. Delivered Baseline

Confirmed delivered import baseline:

- Full fallback imports work with `Credit`.
- Full fallback imports work with `Conduct Score`.
- Interim auto partial fallback imports work from the monitored Discord folder.
- Interim auto partial fallback preserves non-ASCII governor names.
- Partial fallback rows overlay the latest full `KingdomScanData4` snapshot and preserve absent fields.
- Location import remains unchanged for player-visible behavior.
- `shield_time_left` is stored as `ShieldEndsAtUnix` / `ShieldEndsAtUtc` and visible on
  `v_PlayerProfile`.
- Task B uses raw text SQL staging plus explicit typed conversion for the Unicode-preserving
  fallback import path.
- Task C Slice 1 extracted fallback import orchestration into service/DAL wrappers while
  preserving behavior.
- Task C Slice 2 added `dbo.ImportAuditBatch`, `dbo.ImportAuditPhase`, SQL-owned audit writer
  procedures, bot audit DAL/service wrappers, and fallback-first audit wiring correlated to
  `dbo.FallbackImportBatchControl`.
- Task C Slice 3 mapped current non-fallback import state surfaces and wired player-location
  generic audit first.
- Task C Slice 3A added terminal writer support for optional `RowsInSource`, threaded it through
  bot wrappers, and smoke tested fallback/player-location normalization on 2026-06-29.
- Task C Slice 4 added Honor generic audit adoption and smoke tested Honor audit batch 7 on
  2026-06-29 with `RowsInSource=562`, `RowsStaged=562`, `RowsWritten=562`, `RowsSkipped=0`,
  `ExternalBatchTable=dbo.KVK_Honor_Scan`, and `ExternalBatchId=15:92`.

Current PreKvK baseline:

- PreKvK uploads are accepted from the configured PreKvK upload channel.
- Valid filenames match `1198_prekvk.xlsx` or `PreKvK_Rankings_*.xlsx`.
- `upload_routes/prekvk_route.py` handles message-route orchestration and user-facing embed
  output.
- `prekvk_importer.py` parses old and new workbook layouts, validates required columns, rejects
  duplicate governor IDs before DB writes, deduplicates already imported files by hash, writes
  `dbo.PreKvk_Scan` and `dbo.PreKvk_Scores` for accepted imports, and records
  `dbo.PreKvk_ImportHistory` best-effort outcome rows.
- `prekvk/diagnostics_service.py` and `prekvk/dal/import_history_dal.py` own the existing PreKvK
  domain import-history model used by `/prekvk import_history`.
- Ranking/report surfaces read from PreKvK SQL tables/views and must remain unchanged.

## 4. Source Deferred Item Promoted Into This Pack

### Deferred Optimisation
- Area: `upload_routes/prekvk_route.py`, `prekvk_importer.py`, `prekvk/diagnostics_service.py`, `prekvk/dal/import_history_dal.py`, `services/import_audit_service.py`, `stats/dal/import_audit_dal.py`, SQL repo PreKvK objects
- Type: consistency
- Description: Task C Slice 3 mapped PreKvK as a remaining non-fallback import family, Task C Slice 3A normalized the generic audit batch source-row counter, and Task C Slice 4 delivered Honor audit adoption. PreKvK still does not create generic `ImportAuditBatch` / `ImportAuditPhase` rows, so operators must infer PreKvK import lifecycle from route embeds, telemetry, `dbo.PreKvk_ImportHistory`, and domain tables rather than the shared durable audit model.
- Suggested Fix: Adopt generic audit for PreKvK only, using service/DAL-owned best-effort audit wrappers. Validate whether accepted imports should correlate to `dbo.PreKvk_Scan` as `ExternalBatchId = <KVK_NO>:<ScanID>`, and whether duplicate/rejected/failed outcomes should also correlate to `dbo.PreKvk_ImportHistory.HistoryID` if that can be propagated without changing user-facing behavior. Preserve upload route behavior, importer transaction semantics, duplicate/rejection semantics, existing PreKvK import-history behavior, ranking/report refresh, telemetry, user-facing embeds, and output data.
- Impact: medium
- Risk: medium
- Dependencies: Task C Slice 2 audit foundation; Task C Slice 3 non-fallback surface map; Task C Slice 3A `RowsInSource` terminal writer normalization; Task C Slice 4 Honor audit adoption; SQL validation against `C:\K98-bot-SQL-Server`.

## 5. Proposed Implementation Boundary

### In Scope

- Audit current PreKvK state surfaces:
  - upload route and filename handling;
  - current-KVK metadata lookup;
  - SQL headroom preflight;
  - workbook parse and normalization;
  - duplicate-governor rejection;
  - duplicate-file skip;
  - SQL ingest transaction and returned `(ok, note, rows)` route contract;
  - `dbo.PreKvk_Scan` / `dbo.PreKvk_Scores` accepted-import domain id;
  - `dbo.PreKvk_ImportHistory` accepted, duplicate, rejected, and failed outcome rows;
  - route success, skipped, and failure embeds;
  - stats embed refresh behavior;
  - telemetry/logging;
  - existing PreKvK tests.
- Validate SQL PreKvK objects against `C:\K98-bot-SQL-Server`, including:
  - `dbo.PreKvk_Scan`
  - `dbo.PreKvk_Scores`
  - `dbo.PreKvk_ImportHistory`
  - `dbo.PreKvk_Scores_Ranked`
  - `dbo.PreKvk_Phases` legacy/retirement status
  - `dbo.sp_Build_Prekvk_And_Honor_Rankings`
  - PreKvK reporting views such as `dbo.v_PreKvk13_All`, `dbo.v_PreKvk13_Overall`,
    `dbo.v_PreKvk13_Phase1`, `dbo.v_PreKvk13_Phase2`, and `dbo.v_PreKvk13_Phase3`
- Reuse existing generic audit objects and bot wrappers from Task C Slice 2 / Slice 3A.
- Propose PreKvK audit taxonomy:
  - likely `ImportKind = prekvk`;
  - likely `SourceType = discord_upload_xlsx`;
  - likely phases: `prekvk_xlsx_parse`, `prekvk_sql_ingest`, `prekvk_post_import_refresh`;
  - accepted-import external correlation candidate:
    `ExternalBatchTable = dbo.PreKvk_Scan`, `ExternalBatchId = <KVK_NO>:<ScanID>`;
  - duplicate/rejected/failed correlation candidate:
    `ExternalBatchTable = dbo.PreKvk_ImportHistory`, `ExternalBatchId = <HistoryID>`, only if
    SQL/code validation confirms this can be propagated safely.
- Implement PreKvK generic audit wiring only after approval.
- Preserve existing PreKvK route, importer, duplicate/rejection behavior, import-history behavior,
  ranking/report refresh, embed, file, SQL, telemetry, and player-visible behavior.
- Keep audit writes best-effort.
- Update tests and deferred documentation after delivery.

### Out Of Scope

- Discord command changes, including `/prekvk import_history`.
- Upload route UX or embed text changes.
- Queue UX/embed behavior changes.
- Fallback, player-location, Honor, weekly activity, MGE, or inventory behavior changes.
- Wiring weekly activity, MGE, or inventory generic audit adoption.
- Changing PreKvK ranking/report semantics, output files, channel gating, or import-history command
  output.
- Replacing `dbo.PreKvk_ImportHistory` with generic audit history.
- Retiring `dbo.PreKvk_Phases` or other legacy PreKvK SQL objects.
- New SQL schema tables or new generic audit objects unless audit finds a blocker and approval is
  given.
- Adding the `dbo.UPDATE_ALL2` wrapper/audit-output layer.
- Splitting `dbo.IMPORT_STAGING_PROC`.
- Decomposing or replacing `dbo.UPDATE_ALL2`.
- Historical production data backfill.
- Operator UI/reporting dashboards for audit history.

## 6. Remaining Import Audit Slices To Preserve

Do not lose these later slices:

1. **Task C Slice 6 - Weekly Activity Import Audit Adoption**
   - Validate `dbo.AllianceActivitySnapshotHeader.SnapshotId` or current SQL equivalent.
   - Preserve weekly activity output and route behavior.
2. **Task C Slice 7 - MGE Results Import Audit Adoption**
   - Validate `dbo.MGE_ResultImports.ImportId` or current SQL equivalent.
   - Preserve event/result overwrite semantics and MGE DAL ownership.
3. **Task C Slice 8 - Inventory Generic Audit Correlation Adoption**
   - Validate `dbo.InventoryImportBatch.ImportBatchID` or current SQL equivalent.
   - Add generic audit correlation without replacing inventory's domain audit/history model.
4. **Later SQL Slice - `dbo.UPDATE_ALL2` Wrapper/Audit Outputs**
   - Add non-invasive audit output around downstream rebuild phases before attempting procedure
     decomposition.
5. **Later SQL Slice - `dbo.IMPORT_STAGING_PROC` Responsibility Split**
   - Split only after durable audit evidence and compatibility wrappers are stable.
6. **Later SQL Slice - `dbo.UPDATE_ALL2` Decomposition**
   - Prepare only after wrapper/audit-output evidence identifies phase boundaries and hotspots.
7. **Later Python Slice - Residual `stats_module.py` Import Cleanup**
   - Continue shrinking `stats_module.py` into service/DAL boundaries once audit and SQL
     instrumentation are stable.
8. **Later SQL Cleanup - Legacy PreKvK Phase Object Retirement**
   - `dbo.PreKvk_Phases` retirement remains a separate SQL cleanup after live dependencies and
     production cycles are reviewed.

## 7. Required Reading

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
- `docs/reference/archive/deferred_optimisations_resolved.md`
- archived Task C Slice 2, Slice 3, Slice 3A, and Slice 4 task packs

SQL references:

- `C:\K98-bot-SQL-Server\sql_schema\dbo.ImportAuditBatch.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.ImportAuditPhase.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_StartBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_RecordPhase.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_CompleteBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_FailBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.PreKvk_Scan.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.PreKvk_Scores.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.PreKvk_ImportHistory.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.PreKvk_Scores_Ranked.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.sp_Build_Prekvk_And_Honor_Rankings.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\docs\SQL_PROMOTION_GUIDE.md`

## 8. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Confirm upload route/importer/service/DAL/SQL boundaries before implementation. |
| `k98-sql-validation` | use | Validate PreKvK SQL objects, import-history semantics, and generic audit writer compatibility. |
| `k98-test-selection` | use | Required before validation command selection. |
| `k98-deferred-optimisation-capture` | use | Required to update the remaining import-audit backlog after delivery. |
| `k98-pr-review` | use before PR handoff | Confirm architecture, SQL alignment, tests, deferred tracking, and promotion safety. |
| `k98-promotion-check` | use before production promotion | Required if SQL/config/deployment sequencing is involved. |
| `codex-security:security-diff-scan` | use or justify skip | SQL/data access, file upload handling, user-controlled workbook parsing, and audit persistence are security-sensitive surfaces. |

## 9. Files And SQL Objects To Audit

Bot repo:

- `upload_routes/prekvk_route.py`
- `prekvk_importer.py`
- `prekvk/diagnostics_service.py`
- `prekvk/dal/import_history_dal.py`
- `prekvk/dal/report_dal.py`
- `prekvk/report_service.py`
- `services/import_audit_service.py`
- `stats/dal/import_audit_dal.py`
- `tests/test_prekvk_upload_route.py`
- `tests/test_prekvk_importer.py`
- `tests/test_prekvk_diagnostics.py`
- `tests/test_import_audit_service.py`
- `tests/test_import_audit_dal.py`

SQL repo:

- generic import audit tables and writer procedures
- existing PreKvK tables, views, and ranking procedures used by the route/importer/reporting path

## 10. Required First Response

Use this shape and stop for approval before code or SQL changes:

```markdown
**Scope Summary**
<PreKvK-only generic audit adoption objective and explicit no-behavior-change boundary>

**Current PreKvK Import State**
<route, filename handling, current-KVK lookup, parse/normalize, duplicate/rejected/accepted outcomes, SQL ingest, import history, refresh/output, telemetry, tests>

**SQL Position**
<validated PreKvK objects, generic audit writer compatibility, accepted/duplicate/rejected/failure external correlation proposal>

**Audit Taxonomy Proposal**
<ImportKind, SourceType, phase names, counters, details JSON, terminal status policy>

**Implementation Proposal**
<files to change, service/DAL ownership, best-effort behavior, route contract preservation, rollback plan>

**Remaining Slice Map**
<weekly activity, MGE, inventory, UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup, PreKvK legacy SQL cleanup>

**Validation Plan**
<SQL validation, focused tests, broad checks, smoke tests, Codex Security review>

**Open Questions / Approval Needed**
<specific decisions for Chris>
```

## 11. Validation Plan

Baseline commands:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

Likely focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_prekvk_upload_route.py tests\test_prekvk_importer.py tests\test_prekvk_diagnostics.py tests\test_import_audit_service.py tests\test_import_audit_dal.py
```

Broad checks when shared audit helpers or upload behavior are touched:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

SQL validation if SQL objects or assumptions are changed:

```powershell
cd C:\K98-bot-SQL-Server
.\deploy\Validate-SqlRepo.ps1
```

Manual smoke after deployment:

- Upload a normal PreKvK workbook and confirm the existing imported success embed/output behavior
  remains unchanged.
- Confirm one completed `prekvk` audit batch with batch-level row counters, completed parse/SQL
  phases, and completed or failed refresh phase according to the terminal status policy.
- Confirm accepted-import correlation to the inserted PreKvK domain scan id.
- Upload a duplicate workbook only if operationally safe and confirm skipped/duplicate behavior
  remains unchanged while generic audit terminal status is recorded best-effort.
- Exercise or simulate invalid workbook/importer failure in tests rather than production, unless
  an operator explicitly approves a production negative-path smoke.

## 12. Acceptance Criteria

- [ ] PreKvK route/importer/history/SQL state surfaces are audited before implementation.
- [ ] SQL object names, columns, and domain batch/history ids are validated against the SQL repo.
- [ ] First response stops for approval before code or SQL changes.
- [ ] PreKvK generic audit wiring is implemented only after approval.
- [ ] Existing PreKvK route, file, parse, SQL ingest, duplicate/rejection, import-history, ranking/report refresh, telemetry, and embed behavior are preserved.
- [ ] Audit writes remain best-effort.
- [ ] Batch-level counters use the normalized Slice 3A terminal writer contract where applicable.
- [ ] Focused PreKvK/import-audit tests pass.
- [ ] Remaining import-audit slices and deferred SQL/Python cleanup items remain documented.
