# Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 4 Honor Import Audit Adoption

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task C Slice 4 - Honor Import Audit Adoption`
- Date: `2026-06-29`
- Owner/context: `Chris Watts / K98 bot import architecture`
- Task type: `deferred optimisation batch | import audit adoption | Honor ingestion`
- Depends on:
  - Task A, archived at `docs/task_packs/archive/Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md`
  - Task B, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md`
  - Task C Slice 1, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Import Architecture and Service DAL Wrappers.md`
  - Task C Slice 2, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 2 Durable Batch Audit Foundation.md`
  - Task C Slice 3, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3 Non-Fallback Audit Adoption.md`
  - Task C Slice 3A, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3A Import Audit Batch Counter Normalization.md`
- One-pass approved: `no`
- Status: `archived after Task C Slice 4 delivery`

## Delivery Summary

Task C Slice 4 was delivered in mirror PR #185 and production PR #493. It adopted the generic
durable import audit model for the KVK Honor upload/import path only, with no SQL schema changes
and no user-facing Honor route UX changes.

Delivered code:

- `services/honor_import_audit_service.py`
  - Added Honor-specific best-effort audit wrappers around the existing generic import audit
    service/DAL and SQL-owned writer procedures.
  - Added `HonorImportAuditContext`, Honor audit taxonomy constants, SHA-256 source hashing, phase
    helpers, and `dbo.KVK_Honor_Scan` external batch correlation.
  - Normalized audit duration handling so naive UTC and timezone-aware UTC timestamps are both
    accepted safely.
- `upload_routes/honor_route.py`
  - Wired the accepted Honor upload path through `honor_xlsx_parse`, `honor_sql_ingest`, and
    `honor_post_import_refresh` phases.
  - Correlated completed batches as `ExternalBatchTable = dbo.KVK_Honor_Scan` and
    `ExternalBatchId = <KVK_NO>:<ScanID>`.
  - Preserved upload route UX, success/error embeds, filename handling, importer transaction
    behavior, ranking refresh, telemetry, SQL outputs, and channel gating.
  - Fixed the narrow Honor stats-refresh call signature.
  - Added terminal audit fallback so unexpected post-ingest notification/scheduling errors do not
    leave an audit batch in `started` or `staged`.
- Tests:
  - Added `tests/test_honor_import_audit_service.py`.
  - Extended `tests/test_honor_upload_route.py` for audit lifecycle, terminal status behavior,
    test-mode details, refresh failure, ingest failure, post-ingest notification failure, and
    timestamp normalization.

Validation and review evidence:

- Focused Honor/import-audit tests passed during final review fixes.
- Full pytest passed after the final production-review fix: `2091 passed, 2 skipped`.
- Architecture validator, deferred validator, selected-test review, smoke imports, command
  registration, whitespace checks, and Codex Security diff scan completed.
- Codex Security scan `416fcfda-f8d9-45ec-bb13-3d63802e337f` completed with `0` reportable
  findings.
- Review comments from Codex and Copilot were addressed and resolved on mirror and production PRs.
- Production smoke testing on 2026-06-29 confirmed Honor audit batch 7 completed successfully:
  - `ImportKind = honor`
  - `SourceType = discord_upload_xlsx`
  - `ExternalBatchTable = dbo.KVK_Honor_Scan`
  - `ExternalBatchId = 15:92`
  - `Status = completed`
  - `RowsInSource = 562`
  - `RowsStaged = 562`
  - `RowsWritten = 562`
  - `RowsSkipped = 0`
  - phases `honor_xlsx_parse`, `honor_sql_ingest`, and `honor_post_import_refresh` completed
    with no errors.

Historical next slice:

- `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 5 PreKvK Import Audit Adoption.md`
- `docs/task_packs/archive/Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 5 PreKvK Import Audit Adoption.md`

Current active import follow-up:

- `docs/task_packs/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 6 Weekly Activity Import Audit Adoption.md`
- `docs/task_packs/Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 6 Weekly Activity Import Audit Adoption.md`

## 2. Objective

Adopt the generic durable import audit model for the KVK Honor upload/import path after Task C
Slice 3A normalized batch-level `RowsInSource` for already wired imports.

This slice should start with audit/scope only. Confirm the current Honor route, importer, SQL
objects, ranking refresh, telemetry, file handling, and user-facing notifications before proposing
implementation. The expected implementation is a small, behavior-preserving Honor audit wiring
slice that reuses the existing generic audit DAL/service wrappers and SQL-owned audit writer
procedures.

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
- Task C Slice 3 production smoke testing confirmed completed and skipped `player_location` audit
  batches.
- Task C Slice 3A added terminal writer support for optional `RowsInSource`, threaded it through
  bot wrappers, and smoke tested fallback/player-location normalization on 2026-06-29.

Current Honor baseline:

- Honor uploads are accepted from the configured Honor upload channel.
- Valid filenames match `1198_honor*.xlsx` with supported `TEST_`, `DEMO_`, or `SAMPLE_` prefixes.
- `upload_routes/honor_route.py` handles message-route orchestration and user-facing embed output.
- `honor_importer.py` parses the `honor` worksheet and ingests rows into SQL.
- SQL source of truth includes `dbo.KVK_Honor_Scan`, `dbo.KVK_Honor_AllPlayers_Raw`,
  `dbo.KVK_Honor_Ranked`, and Honor ranking views/procedures.
- Ranking refresh/output behavior must be preserved.

## 4. Source Deferred Item Promoted Into This Pack

### Deferred Optimisation
- Area: `upload_routes/honor_route.py`, `honor_importer.py`, `services/import_audit_service.py`, `stats/dal/import_audit_dal.py`, SQL repo Honor objects
- Type: consistency
- Description: Task C Slice 3 mapped Honor as a remaining non-fallback import family, and Task C Slice 3A normalized the generic audit batch source-row counter. Honor still does not create generic `ImportAuditBatch` / `ImportAuditPhase` rows, so operators must infer Honor import lifecycle from route embeds, telemetry, and domain tables rather than the shared durable audit model.
- Suggested Fix: Adopt generic audit for Honor only, using service/DAL-owned best-effort audit wrappers. Correlate completed batches to the SQL-validated Honor domain batch identifier, expected to be `ExternalBatchTable = dbo.KVK_Honor_Scan` and `ExternalBatchId = <KVK_NO>:<ScanID>` unless SQL validation finds a better stable id. Preserve upload route behavior, importer transaction semantics, ranking refresh, telemetry, user-facing embeds, and output data.
- Impact: medium
- Risk: medium
- Dependencies: Task C Slice 2 audit foundation; Task C Slice 3 non-fallback surface map; Task C Slice 3A `RowsInSource` terminal writer normalization; SQL validation against `C:\K98-bot-SQL-Server`.

## 5. Proposed Implementation Boundary

### In Scope

- Audit current Honor state surfaces:
  - upload route and filename handling;
  - workbook parse and row-count discovery;
  - SQL ingest transaction and returned `(KVK_NO, ScanID)` domain id;
  - route success/failure embeds and stats embed refresh behavior;
  - telemetry/logging;
  - existing Honor tests.
- Validate SQL Honor objects against `C:\K98-bot-SQL-Server`, including:
  - `dbo.KVK_Honor_Scan`
  - `dbo.KVK_Honor_AllPlayers_Raw`
  - `dbo.KVK_Honor_Ranked`
  - `dbo.v_KVK_Honor_Latest`
  - `dbo.v_KVK_Honor_TopLatest`
  - `dbo.sp_Build_Prekvk_And_Honor_Rankings`
- Reuse existing generic audit objects and bot wrappers from Task C Slice 2 / Slice 3A.
- Propose Honor audit taxonomy:
  - likely `ImportKind = honor`;
  - likely `SourceType = discord_upload_xlsx`;
  - likely phases: `honor_xlsx_parse`, `honor_sql_ingest`, `honor_post_import_refresh`;
  - expected external correlation: `ExternalBatchTable = dbo.KVK_Honor_Scan`,
    `ExternalBatchId = <KVK_NO>:<ScanID>`.
- Implement Honor generic audit wiring only after approval.
- Preserve existing Honor route, importer, ranking refresh, embed, file, SQL, telemetry, and
  player-visible behavior.
- Keep audit writes best-effort.
- Update tests and deferred documentation after delivery.

### Out Of Scope

- Discord command changes.
- Upload route UX or embed text changes.
- Queue UX/embed behavior changes.
- Fallback, player-location, PreKvK, weekly activity, MGE, or inventory behavior changes.
- Wiring PreKvK, weekly activity, MGE, or inventory generic audit adoption.
- Changing inventory's existing domain audit/history model.
- New SQL schema tables or new generic audit objects unless audit finds a blocker and approval is
  given.
- Changing Honor ranking semantics, output files, or channel gating.
- Adding the `dbo.UPDATE_ALL2` wrapper/audit-output layer.
- Splitting `dbo.IMPORT_STAGING_PROC`.
- Decomposing or replacing `dbo.UPDATE_ALL2`.
- Historical production data backfill.
- Operator UI/reporting dashboards for audit history.

## 6. Remaining Import Audit Slices To Preserve

Do not lose these later slices:

1. **Task C Slice 5 - PreKvK Import Audit Adoption**
   - Validate `dbo.PreKvk_Scan` / `dbo.PreKvk_ImportHistory` or current SQL equivalents.
   - Preserve PreKvK report/ranking output and existing history semantics.
2. **Task C Slice 6 - Weekly Activity Import Audit Adoption**
   - Validate `dbo.AllianceActivitySnapshotHeader.SnapshotId` or current SQL equivalent.
   - Preserve weekly activity output and route behavior.
3. **Task C Slice 7 - MGE Results Import Audit Adoption**
   - Validate `dbo.MGE_ResultImports.ImportId` or current SQL equivalent.
   - Preserve event/result overwrite semantics and MGE DAL ownership.
4. **Task C Slice 8 - Inventory Generic Audit Correlation Adoption**
   - Validate `dbo.InventoryImportBatch.ImportBatchID` or current SQL equivalent.
   - Add generic audit correlation without replacing inventory's domain audit/history model.
5. **Later SQL Slice - `dbo.UPDATE_ALL2` Wrapper/Audit Outputs**
   - Add non-invasive audit output around downstream rebuild phases before attempting procedure
     decomposition.
6. **Later SQL Slice - `dbo.IMPORT_STAGING_PROC` Responsibility Split**
   - Split only after durable audit evidence and compatibility wrappers are stable.
7. **Later SQL Slice - `dbo.UPDATE_ALL2` Decomposition**
   - Prepare only after wrapper/audit-output evidence identifies phase boundaries and hotspots.
8. **Later Python Slice - Residual `stats_module.py` Import Cleanup**
   - Continue shrinking `stats_module.py` into service/DAL boundaries once audit and SQL
     instrumentation are stable.

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
- `docs/reference/honor_scan.md`
- archived Task C Slice 2, Slice 3, and Slice 3A task packs

SQL references:

- `C:\K98-bot-SQL-Server\sql_schema\dbo.ImportAuditBatch.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.ImportAuditPhase.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_StartBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_RecordPhase.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_CompleteBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_FailBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.KVK_Honor_Scan.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.KVK_Honor_AllPlayers_Raw.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.KVK_Honor_Ranked.Table.sql`
- `C:\K98-bot-SQL-Server\docs\SQL_PROMOTION_GUIDE.md`

## 8. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Confirm upload route/importer/service/DAL/SQL boundaries before implementation. |
| `k98-sql-validation` | use | Validate Honor SQL objects and generic audit writer compatibility. |
| `k98-test-selection` | use | Required before validation command selection. |
| `k98-deferred-optimisation-capture` | use | Required to update remaining import-audit backlog after delivery. |
| `k98-pr-review` | use before PR handoff | Confirm architecture, SQL alignment, tests, deferred tracking, and promotion safety. |
| `k98-promotion-check` | use before production promotion | Required if SQL/config/deployment sequencing is involved. |
| `codex-security:security-diff-scan` | use or justify skip | SQL/data access, file upload handling, user-controlled workbook parsing, and audit persistence are security-sensitive surfaces. |

## 9. Files And SQL Objects To Audit

Bot repo:

- `upload_routes/honor_route.py`
- `honor_importer.py`
- `services/import_audit_service.py`
- `stats/dal/import_audit_dal.py`
- `tests/test_honor_upload_route.py`
- `tests/test_honor_importer.py`
- `tests/test_import_audit_service.py`
- `tests/test_import_audit_dal.py`
- `docs/reference/honor_scan.md`

SQL repo:

- generic import audit tables and writer procedures
- existing Honor tables, views, and ranking procedures used by the route/importer/reporting path

## 10. Required First Response

Use this shape and stop for approval before code or SQL changes:

```markdown
**Scope Summary**
<Honor-only generic audit adoption objective and explicit no-behavior-change boundary>

**Current Honor Import State**
<route, filename handling, parse, SQL ingest, returned domain ids, refresh/output, telemetry, tests>

**SQL Position**
<validated Honor objects, generic audit writer compatibility, external batch correlation proposal>

**Audit Taxonomy Proposal**
<ImportKind, SourceType, phase names, counters, details JSON, terminal status policy>

**Implementation Proposal**
<files to change, service/DAL ownership, best-effort behavior, rollback plan>

**Remaining Slice Map**
<PreKvK, weekly, MGE, inventory, UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, stats_module cleanup>

**Validation Plan**
<SQL validation, focused tests, broad checks, smoke tests, security review>

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
.\.venv\Scripts\python.exe -m pytest -q tests\test_import_audit_service.py tests\test_import_audit_dal.py tests\test_honor_upload_route.py tests\test_honor_importer.py
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

- Upload a normal Honor workbook and confirm the existing success embed/output behavior remains
  unchanged.
- Confirm one completed `honor` audit batch with `RowsInSource`, `RowsStaged`/`RowsWritten` as
  approved by the implementation, and completed parse/SQL/refresh phases.
- Confirm the audit batch correlates to the inserted Honor domain batch id.
- Exercise or simulate parse/ingest failure and confirm existing error behavior remains unchanged
  while audit terminal status is recorded best-effort.

## 12. Acceptance Criteria

- [ ] Honor route/importer/SQL state surfaces are audited before implementation.
- [ ] SQL object names, columns, and domain batch ids are validated against the SQL repo.
- [ ] First response stops for approval before code or SQL changes.
- [ ] Honor generic audit wiring is implemented only after approval.
- [ ] Existing Honor route, file, parse, SQL ingest, ranking refresh, telemetry, and embed behavior are preserved.
- [ ] Audit writes remain best-effort.
- [ ] Batch-level counters use the normalized Slice 3A terminal writer contract where applicable.
- [ ] Focused Honor/import-audit tests pass.
- [ ] Remaining import-audit slices and deferred SQL/Python cleanup items remain documented.
