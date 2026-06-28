# Codex Task Pack - Import Pipeline Deferred Optimisation Task B

## 1. Task Header

- Task name: `Import Pipeline Deferred Optimisation Task B`
- Date: `2026-06-28`
- Owner/context: `Chris Watts / K98 bot import reliability`
- Task type: `deferred optimisation | SQL import hardening | architecture cleanup`
- Depends on: completed Task A, archived at `docs/task_packs/archive/Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md`
- One-pass approved: `no`
- Status: `active task pack for next import optimisation slice`

## 2. Task B Confirmed Scope

Task B is the deferred optimisation follow-up to Task A. The confirmed first slice is:

> Replace the temporary ASCII-safe fallback CSV workaround with a Unicode-preserving SQL import
> path, while preserving all Task A behaviour for full fallback, interim auto partial fallback,
> and player-location shield imports.

Task A successfully restored production import reliability. It intentionally writes SQL bulk CSV
text in an ASCII-safe form because SQL Server `BULK INSERT` failed on text width/codepage handling
for `Name` values in the typed `dbo.IMPORT_STAGING_CSV` table. Task B must remove that compromise
and keep player names intact.

The broader import architecture cleanup remains valid but should be sequenced after the
Unicode-preserving import path unless Chris explicitly approves a larger batch.

## 3. Task A Delivery Baseline

Task A delivered:

- Fallback import accepts both `Credit` and `Conduct Score`.
- Full fallback imports work with the old `Credit` header.
- Full fallback imports work with the new `Conduct Score` header.
- Interim auto partial fallback files are accepted from the same Discord monitored folder.
- Partial fallback rows overlay the latest full `dbo.KingdomScanData4` snapshot by `Governor ID`.
- Absent partial-file fields are preserved rather than written as blank, null, or zero.
- `stats.csv` is emitted in the full 36-column `dbo.IMPORT_STAGING_CSV` order.
- Text columns in the generated SQL bulk CSV are currently sanitized/truncated to avoid
  SQL bulk-load failures.
- `stats_import_metadata.json` records source type, source filename, score header, columns
  present, rows in source, rows written, and generation timestamp.
- `dbo.FallbackImportBatchControl` records fallback import metadata for interim partial imports.
- Player-location import parses `shield_time_left` as a shield-end Unix timestamp.
- `ShieldEndsAtUnix` and `ShieldEndsAtUtc` are stored and exposed on `v_PlayerProfile`.
- Location import, shield visibility, full fallback import, and interim auto partial import were
  smoke tested successfully by the operator on 2026-06-28.

Task A branches and PRs:

- Mirror PR: `codex/import-schema-shield-time`, K98-bot-mirror PR #179.
- Production PR: `prod/import-schema-shield-time`, K98-bot PR #487.
- SQL PR: K98-bot-SQL-Server PR #21.

## 4. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

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
- `docs/reference/deferred_optimisations.md`
- `C:\K98-bot-SQL-Server\docs\SQL_DATA_MIGRATION_GUARDRAILS.md`
- `C:\K98-bot-SQL-Server\docs\SQL_PROMOTION_GUIDE.md`
- `C:\K98-bot-SQL-Server\docs\SQL_RELEASE_CHECKLIST.md`

For SQL-facing work, validate all schema, stored procedure, view, index, and `ProcConfig` details
against:

- `C:\K98-bot-SQL-Server`

## 5. Deferred Candidate Scoring

| Candidate | Impact | Frequency | Risk Reduction | Effort | Score | Decision |
|---|---:|---:|---:|---:|---:|---|
| Unicode-preserving fallback SQL import path | 4 | 4 | 4 | 3 | 9 | First Task B slice |
| Durable import batch audit outcome tracking | 4 | 4 | 4 | 3 | 9 | Good follow-up slice |
| Fallback import service/DAL extraction from `stats_module.py` | 4 | 3 | 4 | 4 | 7 | Follow-up after import contract is stable |
| Column-aware SQL import contract beyond fixed CSV order | 4 | 4 | 4 | 4 | 8 | Consider with or after Unicode path |
| Location import service consolidation/logging polish | 3 | 3 | 3 | 2 | 7 | Optional follow-up, not first blocker |

Batch rationale:

- The Unicode import path is first because it removes the only known Task A compromise while the
  smoke-tested behaviour is fresh and representative files are available.
- Durable audit and service extraction are valuable, but doing them before the import contract is
  Unicode-safe risks mixing reliability repair with broader restructuring.
- A raw text staging table or widechar import may also reduce fixed-order fragility; include only
  the minimum needed for the selected Unicode-safe design in the first PR.

## 6. First Slice Objective

Deliver a Unicode-preserving fallback import path that:

1. Preserves non-ASCII governor names from fallback full and interim auto partial source files.
2. Avoids SQL Server typed `BULK INSERT` conversion/truncation failures for text columns.
3. Preserves Task A source-type detection, partial overlay, score-header aliasing, and metadata.
4. Keeps `dbo.UPDATE_ALL2` and downstream stats behaviour compatible.
5. Removes or narrows the ASCII sanitization workaround once the SQL path is safe.

## 7. Candidate Technical Designs

Evaluate these during Task B audit and choose the smallest safe design.

### Option 1: UTF-16 Widechar Bulk File

- Generate a SQL import file in UTF-16.
- Update `dbo.IMPORT_STAGING_PROC` to bulk load with a widechar-compatible option.
- Preserve typed staging if SQL Server handles the text and numeric conversions reliably.
- Validate row terminators, delimiters, and quoting carefully.

### Option 2: Raw Text Staging Table

- Add a raw text staging table with all columns as `nvarchar(...)` or `nvarchar(max)`.
- Bulk load the generated CSV into raw text columns.
- Convert into typed `dbo.IMPORT_STAGING_CSV` or directly into canonical staging with explicit
  `TRY_CONVERT` logic.
- This is likely the most debuggable path because text ingestion is separated from typed
  conversion.

### Option 3: Parameterized/Batched Python Loader

- Avoid SQL `BULK INSERT` for fallback stats and insert rows through parameterized `pyodbc`
  batches.
- Preserves Unicode naturally and can keep typed parameters explicit.
- Must be benchmarked against the usual fallback row counts and transaction/log behaviour.

### Option 4: Keep ASCII Hotfix

- Not acceptable as the long-term Task B outcome.
- May remain as rollback or feature-flag fallback only.

## 8. In Scope

- Audit the live Task A implementation before changing code.
- SQL import path design for Unicode-preserving fallback `stats.csv` or equivalent payload.
- Bot-side output encoding and formatter changes needed by the selected SQL design.
- SQL repo migration/schema/procedure updates for the selected design.
- Tests covering non-ASCII names, padded text, long text, full fallback, interim partial fallback,
  and SQL-shape assumptions.
- Operator/deployment notes for SQL-before-bot rollout and rollback.
- Update or close the related deferred optimisation item.

## 9. Out Of Scope

- New Discord slash commands.
- New Discord upload channels.
- Player-facing shield countdown UI.
- Historical backfill of shield data.
- Dashboard/report redesign unrelated to import durability.
- Broad service extraction unless it is required by the chosen Unicode import path.
- Replacing `UPDATE_ALL2` wholesale.
- Committing real production player files as fixtures.

## 10. Mandatory Workflow

1. Audit current Task A code and SQL repo objects.
2. Confirm which Unicode import option is smallest and safest.
3. Stop for approval before implementation.
4. Implement the approved first slice only.
5. Run focused parser/service tests and SQL validation.
6. Smoke test with:
   - full fallback with `Credit`
   - full fallback with `Conduct Score`
   - interim auto partial fallback with non-ASCII names
   - existing location shield import path unchanged
7. Run or explicitly gate Codex Security review before PR handoff.

## 11. SQL Objects To Validate

Use `C:\K98-bot-SQL-Server` as source of truth for:

- `dbo.IMPORT_STAGING_CSV`
- `dbo.IMPORT_STAGING`
- `dbo.IMPORT_STAGING_PROC`
- `dbo.UPDATE_ALL2`
- `dbo.FallbackImportBatchControl`
- `dbo.KingdomScanData4`
- Any new raw staging table, if selected.
- Any migration scripts needed to deploy the selected design.

Validation questions:

- Does the live staging table width still truncate `Name`, `Alliance`, or other text columns?
- Does the bulk path parse quoted CSV and row terminators consistently?
- Are typed numeric conversions explicit and auditable?
- Can the SQL error output identify the source row/column without rerunning manual diagnostics?
- Does the design preserve existing `UPDATE_ALL2` behaviour and archive movement?

## 12. Python Areas To Validate

- `stats_module.py`
- `services/fallback_import_schema.py`
- tests around fallback import schema and stats module orchestration
- any new service/DAL helpers introduced for the selected design

Validation questions:

- Does `stats.xlsx` keep original source text?
- Does the generated SQL payload preserve Unicode where expected?
- Does partial overlay preserve absent full-snapshot fields?
- Does source metadata still distinguish full vs interim partial import?
- Is ASCII fallback limited to rollback or removed?

## 13. Testing Requirements

Minimum focused tests:

- Full fallback row with non-ASCII `Name` is preserved through the generated SQL payload.
- Interim auto partial row with non-ASCII `Name` overlays correctly.
- Padded `Name` and `Alliance` values do not exceed SQL staging widths or fail import.
- Existing numeric formatter still rejects fractional integer values.
- `Credit` and `Conduct Score` alias behaviour remains unchanged.
- Partial import preserves absent fields from latest SQL snapshot.

Baseline validation commands:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_fallback_import_schema.py tests\test_stats_module.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run --all-files
```

SQL repo validation:

```powershell
cd C:\K98-bot-SQL-Server
.\deploy\Validate-SqlRepo.ps1
```

## 14. Acceptance Criteria

- [ ] Task A behaviour remains green.
- [ ] Non-ASCII fallback governor names are preserved in the SQL-loaded path.
- [ ] Full fallback import works with `Credit`.
- [ ] Full fallback import works with `Conduct Score`.
- [ ] Interim auto partial fallback import works and preserves absent fields.
- [ ] `dbo.IMPORT_STAGING_CSV` or its replacement no longer fails on padded/non-ASCII `Name`.
- [ ] SQL migration and schema snapshots are aligned.
- [ ] `UPDATE_ALL2` remains compatible or has a documented backward-compatible change.
- [ ] Manual SQL diagnostic rerun is no longer required for ordinary import failures.
- [ ] Focused tests and selected validation gates pass.
- [ ] Deployment and rollback steps are documented.
- [ ] Deferred backlog is updated to show this item is delivered or superseded.

## 15. Deployment Notes

- Deploy SQL changes before bot code if the bot writes a new payload shape.
- Keep Task A ASCII-safe bot version as rollback until Task B smoke testing is complete.
- If the selected SQL design is additive, leave old tables/procs available during rollout.
- If import fails after SQL deployment, roll back bot code first and rerun the latest known-good
  full fallback import if data needs restoration.
- Smoke test full fallback, interim partial fallback, and location shield visibility before merge
  or production completion.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. Selected Task B option and rationale
3. Files changed
4. SQL changes
5. Behaviour preserved from Task A
6. Unicode/name-preservation evidence
7. Tests and validation
8. Security review
9. Deployment notes
10. Rollback notes
11. Remaining deferred optimisation items
