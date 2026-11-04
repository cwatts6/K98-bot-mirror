# Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 7 MGE Results Import Audit Adoption

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task C Slice 7 - MGE Results Import Audit Adoption`
- Date: `2026-06-30`
- Owner/context: `Chris Watts / K98 bot import architecture`
- Task type: `deferred optimisation batch | import audit adoption | MGE results ingestion`
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
- One-pass approved: `no`
- Status: `completed and archived after mirror PR #188 / production PR #496`

## 2. Objective

Adopt the generic durable import audit model for the MGE results upload/import path only, after
weekly activity adoption was delivered and smoke tested in Task C Slice 6.

Delivered: Task C Slice 7 started with audit/scope and SQL implementation-boundary confirmation,
then implemented a behavior-preserving MGE results audit wiring slice that reused the existing
generic audit DAL/service wrappers and SQL-owned audit writer procedures. No SQL schema objects or
MGE reporting/import semantics were changed.

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
- Task C Slice 1 extracted fallback import orchestration into service/DAL wrappers while preserving
  behavior.
- Task C Slice 2 added `dbo.ImportAuditBatch`, `dbo.ImportAuditPhase`, SQL-owned audit writer
  procedures, bot audit DAL/service wrappers, and fallback-first audit wiring correlated to
  `dbo.FallbackImportBatchControl`.
- Task C Slice 3 mapped current non-fallback import state surfaces and wired player-location
  generic audit first.
- Task C Slice 3A added terminal writer support for optional `RowsInSource`, threaded it through
  bot wrappers, and smoke tested fallback/player-location normalization.
- Task C Slice 4 added Honor generic audit adoption and smoke tested Honor audit batch 7 on
  2026-06-29.
- Task C Slice 5 added PreKvK generic audit adoption and smoke tested accepted batch 8, duplicate
  batch 9, and rejected batch 10 on 2026-06-29.
- Task C Slice 6 added weekly activity generic audit adoption and smoke tested completed batches
  11 and 12 plus duplicate batch 13 on 2026-06-29.

Current MGE results baseline to validate:

- MGE results uploads are accepted from the configured MGE data channel by
  `upload_routes/mge_results_route.py`.
- Auto uploads expect an `.xlsx` file, currently described to users as
  `mge_rankings_kd####_YYYYMMDD.xlsx`.
- `mge/mge_results_import.py` owns auto/manual import orchestration and delegates SQL writes to
  `mge/dal/mge_results_dal.py`.
- Auto import targets the latest completed MGE event, rejects the same file hash for the event,
  and rejects auto overwrite when the event already has a completed import.
- Manual import requires a completed event and raises `OverwriteConfirmationRequired` unless
  force-overwrite is explicitly confirmed by the existing view path.
- Successful imports create a `dbo.MGE_ResultImports` row, replace `dbo.MGE_FinalResults` rows for
  the event, mark the domain import completed, and return `import_id`, `event_id`, `event_mode`,
  row count, and report payload.
- Importer failures after `create_import_batch` mark the domain import failed through
  `dbo.MGE_ResultImports`.
- Focused route/importer/view tests live in `tests/test_mge_results_upload_route.py`,
  `tests/test_mge_results_import.py`, `tests/test_mge_results_import_service.py`, and
  `tests/test_mge_results_overwrite_confirm_view.py`.

## 4. Source Deferred Item Promoted Into This Pack

### Deferred Optimisation
- Area: `upload_routes/mge_results_route.py`, `mge/mge_results_import.py`, `mge/dal/mge_results_dal.py`, `services/import_audit_service.py`, `stats/dal/import_audit_dal.py`, SQL repo MGE result objects
- Type: consistency
- Description: Task C Slice 3 mapped MGE as a remaining non-fallback import family, Task C Slice 3A normalized the generic audit batch source-row counter, and Slices 4 through 6 delivered Honor, PreKvK, and weekly activity generic audit adoption. MGE results still do not create generic `ImportAuditBatch` / `ImportAuditPhase` rows, so operators must infer lifecycle from route embeds, logs, `dbo.MGE_ResultImports`, and MGE final result tables rather than the shared durable audit model.
- Suggested Fix: Adopt generic audit for MGE results only, using service/DAL-owned best-effort audit wrappers. Validate accepted-import correlation to `dbo.MGE_ResultImports` with `ExternalBatchId = <ImportId>`, and validate whether duplicate pre-check failures or other failed outcomes have a stable pre-existing domain row or should remain uncorrelated when no `MGE_ResultImports` row exists. Preserve upload route behavior, importer transaction/order semantics, duplicate/overwrite behavior, report generation, embeds, telemetry/logging, and SQL table behavior.
- Impact: medium
- Risk: medium
- Dependencies: Task C Slice 2 audit foundation; Task C Slice 3 non-fallback surface map; Task C Slice 3A `RowsInSource` terminal writer normalization; Task C Slice 4 Honor audit adoption; Task C Slice 5 PreKvK audit adoption; Task C Slice 6 weekly activity audit adoption; SQL validation against `C:\K98-bot-SQL-Server`.

## 5. Proposed Implementation Boundary

### In Scope

- Audit current MGE results state surfaces:
  - upload route and filename handling;
  - SQL headroom preflight;
  - workbook read and offload dispatch;
  - parser required-column validation;
  - latest-completed-event auto targeting;
  - same-hash duplicate rejection and event-already-imported auto rejection;
  - manual overwrite confirmation path and force-overwrite importer contract;
  - `dbo.MGE_ResultImports` domain batch creation/completion/failure;
  - `dbo.MGE_FinalResults` replacement behavior;
  - open and controlled report payload generation;
  - route success/no-file/error embeds;
  - notify-channel fallback;
  - best-effort log-backup scheduling;
  - telemetry/logging;
  - existing MGE results tests.
- Validate SQL MGE result objects against `C:\K98-bot-SQL-Server`, including:
  - `dbo.MGE_ResultImports`
  - `dbo.MGE_FinalResults`
  - `dbo.MGE_Events`
  - MGE award/reporting tables or views touched by report generation.
- Reuse existing generic audit objects and bot wrappers from Task C Slice 2 / Slice 3A.
- Propose MGE results audit taxonomy:
  - likely `ImportKind = mge_results`;
  - likely `SourceType = discord_upload_xlsx`;
  - likely phases: `mge_results_xlsx_parse`, `mge_results_sql_ingest`,
    `mge_results_post_import_backup`;
  - accepted-import external correlation candidate:
    `ExternalBatchTable = dbo.MGE_ResultImports`, `ExternalBatchId = <ImportId>`;
  - failed-after-domain-import correlation candidate:
    `ExternalBatchTable = dbo.MGE_ResultImports`, `ExternalBatchId = <ImportId>` if the existing
    importer can expose the created import id without changing behavior;
  - duplicate pre-check failures:
    no external correlation unless SQL/code validation finds a stable pre-existing domain row that
    can be propagated without changing behavior.
- Implement MGE results generic audit wiring only after approval.
- Preserve existing MGE route, file, parse, SQL ingest, duplicate/overwrite behavior, embeds,
  telemetry/logging, output data, and user-facing behavior.
- Keep audit writes best-effort.
- Update tests and deferred documentation after delivery.

### Out Of Scope

- Discord command changes.
- Upload route UX or embed text changes.
- Queue UX/embed behavior changes.
- Fallback, player-location, Honor, PreKvK, weekly activity, or inventory behavior changes.
- Wiring inventory generic audit adoption.
- Changing MGE SQL table schemas, reporting semantics, output files, event completion behavior, or
  channel gating.
- Redesigning MGE signup, roster, award, event, or publish workflows.
- New SQL schema tables or new generic audit objects unless audit finds a blocker and approval is
  granted.
- Replacing the MGE results importer.
- Adding the `dbo.UPDATE_ALL2` wrapper/audit-output layer.
- Splitting `dbo.IMPORT_STAGING_PROC`.
- Decomposing or replacing `dbo.UPDATE_ALL2`.
- Historical production data backfill.
- Operator UI/reporting dashboards for audit history.

## 6. Remaining Import Audit Slices To Preserve

Do not lose these later slices:

1. **Task C Slice 8 - Inventory Generic Audit Correlation Adoption**
   - Validate `dbo.InventoryImportBatch.ImportBatchID` or the current SQL equivalent.
   - Add generic audit correlation without replacing inventory's domain audit/history model.
2. **Later SQL Slice - `dbo.UPDATE_ALL2` Wrapper/Audit Outputs**
   - Add non-invasive audit output around downstream rebuild phases before attempting procedure
     decomposition.
3. **Later SQL Slice - `dbo.IMPORT_STAGING_PROC` Responsibility Split**
   - Split only after durable audit evidence and compatibility wrappers are stable.
4. **Later SQL Slice - `dbo.UPDATE_ALL2` Decomposition**
   - Prepare only after wrapper/audit-output evidence identifies phase boundaries and hotspots.
5. **Later Python Slice - Residual `stats_module.py` Import Cleanup**
   - Continue shrinking `stats_module.py` into service/DAL boundaries once audit and SQL
     instrumentation are stable.
6. **Later SQL Cleanup - Legacy PreKvK Phase Object Retirement**
   - `dbo.PreKvk_Phases` retirement remains a separate SQL cleanup after live dependencies and
     production cycles are reviewed.
7. **Later SQL Cleanup - `dbo.vAllianceActivity_WeeklyCumulative` Review**
   - Confirm downstream/manual usage before correcting or retiring the currently suspicious weekly
     activity cumulative reporting view through the SQL repo process.

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
- archived Task C Slice 2, Slice 3, Slice 3A, Slice 4, Slice 5, and Slice 6 task packs

SQL references:

- `C:\K98-bot-SQL-Server\sql_schema\dbo.ImportAuditBatch.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.ImportAuditPhase.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_StartBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_RecordPhase.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_CompleteBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_FailBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.MGE_ResultImports.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.MGE_FinalResults.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.MGE_Events.Table.sql`
- MGE award/reporting SQL objects touched by import report generation.

## 8. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Confirm upload route/importer/service/DAL/SQL boundaries before implementation. |
| `k98-sql-validation` | use | Validate MGE result SQL objects, duplicate/overwrite semantics, and generic audit writer compatibility. |
| `k98-test-selection` | use | Required before validation command selection. |
| `k98-deferred-optimisation-capture` | use | Required to update the remaining import-audit backlog after delivery. |
| `k98-pr-review` | use before PR handoff | Confirm architecture, SQL alignment, tests, deferred tracking, and promotion safety. |
| `k98-promotion-check` | use before production promotion | Required if SQL/config/deployment sequencing is involved. |
| `codex-security:security-diff-scan` | use or justify skip | SQL/data access, file upload handling, user-controlled workbook parsing, and audit persistence are security-sensitive surfaces. |

## 9. Files And SQL Objects To Audit

Bot repo:

- `upload_routes/mge_results_route.py`
- `mge/mge_results_import.py`
- `mge/mge_xlsx_parser.py`
- `mge/dal/mge_results_dal.py`
- `ui/views/mge_results_overwrite_confirm_view.py`
- `services/import_audit_service.py`
- `stats/dal/import_audit_dal.py`
- `tests/test_mge_results_upload_route.py`
- `tests/test_mge_results_import.py`
- `tests/test_mge_results_import_service.py`
- `tests/test_mge_results_overwrite_confirm_view.py`
- `tests/test_import_audit_service.py`
- `tests/test_import_audit_dal.py`

SQL repo:

- generic import audit tables and writer procedures
- existing MGE result import, final result, event, award, and reporting objects used by the
  route/importer/reporting path

## 10. Required First Response

Use this shape and stop for approval before code or SQL changes:

```markdown
**Scope Summary**
<MGE-results-only generic audit adoption objective and explicit no-behavior-change boundary>

**Current MGE Results Import State**
<route, filename handling, SQL preflight, parse/normalize, duplicate/overwrite/accepted/failed outcomes, SQL ingest, reporting surfaces, telemetry/logging, tests>

**SQL Position**
<validated MGE objects, generic audit writer compatibility, accepted/duplicate/failure external correlation proposal>

**Audit Taxonomy Proposal**
<ImportKind, SourceType, phase names, counters, details JSON, terminal status policy>

**Implementation Proposal**
<files to change, service/DAL ownership, best-effort behavior, route/importer contract preservation, rollback plan>

**Remaining Slice Map**
<inventory, UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup, PreKvK legacy SQL cleanup, weekly cumulative view cleanup>

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
.\.venv\Scripts\python.exe -m pytest -q tests\test_mge_results_upload_route.py tests\test_mge_results_import.py tests\test_mge_results_import_service.py tests\test_mge_results_overwrite_confirm_view.py tests\test_import_audit_service.py tests\test_import_audit_dal.py
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

- Upload a valid MGE results workbook for an event where auto import is operationally safe and
  confirm the existing success embed remains unchanged.
- Confirm one completed `mge_results` audit batch with source-row counters and completed parse/SQL
  phases.
- Confirm accepted-import correlation to `dbo.MGE_ResultImports` and the inserted `ImportId`.
- Exercise duplicate/overwrite outcomes only if operationally safe; otherwise cover them in tests.
- Exercise or simulate invalid workbook/importer failure in tests rather than production, unless
  an operator explicitly approves a production negative-path smoke.

## 12. Acceptance Criteria

- [x] MGE results route/importer/SQL state surfaces are audited before implementation.
- [x] SQL object names, columns, and domain batch ids are validated against the SQL repo.
- [x] First response stops for approval before code or SQL changes.
- [x] MGE results generic audit wiring is implemented only after approval.
- [x] Existing MGE route, file, parse, SQL ingest, duplicate/overwrite behavior, embeds,
  telemetry/logging, output tables, and user-facing behavior are preserved.
- [x] Audit writes remain best-effort.
- [x] Batch-level counters use the normalized Slice 3A terminal writer contract where applicable.
- [x] Focused MGE results/import-audit tests pass.
- [x] Remaining import-audit slices and deferred SQL/Python cleanup items remain documented.

## 13. Delivery Record

- Mirror PR: `https://github.com/cwatts6/K98-bot-mirror/pull/188`
- Production PR: `https://github.com/cwatts6/k98-bot/pull/496`
- Main implementation files:
  - `mge/mge_results_import.py`
  - `services/mge_results_import_audit_service.py`
  - `upload_routes/mge_results_route.py`
  - `tests/test_mge_results_import_audit_service.py`
  - `tests/test_mge_results_import_service.py`
  - `tests/test_mge_results_upload_route.py`
- Accepted correlation: `ExternalBatchTable=dbo.MGE_ResultImports`,
  `ExternalBatchId=<ImportId>`.
- Duplicate/pre-domain outcomes remain uncorrelated. Failures after `dbo.MGE_ResultImports`
  creation correlate to the created import id when available without changing importer behavior.
- Manual command/overwrite imports are audited through the importer, matching the approved
  implementation boundary.
- Post-review hardening accepted only real `MgeResultsImportAuditContext` values, reconstructed
  compatible dictionaries, fell back for unexpected serialized values, and reused a precomputed
  workbook SHA-256 for audit start plus duplicate checks.
- Operator smoke testing was reported successful on 2026-06-30.
- Focused validation after review comments: `39 passed` for MGE results/import-audit route,
  importer, service, view, and DAL tests.
- Broad validation completed before smoke: explicit `tests/test_mge_*.py` run passed with
  `302 passed`; full pytest passed with `2118 passed, 2 skipped`; `scripts/smoke_imports.py`,
  `scripts/validate_architecture_boundaries.py`, `scripts/validate_deferred_items.py`,
  `scripts/select_tests.py`, `scripts/validate_command_registration.py`,
  `scripts/analyse_pytest_log_noise.py`, `git diff --check`, and Codex Security diff scan
  completed successfully. `pyright` reported no errors and only the existing optional-import
  warnings.
