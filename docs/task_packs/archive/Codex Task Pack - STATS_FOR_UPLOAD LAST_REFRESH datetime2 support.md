# Codex Task Pack - STATS_FOR_UPLOAD LAST_REFRESH datetime2 support

## 1. Task Header

- Task name: `STATS_FOR_UPLOAD LAST_REFRESH datetime2 support`
- Date: `2026-06-07`
- Owner/context: User request to change `dbo.STATS_FOR_UPLOAD.LAST_REFRESH` from `date` to `datetime2`, with `KingdomScanData4.ScanDate` confirmed as UTC.
- Task type: `feature`
- One-pass approved: `no`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

`C:\K98-bot-SQL-Server`

## 3. Objective

Support `dbo.STATS_FOR_UPLOAD.LAST_REFRESH` as a UTC `datetime2` value end to end, preserving scan time instead of truncating to date. Keep bot cache, Discord embeds/cards, rankings footers, and Google Sheets exports stable and readable after the SQL schema change.

## 4. Background

Current SQL source-of-truth findings:

- `C:\K98-bot-SQL-Server\sql_schema\dbo.STATS_FOR_UPLOAD.Table.sql` defines `[LAST_REFRESH] [date] NULL`.
- `C:\K98-bot-SQL-Server\sql_schema\dbo.SP_Stats_for_Upload.StoredProcedure.sql` inserts `CAST(@MAXDATE AS date) AS [LAST_REFRESH]`.
- `@MAXDATE` is sourced from `MAX(ScanDate)` in `dbo.KingdomScanData4`.
- `KingdomScanData4.ScanDate` is confirmed UTC by the requester.
- `C:\K98-bot-SQL-Server\sql_schema\dbo.UPDATE_ALL.StoredProcedure.sql` also contains an older direct `STATS_FOR_UPLOAD` insert with `CAST(@MAXDATE AS DATE) AS LAST_REFRESH`.
- `dbo.UPDATE_ALL2` calls `dbo.SP_Stats_for_Upload`, so it should inherit the stored procedure fix.

Bot-side findings:

- `player_stats_cache.py` reads `SELECT * FROM dbo.[STATS_FOR_UPLOAD]` and maps `LAST_REFRESH` into `player_stats_cache.json`.
- `utils.score_player_stats_rec()` already parses ISO datetime values and prefers newer `LAST_REFRESH` values for dedupe.
- `build_KVKrankings_embed.py` shows the max `LAST_REFRESH` in ranking embed footers, currently by lexical string max.
- `kvk/services/kvk_stats_card_service.py` formats datetime strings as `YYYY-MM-DD HH:MM UTC`.
- `embed_utils.py` legacy stats embeds currently format `LAST_REFRESH` as date only.
- `config/sheet_config.json` marks `LAST_REFRESH` as a date column for Google Sheets export.
- `gsheet_module.py` formats configured date columns as `%Y-%m-%d %H:%M:%S`, so Sheets export can preserve time.

## 5. Scope

### In Scope

- Update SQL source-of-truth files in `C:\K98-bot-SQL-Server`:
  - `sql_schema\dbo.STATS_FOR_UPLOAD.Table.sql`
  - `sql_schema\dbo.SP_Stats_for_Upload.StoredProcedure.sql`
  - `sql_schema\dbo.UPDATE_ALL.StoredProcedure.sql` if still considered active or retained as operational fallback
- Add a deployable SQL migration script to alter the existing table column to `datetime2(2) NULL`.
- Preserve `LAST_REFRESH` as UTC scan timestamp from `KingdomScanData4.ScanDate`.
- Update bot display paths so user-visible output consistently shows date and time where appropriate.
- Keep cache serialization and dedupe behavior compatible with `date`, `datetime`, and `datetime2` values.
- Add or update focused tests for cache mapping, dedupe, rankings footer, stats card payload, and legacy embed formatting where practical.
- Document deployment order and rollback/compatibility notes.

### Out of Scope

- Changing the source type of `KingdomScanData4.ScanDate`.
- Redesigning player stats cache structure beyond `LAST_REFRESH` handling.
- Reworking KVK ranking sort/filter behavior unrelated to freshness display.
- Replacing legacy `embed_utils.py` flows with the newer KVK stats card architecture.
- Production promotion or bot-machine deployment.

## 6. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before implementation to confirm affected SQL, cache, display, and test surfaces. |
| `k98-discord-command-feature` | use | User-facing embeds/cards are affected, even though no slash command surface should change. |
| `k98-sql-validation` | use | Required for table datatype, stored procedure insert expression, migration order, and SQL repo alignment. |
| `k98-test-selection` | use | Required before validation to choose focused tests and quality gates. |
| `k98-deferred-optimisation-capture` | use if findings appear | Capture any out-of-scope legacy display or SQL fallback debt structurally. |
| `k98-pr-review` | use before merge or PR handoff | Validate architecture, SQL alignment, tests, and deployment notes. |
| `k98-promotion-check` | not applicable for implementation PR | Use only when preparing SQL deployment, production promotion, or bot-machine rollout. |
| `codex-security:security-scan` | use or justify skip | SQL/data access and exports are touched. Run before PR handoff unless changes are SQL-only with a documented skip decision. |

## 7. Mandatory Workflow

1. Audit and scope review, then stop for approval.
2. Validate SQL contract and proposed architecture, then stop for approval.
3. Present implementation plan, then stop for approval.
4. Implement SQL repo changes and bot mirror changes after approval.
5. Run focused validation and update tests.
6. Run or justify Codex Security review before PR handoff.

Proceed in one pass only if explicitly approved after this task pack.

## 8. Audit Requirements

Review these areas before coding:

- SQL table datatype and current deployment idempotency.
- Stored procedures and operational fallbacks that populate `STATS_FOR_UPLOAD`.
- Bot cache row mapping and JSON serialization of `date`, `datetime`, and `datetime2` values.
- Dedupe scoring for duplicate governor rows with same date but different scan time.
- Discord display strings for rankings and stats cards.
- Google Sheets export formatting for `LAST_REFRESH`.
- Tests that currently assume date-only strings.

Specific object searches:

```powershell
rg -n "STATS_FOR_UPLOAD|LAST_REFRESH" C:\K98-bot-SQL-Server
rg -n "STATS_FOR_UPLOAD|LAST_REFRESH" C:\discord_file_downloader
rg -n "CAST\(@MAXDATE AS date\)|CAST\(@MAXDATE AS DATE\)" C:\K98-bot-SQL-Server
rg -n "def _get_last_refresh|_fmt_last_refresh|score_player_stats_rec|LAST_REFRESH" C:\discord_file_downloader
```

## 9. Architecture Targets

| Concern | Target |
|---|---|
| SQL schema | SQL repo `sql_schema\dbo.STATS_FOR_UPLOAD.Table.sql` plus migration script |
| SQL refresh logic | SQL repo stored procedure files |
| Cache row mapping | `player_stats_cache.py` |
| Shared freshness parsing | `utils.py` or local helper if existing helper is unsuitable |
| Rankings display | `build_KVKrankings_embed.py` |
| Modern KVK stats card display | `kvk/services/kvk_stats_card_service.py` |
| Legacy embed display | `embed_utils.py` |
| Sheets export config | `config/sheet_config.json` only if format or naming needs explicit documentation |
| Tests | `tests/` focused existing files |

No new command modules, views, or command registration changes are expected.

## 10. Likely Files

### Review

- `C:\K98-bot-SQL-Server\sql_schema\dbo.STATS_FOR_UPLOAD.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.SP_Stats_for_Upload.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.UPDATE_ALL.StoredProcedure.sql`
- `C:\discord_file_downloader\player_stats_cache.py`
- `C:\discord_file_downloader\utils.py`
- `C:\discord_file_downloader\build_KVKrankings_embed.py`
- `C:\discord_file_downloader\embed_utils.py`
- `C:\discord_file_downloader\kvk\services\kvk_stats_card_service.py`
- `C:\discord_file_downloader\config\sheet_config.json`
- `C:\discord_file_downloader\gsheet_module.py`

### Modify

- `C:\K98-bot-SQL-Server\sql_schema\dbo.STATS_FOR_UPLOAD.Table.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.SP_Stats_for_Upload.StoredProcedure.sql`
- `C:\K98-bot-SQL-Server\sql_schema\dbo.UPDATE_ALL.StoredProcedure.sql` if retained as an active fallback
- `C:\discord_file_downloader\build_KVKrankings_embed.py`
- `C:\discord_file_downloader\embed_utils.py`
- `C:\discord_file_downloader\kvk\services\kvk_stats_card_service.py` if formatting needs consistency polish
- `C:\discord_file_downloader\tests\test_build_kvkrankings_embed.py`
- `C:\discord_file_downloader\tests\test_player_stats_cache.py`
- `C:\discord_file_downloader\tests\test_kvk_stats_card_payload.py`

### Create

- SQL migration script in the SQL repo, using the repo's existing migration/script convention if one exists.

## 11. Implementation Requirements

### SQL Requirements

- Change `dbo.STATS_FOR_UPLOAD.LAST_REFRESH` source definition to `datetime2(2) NULL`.
- Add a migration for existing databases:

```sql
ALTER TABLE dbo.STATS_FOR_UPLOAD
ALTER COLUMN LAST_REFRESH datetime2(2) NULL;
```

- Update `dbo.SP_Stats_for_Upload` from:

```sql
CAST(@MAXDATE AS date) AS [LAST_REFRESH]
```

to:

```sql
CAST(@MAXDATE AS datetime2(2)) AS [LAST_REFRESH]
```

- If `dbo.UPDATE_ALL` remains active, update its `CAST(@MAXDATE AS DATE)` expression to `CAST(@MAXDATE AS datetime2(2))`.
- Do not change the meaning of `LAST_REFRESH`: it must remain the UTC max scan timestamp for the refreshed stats snapshot.
- Do not add indexes on `LAST_REFRESH` unless a verified query path starts filtering or ordering by it.

### Bot Requirements

- Keep `player_stats_cache.py` compatible with `date`, `datetime`, and string values.
- Keep JSON cache output stable: `LAST_REFRESH` should serialize as an ISO-like string.
- Prefer UTC-aware parsing/display where possible. Naive SQL datetime values from `KingdomScanData4.ScanDate` may be treated as UTC because the source is confirmed UTC.
- Update rankings footer to compute max freshness by parsed datetime, with string fallback for compatibility.
- Update rankings footer and legacy embeds to display a readable UTC timestamp rather than raw ISO strings.
- Keep the modern KVK stats card format stable, preferably `YYYY-MM-DD HH:MM UTC`.
- Confirm Sheets export still emits `YYYY-MM-DD HH:MM:SS` for `LAST_REFRESH`; update tests/docs if there is coverage.

### Command Surface Governance

- [x] No slash command count, command group, command decorator, or command registration change is expected.
- [x] `scripts/validate_command_registration.py` can be skipped unless implementation unexpectedly touches command files.

## 12. Refactor Decisions

| Issue | Decision | Reason |
|---|---|---|
| Direct SQL in command/view layers | not applicable | Expected changes are SQL repo files, cache module, and render helpers only. |
| Business logic in interaction layers | not applicable | No command/view interaction flow should change. |
| Duplicate datetime formatting helpers | defer unless very small | Several local formatters exist; only consolidate if a small existing helper can be reused without broad churn. |
| Legacy `embed_utils.py` date-only freshness display | fix now | It directly affects user-visible support for the new field precision. |
| `build_KVKrankings_embed.py` lexical max for `LAST_REFRESH` | fix now | Datetime precision makes parsed comparison safer than raw string comparison. |
| Old `dbo.UPDATE_ALL` direct table insert | fix now if active, otherwise document | Leaving date truncation in a retained fallback can recreate inconsistent data. |

Any additional out-of-scope findings must be captured using:

```md
### Deferred Optimisation
- Area:
- Type: performance | architecture | cleanup | refactor | consistency
- Description:
- Suggested Fix:
- Impact: low | medium | high
- Risk: low | medium | high
- Dependencies:
```

## 13. Testing Requirements

Consider each category:

- Happy path: cache maps a SQL datetime value and display paths show date plus time.
- Negative path: missing, null, malformed, or date-only `LAST_REFRESH` does not crash.
- Regression: date-only values still display acceptably.
- Permission boundary: not applicable; no permission behavior changes.
- Restart/persistence: cache JSON remains parseable after process restart.
- Cache safety: duplicate governor rows prefer later timestamp when same status.
- Format/output shape: embeds/cards/Sheets display readable UTC timestamps.

Focused tests to add or update:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_player_stats_cache.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_build_kvkrankings_embed.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_payload.py
```

Consider adding or updating tests for:

- `utils.score_player_stats_rec()` comparing same-date different-time values.
- `build_KVKrankings_embed._get_last_refresh()` choosing the latest parsed timestamp.
- KVK stats card payload formatting `2026-06-03T07:53:12.34` as `2026-06-03 07:53 UTC`.
- Legacy `embed_utils` freshness formatting with datetime strings.
- `player_stats_cache._map_row()` preserving datetime values as ISO strings in the cache.

Baseline validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

Run broader validation before PR if runtime code changes are made:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
```

For SQL repo validation, use available SQL repo validation scripts or a deployment dry-run against a non-production database where practical.

## 14. Acceptance Criteria

- [ ] SQL source definition for `dbo.STATS_FOR_UPLOAD.LAST_REFRESH` is `datetime2(2) NULL`.
- [ ] Existing database migration alters the column to `datetime2(2) NULL`.
- [ ] `dbo.SP_Stats_for_Upload` no longer truncates `@MAXDATE` to date.
- [ ] Any retained active fallback procedure that populates `STATS_FOR_UPLOAD` no longer truncates `LAST_REFRESH`.
- [ ] Bot cache generation still writes valid JSON and preserves timestamp precision.
- [ ] Duplicate stat rows prefer the newer timestamp, not just the newer date.
- [ ] Rankings footer shows readable latest refresh timestamp.
- [ ] Modern KVK stats card shows readable UTC refresh timestamp.
- [ ] Legacy stats embed shows readable UTC refresh timestamp or has an explicit compatibility decision.
- [ ] Google Sheets export preserves date and time for `LAST_REFRESH`.
- [ ] Focused tests pass.
- [ ] SQL deployment order and rollback are documented.
- [ ] Codex Security review is run or skipped with a clear reason.

## 15. Deployment Steps

Recommended order:

1. Deploy SQL migration to alter `dbo.STATS_FOR_UPLOAD.LAST_REFRESH` to `datetime2(2) NULL`.
2. Deploy updated `dbo.SP_Stats_for_Upload`.
3. Deploy/update `dbo.UPDATE_ALL` only if it remains active or available as fallback.
4. Execute `dbo.SP_Stats_for_Upload` on a non-production or approved target database.
5. Verify sample data:

```sql
SELECT TOP (5)
    LAST_REFRESH,
    SQL_VARIANT_PROPERTY(LAST_REFRESH, 'BaseType') AS BaseType,
    SQL_VARIANT_PROPERTY(LAST_REFRESH, 'Scale') AS Scale
FROM dbo.STATS_FOR_UPLOAD
ORDER BY LAST_REFRESH DESC;
```

6. Deploy bot changes after SQL is compatible.
7. Rebuild `player_stats_cache.json`.
8. Verify a rankings embed, a modern KVK stats card, and the Sheets export path.

Compatibility note:

- If bot changes deploy before SQL changes, existing date-only values should still work.
- If SQL changes deploy before bot changes, cache parsing should mostly work already, but user-facing display may be raw or date-only until bot polish is deployed.

Rollback note:

- Rolling the column back to `date` truncates time precision. Only do this if losing scan-time detail is acceptable.
- A safer rollback is to leave the column as `datetime2(2)` and temporarily restore date-only display or insert behavior if needed.

## 16. AI Review Gates

- Codex Security: run or justify skipping because SQL/data access and export surfaces are touched.
- K98 PR review: run before merge or PR handoff.
- K98 promotion check: run before production SQL deployment or bot-machine rollout, not during initial implementation unless promotion is requested.

## 17. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. Helpers Reused
7. Refactor Findings
8. Test Plan
9. AI Review Gates
10. Deployment Steps
11. Deferred Optimisations

## 18. PR Summary Template

```md
## Summary

- Support `dbo.STATS_FOR_UPLOAD.LAST_REFRESH` as UTC `datetime2(2)`.
- Preserve scan time in SQL refresh output and render readable freshness timestamps in bot surfaces.

## Changes

- Updated SQL schema/procedure definitions to stop truncating `LAST_REFRESH` to date.
- Updated bot freshness formatting and ranking freshness selection.
- Added regression coverage for datetime freshness values.

## Tests

- `.\.venv\Scripts\python.exe -m pytest -q tests\test_player_stats_cache.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_build_kvkrankings_embed.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests\test_kvk_stats_card_payload.py`
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`

## AI Review Gates

- Codex Security: run, or skipped only with documented reason.

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- Risk: low to medium; SQL precision change is compatible with current bot parsing but display paths need polish.
- Rollback: preserve `datetime2(2)` when possible; reverting to `date` truncates scan-time detail.
```
