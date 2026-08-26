# Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3 Non-Fallback Audit Adoption

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task C Slice 3 - Non-Fallback Audit Adoption`
- Date: `2026-06-29`
- Owner/context: `Chris Watts / K98 bot import architecture`
- Task type: `deferred optimisation batch | import architecture | durable audit adoption`
- Depends on:
  - Task A, archived at `docs/task_packs/archive/Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md`
  - Task B, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md`
  - Task C Slice 1, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Import Architecture and Service DAL Wrappers.md`
  - Task C Slice 2, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 2 Durable Batch Audit Foundation.md`
- One-pass approved: `no`
- Status: `archived after Task C Slice 3 delivery`

## Delivery Summary

Task C Slice 3 was delivered in mirror PR #183 and production PR #491. It mapped non-fallback
import state surfaces for player location, Honor, PreKvK, weekly activity, MGE, and inventory, then
wired the approved player-location scope first while preserving route, command, SQL procedure,
cache refresh, file, output, and Discord UX behavior.

Delivered code:

- `services/location_import_service.py`
  - Added `player_location` generic audit taxonomy.
  - Added service-owned location audit helpers and `LocationImportAuditContext`.
  - Wired `/location import` merge semantics through `location_csv_parse`,
    `location_sql_merge`, and `location_post_import_refresh`.
  - Kept audit writes best-effort and preserved user-facing command success behavior when refresh
    signaling fails.
- `upload_routes/player_location_route.py`
  - Wired the auto `scan_1198.csv` route through `location_csv_parse`,
    `location_sql_replace`, and `location_post_import_refresh`.
  - Ensured the batch completes once after refresh-phase audit and before Discord success
    notification.
  - Preserved existing empty-row skip, SQL headroom skip, error embed, cache refresh, and backup
    scheduling behavior.
- `commands/location_cmds.py`
  - Passed audit context into the service-owned command import path while keeping the command
    layer thin.
- Focused route/service tests cover audit phase sequencing, audit-start failure preservation,
  refresh failure status, notification failure after SQL write, and no-valid-row skip behavior.

SQL position:

- No SQL schema or stored procedure changes were made in this slice.
- Existing Task C Slice 2 audit tables and SQL-owned writer procedures were reused.
- Batch-level `RowsInSource` normalization was explicitly deferred to Task C Slice 3A:
  `Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3A Import Audit Batch Counter Normalization.md`.

Validation and smoke evidence:

- Focused route/audit pytest passed after final review fixes: `36 passed`.
- Full pytest passed after final review fixes: `2084 passed, 2 skipped`.
- Architecture validator, deferred validator, smoke imports, command registration, and
  `git diff --check` passed.
- Codex Security diff scan for the mirror PR completed with `0` findings.
- Production smoke testing on 2026-06-29 confirmed:
  - successful auto `scan_1198.csv` import created `player_location` batch `completed` with
    `RowsStaged=301`, `RowsWritten=301`, `RowsSkipped=0`;
  - success phases `location_csv_parse`, `location_sql_replace`, and
    `location_post_import_refresh` were present and completed;
  - no-valid-row auto import created a `skipped` batch with skipped `location_csv_parse` and
    `NoValidLocationRows`.

## 2. Objective

Adopt the generic durable import audit foundation delivered in Task C Slice 2 for non-fallback
imports in a behavior-preserving way. Start by auditing location, honor, PreKvK, weekly activity,
MGE, and inventory import state surfaces, then propose player location import as the first
non-fallback wiring target because it is smaller, already service-backed for command imports, and
has focused route/service tests.

The first response for this slice must confirm the exact implementation boundary before code or
SQL changes. The proposed first implementation is: no new SQL schema, reuse the existing
`dbo.ImportAuditBatch` / `dbo.ImportAuditPhase` writer procedures, add only DAL/service helper
extensions needed by non-fallback import callers, and wire player location import first.

## 3. Background

Task C Slice 2 delivered:

- `dbo.ImportAuditBatch`
- `dbo.ImportAuditPhase`
- `dbo.usp_ImportAudit_StartBatch`
- `dbo.usp_ImportAudit_RecordPhase`
- `dbo.usp_ImportAudit_CompleteBatch`
- `dbo.usp_ImportAudit_FailBatch`
- `stats/dal/import_audit_dal.py`
- `services/import_audit_service.py`
- fallback-first audit wiring correlated to `dbo.FallbackImportBatchControl`

Smoke testing on 2026-06-29 confirmed completed audit batches for full fallback and interim auto
partial fallback imports. Route, command, queue, CSV/XLSX, staging, SQL procedure, and output
behavior remained unchanged.

Remaining import audit work should now move one import family at a time, using the existing audit
model before introducing more SQL instrumentation.

## 4. Source Deferred Items

### Deferred Optimisation
- Area: location, honor, PreKvK, weekly activity, MGE, and inventory upload routes/workers
- Type: consistency
- Description: Task C Slice 2 delivered the generic durable audit foundation and fallback-first wiring. The remaining non-fallback import paths still need deliberate adoption planning because they have different route, worker, file, SQL procedure, cache refresh, and operator-observable state surfaces.
- Suggested Fix: Map each non-fallback import path and wire audit events through service/DAL boundaries one import family at a time, with player location import proposed as the first low-risk target. Preserve route/command UX, output files, SQL procedure behavior, cache refresh signaling, and existing worker recovery semantics unless separately approved.
- Impact: medium
- Risk: medium
- Dependencies: Generic durable import batch audit foundation delivered and smoke tested in Task C Slice 2; import-kind-specific tests identified for each adopted route/worker path.

### Deferred Optimisation
- Area: `services/import_audit_service.py`, `stats/dal/import_audit_dal.py`, `stats_module.py`, SQL repo `dbo.usp_ImportAudit_CompleteBatch`
- Type: consistency
- Description: Task C Slice 2 smoke testing confirmed fallback audit batches and phase rows are durable and correctly completed, but batch-level `RowsInSource` remains `NULL` when the source row count is only known after batch start.
- Suggested Fix: Decide whether this slice should only document the row-counter policy or make a small SQL/DAL writer-procedure update so batch-level `RowsInSource` can be populated at completion. Keep this separate from non-fallback behavior unless it is low-risk and explicitly approved.
- Impact: low
- Risk: low
- Dependencies: Task C Slice 2 audit foundation delivered; SQL owner approval for any writer-procedure signature change.

## 5. Candidate Scoring

| Candidate | Impact | Frequency | Risk Reduction | Effort | Score | Decision |
|---|---:|---:|---:|---:|---:|---|
| Audit all non-fallback import state surfaces | 4 | 4 | 4 | 2 | 10 | Include first |
| Wire player location import to generic audit | 4 | 4 | 4 | 3 | 9 | Proposed Slice 3 implementation |
| Wire Honor, PreKvK, weekly activity, MGE, and inventory together | 4 | 4 | 4 | 5 | 7 | Defer; too broad for one PR |
| Normalize batch-level row counters | 2 | 3 | 2 | 2 | 7 | Decide after audit; implement only if low-risk |
| `dbo.UPDATE_ALL2` wrapper/audit outputs | 4 | 5 | 4 | 3 | 10 | Separate SQL slice |
| Split `dbo.IMPORT_STAGING_PROC` responsibilities | 4 | 4 | 4 | 4 | 8 | Separate SQL slice |
| Decompose `dbo.UPDATE_ALL2` into phase procedures | 5 | 4 | 5 | 5 | 9 | Defer until wrapper evidence exists |

## 6. Scope

### In Scope

- Audit current state surfaces for:
  - player location upload/import
  - Honor upload/import
  - PreKvK upload/import
  - weekly activity upload/import
  - MGE results upload/import
  - inventory image import and approval flow
- Confirm the generic import-audit taxonomy for each import kind:
  - `ImportKind`
  - `SourceType`
  - source file/message/channel identifiers
  - actor/uploader identifiers
  - queue/channel identifiers where available
  - external domain batch table/id where one exists
  - row/source counters and phase names
- Reuse the existing SQL audit objects and stored procedures from Slice 2.
- Propose player location import as the first non-fallback audit adoption target.
- Preserve current route, command, queue, embed, file, staging, cache refresh, and output behavior.
- Keep audit writes best-effort; the import should continue if a durable audit write fails.
- Add focused tests for the audited/wired path and audit best-effort behavior.
- Update deferred optimisation tracking after delivery.

### Out Of Scope

- Discord command changes.
- Upload route UX or embed text changes.
- Queue UX/embed behavior changes.
- Fallback import behavior changes, except shared audit helper test adjustments if required.
- Wiring Honor, PreKvK, weekly activity, MGE, or inventory in the same implementation unless
  explicitly approved after audit.
- Changing inventory's existing domain audit/history model unless required for correlation mapping.
- New SQL schema objects unless a gap is found and separately approved.
- Splitting `dbo.IMPORT_STAGING_PROC`.
- Adding the `dbo.UPDATE_ALL2` wrapper/audit-output layer.
- Decomposing or replacing `dbo.UPDATE_ALL2`.
- Historical production data backfill.
- Operator UI/reporting dashboards for audit history.

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
- `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 2 Durable Batch Audit Foundation.md`

SQL references:

- `C:\K98-bot-SQL-Server\sql_schema\dbo.ImportAuditBatch.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.ImportAuditPhase.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_StartBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_RecordPhase.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_CompleteBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_FailBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\docs\SQL_PROMOTION_GUIDE.md`

## 8. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required to confirm route/service/DAL/SQL boundaries before implementation. |
| `k98-discord-command-feature` | not applicable | Commands and interaction UX must not change in this slice. Use only if audit discovers unavoidable command impact and stop for approval. |
| `k98-sql-validation` | use | Required to validate existing audit writer procedures and any row-counter signature proposal. |
| `k98-test-selection` | use | Required before validation command selection. |
| `k98-deferred-optimisation-capture` | use | Required to update the remaining import audit backlog. |
| `k98-pr-review` | use before PR handoff | Review architecture, SQL alignment, tests, deferred tracking, and promotion safety. |
| `k98-promotion-check` | use before production promotion | Required if SQL changes or production deployment sequencing are involved. |
| `codex-security:security-scan` | use or justify skip | SQL/data access, file handling, imports, and persistence are security-sensitive surfaces. |

## 9. Files And SQL Objects To Audit

Bot repo:

- `services/import_audit_service.py`
- `stats/dal/import_audit_dal.py`
- `upload_routes/player_location_route.py`
- `services/location_import_service.py`
- `location_importer.py`
- `tests/test_player_location_upload_route.py`
- `tests/test_location_import_service.py`
- `upload_routes/honor_route.py`
- `honor_importer.py`
- `tests/test_honor_upload_route.py`
- `tests/test_honor_importer.py`
- `upload_routes/prekvk_route.py`
- `prekvk_importer.py`
- `prekvk/dal/import_history_dal.py`
- `tests/test_prekvk_upload_route.py`
- `tests/test_prekvk_importer.py`
- `upload_routes/weekly_activity_route.py`
- `weekly_activity_importer.py`
- `tests/test_weekly_activity_upload_route.py`
- `upload_routes/mge_results_route.py`
- `mge/mge_results_import.py`
- `mge/dal/mge_results_dal.py`
- `tests/test_mge_results_upload_route.py`
- `tests/test_mge_results_import.py`
- `upload_routes/inventory_route.py`
- `ui/views/inventory_views.py`
- `inventory/inventory_service.py`
- `inventory/dal/inventory_dal.py`
- `inventory/audit_service.py`
- `inventory/dal/inventory_audit_dal.py`
- `tests/test_inventory_upload_route.py`
- `tests/test_inventory_upload_flow.py`
- `tests/test_inventory_service.py`
- `tests/test_inventory_audit_service.py`

SQL repo:

- Slice 2 import audit tables and stored procedures
- existing location, Honor, PreKvK, weekly activity, MGE, and inventory tables/procedures used by the audited paths
- any existing domain batch/history table that should become `ExternalBatchTable` / `ExternalBatchId`

## 10. Required First Response

Use this shape and stop for approval before implementation:

```markdown
**Scope Summary**
<non-fallback audit adoption objective, proposed location-first boundary, explicit exclusions>

**Current Non-Fallback Import State Surfaces**
<location/honor/PreKvK/weekly/MGE/inventory queue, file, staging, procedure, output, cache, domain batch, and error state>

**Audit Taxonomy Proposal**
<ImportKind/SourceType/phase names/external batch correlation/counter policy for each import kind>

**Location-First Implementation Proposal**
<exact files, service/DAL ownership, best-effort audit behavior, rollback plan>

**SQL Position**
<reuse existing Slice 2 objects, whether row-counter writer change is needed, SQL validation plan>

**Remaining Slices**
<Honor/PreKvK/weekly/MGE/inventory adoption, UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, residual stats_module cleanup>

**Validation Plan**
<focused pytest, SQL validation, smoke tests, security review, promotion checks>

**Open Questions / Approval Needed**
<specific decisions for Chris>
```

## 11. Implementation Requirements After Approval

- Keep routes and commands thin; audit ownership belongs in service/DAL helpers.
- Do not add direct SQL to upload routes, command modules, or views.
- Treat audit writes as best-effort and log failures without failing the import.
- Preserve all existing messages, embeds, file handling, cache refresh signaling, SQL procedure behavior, and output rows.
- Do not alter inventory's existing audit/history semantics unless the implementation only adds generic audit correlation around them.
- Use existing `ExternalBatchTable` / `ExternalBatchId` fields when an import has its own domain batch/history id.
- Keep rollback simple: removing audit calls must leave the import path operational.
- Add or update focused tests for success, failure, audit failure, and no-behavior-change paths.
- Update task packs, starters, and deferred optimisation records after delivery.

## 12. Validation Plan

Baseline commands:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

Likely focused tests for location-first implementation:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_import_audit_service.py tests\test_import_audit_dal.py tests\test_player_location_upload_route.py tests\test_location_import_service.py
```

Likely audit-only tests to run or justify:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_honor_upload_route.py tests\test_prekvk_upload_route.py tests\test_weekly_activity_upload_route.py tests\test_mge_results_upload_route.py tests\test_inventory_upload_route.py
```

Broad checks when implementation touches shared audit helpers:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests
```

SQL validation if any SQL repo change is proposed:

```powershell
cd C:\K98-bot-SQL-Server
.\deploy\Validate-SqlRepo.ps1
```

Manual smoke tests after deployment should include:

- player location auto upload/import still succeeds and refreshes profile/location cache behavior
- location audit batch and phase rows are present and completed
- audit write failure simulation does not break location import
- no change to fallback import output behavior
- no change to Honor, PreKvK, weekly activity, MGE, or inventory behavior if not wired in this slice

## 13. Acceptance Criteria

- [ ] Current non-fallback import state surfaces are mapped across all named import kinds.
- [ ] A consistent audit taxonomy is proposed for `ImportKind`, `SourceType`, phase names, counters, and external batch correlation.
- [ ] The first implementation boundary is explicitly approved before code or SQL changes.
- [ ] Player location import is wired to durable audit only if approved.
- [ ] Route, command, queue, embed, file, staging, cache refresh, SQL procedure, and output behavior remain unchanged.
- [ ] Existing Slice 2 audit objects are reused unless a SQL gap is explicitly approved.
- [ ] Batch-level row-counter policy is decided or captured for follow-up.
- [ ] Focused tests cover the wired path and audit best-effort behavior.
- [ ] SQL validation and bot validation are run or documented.
- [ ] Remaining deferred items are updated after delivery.
