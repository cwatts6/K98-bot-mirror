# Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 10 Rally Forts Import Audit Adoption

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task C Slice 10 - Rally Forts Import Audit Adoption`
- Date: `2026-06-30`
- Owner/context: `Chris Watts / K98 bot import architecture`
- Task type: `deferred optimisation batch | import audit adoption | Rally Forts upload route`
- One-pass approved: `no`
- Status: `active next-slice task pack, starts with Rally Forts audit/scope and SQL implementation-boundary confirmation`

## 2. Objective

Adopt generic durable `ImportAuditBatch` / `ImportAuditPhase` audit for the Rally Forts Discord
upload route while preserving the current Rally Forts user experience, local file staging, importer
contracts, SQL table/procedure behavior, result embed contract, log-backup scheduling, telemetry,
and user-facing behavior.

This is the second implementation PR from the split Task C Slice 9 audit. KVK_ALL audit adoption
was delivered first and is now archived as Slice 9. Rally Forts route extraction is already
complete from the DL_bot upload-routing programme; the remaining gap is generic durable import
audit adoption.

## 3. Completed Dependencies And Baseline

Completed import architecture baseline:

- Task A restored fallback import resilience and shield-time support.
- Task B delivered Unicode-preserving fallback import staging.
- Task C Slice 1 extracted fallback import orchestration into service/DAL wrappers.
- Task C Slice 2 added the generic durable audit foundation:
  - `dbo.ImportAuditBatch`
  - `dbo.ImportAuditPhase`
  - SQL-owned writer procedures
  - bot audit DAL/service wrappers
  - fallback-first wiring correlated to `dbo.FallbackImportBatchControl`
- Task C Slice 3 wired player-location generic audit.
- Task C Slice 3A normalized batch-level `RowsInSource` through terminal audit writers.
- Task C Slice 4 adopted generic durable audit for Honor uploads.
- Task C Slice 5 adopted generic durable audit for PreKvK uploads.
- Task C Slice 6 adopted generic durable audit for weekly activity uploads.
- Task C Slice 7 adopted generic durable audit for MGE results uploads and manual/overwrite
  imports.
- Task C Slice 8 adopted generic durable audit for inventory image upload/import lifecycles.
- Task C Slice 9 adopted generic durable audit for KVK_ALL uploads.

KVK_ALL Slice 9 closure evidence:

- Mirror PR: `cwatts6/K98-bot-mirror#190`
- Production PR: `cwatts6/k98-bot#498`
- Production smoke batch `23` completed with `ImportKind=kvk_all`,
  `ExternalBatchTable=KVK.KVK_Scan`, `ExternalBatchId=15:83`, `RowsInSource=9194`,
  `RowsStaged=9194`, `RowsWritten=9194`, `RowsSkipped=0`, and completed auto-export schedule
  phase.
- Production smoke batch `22` failed as `KvkDetailsTimestampRejected` with
  `ExternalBatchTable=KVK.KVK_Ingest_Diagnostics`, `ExternalBatchId=2`,
  `RowsInSource=9194`, `RowsStaged=9194`, `RowsWritten=0`, and `RowsSkipped=9194`.
- Review follow-up preserved valid `staged_rows=0` without falling back to `row_count`.

Rally Forts current baseline to validate:

- `DL_bot.py` delegates to `upload_routes/rally_forts_route.py`.
- The route is gated by `FORT_RALLY_CHANNEL_ID`; channel id `0` disables the route.
- The route accepts only `.xlsx` attachments.
- The route rejects path separators before local save.
- The route stages local files under `LOG_DIR/downloads`.
- The route lazy-loads `forts_ingest` importers.
- The route runs SQL headroom preflight.
- The route offloads daily/all-time imports, aggregates per-file success/skip/error results,
  renders the existing final embed, and schedules best-effort log backup after successful imports.
- `forts_ingest.import_rally_daily_xlsx()` parses `Rally_data_DD-MM-YYYY.xlsx`, writes
  `dbo.stg_RallyDaily`, runs `dbo.sp_Import_Rally_Daily`, writes `dbo.IngestionLog`, and returns
  `status`, `rows`, and `as_of`.
- `forts_ingest.import_rally_alltime_xlsx()` parses all-time Rally filenames, writes
  `dbo.stg_RallyAllTime`, runs `dbo.sp_Import_Rally_AllTime`, writes `dbo.IngestionLog`, and
  returns `status` and `rows`.

## 4. Source Deferred Item

### Deferred Optimisation
- Area: Rally Forts upload/import route
- Type: consistency
- Description: Task C Slice 9 was split into two implementation PRs after audit/scope approval. KVK_ALL generic durable audit adoption is delivered and smoke tested. The remaining active gap is Rally Forts generic durable `ImportAuditBatch` / `ImportAuditPhase` adoption. Rally Forts route extraction is already complete from the DL_bot upload-routing programme, but the route still relies on route embeds, logs, local file staging, `dbo.IngestionLog`, Rally staging/current tables, and importer return dictionaries rather than the shared durable audit surface.
- Suggested Fix: Adopt generic durable audit for Rally Forts using service/DAL-owned best-effort audit wrappers. Validate Rally Forts correlation to `dbo.IngestionLog/<IngestionID>` only if a safe tiny return/lookup helper can expose it without changing behavior, and leave duplicate/no-row/unrecognized/preflight failures externally uncorrelated. Preserve Rally route UX, embed text, attachment/file handling, importer contracts, SQL table/procedure behavior, log-backup scheduling, telemetry/logging, and user-facing behavior.
- Impact: medium
- Risk: medium
- Dependencies: Generic durable import audit foundation from Task C Slice 2; terminal counter normalization from Task C Slice 3A; KVK_ALL closure from Task C Slice 9; Rally Forts route extraction completed in upload-routing Phase 5C / PR 115; SQL validation against `C:\K98-bot-SQL-Server`.

## 5. Scope

### In Scope

- Audit the current Rally Forts route/importer/SQL behavior before implementation.
- Wire the Rally Forts upload route to generic durable audit with best-effort writes.
- Reuse existing Task C Slice 2 / Slice 3A audit DAL/service wrappers and SQL-owned writer
  procedures.
- Add a Rally-specific audit service helper only if it keeps the route/importer code small and
  matches the Honor, PreKvK, weekly, MGE, inventory, and KVK_ALL pattern.
- Add a tiny Rally importer return/lookup change to expose `dbo.IngestionLog.IngestionID` only if
  tests prove behavior is unchanged.
- Preserve duplicate/no-row/unrecognized/preflight outcomes as externally uncorrelated.
- Preserve all route UX, embed text, accepted extension rules, filename safety checks, local file
  staging behavior, importer contracts, SQL table/procedure behavior, log-backup scheduling,
  logging, telemetry, and user-facing behavior.
- Add focused route/importer/audit tests for completed daily/all-time imports, duplicate/no-row
  skips, unrecognized files, unsafe filenames, SQL preflight aborts, importer failures, and
  log-backup scheduling audit behavior where practical.
- Update deferred documentation after delivery.

### Out Of Scope

- Discord route UX or embed text changes.
- Accepted filename/extension changes.
- Replacing Rally importer or offload mechanics.
- Rally workbook format redesign.
- SQL table schema, stored procedure, view, export, report, dashboard, or Google Sheets behavior
  changes.
- New SQL schema tables or new generic audit objects unless SQL validation finds a blocker and
  operator approval is granted.
- Historical production data backfill.
- KVK_ALL changes except for documentation references to its completed Slice 9 delivery.
- `dbo.UPDATE_ALL2` wrapper/audit-output instrumentation.
- `dbo.IMPORT_STAGING_PROC` decomposition.
- `dbo.UPDATE_ALL2` decomposition.
- Residual `stats_module.py` cleanup.
- Legacy PreKvK SQL cleanup.
- Weekly cumulative view cleanup.
- Inventory view-orchestration extraction.

## 6. SQL Position To Validate

Validate these SQL objects against `C:\K98-bot-SQL-Server` before implementation:

- generic import audit tables and writer procedures:
  - `dbo.ImportAuditBatch`
  - `dbo.ImportAuditPhase`
  - `dbo.usp_ImportAudit_StartBatch`
  - `dbo.usp_ImportAudit_RecordPhase`
  - `dbo.usp_ImportAudit_CompleteBatch`
  - `dbo.usp_ImportAudit_FailBatch`
- Rally log/staging/current/procedure objects:
  - `dbo.IngestionLog`
  - `dbo.stg_RallyDaily`
  - `dbo.stg_RallyAllTime`
  - `dbo.cur_RallyDaily`
  - `dbo.cur_RallyTotals_Base`
  - `dbo.sp_Import_Rally_Daily`
  - `dbo.sp_Import_Rally_AllTime`

Expected correlation policy:

- Successful daily/all-time imports may correlate to `ExternalBatchTable=dbo.IngestionLog` and
  `ExternalBatchId=<IngestionID>` only if implementation can safely expose or look up the inserted
  `IngestionID` without changing route behavior or SQL procedure semantics.
- Duplicate outcomes should remain uncorrelated unless a stable existing `IngestionID` is already
  available without changing behavior.
- No-row, unrecognized-file, unsafe-filename, and SQL preflight outcomes should remain externally
  uncorrelated.
- Importer exceptions should correlate to `dbo.IngestionLog/<IngestionID>` only if the importer
  already wrote or can safely expose the log row. Pre-log failures remain uncorrelated.

## 7. Audit Taxonomy Proposal

- `ImportKind`: `rally_forts`
- `SourceType`: `discord_upload_xlsx`
- Candidate phases:
  - `rally_forts_attachment_save`
  - `rally_forts_file_classify`
  - `rally_forts_sql_preflight`
  - `rally_forts_daily_ingest`
  - `rally_forts_alltime_ingest`
  - `rally_forts_log_backup_schedule`
- Terminal statuses:
  - successful daily/all-time import: `completed`
  - duplicate importer skip: `skipped`
  - no-row importer skip: `skipped`
  - unrecognized file: `skipped`
  - unsafe filename: `failed`
  - SQL preflight abort: `failed` unless route audit confirms current semantics are better
    represented as `skipped`
  - importer/offload exception: `failed`
- Details JSON should include only behavior-preserving metadata such as:
  - `entry_point`
  - `filename`
  - `file_kind`
  - `rows_parsed`
  - `rows_staged`
  - `rows_written`
  - `rows_skipped`
  - `as_of`
  - `ingestion_id`
  - `error`

## 8. Files To Audit

Bot repo:

- `upload_routes/rally_forts_route.py`
- `forts_ingest.py`
- `services/import_audit_service.py`
- `stats/dal/import_audit_dal.py`
- `tests/test_rally_forts_upload_route.py`
- `tests/test_import_audit_service.py`
- `tests/test_import_audit_dal.py`

SQL repo:

- generic audit objects and writer procedures
- `dbo.IngestionLog`
- `dbo.stg_RallyDaily`
- `dbo.stg_RallyAllTime`
- `dbo.cur_RallyDaily`
- `dbo.cur_RallyTotals_Base`
- `dbo.sp_Import_Rally_Daily`
- `dbo.sp_Import_Rally_AllTime`

## 9. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Confirm Rally route/importer/DAL/SQL boundaries before implementation. |
| `k98-sql-validation` | use | Validate Rally SQL objects, `dbo.IngestionLog` identity/correlation, and audit writer compatibility. |
| `k98-test-selection` | use | Required before validation command selection. |
| `k98-deferred-optimisation-capture` | use | Required to update the import-audit backlog after Rally delivery. |
| `k98-pr-review` | use before PR handoff | Confirm architecture, SQL alignment, tests, deferred tracking, and promotion safety. |
| `k98-promotion-check` | use before production promotion | Required before pushing or promoting to production. |
| `codex-security:security-diff-scan` | use or justify skip | File upload handling, local file staging, workbook parsing, SQL/data access, and audit persistence are security-sensitive surfaces. |

## 10. Mandatory First Response

Use this shape and stop for approval before code or SQL changes:

```markdown
**Scope Summary**
<Rally Forts generic audit adoption objective, plus explicit route-extraction-complete / generic-audit-not-complete distinction>

**Current Route State**
<Rally route/importer/SQL flow, local staging, preflight, aggregation, embed, backup scheduling>

**SQL Position**
<validated dbo.IngestionLog and Rally staging/current/procedure objects, and correlation decision>

**Audit Taxonomy Proposal**
<ImportKind, SourceType, phase names, counters, details JSON, terminal status policy>

**Implementation Proposal**
<files to change, service/importer ownership, best-effort behavior, tiny IngestionID return/lookup if safe, behavior preservation>

**Remaining Slice Map**
<UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup, PreKvK legacy SQL cleanup, weekly cumulative view cleanup, inventory orchestration follow-up>

**Validation Plan**
<SQL validation, focused tests, broad checks, smoke tests, Codex Security review>

**Open Questions / Approval Needed**
<specific decisions for Chris>
```

## 11. Validation Plan

Baseline validators:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

Likely focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_rally_forts_upload_route.py tests\test_import_audit_service.py tests\test_import_audit_dal.py
```

Broader checks when route/importer/audit behavior is touched:

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

- Upload a valid Rally daily workbook where operationally safe.
- Upload a valid Rally all-time workbook where operationally safe.
- Confirm existing final embed text/shape remains unchanged.
- Confirm successful import audit batch:
  - `ImportKind=rally_forts`
  - `SourceType=discord_upload_xlsx`
  - `Status=completed`
  - `RowsInSource`, `RowsStaged`, `RowsWritten`, and `RowsSkipped` populated consistently.
  - `ExternalBatchTable=dbo.IngestionLog` and `ExternalBatchId=<IngestionID>` only if the
    implementation safely exposes the log id.
- Confirm duplicate/no-row/unrecognized/preflight outcomes are skipped or failed per the accepted
  taxonomy and remain externally uncorrelated.
- Confirm log-backup scheduling behavior is unchanged and audit records the scheduling phase when
  applicable.

## 12. Remaining Slice Map To Preserve

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
8. **Later Audit Polish Slice - ImportAuditPhase Timestamp Normalization**
   - Normalize generic audit phase timestamp boundaries so persisted phase rows cannot show
     `CompletedAtUtc` slightly earlier than `StartedAtUtc` while preserving duration semantics.

## 13. Acceptance Criteria

- [ ] Rally Forts route/importer/SQL state surfaces are audited before implementation.
- [ ] SQL object names, columns, statuses, constraints, indexes, and correlation candidates are
  validated against the SQL repo.
- [ ] Generic audit wiring is implemented only after approval.
- [ ] Existing route UX, embed text, attachment/file handling, importer contracts, SQL
  procedure/table behavior, log-backup scheduling, telemetry/logging, and user-facing behavior are
  preserved.
- [ ] Audit writes remain best-effort.
- [ ] Batch-level counters use the normalized Slice 3A terminal writer contract where applicable.
- [ ] Successful Rally imports correlate to `dbo.IngestionLog/<IngestionID>` only when safely
  available.
- [ ] Duplicate/no-row/unrecognized/preflight outcomes remain externally uncorrelated.
- [ ] Focused Rally/import-audit tests pass.
- [ ] Remaining SQL/Python cleanup items remain documented.
