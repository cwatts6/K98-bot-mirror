# Codex Task Pack - Main Fallback Upload Conduct Field

## 1. Task Header

- Task name: `Main fallback upload Conduct field`
- Date: `2026-06-15`
- Owner/context: `Chris Watts / K98 Bot + SQL Server import pipeline`
- Task type: `feature | SQL schema/data pipeline | bot import update`
- One-pass approved: `no`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by `docs/reference/README.md`. Do not add every reference document to this task pack by default.

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

- `C:\K98-bot-SQL-Server`
- SQL Promotion Guide: `docs/reference/SQL_PROMOTION_GUIDE.md` or the current repo equivalent.
- SQL Release Checklist: `docs/reference/SQL_RELEASE_CHECKLIST.md` or the current repo equivalent.

Also review the current bot import/upload flow in the bot repository, especially the monitored fallback upload path and any scripts/modules it delegates to.

## 3. Objective

Add support for a new general governor reporting field named `Conduct`, sourced from the new `Credit` column in the main fallback upload file.

The change must update the SQL database schema, fallback import path, relevant import/staging/history/current/output tables, and bot-side file import logic so the new column imports safely and is available for downstream general player/kingdom reporting. This is a reporting-only point-in-time value, not a target, not KVK-specific, and not part of KVK performance scoring.

## 4. Background

The main fallback upload file received by the bot now contains an additional final column:

- Excel column: `AI`
- Source header: `Credit`
- Required database/output name: `Conduct`
- Sample workbook: `1198_15th June 26a_15Jun-05h57m.xlsx`
- Sample sheet: `Data`
- Sample used range inspected: `A1:AI404`
- Existing final source column before this change appears to be `AOO Avg Heal`; the new `Credit` column is now after it.

Business meaning:

- `Credit` in the source file must be imported and stored as `Conduct`.
- It is a percentage value.
- `100` means `100%` and is good.
- `0` means `0%` and is bad.
- All established governors should normally be `100%` at all times.
- New governors may have no value, so `NULL` must be accepted.
- No historical backfill is available before the first file containing this value.
- The value is point-in-time and reporting should always use the latest available value.
- This is a general governor value similar to `Power`, `RSS Gathered`, etc.
- This value is not KVK-related and must not be added into KVK scoring, KVK targets, DKP, KVK rankings, or KVK performance calculations.

The fallback queue route currently accepts `.xlsx`, `.xls`, and `.csv` attachments and queues matching uploads from monitored channels for worker processing. The task must trace what happens after the message is queued and update the actual parsing/import code, not only the route entry point.

## 5. Scope

### In Scope

- Audit the full main fallback upload path from Discord attachment queueing through file parsing, SQL import, staging, merge/update procedures, and reporting/output table generation.
- Confirm every SQL table, view, stored procedure, staging table, output table, export table, and cache populated by the main fallback upload that should carry a general governor point-in-time field.
- Add a nullable `Conduct` column to all relevant SQL objects.
- Map source header `Credit` to database/output field `Conduct`.
- Ensure the bot import/parser accepts both:
  - new files containing `Credit`
  - older files without `Credit`
- Ensure missing, blank, or invalid `Credit` values do not fail the whole import unless existing import validation standards require rejecting malformed numeric values.
- Ensure `Conduct` is treated as latest point-in-time data when producing current/general player reporting outputs.
- Update SQL stored procedures, views, merge statements, `INSERT` column lists, temp tables, table variables, output tables, and downstream SELECT projections as needed.
- Audit Google Sheet exports and explicitly document whether any export must change. Current expectation: no GSheet export changes are required, but this must be proven by audit.
- Update bot-side tests and SQL tests/smoke checks to cover the new column and backwards compatibility with old files.
- Update documentation or operator notes for the fallback upload format.

### Out of Scope

- Updating Discord embeds, player profile embeds, kingdom embeds, slash command responses, or other Discord display surfaces to show `Conduct`.
- Adding Conduct targets, thresholds, scoring, enforcement, ranking, alerts, or automated warnings.
- Adding KVK-specific Conduct reporting or KVK performance logic.
- Backfilling historical Conduct values before the first file containing `Credit`.
- Changing the source file header from `Credit`; the source remains `Credit` and the database/reporting name is `Conduct`.
- Major import pipeline redesign unless a blocking defect is discovered and approved separately.

## 6. Source Deferred Items

Not applicable. This is a new feature/data-contract update, not a deferred optimisation capture.

## 7. Codex Skills To Use

| Skill | Use when |
|---|---|
| `k98-architecture-scope` | Required before implementation to identify affected bot layers, SQL objects, data contracts, tests, and approval checkpoints. |
| `k98-discord-command-feature` | Not expected to apply because no slash command, view, modal, or embed output should be changed in this task. Use only if audit discovers command-surface impact. |
| `k98-sql-validation` | Required because this task touches SQL schema, stored procedures, staging/output tables, import contracts, and reporting views. |
| `k98-test-selection` | Required before validation to select focused bot/import/SQL tests and justify wider smoke tests. |
| `k98-deferred-optimisation-capture` | Required if audit discovers out-of-scope debt, duplicate import logic, brittle column mapping, direct SQL leakage, or reporting contract issues. |
| `k98-pr-review` | Required before PR handoff. |
| `k98-promotion-check` | Required before production promotion because both SQL deployment and bot deployment must be sequenced safely. |
| `codex-security:security-scan` | Required because the task touches file ingestion, SQL/data access, and user-controlled input from uploaded files. |

### Skill Decisions

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | `use` | Multi-layer data contract change across bot import and SQL reporting. |
| `k98-discord-command-feature` | `not applicable` | No command or Discord output changes are in scope. Reassess only if audit finds command-coupled import logic. |
| `k98-sql-validation` | `use` | SQL schema/procedure/view/output table changes are central. |
| `k98-test-selection` | `use` | Must select import parser, SQL migration, and regression tests. |
| `k98-deferred-optimisation-capture` | `use` | Capture brittle import column mapping or duplicated SQL/output logic if discovered. |
| `k98-pr-review` | `use` | Required before merge/handoff. |
| `k98-promotion-check` | `use` | Required due to SQL + bot deployment sequencing. |
| `codex-security:security-scan` | `use` | File import and SQL ingestion are security-sensitive surfaces. |

## 8. Mandatory Workflow

1. Audit / scope review, then stop for approval.
2. Architecture validation, then stop for approval.
3. Implementation plan, then stop for approval.
4. Implementation after approval.
5. Validation and final review.
6. Codex Security review because file upload/import and SQL ingestion are touched.

Proceed in one pass only if explicitly approved by the operator.

## 9. Audit Requirements

### 9.1 Bot upload/import audit

Trace the fallback upload path from Discord message receipt to SQL persistence:

- Entry route for monitored channel upload queueing.
- Worker/consumer that receives queued fallback upload jobs.
- Attachment download logic.
- Excel/CSV parser.
- Header validation / column normalisation.
- Dataframe/list-of-dicts transformation, if used.
- SQL insert/bulk-load call.
- Stored procedure execution after upload.
- Logging and error handling when the file has unexpected/missing columns.
- Tests covering fallback upload and import parsing.

Specific checks:

- Identify where the expected column list is defined.
- Identify whether column matching is positional, header-based, or mixed.
- If positional, update to tolerate the new trailing `Credit` column safely and consider whether header-based mapping should be used for this field.
- Confirm old files without `Credit` still import successfully with `Conduct = NULL`.
- Confirm new files with `Credit` import successfully with `Conduct` populated.
- Confirm CSV fallback, if supported for the same data shape, also handles the new column.

### 9.2 SQL audit

Search the SQL repository for all objects that reference the main governor import tables/fields. Include at least:

- Raw import tables.
- Current/latest governor tables.
- Staging tables.
- Archive/history tables.
- Output/reporting tables.
- Views used by bot/player/kingdom reporting.
- Stored procedures that ingest, transform, merge, refresh, or export player data.
- Table creation scripts and deployment/migration scripts.
- Any generated output table families used for general reporting.

Use SQL repo search terms including, but not limited to:

```text
KingdomScanData
Governor ID
GovernorID
governor_id
Rss Gathered
RSS_Gathered
Alliance Helps
AOO Avg Heal
latest_power
STAGING_STATS
EXCEL_FOR
STATS_FOR_UPLOAD
UPDATE_ALL
fallback
bulk insert
```

Expected SQL findings to confirm or correct during audit:

- Which `KingdomScanData*` tables receive the fallback file.
- Whether both current and archive/raw variants need `Conduct`.
- Whether `STAGING_STATS`, `STATS_FOR_UPLOAD`, `v_PlayerLatestStats`, `v_PlayerProfile`, kingdom summary views, or other general reporting objects should include it.
- Whether any KVK-specific objects reference the same base tables but must not project/use `Conduct` unless they are generic player snapshots.
- Whether output tables are dynamically generated and need dynamic SQL changes.
- Whether any stored procedure creates temp tables from `SELECT INTO` or explicit `CREATE TABLE` definitions that need column additions.

### 9.3 Google Sheet/export audit

Audit bot and SQL export paths to confirm whether `Conduct` needs any Google Sheet exposure in this task.

Current expectation:

- No GSheet export update is required in this task.

But Codex must verify:

- Existing general player exports do not require parity with SQL output tables.
- Any export that mirrors all current player fields will not break due to schema drift.
- If an export uses `SELECT *`, confirm whether adding `Conduct` would change output shape unexpectedly and fix or document it.

### 9.4 Data model and naming audit

- Source file header remains `Credit`.
- SQL/output/reporting field name must be `Conduct`.
- Use one canonical database column name: `Conduct`.
- Avoid introducing both `Credit` and `Conduct` into SQL.
- Avoid ambiguous naming such as `CreditPercent` unless explicitly approved.

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Discord upload route | Existing `upload_routes/` route/module; keep route thin. |
| File parsing/import mapping | Existing import/parser service/module, not commands/views. |
| SQL data access | Existing repository/DAL/import helper modules. |
| SQL schema | SQL repo under `sql_schema/` and/or current migration/deployment conventions. |
| SQL procedures/views | SQL repo object scripts for affected stored procedures, views, table scripts, and migrations. |
| Tests | Existing import/parser/SQL tests under `tests/`, plus SQL validation scripts where available. |
| Documentation | Existing docs/reference/operator notes for upload format and SQL promotion guide if applicable. |

## 11. Likely Files

Codex must audit and replace this list with confirmed paths from the current repos.

### Review

- `fallback_queue_route.py`
- `upload_routes/`
- `file_utils.py`
- `stats_module.py`
- `gsheet_module.py`
- modules/scripts that parse the fallback upload workbook
- modules/scripts that bulk insert or call SQL stored procedures after fallback upload
- tests for fallback upload routing/import/parsing
- `C:\K98-bot-SQL-Server\**\*.sql`
- SQL schema scripts for `KingdomScanData*`, staging, current/latest stats, profile/latest views, and output/reporting tables
- SQL stored procedures such as `UPDATE_ALL`, `UPDATE_ALL2`, and any procedures that build general player output/reporting tables

### Modify

Likely, subject to audit:

- Bot import parser/header mapping for the main fallback upload.
- Bot import tests/fixtures for old and new file shapes.
- SQL table schema scripts for raw/current/history player scan tables that store general governor snapshot values.
- SQL stored procedures that insert/merge/update from the raw import into reporting/output tables.
- SQL views/output tables used for general player/kingdom reporting.
- SQL migration/deployment script adding nullable `Conduct` columns.
- Documentation for upload column contract.

### Create

Likely, subject to audit:

- SQL migration script, for example `migrations/YYYYMMDD_add_conduct_to_main_fallback_upload.sql` or repo-standard equivalent.
- Test fixture using the new file shape or a minimal synthetic file with `Credit`.
- Optional SQL audit notes under `docs/` or task report if this repo convention exists.

## 12. Implementation Requirements

### 12.1 SQL schema requirements

- Add `Conduct` as nullable to all relevant persisted SQL tables.
- Recommended type: choose based on current numeric convention after audit.
  - Prefer `decimal(5,2) NULL` if percentage values may need decimals.
  - `int NULL` is acceptable only if all existing source values are whole-number percentages and existing schema conventions favour integer metrics.
- Do not use `NOT NULL` or default `100` because new governors and older imported rows may legitimately have no value.
- Add idempotent migration logic where repo conventions support it, for example guarded `ALTER TABLE ... ADD Conduct ...`.
- Update table creation scripts, not only migration scripts, so clean rebuilds include the column.
- Update explicit `INSERT`/`MERGE` column lists.
- Update temp table and table variable definitions.
- Update dynamic SQL output table builders where relevant.
- Avoid `SELECT *` dependencies; if they exist, either replace with explicit columns or document/fix the output shape risk.

### 12.2 SQL transform/reporting requirements

- The latest/current reporting value must use the latest imported `Conduct` value for each governor.
- Historical rows before this change should retain `NULL`.
- Do not calculate Conduct deltas.
- Do not add Conduct targets.
- Do not include Conduct in DKP, KVK score, kill/dead target logic, matchmaking calculations, or contribution scoring.
- Include `Conduct` only in general player/current/reporting output tables where a current governor snapshot field belongs.
- If a general kingdom-level report needs aggregate visibility, only expose it as reporting data after explicit approval; do not create enforcement logic.

### 12.3 Bot import requirements

- Map source header `Credit` to canonical field `Conduct` before SQL persistence.
- Accept files where `Credit` is missing; populate `Conduct = None`/`NULL`.
- Accept files where `Credit` is blank for some rows.
- Validate numeric values according to existing standards.
- Do not reject a full upload because new governors have blank Conduct.
- Ensure the new trailing column does not break positional column assumptions.
- Preserve current support for `.xlsx`, `.xls`, and `.csv` where that route applies.
- Add operational logging that records whether `Credit` was present and how many non-null Conduct values were imported, without logging excessive row-level data.
- Keep commands/views thin; import logic belongs in parser/service/DAL layers.

### 12.4 Backwards compatibility requirements

Test both file shapes:

1. Old fallback upload without `Credit`.
2. New fallback upload with `Credit` in column `AI`.

Both must complete import without breaking the worker flow or SQL procedure execution.

### 12.5 Command Surface Governance

This task should not create, move, rename, retire, or modify any slash command.

- [ ] Confirm top-level command count is unchanged.
- [ ] Confirm grouped subcommand count is unchanged.
- [ ] Do not update command registration baselines unless audit proves command-surface impact.
- [ ] If command-surface impact is discovered, stop and request approval before expanding scope.

## 13. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| Brittle positional import mapping breaks when source adds a trailing column | `fix now` if present | Directly affects this data-contract change and future upload resilience. |
| Duplicate fallback import parsing logic | `fix now` only if needed to safely support `Conduct`; otherwise `defer` | Avoid broad refactor unless required for correctness. |
| `SELECT *` in SQL output generation | `fix now` if it changes output shape or hides schema drift; otherwise `defer with evidence` | Schema changes can cause silent downstream breakage. |
| GSheet export parity gap | `defer` unless export breaks or operator approves adding Conduct to exports | User expectation is no GSheet export change in this task. |
| Discord embed/display gap for Conduct | `defer` | Explicitly out of scope and planned as a separate task. |

Deferred items must use the structured format from `docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 14. Testing Requirements

Use `k98-test-selection` before finalising the test set.

### Required coverage

- Happy path: new `.xlsx` file with `Credit = 100` imports and stores `Conduct = 100`.
- Backwards compatibility: old `.xlsx` file without `Credit` imports and stores `Conduct = NULL`.
- Blank value: row with blank `Credit` imports as `NULL`.
- Header mapping: `Credit` maps to SQL/output `Conduct`; no SQL column named `Credit` is introduced unless source staging conventions absolutely require source-name preservation and are approved.
- Regression: existing fallback upload route still queues supported file types.
- Regression: SQL post-import procedure still completes.
- Reporting shape: relevant general output/current player tables include `Conduct`; KVK-specific scoring outputs do not add or use it.
- GSheet audit: exports either remain unchanged safely or are updated only if audit proves required.

### Suggested validation commands

Run baseline architecture/deferred/test selection gates:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

Run focused tests identified by `scripts/select_tests.py`, likely including import/upload tests, parser tests, SQL-related tests, and fallback queue route tests.

For broader validation before PR handoff, consider:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\smoke_imports.py
```

For SQL validation, use repo-standard SQL deployment checks and a controlled non-production database if available:

```powershell
# Use the repo-standard SQL validation/deployment commands after audit identifies them.
# Validate idempotent migration.
# Validate clean schema creation scripts include Conduct.
# Validate import procedure with old and new sample-shaped data.
```

### Manual verification checklist

- [ ] Import the provided sample workbook into a non-production/dev database.
- [ ] Confirm row count matches expected input rows.
- [ ] Confirm `Conduct` is populated as `100` for sample rows where `Credit = 100`.
- [ ] Confirm `Conduct` allows `NULL`.
- [ ] Confirm latest/current player output has the latest Conduct value.
- [ ] Confirm no KVK target/performance scoring result changed unexpectedly.
- [ ] Confirm no GSheet export changed unless explicitly required by audit.

## 15. Acceptance Criteria

- [ ] Audit identifies every affected bot import file/module and SQL object.
- [ ] New source column `Credit` imports as canonical database/reporting field `Conduct`.
- [ ] Relevant persisted SQL tables include nullable `Conduct`.
- [ ] Relevant general current/output/reporting tables include `Conduct`.
- [ ] Import remains backwards compatible with files that do not contain `Credit`.
- [ ] Blank/missing Conduct values are accepted as `NULL`.
- [ ] Latest/current reporting uses the latest available Conduct value.
- [ ] No Conduct target, score, delta, KVK performance, DKP, or enforcement logic is added.
- [ ] Discord embeds/outputs are not changed in this task.
- [ ] GSheet exports are audited and either unchanged with justification or updated only where required to avoid breakage.
- [ ] SQL scripts are updated for both migration and clean rebuild paths.
- [ ] Tests cover new file shape, old file shape, blank values, and SQL/reporting output shape.
- [ ] Quality gates are run or documented with clear exceptions.
- [ ] Codex Security review is completed because file ingestion and SQL data access are touched.
- [ ] Deployment steps sequence SQL changes before bot import changes where required.
- [ ] SQL migration follows the SQL Promotion Guide workflow, including migration file, `sql_schema` snapshot updates where applicable, validation, backup readiness, deployment history verification, and drift check.
- [ ] SQL Release Checklist items are completed or explicitly marked not applicable in the delivery output.
- [ ] Rollback posture is declared using the current SQL release categories and is documented in the PR/deployment notes.
- [ ] Rollback steps are documented.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. Bot Import Changes
7. GSheet Export Audit Result
8. Helpers Reused
9. Refactor Findings
10. Test Plan and Results
11. AI Review Gates
12. Deployment Steps
13. Rollback Steps
14. Deferred Optimisations

## 17. SQL Deployment Governance

This task must follow the current K98 SQL deployment model, not an ad-hoc SSMS/manual change path.

### Required SQL repo workflow

- Create the SQL change in `C:\K98-bot-SQL-Server` on a SQL feature branch.
- Add one or more idempotent migration scripts under `migrations/`.
- Update matching expected-state scripts under `sql_schema/` for every altered table, view, procedure, or function where practical.
- Declare rollback posture in the migration metadata:
  - `Included` if a reviewed rollback script is provided.
  - `Manual` if rollback requires operator action.
  - `Forward Fix Only` if this is safest.
  - `Not Possible` only with clear restore/forward-fix notes.
- Because this is an additive nullable column change, expected posture is either:
  - `Rollback: Included` with a rollback script that removes the new nullable columns and restores affected object definitions, only if safe; or
  - `Rollback: Forward Fix Only` with explicit reason if removing the field after live imports could risk data/report inconsistency.
- Mark whether this is a data migration. Expected answer: schema/data-contract change only, unless backfill or repair SQL is added.
- Do not use emergency hotfix process unless production is broken and owner approval is recorded.

### Required SQL validation before PR

Run or document:

```powershell
cd C:\K98-bot-SQL-Server
.\deploy\Validate-SqlRepo.ps1
```

The PR must include:

- migration summary
- affected SQL objects
- rollback posture
- backup requirement
- bot dependency order
- validation output
- GSheet export audit result
- confirmation that KVK-specific outputs were not changed unless audit proves a generic dependency

### Required SQL deployment sequence

SQL must be deployed from merged `main`, using the deployment tooling.

On the bot machine:

```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
.\dev.ps1

cd C:\K98-bot-SQL-Server
git switch main
git pull origin main
git status
.\deploy\Validate-SqlRepo.ps1 -RepoPath C:\K98-bot-SQL-Server
.\deploy\Test-SqlBackupReadiness.ps1 `
  -RepoPath C:\K98-bot-SQL-Server `
  -ServerName "MINI_AMD" `
  -DatabaseName "ROK_TRACKER" `
  -BackupPath "C:\sql_backup"
.\deploy\Deploy-SqlMigration.ps1 `
  -RepoPath C:\K98-bot-SQL-Server `
  -ServerName "MINI_AMD" `
  -DatabaseName "ROK_TRACKER"
```

After deployment, verify migration history and deployment history:

```sql
SELECT TOP (20) *
FROM dbo.SchemaMigrationHistory
ORDER BY AppliedAtUtc DESC;

SELECT TOP (20) *
FROM dbo.DeploymentRunHistory
ORDER BY StartedAtUtc DESC;
```

Then run drift check:

```powershell
.\deploy\Invoke-DriftCheck.ps1 `
  -RepoPath C:\K98-bot-SQL-Server `
  -ServerName "MINI_AMD" `
  -DatabaseName "ROK_TRACKER"
```

### SQL/bot promotion ordering

Because bot code will read the new source column and SQL will store/project the new `Conduct` field:

1. Prefer backward-compatible SQL first:
   - nullable `Conduct` columns
   - updated procedures/views that tolerate missing/NULL values
   - no breaking change to old imports
2. Deploy SQL migration and confirm history/drift checks.
3. Deploy bot import/parser changes.
4. Run controlled import smoke using the provided sample workbook.
5. Run post-import SQL checks for the latest `Conduct` value.
6. Only after this task is complete should a separate task update Discord embeds or command outputs.

### Release checklist coverage

Before handoff, Codex must explicitly complete or mark not applicable the SQL release checklist areas:

- Pre-deployment validation
- Rollback review
- Data migration review
- Deployment
- Post-deployment drift check
- Bot dependency order
- Nightly export impact, if altered SQL snapshots affect export/drift expectations


## 17. Deployment Steps

Codex must refine these after audit, but the expected high-level sequence is:

1. Backup production database or confirm latest safe restore point.
2. Deploy idempotent SQL migration adding nullable `Conduct` columns.
3. Deploy updated SQL stored procedures/views/output table scripts.
4. Validate SQL object compilation.
5. Deploy bot import/parser changes.
6. Run controlled import with the provided sample file or approved test copy.
7. Confirm post-import stored procedure completes.
8. Confirm general output/current reporting tables contain `Conduct`.
9. Confirm no KVK scoring/output changed unexpectedly.
10. Monitor bot logs and SQL logs for fallback upload/import errors.

## 18. Rollback Steps

Codex must refine these after implementation, but include at least:

- Bot rollback: revert the bot import/parser deployment to the previous production version if the worker fails.
- SQL rollback: because nullable columns are additive, prefer disabling use of `Conduct` in procedures/views before dropping columns.
- If a procedure/view deployment causes issues, redeploy the previous known-good SQL object scripts from the SQL repo.
- Do not drop `Conduct` columns containing production data unless an explicit data-retention decision is made.
- If imports fail after bot deployment, temporarily process files with the previous file format or pause fallback processing until fixed.

## 19. PR Summary Template

```md
## Summary

- Added support for the new main fallback upload `Credit` source column as SQL/reporting field `Conduct`.
- Updated SQL schema/import/output objects for nullable point-in-time Conduct reporting.
- Updated bot import parsing to accept both old and new fallback upload file shapes.

## Changes

- Added nullable `Conduct` to relevant SQL tables and output/reporting objects.
- Mapped source header `Credit` to canonical field `Conduct`.
- Updated import parser/header validation and SQL insert/merge logic.
- Added tests for new file shape, old file shape, and blank Conduct values.
- Audited GSheet exports and documented whether they remain unchanged.

## Tests

- <test command and result>
- <SQL validation command/result>
- <manual sample import verification>

## AI Review Gates

- Codex Security: run, because file ingestion and SQL data access were touched.
- k98-pr-review: run.
- k98-promotion-check: run before production promotion.

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- Risk: additive schema change plus parser/import logic change could affect fallback upload processing if column mapping is brittle.
- Rollback: revert bot parser/import changes and redeploy previous SQL procedures/views; keep nullable columns unless explicitly approved to remove.
```

## 20. Codex Chat Starter

```md
Codex, start the task pack: `Codex Task Pack - Main Fallback Upload Conduct Field.md`.

Goal: update the main fallback upload pipeline so the new source file column `Credit` imports and stores as canonical SQL/reporting field `Conduct`.

Important business rules:
- Source header is `Credit`; database/output name is `Conduct`.
- Value is a percentage where 100 means 100% and good; 0 means 0% and bad.
- Nullable is required for old rows and new governors.
- Latest/current reporting should use the latest point-in-time value.
- No targets, scoring, enforcement, deltas, KVK logic, DKP, or Discord embed display changes in this task.
- Audit GSheet exports, but expectation is no GSheet export change unless required to prevent breakage.

Use the attached/new sample file shape as evidence: sheet `Data`, used range `A1:AI404`, final column `AI` header `Credit`.

Follow the mandatory staged workflow in the task pack: audit/scope first, architecture validation second, implementation plan third, then stop for approval before implementation unless explicitly approved otherwise.
```
