# Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 6 Weekly Activity Import Audit Adoption

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task C Slice 6 - Weekly Activity Import Audit Adoption`
- Date: `2026-06-29`
- Owner/context: `Chris Watts / K98 bot import architecture`
- Task type: `deferred optimisation batch | import audit adoption | weekly activity ingestion`
- Depends on:
  - Task A, archived at `docs/task_packs/archive/Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md`
  - Task B, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md`
  - Task C Slice 1, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Import Architecture and Service DAL Wrappers.md`
  - Task C Slice 2, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 2 Durable Batch Audit Foundation.md`
  - Task C Slice 3, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3 Non-Fallback Audit Adoption.md`
  - Task C Slice 3A, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3A Import Audit Batch Counter Normalization.md`
  - Task C Slice 4, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 4 Honor Import Audit Adoption.md`
  - Task C Slice 5, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 5 PreKvK Import Audit Adoption.md`
- One-pass approved: `no`
- Status: `active task pack, starts with audit/scope and SQL implementation-boundary confirmation`

## 2. Objective

Adopt the generic durable import audit model for the weekly alliance activity upload/import path
after PreKvK adoption was delivered and smoke tested in Task C Slice 5.

This slice must start with audit/scope only. Confirm the current weekly activity route, parser,
importer transaction, SQL snapshot/delta/daily objects, duplicate semantics, output embeds,
telemetry/logging, and tests before proposing implementation. The expected implementation is a
small, behavior-preserving weekly activity audit wiring slice that reuses the existing generic
audit DAL/service wrappers and SQL-owned audit writer procedures.

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
  2026-06-29.
- Task C Slice 5 added PreKvK generic audit adoption and smoke tested accepted batch 8, duplicate
  batch 9, and rejected batch 10 on 2026-06-29.

Current weekly activity baseline:

- Weekly activity uploads are accepted from the configured activity upload channel.
- Valid filenames currently end with `1198_alliance_activity.xlsx`.
- `upload_routes/weekly_activity_route.py` handles message-route orchestration, SQL preflight,
  offload dispatch, duplicate/success/error embeds, notify-channel fallback, and best-effort
  log-backup scheduling.
- `weekly_activity_importer.py` parses the workbook, validates required logical columns, writes
  `dbo.AllianceActivitySnapshotHeader`, `dbo.AllianceActivitySnapshotRow`,
  `dbo.AllianceActivityDelta`, and `dbo.AllianceActivityDaily`, and returns `(snapshot_id,
  delta_row_count)`.
- Duplicate files for the same week return `(0, 0)` and produce the existing duplicate/skipped
  embed.
- The importer owns a single transaction and rolls back on exceptions.
- Focused route tests live in `tests/test_weekly_activity_upload_route.py`.
- `docs/reference/weekly_activity_importer.md` documents the current domain contract.

## 4. Source Deferred Item Promoted Into This Pack

### Deferred Optimisation
- Area: `upload_routes/weekly_activity_route.py`, `weekly_activity_importer.py`, `docs/reference/weekly_activity_importer.md`, `services/import_audit_service.py`, `stats/dal/import_audit_dal.py`, SQL repo weekly activity objects
- Type: consistency
- Description: Task C Slice 3 mapped weekly activity as a remaining non-fallback import family, Task C Slice 3A normalized the generic audit batch source-row counter, Task C Slice 4 delivered Honor audit adoption, and Task C Slice 5 delivered PreKvK audit adoption. Weekly activity still does not create generic `ImportAuditBatch` / `ImportAuditPhase` rows, so operators must infer lifecycle from route embeds, logs, and the weekly activity SQL tables rather than the shared durable audit model.
- Suggested Fix: Adopt generic audit for weekly activity only, using service/DAL-owned best-effort audit wrappers. Validate whether accepted imports should correlate to `dbo.AllianceActivitySnapshotHeader` as `ExternalBatchId = <SnapshotId>`, and whether duplicate/failed outcomes have a stable domain correlation candidate or should remain uncorrelated when no snapshot row exists. Preserve upload route behavior, importer transaction semantics, duplicate semantics, weekly activity output data, embeds, telemetry/logging, and SQL table behavior.
- Impact: medium
- Risk: medium
- Dependencies: Task C Slice 2 audit foundation; Task C Slice 3 non-fallback surface map; Task C Slice 3A `RowsInSource` terminal writer normalization; Task C Slice 4 Honor audit adoption; Task C Slice 5 PreKvK audit adoption; SQL validation against `C:\K98-bot-SQL-Server`.

## 5. Proposed Implementation Boundary

### In Scope

- Audit current weekly activity state surfaces:
  - upload route and filename handling;
  - SQL headroom preflight;
  - workbook read and offload dispatch;
  - parser required-column validation;
  - duplicate-file/week skip;
  - SQL ingest transaction and returned `(snapshot_id, row_count)` route contract;
  - accepted snapshot id and row/delta/daily table writes;
  - route success, skipped, and failure embeds;
  - notify-channel fallback;
  - best-effort log-backup scheduling;
  - telemetry/logging;
  - existing weekly activity tests.
- Validate SQL weekly activity objects against `C:\K98-bot-SQL-Server`, including:
  - `dbo.AllianceActivitySnapshotHeader`
  - `dbo.AllianceActivitySnapshotRow`
  - `dbo.AllianceActivityDelta`
  - `dbo.AllianceActivityDaily`
  - weekly activity reporting views such as `dbo.vAllianceActivitySnapshots`,
    `dbo.vAllianceActivity_WeeklyDelta`, `dbo.vAllianceActivity_WeeklyCumulative`,
    `dbo.vDaily_AllianceActivity`, and `dbo.vWeekly_AllianceActivity`
- Reuse existing generic audit objects and bot wrappers from Task C Slice 2 / Slice 3A.
- Propose weekly activity audit taxonomy:
  - likely `ImportKind = weekly_activity`;
  - likely `SourceType = discord_upload_xlsx`;
  - likely phases: `weekly_activity_xlsx_parse`, `weekly_activity_sql_ingest`,
    `weekly_activity_post_import_backup`;
  - accepted-import external correlation candidate:
    `ExternalBatchTable = dbo.AllianceActivitySnapshotHeader`, `ExternalBatchId = <SnapshotId>`;
  - duplicate/failed correlation candidate:
    none unless SQL/code validation finds a stable pre-existing domain row that can be propagated
    without changing behavior.
- Implement weekly activity generic audit wiring only after approval.
- Preserve existing weekly activity route, file, parse, SQL ingest, duplicate behavior, embeds,
  telemetry/logging, output data, and user-facing behavior.
- Keep audit writes best-effort.
- Update tests and deferred documentation after delivery.

### Out Of Scope

- Discord command changes, including `/activity`.
- Upload route UX or embed text changes.
- Queue UX/embed behavior changes.
- Fallback, player-location, Honor, PreKvK, MGE, or inventory behavior changes.
- Wiring MGE or inventory generic audit adoption.
- Changing weekly activity SQL table schemas, reporting view semantics, output files, or channel
  gating.
- New SQL schema tables or new generic audit objects unless audit finds a blocker and approval is
  granted.
- Replacing weekly activity SQL tables or redesigning the importer.
- Adding the `dbo.UPDATE_ALL2` wrapper/audit-output layer.
- Splitting `dbo.IMPORT_STAGING_PROC`.
- Decomposing or replacing `dbo.UPDATE_ALL2`.
- Historical production data backfill.
- Operator UI/reporting dashboards for audit history.

## 6. Remaining Import Audit Slices To Preserve

Do not lose these later slices:

1. **Task C Slice 7 - MGE Results Import Audit Adoption**
   - Validate `dbo.MGE_ResultImports.ImportId` or the current SQL equivalent.
   - Preserve event/result overwrite semantics, MGE DAL ownership, MGE upload route UX, and result
     publish/refresh behavior.
2. **Task C Slice 8 - Inventory Generic Audit Correlation Adoption**
   - Validate `dbo.InventoryImportBatch.ImportBatchID` or the current SQL equivalent.
   - Add generic audit correlation without replacing inventory's domain audit/history model.
3. **Later SQL Slice - `dbo.UPDATE_ALL2` Wrapper/Audit Outputs**
   - Add non-invasive audit output around downstream rebuild phases before attempting procedure
     decomposition.
4. **Later SQL Slice - `dbo.IMPORT_STAGING_PROC` Responsibility Split**
   - Split only after durable audit evidence and compatibility wrappers are stable.
5. **Later SQL Slice - `dbo.UPDATE_ALL2` Decomposition**
   - Prepare only after wrapper/audit-output evidence identifies phase boundaries and hotspots.
6. **Later Python Slice - Residual `stats_module.py` Import Cleanup**
   - Continue shrinking `stats_module.py` into service/DAL boundaries once audit and SQL
     instrumentation are stable.
7. **Later SQL Cleanup - Legacy PreKvK Phase Object Retirement**
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
- `docs/reference/weekly_activity_importer.md`
- archived Task C Slice 2, Slice 3, Slice 3A, Slice 4, and Slice 5 task packs

SQL references:

- `C:\K98-bot-SQL-Server\sql_schema\dbo.ImportAuditBatch.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.ImportAuditPhase.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_StartBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_RecordPhase.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_CompleteBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_FailBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.AllianceActivitySnapshotHeader.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.AllianceActivitySnapshotRow.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.AllianceActivityDelta.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.AllianceActivityDaily.Table.sql`

## 8. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Confirm upload route/importer/service/DAL/SQL boundaries before implementation. |
| `k98-sql-validation` | use | Validate weekly activity SQL objects, duplicate semantics, and generic audit writer compatibility. |
| `k98-test-selection` | use | Required before validation command selection. |
| `k98-deferred-optimisation-capture` | use | Required to update the remaining import-audit backlog after delivery. |
| `k98-pr-review` | use before PR handoff | Confirm architecture, SQL alignment, tests, deferred tracking, and promotion safety. |
| `k98-promotion-check` | use before production promotion | Required if SQL/config/deployment sequencing is involved. |
| `codex-security:security-diff-scan` | use or justify skip | SQL/data access, file upload handling, user-controlled workbook parsing, and audit persistence are security-sensitive surfaces. |

## 9. Files And SQL Objects To Audit

Bot repo:

- `upload_routes/weekly_activity_route.py`
- `weekly_activity_importer.py`
- `docs/reference/weekly_activity_importer.md`
- `services/import_audit_service.py`
- `stats/dal/import_audit_dal.py`
- `tests/test_weekly_activity_upload_route.py`
- `tests/test_import_audit_service.py`
- `tests/test_import_audit_dal.py`

SQL repo:

- generic import audit tables and writer procedures
- existing weekly activity tables, indexes, and reporting views used by the route/importer/reporting path

## 10. Required First Response

Use this shape and stop for approval before code or SQL changes:

```markdown
**Scope Summary**
<weekly-activity-only generic audit adoption objective and explicit no-behavior-change boundary>

**Current Weekly Activity Import State**
<route, filename handling, SQL preflight, parse/normalize, duplicate/accepted/failed outcomes, SQL ingest, reporting surfaces, telemetry/logging, tests>

**SQL Position**
<validated weekly activity objects, generic audit writer compatibility, accepted/duplicate/failure external correlation proposal>

**Audit Taxonomy Proposal**
<ImportKind, SourceType, phase names, counters, details JSON, terminal status policy>

**Implementation Proposal**
<files to change, service/DAL ownership, best-effort behavior, route contract preservation, rollback plan>

**Remaining Slice Map**
<MGE, inventory, UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup, PreKvK legacy SQL cleanup>

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
.\.venv\Scripts\python.exe -m pytest -q tests\test_weekly_activity_upload_route.py tests\test_import_audit_service.py tests\test_import_audit_dal.py
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

- Upload a valid `1198_alliance_activity.xlsx` workbook and confirm the existing success embed
  remains unchanged.
- Confirm one completed `weekly_activity` audit batch with row counters and completed parse/SQL
  phases.
- Confirm accepted-import correlation to `dbo.AllianceActivitySnapshotHeader` and the inserted
  `SnapshotId`.
- Upload the same workbook again only if operationally safe and confirm duplicate/skipped behavior
  remains unchanged while generic audit terminal status is recorded best-effort.
- Exercise or simulate invalid workbook/importer failure in tests rather than production, unless
  an operator explicitly approves a production negative-path smoke.

## 12. Acceptance Criteria

- [ ] Weekly activity route/importer/SQL state surfaces are audited before implementation.
- [ ] SQL object names, columns, and domain batch ids are validated against the SQL repo.
- [ ] First response stops for approval before code or SQL changes.
- [ ] Weekly activity generic audit wiring is implemented only after approval.
- [ ] Existing weekly activity route, file, parse, SQL ingest, duplicate behavior, embeds,
  telemetry/logging, output tables, and user-facing behavior are preserved.
- [ ] Audit writes remain best-effort.
- [ ] Batch-level counters use the normalized Slice 3A terminal writer contract where applicable.
- [ ] Focused weekly activity/import-audit tests pass.
- [ ] Remaining import-audit slices and deferred SQL/Python cleanup items remain documented.
