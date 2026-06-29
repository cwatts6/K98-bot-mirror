# Codex Task Pack - Import Pipeline Deferred Optimisation Task C

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task C - Import Architecture and Service/DAL Wrappers`
- Date: `2026-06-29`
- Owner/context: `Chris Watts / K98 bot import architecture`
- Task type: `deferred optimisation | import architecture | audit design | service extraction`
- Depends on:
  - Task A, archived at `docs/task_packs/archive/Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md`
  - Task B, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md`
- One-pass approved: `no`
- Status: `completed and archived`

## 2. Confirmed Baseline

Task A and Task B are complete. The current production baseline is:

- Full fallback imports work with `Credit`.
- Full fallback imports work with `Conduct Score`.
- Interim auto partial fallback imports work from the monitored Discord folder.
- Interim auto partial fallback imports preserve non-ASCII governor names.
- Partial fallback rows overlay the latest full `dbo.KingdomScanData4` snapshot and preserve absent fields.
- Location import remains unchanged.
- `shield_time_left` is stored as `ShieldEndsAtUnix` / `ShieldEndsAtUtc` and is visible on `v_PlayerProfile`.
- Task B selected raw text SQL staging plus explicit typed conversion as the Unicode-preserving path.

Delivery references:

- Task A mirror PR #179, production PR #487, SQL PR #21.
- Task B mirror PR #180, production PR #488, SQL PR #22.
- Task C Slice 1 mirror PR #181 and production PR #489.
- Production smoke testing completed on 2026-06-29:
  - full fallback with `Credit` succeeded
  - full fallback with `Conduct Score` succeeded
  - interim auto partial fallback with non-ASCII names succeeded
  - existing location shield import remained unchanged
- Slice 1 smoke testing completed successfully after production PR #489 review updates.

## 3. Completed Delivery

Task C completed its audit/scope phase and delivered the approved first implementation slice:

- Extracted fallback import file orchestration out of legacy `stats_module.py` into
  `services/fallback_import_service.py`.
- Extracted fallback import SQL/data-access helpers into `stats/dal/fallback_import_dal.py`.
- Kept `stats_module.py` as the compatibility entry point for current route, worker, and command
  callers.
- Preserved fallback import metadata, archive movement, CSV/XLSX generation, SQL procedure
  polling, and `FallbackImportBatchControl` recording behavior.
- Added focused DAL coverage in `tests/test_fallback_import_dal.py`.
- Made no SQL changes.
- Made no upload route changes.
- Made no Discord command changes.
- Made no durable audit implementation changes.

Validation completed during PR preparation:

- `.\.venv\Scripts\python.exe -m pytest -q tests`: `2065 passed, 2 skipped`.
- Focused fallback/stat tests passed.
- Queue/pipeline regression tests passed.
- Architecture, deferred optimisation, smoke import, and command registration validators passed.
- Review feedback fixed the `now_fn` typing annotation and an adjacent Pyright narrowing issue;
  follow-up validation reported `0 errors` with only environment missing-import warnings.

The remaining Task C work was promoted into Slice 2 and later deferred optimisation items. Slice 2
and Slice 3 are complete and archived. The active follow-up is:

`docs/task_packs/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3A Import Audit Batch Counter Normalization.md`

## 4. Task C Purpose

Task C captures the import architecture cleanup intentionally left out of Task B. The first pass
must audit and scope the work before any implementation.

Task C should answer:

1. Which import orchestration responsibilities should move out of legacy `stats_module.py`?
2. What durable batch audit and outcome tracking is needed for full fallback, interim partial
   fallback, and location imports?
3. Which upload route, queue worker, command, or operator surfaces are affected, if any?
4. Whether `dbo.UPDATE_ALL2` should stay as-is, be wrapped, be decomposed, or be replaced in a
   later approved SQL slice.
5. How to split the work into PR-sized implementation slices without regressing the Task A/B
   import contract.

## 5. In Scope For Audit

- Map fallback upload route and worker orchestration.
- Map the other upload routes and worker orchestration for locations, honor, prekvk, rally_forts,
  weekly_activity, mge-results, and inventory to ensure we have a complete picture before
  progressing.
- Map `stats_module.py` import responsibilities and current direct SQL/import side effects.
- Map `services/fallback_import_schema.py` boundaries after Task A/B.
- Map current fallback metadata and `dbo.FallbackImportBatchControl` usage.
- Design durable batch audit outcome/status tracking for import attempts, phases, row counts,
  source files, source type, SQL procedure outcome, and errors.
- Validate SQL object shapes in `C:\K98-bot-SQL-Server`.
- Review `dbo.IMPORT_STAGING_PROC`, raw fallback staging, `dbo.IMPORT_STAGING_CSV`,
  `dbo.IMPORT_STAGING`, and `dbo.UPDATE_ALL2` responsibilities.
- Identify command and route behavior that must remain unchanged.
- Produce implementation slices, rollback strategy, and test plan.

## 6. Explicitly Out Of Scope For The First Pass

- Code or SQL changes before audit approval.
- Broad `stats_module.py` service extraction implementation.
- Durable batch audit table/procedure implementation.
- Discord command changes.
- Upload route behavior changes.
- Replacing or substantially rewriting `dbo.UPDATE_ALL2`.
- Player-facing feature changes.
- Historical production data backfill.
- Committing real production player files as fixtures.

These items are Task C subject matter, but the first pass must only scope them and recommend
sequenced slices.

## 7. Required Reading

Before audit work, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`

Task-specific references:

- `docs/task_packs/archive/Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md`
- `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md`
- `docs/reference/deferred_optimisations.md`
- `docs/reference/archive/deferred_optimisations_resolved.md`
- `C:\K98-bot-SQL-Server\docs\SQL_DATA_MIGRATION_GUARDRAILS.md`
- `C:\K98-bot-SQL-Server\docs\SQL_PROMOTION_GUIDE.md`
- `C:\K98-bot-SQL-Server\docs\SQL_RELEASE_CHECKLIST.md`

## 8. Files And SQL Objects To Audit

Bot repo:

- `stats_module.py`
- `services/fallback_import_schema.py`
- `upload_routes/fallback_queue_route.py`
- `bot_helpers.py`
- `update_all2_log_manager.py`
- `tests/test_fallback_import_schema.py`
- `tests/test_stats_module.py`
- any focused queue/import tests discovered during audit

SQL repo:

- `sql_schema/dbo.IMPORT_STAGING_PROC.StoredProcedure.sql`
- `sql_schema/dbo.IMPORT_STAGING_CSV.Table.sql`
- raw fallback staging table introduced by Task B
- `sql_schema/dbo.IMPORT_STAGING.Table.sql`
- `sql_schema/dbo.FallbackImportBatchControl.Table.sql`
- `sql_schema/dbo.UPDATE_ALL2.StoredProcedure.sql`
- relevant Task A and Task B migrations

## 9. Audit Questions

- Where does the current import flow transition from Discord upload, queue state, local file
  generation, SQL import, metadata recording, and downstream rebuild?
- Which failures are currently visible only through logs or operator observation?
- What batch lifecycle states are needed: queued, started, staged, converted, downstream rebuild
  started, completed, failed, skipped, retried, or rolled back?
- Should batch audit live entirely in SQL, or should local metadata remain as a source-specific
  diagnostic artifact?
- Which status fields are operator-visible requirements and which are internal diagnostics?
- What minimum service/DAL boundary removes orchestration from `stats_module.py` without mixing in
  route/command behavior changes?
- Does `dbo.UPDATE_ALL2` need a wrapper, smaller procedures, output status, or only clearer
  logging in the first implementation slice?
- Which parts can be delivered independently while preserving all Task A/B smoke-test behavior?

## 10. Required Audit Output

Use this shape for the first response:

```markdown
**Scope Summary**
<what Task C covers, what remains out of scope for the first implementation slice>

**Current Import Flow**
<route, worker, stats_module, fallback schema, SQL procedures, metadata/audit>

**SQL Object Responsibilities**
<confirmed table/procedure shapes and ownership>

**Recommended Architecture**
<service/DAL split, durable audit model, UPDATE_ALL2 strategy>

**Implementation Slices**
<PR-sized sequence, each with risks and rollback>

**Validation Plan**
<focused tests, SQL validation, smoke tests, security review>

**Open Questions / Approval Needed**
<specific decisions for Chris>
```

## 11. Validation Plan For Later Implementation

The audit should choose exact validation commands, but likely gates include:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_fallback_import_schema.py tests\test_stats_module.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
```

SQL validation:

```powershell
cd C:\K98-bot-SQL-Server
.\deploy\Validate-SqlRepo.ps1
```

Smoke tests must continue to include:

- full fallback with `Credit`
- full fallback with `Conduct Score`
- interim auto partial fallback with non-ASCII names
- existing location shield import unchanged

## 12. Acceptance Criteria For Task C Audit

- [x] Current import flow is mapped from upload through downstream SQL rebuild.
- [x] SQL object responsibilities are confirmed from the SQL repo, not inferred from Python.
- [x] Service/DAL extraction scope is proposed before code changes.
- [x] Approved Slice 1 service/DAL wrappers are implemented without SQL, route, or command changes.
- [x] Durable audit outcome tracking design is promoted to the next active slice without
  implementation in Slice 1.
- [x] Command and route behavior changes are excluded from Slice 1.
- [x] `dbo.UPDATE_ALL2` strategy is scoped without wholesale replacement in Slice 1.
- [x] Implementation slices are PR-sized and ordered by safety.
- [x] Rollback and smoke-test strategy preserves the Task A/B baseline.
- [x] Deferred optimisation backlog is synchronized with the selected remaining Task C plan.
