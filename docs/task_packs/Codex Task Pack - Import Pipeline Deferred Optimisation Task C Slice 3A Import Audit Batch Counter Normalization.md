# Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3A Import Audit Batch Counter Normalization

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task C Slice 3A - Import Audit Batch Counter Normalization`
- Date: `2026-06-29`
- Owner/context: `Chris Watts / K98 bot import architecture`
- Task type: `deferred optimisation batch | SQL/DAL audit writer follow-up | import audit consistency`
- Depends on:
  - Task A, archived at `docs/task_packs/archive/Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md`
  - Task B, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md`
  - Task C Slice 1, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Import Architecture and Service DAL Wrappers.md`
  - Task C Slice 2, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 2 Durable Batch Audit Foundation.md`
  - Task C Slice 3, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3 Non-Fallback Audit Adoption.md`
- One-pass approved: `no`
- Status: `active task pack, starts with audit/scope and SQL implementation-boundary confirmation`

## 2. Objective

Normalize batch-level import audit row counters now that fallback and player-location imports are
writing durable generic audit rows. The specific target is `RowsInSource`, which remains `NULL`
when the source row count is only known after `dbo.usp_ImportAudit_StartBatch` runs.

This slice should decide and implement the smallest SQL-owned writer-procedure and bot DAL/service
change needed for callers to set `RowsInSource` at terminal completion/failure time. It should
land before broader Honor, PreKvK, weekly activity, MGE, and inventory audit adoption so later
import-family slices share one counter contract.

## 3. Delivered Baseline

Task C Slice 3 delivered and smoke tested player-location audit adoption:

- Auto `scan_1198.csv` route:
  - `ImportKind = player_location`
  - `SourceType = discord_upload_csv`
  - phases: `location_csv_parse`, `location_sql_replace`, `location_post_import_refresh`
  - success batch completes once after refresh-phase audit and before Discord success notification
- `/location import` command merge path:
  - phases: `location_csv_parse`, `location_sql_merge`, `location_post_import_refresh`
  - audit writes are best-effort and refresh callback failure preserves user-facing import success
- Production smoke on 2026-06-29 confirmed:
  - successful auto import batch `completed` with `RowsStaged=301`, `RowsWritten=301`, `RowsSkipped=0`
  - no-valid-row auto import batch `skipped` with skipped parse phase and `NoValidLocationRows`

Known remaining counter gap:

- `RowsInSource` is not normalized at batch level for imports whose source row count is learned
  after batch start.
- Phase-level `RowsIn` / `RowsOut` and `DetailsJson.rows_parsed` are valid today and remain the
  current source of truth until this slice is delivered.

## 4. Source Deferred Item Promoted Into This Pack

### Deferred Optimisation
- Area: `services/import_audit_service.py`, `stats/dal/import_audit_dal.py`, SQL repo `dbo.usp_ImportAudit_CompleteBatch`, SQL repo `dbo.usp_ImportAudit_FailBatch`
- Type: consistency
- Description: Task C Slice 2 and Slice 3 smoke testing confirmed durable batch and phase audit rows, but batch-level `RowsInSource` remains `NULL` when the source row count is only known after batch start. The count is preserved in phase rows and details JSON, but future audit consumers should not need import-kind-specific JSON parsing for the basic source-row count.
- Suggested Fix: Extend the SQL-owned terminal writer procedure contract so `RowsInSource` can be populated at completion/failure time, then thread the optional value through bot DAL/service wrappers and currently wired fallback/location callers. Avoid historical production backfill unless separately approved.
- Impact: low
- Risk: low
- Dependencies: Task C Slice 2 audit foundation and Task C Slice 3 location adoption deployed; SQL owner approval for writer-procedure signature updates.

## 5. Proposed Implementation Boundary

### In Scope

- SQL repo review for:
  - `dbo.ImportAuditBatch`
  - `dbo.usp_ImportAudit_CompleteBatch`
  - `dbo.usp_ImportAudit_FailBatch`
  - any SQL migration/schema-generation convention needed to update procedure signatures
- Bot repo review for:
  - `stats/dal/import_audit_dal.py`
  - `services/import_audit_service.py`
  - `services/fallback_import_service.py`
  - `stats_module.py` compatibility paths that complete/fail fallback audit batches
  - `services/location_import_service.py`
  - `upload_routes/player_location_route.py`
  - focused audit DAL/service/location/fallback tests
- Add optional `rows_in_source` support to bot DAL/service terminal audit wrappers only after SQL
  boundary is confirmed.
- Populate `RowsInSource` for already wired fallback and player-location audit paths where the
  source row count is known.
- Preserve all existing import behavior, route/command UX, queue/embed behavior, file handling,
  staging, SQL import procedures, output tables, and cache refresh behavior.
- Keep audit writes best-effort.
- Confirm no historical production backfill is included.

### Out Of Scope

- New SQL tables or indexes.
- Any change to `dbo.ImportAuditBatch` column names or existing meaning.
- Historical audit row backfill.
- Wiring Honor, PreKvK, weekly activity, MGE, or inventory audit adoption in this slice.
- Changing inventory's existing domain audit/history model.
- Adding the `dbo.UPDATE_ALL2` wrapper/audit-output layer.
- Splitting `dbo.IMPORT_STAGING_PROC`.
- Decomposing or replacing `dbo.UPDATE_ALL2`.
- Operator UI/reporting dashboards.
- Discord command, route UX, or embed text changes.

## 6. SQL Position To Confirm First

Preferred approach:

- Add optional `@RowsInSource int = NULL` to:
  - `dbo.usp_ImportAudit_CompleteBatch`
  - `dbo.usp_ImportAudit_FailBatch`
- In each procedure, update `dbo.ImportAuditBatch.RowsInSource` only when `@RowsInSource IS NOT NULL`.
- Preserve procedure result shape and existing callers.
- Add migration/schema updates in `C:\K98-bot-SQL-Server` using the repo's current SQL promotion conventions.

Alternative to reject unless SQL review finds a blocker:

- Do not add a generic ad hoc update statement in Python.
- Do not update `RowsInSource` through route/command modules.
- Do not overload `RowsStaged`, `RowsWritten`, or JSON details as the normalized counter.

## 7. Remaining Import Audit Slices To Preserve

Do not lose these later slices:

1. **Task C Slice 4 - Honor Import Audit Adoption**
   - Proposed focus: KVK Honor upload/import path.
   - Expected external correlation: `ExternalBatchTable = dbo.KVK_Honor_Scan`; `ExternalBatchId = <KVK_NO>:<ScanID>` or another SQL-validated stable domain id.
   - Preserve Honor route, importer, ranking refresh, output, and channel behavior.
2. **Task C Slice 5 - PreKvK Import Audit Adoption**
   - Proposed focus: PreKvK upload/import and import-history correlation.
   - Expected external correlation: `dbo.PreKvk_Scan` / `dbo.PreKvk_ImportHistory`, validated against SQL repo.
   - Preserve PreKvK report/ranking output and existing history semantics.
3. **Task C Slice 6 - Weekly Activity Import Audit Adoption**
   - Proposed focus: weekly activity upload/import.
   - Expected external correlation: `dbo.AllianceActivitySnapshotHeader.SnapshotId`, validated against SQL repo.
   - Preserve existing activity output and route behavior.
4. **Task C Slice 7 - MGE Results Import Audit Adoption**
   - Proposed focus: MGE results upload/import.
   - Expected external correlation: `dbo.MGE_ResultImports.ImportId`, validated against SQL repo.
   - Preserve event/result overwrite semantics and MGE DAL ownership.
5. **Task C Slice 8 - Inventory Generic Audit Correlation Adoption**
   - Proposed focus: generic audit correlation around inventory import batches.
   - Expected external correlation: `dbo.InventoryImportBatch.ImportBatchID`, validated against SQL repo.
   - Do not replace inventory's existing domain audit/history model.
6. **Later SQL Slice - `dbo.UPDATE_ALL2` Wrapper/Audit Outputs**
   - Add non-invasive audit output around downstream rebuild phases before attempting procedure decomposition.
7. **Later SQL Slice - `dbo.IMPORT_STAGING_PROC` Responsibility Split**
   - Split only after durable audit evidence and compatibility wrappers are stable.
8. **Later SQL Slice - `dbo.UPDATE_ALL2` Decomposition**
   - Prepare only after wrapper/audit-output evidence identifies phase boundaries and hotspots.
9. **Later Python Slice - Residual `stats_module.py` Import Cleanup**
   - Continue shrinking `stats_module.py` into service/DAL boundaries once audit and SQL instrumentation are stable.

## 8. Required Reading

Before implementation, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 2 Durable Batch Audit Foundation.md`
- `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3 Non-Fallback Audit Adoption.md`

SQL references:

- `C:\K98-bot-SQL-Server\sql_schema\dbo.ImportAuditBatch.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_CompleteBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.usp_ImportAudit_FailBatch.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\migrations\README.md`
- SQL promotion/deployment references required by the SQL repo.

## 9. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Confirm bot/SQL/service/DAL boundary before implementation. |
| `k98-sql-validation` | use | Required because this slice changes SQL-owned writer procedure signatures. |
| `k98-test-selection` | use | Required before validation command selection. |
| `k98-deferred-optimisation-capture` | use | Required to update deferred tracking after delivery. |
| `k98-pr-review` | use before PR handoff | Confirm SQL alignment, tests, and remaining-slice tracking. |
| `k98-promotion-check` | use before production promotion | Required because SQL deployment sequencing is involved. |
| `codex-security:security-diff-scan` | use or justify skip | SQL/data access and import audit persistence are security-sensitive surfaces. |

## 10. Required First Response

Use this shape and stop for approval before code or SQL changes:

```markdown
**Scope Summary**
<RowsInSource normalization objective and explicit no-behavior-change boundary>

**Current Counter State**
<where RowsInSource, RowsStaged, RowsWritten, RowsSkipped, phase counters, and details JSON are populated today>

**SQL Position**
<preferred procedure signature change, migration/schema files, compatibility and rollback plan>

**Bot DAL/Service Position**
<exact optional parameter additions and callers to update>

**Remaining Slice Map**
<confirm Honor, PreKvK, weekly, MGE, inventory, UPDATE_ALL2 wrapper, IMPORT_STAGING_PROC split, UPDATE_ALL2 decomposition, stats_module cleanup>

**Validation Plan**
<SQL validation, focused bot tests, full bot tests if needed, smoke tests, security review>

**Open Questions / Approval Needed**
<SQL signature approval, backfill exclusion, which smoke imports to run after deployment>
```

## 11. Validation Plan

Baseline bot validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_import_audit_service.py tests\test_import_audit_dal.py tests\test_location_import_service.py tests\test_player_location_upload_route.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

Run full pytest if shared audit wrappers or fallback paths are materially touched:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
```

SQL validation:

```powershell
cd C:\K98-bot-SQL-Server
.\deploy\Validate-SqlRepo.ps1
```

Manual smoke after SQL and bot deployment:

- Run one fallback import or use the safest available existing fallback smoke path and confirm
  `RowsInSource` is populated when the source row count is known.
- Run auto `scan_1198.csv` player-location import and confirm:
  - batch `Status = completed`;
  - `RowsInSource = RowsStaged = RowsWritten` for normal success;
  - phases remain `location_csv_parse`, `location_sql_replace`, `location_post_import_refresh`.
- Run no-valid-row location smoke only if safe, and confirm skipped batch counter behavior matches
  the approved policy.

## 12. Acceptance Criteria

- [ ] SQL writer procedure approach is approved before implementation.
- [ ] `RowsInSource` can be set at terminal completion/failure time through SQL-owned procedures.
- [ ] Bot DAL/service wrappers expose optional `rows_in_source` without breaking existing callers.
- [ ] Already wired fallback and player-location audit paths populate batch-level `RowsInSource` where the row count is known.
- [ ] Existing phase counters and details JSON remain intact.
- [ ] No route/command UX, queue, file, staging, SQL import procedure, output, or cache refresh behavior changes.
- [ ] Historical production data backfill is excluded unless separately approved.
- [ ] Remaining import-family adoption slices are preserved and documented.
- [ ] Focused tests and SQL validation pass.
- [ ] Deferred optimisation tracking is updated after delivery.
