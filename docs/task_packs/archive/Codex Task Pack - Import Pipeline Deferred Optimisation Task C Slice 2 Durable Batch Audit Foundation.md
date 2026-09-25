# Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 2 Durable Batch Audit Foundation

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task C Slice 2 - Durable Batch Audit Foundation`
- Date: `2026-06-29`
- Owner/context: `Chris Watts / K98 bot import architecture`
- Task type: `deferred optimisation batch | import architecture | SQL audit | durable audit`
- Depends on:
  - Task A, archived at `docs/task_packs/archive/Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md`
  - Task B, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md`
  - Task C Slice 1, archived at `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Import Architecture and Service DAL Wrappers.md`
- One-pass approved: `no`
- Status: `complete; archived after mirror PR #182 and SQL PR #23 review/smoke validation`

Completion note: Task C Slice 2 delivered the generic SQL-owned durable import audit foundation
and fallback-first wiring. It added `dbo.ImportAuditBatch`, `dbo.ImportAuditPhase`, and SQL writer
procedures in the SQL repo; added bot DAL/service audit wrappers; correlated fallback imports to
`dbo.FallbackImportBatchControl`; preserved route, command, queue, staging, stored procedure, CSV/XLSX,
and output behavior; and smoke tested full fallback plus interim auto partial fallback audit rows on
2026-06-29. Remaining non-fallback adoption, `dbo.UPDATE_ALL2` wrapper instrumentation,
`dbo.IMPORT_STAGING_PROC` split, and `dbo.UPDATE_ALL2` decomposition are tracked as later slices.

## 2. Objective

Design and prepare the generic durable import batch audit foundation for the K98 import pipeline.
The model must be generic enough for fallback, location, honor, PreKvK, weekly activity, MGE, and
inventory imports, while keeping the first implementation slice behavior-preserving and reversible.

The first response for this slice must confirm the audit model, SQL object names, Python service/DAL
boundaries, and exact implementation boundaries before any code or SQL is changed.

## 3. Background

Task A and Task B restored and hardened the fallback import data contract:

- Full fallback imports work with `Credit`.
- Full fallback imports work with `Conduct Score`.
- Interim auto partial fallback imports work from the monitored Discord folder.
- Interim auto partial fallback imports preserve non-ASCII governor names.
- Partial fallback rows overlay the latest full `dbo.KingdomScanData4` snapshot and preserve absent fields.
- Location import remains unchanged.
- `shield_time_left` is stored as `ShieldEndsAtUnix` / `ShieldEndsAtUtc` and is visible on `v_PlayerProfile`.
- Task B uses raw text SQL staging plus explicit typed conversion for the Unicode-preserving fallback path.

Task C Slice 1 completed the first approved architecture extraction:

- `services/fallback_import_service.py` owns fallback file/source/metadata orchestration.
- `stats/dal/fallback_import_dal.py` owns fallback snapshot, batch-control, and `UPDATE_ALL2`
  status reads.
- `stats_module.py` remains the compatibility entry point for existing route, worker, and command callers.
- No SQL, upload route, or Discord command behavior changed.
- Smoke testing completed successfully after production PR #489.

The next agreed sequence is:

1. Add durable SQL-backed result/audit hooks without changing output behavior.
2. Later split `dbo.IMPORT_STAGING_PROC` responsibilities.
3. Later add `dbo.UPDATE_ALL2` wrapper/audit outputs.
4. Decompose `dbo.UPDATE_ALL2` only after audit data shows which phase fails or dominates runtime.

## 4. Source Deferred Items

### Deferred Optimisation
- Area: `services/fallback_import_service.py`, `stats/dal/fallback_import_dal.py`, `stats_module.py`, upload route/import worker flow, SQL repo import audit objects
- Type: architecture
- Description: Import attempts across fallback, location, honor, PreKvK, weekly activity, MGE, and inventory do not share a durable SQL-backed batch lifecycle model. Failures are still spread across logs, sidecar metadata, worker state, and procedure polling, which makes recovery and operator support harder.
- Suggested Fix: Design a generic import batch audit model with batch and phase/status records that can capture import kind, source file, source type, queue/upload context, row counts, staging outcome, SQL procedure outcome, downstream rebuild outcome, timestamps, errors, and retry/correlation identifiers. Implement the first approved behavior-preserving slice through service/DAL wrappers without route or command behavior changes.
- Impact: high
- Risk: medium
- Dependencies: Task C Slice 1 service/DAL wrappers completed in mirror PR #181 and production PR #489; SQL object design must be validated against `C:\K98-bot-SQL-Server` before implementation.

## 5. Candidate Scoring

| Candidate | Impact | Frequency | Risk Reduction | Effort | Score | Decision |
|---|---:|---:|---:|---:|---:|---|
| Generic durable import batch audit foundation | 5 | 5 | 5 | 4 | 11 | Include in Slice 2 |
| Non-fallback import route/worker audit adoption | 4 | 4 | 4 | 4 | 8 | Defer until foundation exists |
| `dbo.UPDATE_ALL2` wrapper and audit outputs | 4 | 5 | 4 | 3 | 10 | Defer to next SQL slice after foundation |
| Split `dbo.IMPORT_STAGING_PROC` responsibilities | 4 | 4 | 4 | 4 | 8 | Defer until audit hooks exist |
| Decompose `dbo.UPDATE_ALL2` into phase procedures | 5 | 4 | 5 | 5 | 9 | Defer until audit data supports the split |
| Residual legacy import orchestration cleanup in `stats_module.py` | 3 | 4 | 3 | 3 | 7 | Defer to later service extraction |

## 6. Scope

### In Scope

- Audit existing import batch/state surfaces for fallback, location, honor, PreKvK, weekly activity,
  MGE, and inventory.
- Validate current SQL objects in `C:\K98-bot-SQL-Server` before naming or implementing new objects.
- Design a generic SQL-backed durable import batch audit contract.
- Decide whether the first implementation should:
  - create only SQL objects and DAL/service helpers, or
  - create SQL objects and wire fallback imports first, leaving other import types for later slices.
- Preserve current route, command, queue, CSV/XLSX, staging, procedure, and output behavior.
- Preserve interim partial metadata protection; audit failures are best-effort except where metadata
  is needed to protect data.
- Keep local metadata sidecars as source-specific diagnostics unless the audit design explicitly
  replaces them with durable SQL state and a rollback plan.
- Add focused tests for the audit service/DAL and any fallback wiring approved for implementation.
- Update deferred optimisation tracking when the slice is complete.

### Out Of Scope

- Discord command changes.
- Upload route behavior changes.
- Queue UX or embed behavior changes.
- Non-fallback import behavior changes unless explicitly approved after audit.
- Replacing `FallbackImportBatchControl` without a compatibility plan.
- Splitting `dbo.IMPORT_STAGING_PROC`.
- Decomposing or replacing `dbo.UPDATE_ALL2`.
- Historical production data backfill.
- Operator UI/reporting dashboards for audit history.
- Committing real production player files as fixtures.

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
- `docs/task_packs/archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Import Architecture and Service DAL Wrappers.md`

SQL references:

- `C:\K98-bot-SQL-Server\docs\SQL_DATA_MIGRATION_GUARDRAILS.md`
- `C:\K98-bot-SQL-Server\docs\SQL_PROMOTION_GUIDE.md`
- `C:\K98-bot-SQL-Server\docs\SQL_RELEASE_CHECKLIST.md`
- SQL repo migration conventions and current import object definitions.

## 8. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before implementation to confirm service/DAL/SQL boundaries. |
| `k98-discord-command-feature` | not applicable | Commands must not change in this slice. Use only if audit discovers unavoidable command impact and stop for approval. |
| `k98-sql-validation` | use | Required for audit table/procedure design, migration ordering, and SQL repo validation. |
| `k98-test-selection` | use | Required before validation command selection. |
| `k98-deferred-optimisation-capture` | use | Required to split remaining import optimisation items and close completed ones. |
| `k98-pr-review` | use before PR handoff | Review architecture, SQL alignment, tests, and deferred tracking. |
| `k98-promotion-check` | use before production promotion | Required if SQL or production PR/deploy sequencing is involved. |
| `codex-security:security-scan` | use or justify skip | SQL/data access, file handling, imports, and persistence are security-sensitive surfaces. |

## 9. Files And SQL Objects To Audit

Bot repo:

- `stats_module.py`
- `services/fallback_import_service.py`
- `services/fallback_import_schema.py`
- `stats/dal/fallback_import_dal.py`
- `upload_routes/fallback_queue_route.py`
- relevant location, honor, PreKvK, weekly activity, MGE, and inventory upload routes/workers
- `bot_helpers.py`
- `update_all2_log_manager.py`
- `tests/test_fallback_import_schema.py`
- `tests/test_stats_module.py`
- `tests/test_fallback_import_dal.py`
- focused queue/import tests discovered during audit

SQL repo:

- `sql_schema/dbo.FallbackImportBatchControl.Table.sql`
- `sql_schema/dbo.IMPORT_STAGING_PROC.StoredProcedure.sql`
- `sql_schema/dbo.IMPORT_STAGING_CSV.Table.sql`
- raw fallback staging table introduced by Task B
- `sql_schema/dbo.IMPORT_STAGING.Table.sql`
- `sql_schema/dbo.UPDATE_ALL2.StoredProcedure.sql`
- Task A, Task B, and any Task C-related migrations
- existing SQL audit/status tables or procedures, if any

## 10. Required First Response

Use this shape and stop for approval before implementation:

```markdown
**Scope Summary**
<generic durable audit objective, first implementation boundary, explicit out-of-scope items>

**Current Import State Surfaces**
<where fallback/location/honor/PreKvK/weekly/MGE/inventory currently record queue, file, staging, procedure, output, and error state>

**SQL Design Proposal**
<proposed batch/phase/outcome tables or procedures, compatibility with FallbackImportBatchControl, migration/rollback plan>

**Service/DAL Architecture**
<Python modules, responsibilities, transaction/error handling, best-effort audit behavior>

**Implementation Boundary**
<SQL-only, DAL/service-only, fallback-first wiring, or other proposed slice; include risks>

**Remaining Slices**
<non-fallback adoption, IMPORT_STAGING_PROC split, UPDATE_ALL2 wrapper, UPDATE_ALL2 decomposition>

**Validation Plan**
<focused pytest, SQL validation, smoke tests, security review, promotion checks>

**Open Questions / Approval Needed**
<specific decisions for Chris>
```

## 11. Implementation Requirements After Approval

- Keep the model generic for all named import kinds even if only fallback is wired first.
- Use service/DAL boundaries; do not put audit SQL directly in routes or commands.
- Treat audit writes as best-effort unless missing metadata would risk partial fallback data protection.
- Preserve `FallbackImportBatchControl` compatibility until a later explicit replacement is approved.
- Preserve all current import output behavior.
- Keep rollback simple: dropping/disabling audit hooks must not break import execution.
- Add tests around audit success, audit failure best-effort behavior, partial metadata protection,
  and any procedure status mapping.
- Update task packs, starters, and deferred optimisation records after delivery.

## 12. Validation Plan

Baseline commands:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

Likely focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_fallback_import_schema.py tests\test_stats_module.py tests\test_fallback_import_dal.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_fallback_queue_route.py tests\test_processing_pipeline.py
```

Likely broad checks:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests
```

SQL validation:

```powershell
cd C:\K98-bot-SQL-Server
.\deploy\Validate-SqlRepo.ps1
```

Manual smoke tests after deployment must include:

- full fallback with `Credit`
- full fallback with `Conduct Score`
- interim auto partial fallback with non-ASCII names
- partial fallback overlay preserving absent fields
- existing location shield import unchanged
- audit records present for the wired import path without changing player-visible output

## 13. Acceptance Criteria

- [ ] Current import state/audit surfaces are mapped across all named import kinds.
- [ ] SQL object responsibilities and proposed new objects are validated against the SQL repo.
- [ ] The generic audit model can represent queued, started, staged, converted, procedure-started,
  downstream-rebuild-started, completed, failed, skipped, retried, and rolled-back states.
- [ ] The first implementation boundary is explicitly approved before code or SQL changes.
- [ ] Route and command behavior remains unchanged.
- [ ] `FallbackImportBatchControl` compatibility is preserved or migration is separately approved.
- [ ] `dbo.IMPORT_STAGING_PROC` and `dbo.UPDATE_ALL2` are not decomposed in this slice.
- [ ] Tests cover audit success, best-effort failure, and any approved fallback wiring.
- [ ] SQL validation and bot validation are run or documented.
- [ ] Remaining deferred items are updated after delivery.
