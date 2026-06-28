# Codex Task Pack - Import Pipeline Deferred Optimisation Task B

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task B`
- Date: `2026-06-28`
- Owner/context: `Chris Watts / K98 bot import reliability`
- Task type: `deferred optimisation | architecture cleanup | SQL import hardening`
- Depends on: `Task A - Import Process Schema Resilience and Shield Time Support`
- One-pass approved: `no`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by `docs/reference/README.md`.

Required task-specific references:

- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/task_packs/Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md`

For SQL-facing work, validate all schema, stored procedure, view, index, and `ProcConfig`
details against:

- `C:\K98-bot-SQL-Server`

Review SQL promotion docs before any SQL deployment:

- `C:\K98-bot-SQL-Server\docs\SQL_DATA_MIGRATION_GUARDRAILS.md`
- `C:\K98-bot-SQL-Server\docs\SQL_PROMOTION_GUIDE.md`
- `C:\K98-bot-SQL-Server\docs\SQL_RELEASE_CHECKLIST.md`

## 3. Objective

Task A provides the urgent compatibility fix for fallback import schema drift and player
location shield timestamps. Task B should convert that emergency-compatible path into a
cleaner, durable import architecture.

The finished work must:

1. Move fallback import normalization, partial-overlay behavior, and SQL snapshot reads out
   of legacy root-module orchestration and into clear service/DAL boundaries.
2. Replace fragile fixed-position import assumptions with explicit column-aware contracts.
3. Make full fallback imports, interim auto imports, and location imports auditable as
   durable batches with visible source type, field presence, row counts, and failure context.
4. Keep Task A behavior unchanged unless a specific improvement is approved and covered by
   tests.

## 4. Task A Baseline

Task A is expected to have delivered:

- `Credit` and `Conduct Score` accepted as score aliases for fallback import.
- Interim auto partial fallback files accepted from the same monitored Discord folder.
- Partial fallback files overlaid against the latest full SQL snapshot so absent fields are
  preserved.
- `shield_time_left` parsed as a Unix shield-end timestamp.
- `ShieldEndsAtUnix` and `ShieldEndsAtUtc` persisted through player-location staging,
  final storage, `v_PlayerProfile`, and cache contracts.
- `dbo.FallbackImportBatchControl` added as minimal import metadata/audit support.

Task B must begin by confirming the actual Task A merge state instead of assuming these
files or exact names still match the implementation.

## 5. Scope

### In Scope

- Fallback import service/DAL extraction and dependency cleanup.
- Explicit import batch model for full and interim fallback imports.
- Column-presence metadata and safer SQL merge/update semantics.
- Operator-friendly logging and failure reporting for file schema variants.
- Player-location import service consolidation if current route/service split still causes
  duplicate parsing or persistence behavior.
- Focused SQL migrations and schema snapshots required by the cleanup.
- Tests that preserve Task A behavior and cover the new architecture boundaries.
- Deployment and rollback plan for SQL plus bot code ordering.

### Out of Scope

- New Discord slash commands.
- New Discord upload channels.
- Player-facing shield countdown UI.
- Historical backfill of shield data before source files included `shield_time_left`.
- Broad dashboard/report redesign unrelated to import durability.
- Committing real production player files as fixtures.

## 6. Skills To Use

| Skill | Decision | Reason |
|---|---|---|
| `k98-architecture-scope` | `use` | Required before changing service/DAL boundaries. |
| `k98-sql-validation` | `use` | Required for import tables, procs, views, and migrations. |
| `k98-test-selection` | `use` | Required to select parser, service, route, SQL contract, and smoke tests. |
| `k98-deferred-optimisation-capture` | `use` | This is deferred optimisation delivery. |
| `k98-discord-command-feature` | `use if upload route behavior changes` | Use when Discord interaction, upload routing, or notifications are touched. |
| `k98-pr-review` | `use before PR handoff` | Required quality gate. |
| `k98-promotion-check` | `use before deployment/promotion` | Required for SQL and production rollout. |
| `codex-security:security-diff-scan` | `use before PR handoff` | File upload parsing and SQL writes are security-sensitive. |

## 7. Mandatory Workflow

Default workflow applies. Step 1 is review/scope only unless Chris explicitly approves
implementation.

1. Audit Task A final diff and current import architecture.
2. Identify the smallest PR-sized Task B slice.
3. Stop for approval with a concrete implementation plan.
4. Implement only the approved slice.
5. Run selected tests and SQL validation.
6. Run or explicitly gate the Codex Security review.
7. Produce delivery notes with remaining deferred items.

## 8. Audit Questions

Answer these before implementation:

- Which module owns fallback import orchestration after Task A?
- Which code reads the latest full SQL snapshot for interim partial overlay?
- Which code writes `stats.xlsx`, `stats.csv`, and metadata sidecars?
- Which SQL object is the durable audit source for import batches?
- Which stored procedures consume fallback import output and in what shape?
- Does SQL still depend on fixed CSV column order?
- Can a partial file introduce a new governor with incomplete non-present fields?
- Are import batch failures visible to operators without reading raw logs?
- Do location route and slash/import paths share one parser and one persistence service?
- Are tests using sanitized fixtures that represent the three observed real file shapes?

## 9. Architecture Targets

| Concern | Target |
|---|---|
| Discord upload routing | Thin route layer only: classify route, enqueue/dispatch, report status. |
| File reading | Service layer with explicit CSV/XLSX reader and sheet-selection policy. |
| Header normalization | Shared parser module with canonical schema and strict alias map. |
| Partial overlay | Service/DAL boundary with explicit latest-snapshot repository call. |
| SQL persistence | DAL/stored procedure path, no business logic in route modules. |
| Import batch audit | Durable SQL batch row with source type, filename, field presence, row counts, and outcome. |
| Tests | Unit tests for parser rules, service tests for overlay rules, route tests for dispatch, SQL validation for schema. |
| Security | Treat all upload content as untrusted operator input; validate before SQL/file writes. |

## 10. Candidate Implementation Slices

Choose one PR-sized slice unless Chris approves a larger batch.

### Slice B1: Fallback Import Service Boundary

- Extract fallback file read/normalize/overlay/write orchestration from `stats_module.py`.
- Introduce a service object or functional service module for:
  - reading source files
  - detecting source type
  - fetching latest snapshot through a DAL helper
  - writing canonical output
  - writing metadata sidecar or SQL batch metadata
- Keep `stats_module.py` as orchestration glue.

### Slice B2: Durable Import Batch Audit

- Expand `dbo.FallbackImportBatchControl` or introduce a related batch detail table.
- Record source type, filename, score header, columns present, row counts, status,
  started/completed timestamps, and error summary.
- Update bot code to mark success/failure around `UPDATE_ALL2`.
- Add operator-readable logs that include the batch id.

### Slice B3: Column-Aware SQL Import Contract

- Reduce dependency on fixed generated CSV column order where practical.
- Evaluate table-valued parameter, typed staging table, or explicit stored procedure
  contract for fallback imports.
- Preserve existing `UPDATE_ALL2` behavior while making absent partial columns explicit.

### Slice B4: Location Import Consolidation

- Confirm all location import paths use the same parser and persistence service.
- Add shield-field summary logging, for example total rows and active-shield rows.
- Keep profile command output unchanged unless separately approved.

## 11. Testing Requirements

At minimum, preserve all Task A tests and add focused tests for the selected slice.

Expected baseline commands:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

Likely focused tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_fallback_import_schema.py tests\test_stats_module.py tests\test_location_import_service.py
```

For broader service/DAL extraction, also run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe -m pre_commit run --all-files
```

SQL repo validation:

```powershell
.\deploy\Validate-SqlRepo.ps1
```

## 12. Acceptance Criteria

- [ ] Task A behavior remains green.
- [ ] Fallback import orchestration no longer concentrates parser, SQL snapshot, file output,
      and metadata concerns in a legacy root module.
- [ ] Partial import behavior is explicit and tested at the service boundary.
- [ ] Import batch audit data is durable enough to diagnose source type and field presence.
- [ ] SQL-facing changes are present in both migration and `sql_schema`.
- [ ] No new direct SQL is added to command modules or Discord route files.
- [ ] Route behavior remains backward-compatible for supported uploads.
- [ ] Focused and selected validation gates pass or are clearly justified.
- [ ] Codex Security review is run or intentionally left as a blocking handoff item.

## 13. Delivery Output

Use this delivery shape:

1. Summary
2. Task B slice delivered
3. Files changed
4. SQL changes
5. Behavior preserved from Task A
6. Tests and validation
7. Security review
8. Deployment notes
9. Remaining deferred optimisation items

## 14. Deployment Notes

- SQL changes must be backward-compatible and deployed before bot code that depends on them.
- Avoid destructive data changes. If a procedure body includes existing full-replace
  semantics, call this out separately from migration execution.
- For rollback, prefer redeploying the previous bot version while leaving nullable additive
  SQL columns in place unless a migration-specific issue requires SQL rollback.
- Validate with sanitized full fallback, interim fallback, and location CSV fixtures before
  production promotion.
