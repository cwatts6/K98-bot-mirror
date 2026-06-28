# Codex Task Pack - Import Process Schema Resilience and Shield Time Support

Status: completed and archived.

Completion record:

- Completed in mirror PR #179 (`codex/import-schema-shield-time`), production PR #487
  (`prod/import-schema-shield-time`), and SQL PR #21.
- SQL deployment completed successfully on 2026-06-28.
- Smoke testing confirmed full fallback import with `Credit`, full fallback import with
  `Conduct Score`, player-location import, shield timestamp visibility on `v_PlayerProfile`, and
  interim auto partial fallback import.
- Interim auto partial fallback rows were confirmed in `dbo.KingdomScanData4`: latest governor
  data matched the partial file updates while absent full-snapshot fields remained present.
- The delivered Task A hotfix includes temporary ASCII-safe formatting for the SQL bulk CSV path.
  The Unicode-preserving replacement is promoted to active Task B:
  `docs/task_packs/Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md`.

## 1. Task Header

- Task name: `Import Process Schema Resilience and Shield Time Support`
- Date: `2026-06-26`
- Owner/context: `Chris Watts / KD98 bot import reliability`
- Task type: `bug fix | feature | SQL migration`
- One-pass approved: `no`
- Final status: `delivered`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by `docs/reference/README.md`.
Do not add every reference document to this task by default.

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

- `C:\K98-bot-SQL-Server`

Also review the current promotion guide and SQL promotion/deployment guide before any production deployment.

## 3. Objective

Update the import stack so recent source-file schema changes are handled safely without breaking full fallback imports, interim auto imports, or player-location imports.

The finished work must:

1. Accept `Conduct Score` as the new fallback score column name while preserving backward compatibility with the previous `Credit` header.
2. Correctly process frequent interim auto fallback files that arrive in the same Discord monitored folder but contain only a subset of the full fallback columns.
3. Import and persist the new player-location `shield_time_left` timestamp field into SQL-backed player location storage and any relevant views/cache contracts.

## 4. Background

The import process now receives multiple schema variants:

| Source file | Observed shape | Meaning |
|---|---:|---|
| `1198_25th June 26a_25Jun-08h14m.xlsx` | Sheet `Data`, range `A1:AI408`, 35 columns | Full fallback snapshot. Sample still uses the old `Credit` header. |
| `1198_auto_ruins_27_before_25Jun-19h30m.xlsx` | Sheet `Data`, range `A1:AA173`, 27 columns | Interim auto snapshot. More frequent, same Discord folder, partial field set only. |
| `scan_1198.csv` | 9 columns | Player location snapshot now includes `shield_time_left`. |

Current attached route evidence:

- `upload_routes/fallback_queue_route.py` accepts `.xlsx`, `.xls`, and `.csv` attachments from monitored channels and enqueues the entire Discord message for worker processing.
- `DL_bot.py` routes player-location imports as a fast path before other upload routes, then falls back to the main monitored-channel queue.
- `upload_routes/player_location_route.py` currently targets `scan_1198.csv`, parses CSV bytes with `parse_output_csv`, and calls `load_staging_and_replace`.

Important interpretation:

- `shield_time_left` is not actually a duration in the sample; it is a Unix epoch timestamp for when the shield ends. Example: `1782483442`.
- A value of `0` means the player has no shield.
- Use UTC consistently for derived datetime values.
- The attached full fallback example still uses `Credit`, so implementation must support both old and new headers until all upstream files have moved to `Conduct Score`.

## 5. Scope

### In Scope

- Main fallback XLS/XLSX/CSV parser and import worker audit.
- Header normalization for `Credit` / `Conduct Score`.
- Interim auto fallback file detection and safe partial-field processing.
- SQL schema/procedure/view changes required by fallback import and player-location import.
- Player-location parser, staging load, final storage, and cache/view contract updates for `shield_time_left`.
- Import logging and Discord notification improvements where needed to make variant detection visible.
- Focused automated tests and sanitized fixtures for all three changes.
- Deployment sequencing and rollback notes.

### Out of Scope

- New slash commands.
- New Discord upload channels.
- Major redesign of the fallback import architecture beyond what is needed for schema-safe imports.
- Player-facing shield countdown UI unless an existing location/profile output already naturally exposes all location fields.
- Committing full real player-data sample files to the repo unless explicitly approved; prefer sanitized minimal fixtures.
- Historical backfill of shield values before the first source file that contains `shield_time_left`.

## 6. Codex Skills To Use

| Skill | Use when |
|---|---|
| `k98-architecture-scope` | Always before implementation, to identify affected routes, import workers, SQL objects, caches, tests, and approval checkpoints. |
| `k98-discord-command-feature` | Use because Discord upload routing and import notification flows are touched, even though no slash commands are added. |
| `k98-sql-validation` | Required. This task changes SQL import/storage contracts and may touch staging tables, procedures, views, indexes, or `ProcConfig`. |
| `k98-test-selection` | Required before validation to select focused import/parser/SQL/route tests. |
| `k98-deferred-optimisation-capture` | Required if audit finds import-worker debt, duplicate parsers, direct SQL leakage, weak fixture coverage, or queue-routing ambiguity outside this scope. |
| `k98-pr-review` | Required before PR handoff. |
| `k98-promotion-check` | Required before SQL deployment, production promotion, and bot-machine deployment. |
| `codex-security:security-scan` | Required because user-controlled files, SQL writes, and Discord upload surfaces are touched. |

### Skill Decisions

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | `use` | Import routes, workers, SQL storage, and caches must be mapped before changes. |
| `k98-discord-command-feature` | `use` | Upload routing/notification behavior is user-visible Discord flow. |
| `k98-sql-validation` | `use` | SQL schema/procs/views will likely change. |
| `k98-test-selection` | `use` | Must select targeted parser/import/SQL tests and fixture strategy. |
| `k98-deferred-optimisation-capture` | `use` | Capture out-of-scope import refactors or route consolidation findings. |
| `k98-pr-review` | `use` | Required quality gate. |
| `k98-promotion-check` | `use` | Required because SQL and production deployment sequencing matters. |
| `codex-security:security-scan` | `use` | File upload parsing and SQL ingestion are security-sensitive. |

## 7. Mandatory Workflow

Default workflow applies. Do not implement in one pass unless Chris explicitly approves after audit.

1. Audit / scope review, then stop for approval.
2. Architecture validation, then stop for approval.
3. Implementation plan, then stop for approval.
4. Implementation after approval.
5. Validation and final review.
6. Codex Security review because risk triggers apply.

The audit must include enough evidence to answer:

- Which Python module actually parses and persists the main fallback import after `fallback_queue_route.py` enqueues it?
- Which SQL tables/procedures receive fallback import data?
- Which SQL tables/procedures receive player location data?
- Which reports/views/cache layers depend on those tables?
- Does the current fallback importer overwrite missing columns with `NULL`/`0`, reject files, or silently mis-map columns?

## 8. Audit Requirements

Review the touched area for:

- Direct SQL in upload routes, import workers, commands, or views.
- Business logic in Discord routing layers that should live in parser/service modules.
- Duplicate import header mapping helpers.
- Separate full-file and partial-file importer paths that could drift.
- Missing operational logging for detected schema variant.
- Weak handling of missing columns, renamed columns, and unexpected extra columns.
- Cache invalidation or profile-cache warming implications.
- Restart-safety and queue idempotency for messages containing multiple attachments.
- Test coverage gaps for real source-file drift.

Map the likely:

- Discord routes:
  - `upload_routes/fallback_queue_route.py`
  - `upload_routes/player_location_route.py`
  - `DL_bot.py`
- Queue/worker/import modules discovered from `bot_helpers.channel_queues`, worker startup code, and existing fallback importer entry points.
- Parser/normalization helpers for fallback files.
- Player location importer:
  - `location_importer.py`
  - any repository/DAL code it calls.
- SQL objects:
  - fallback staging table(s)
  - fallback final/player stats table(s)
  - player location staging table(s)
  - player location final table(s)
  - relevant views used by profile/location commands
  - relevant import stored procedures
  - relevant indexes and `ProcConfig` rows
- Caches/signals:
  - `profile_cache`
  - `services.location_refresh_signal`
  - any SQL-backed caches used by `/player_profile`, `/player_location`, or map/location outputs.

## 9. Architecture Targets

| Concern | Target |
|---|---|
| Discord upload routing | Keep thin in `upload_routes/`; only route and report status. |
| File schema detection | Parser/service layer, not Discord route layer. |
| Header normalization | Shared import helper or fallback importer module. |
| Business rules for partial imports | Import service layer. |
| SQL writes | Repository/DAL/import stored procedures only. |
| SQL schema | SQL repo under `sql_schema/` and migration/deployment scripts. |
| Cache invalidation | Existing signal/cache modules. |
| Tests | `tests/` with sanitized fixtures and SQL contract checks where available. |
| Documentation | Update operator/import docs if they exist. |

## 10. Likely Files

### Review

- `upload_routes/fallback_queue_route.py`
- `upload_routes/player_location_route.py`
- `DL_bot.py`
- `bot_helpers.py`
- Worker startup/queue consumer modules discovered by audit.
- Main fallback importer modules discovered by audit.
- `location_importer.py`
- Any repository/DAL modules called by the fallback importer or location importer.
- Existing import fixture/test modules.
- SQL repo `C:\K98-bot-SQL-Server`

### Modify

To be confirmed by audit. Likely areas:

- Main fallback parser/header mapper.
- Main fallback import worker/service.
- Player location parser/load logic.
- SQL migration scripts for fallback import and location import.
- Views/procs that expose location/player data.
- Tests and sanitized fixtures.
- Operator/import documentation if present.

### Create

To be confirmed by audit. Likely:

- Sanitized fixture for full fallback file with `Credit`.
- Sanitized fixture for full fallback file with `Conduct Score`.
- Sanitized fixture for interim auto fallback file with 27-column partial schema.
- Sanitized fixture for location CSV with `shield_time_left`.
- SQL migration script(s) for `shield_time_left`.
- Focused import schema-contract tests.

## 11. Implementation Requirements

### 11.1 Main fallback import: `Credit` renamed to `Conduct Score`

Implement header normalization so both names are accepted:

| Incoming header | Canonical import field |
|---|---|
| `Credit` | `ConductScore` or existing score/credit canonical field |
| `Conduct Score` | same canonical field |

Requirements:

- Preserve backward compatibility with current files that still contain `Credit`.
- Add case/spacing tolerant normalization where practical, but do not silently map unrelated headers.
- If both `Credit` and `Conduct Score` appear in one file, fail safely with a clear error unless values are identical and the existing import policy supports duplicate aliases.
- Update import success/error logging to include the detected score header name.
- Update tests so old and new headers both produce the same canonical row shape.
- Do not rename final SQL columns casually if the current schema uses `Credit`; prefer parser-level aliasing unless there is a clear SQL/domain reason to rename.
- If SQL naming is changed, provide a backward-compatible view/alias or migration plan and explicit rollback.

### 11.2 Main fallback import: interim auto partial files in the same Discord folder

The importer must detect whether an uploaded fallback file is:

- `full_fallback_snapshot`
- `interim_auto_partial_snapshot`
- `unknown_or_invalid`

Based on headers and/or trusted filename patterns. Prefer header-based detection as the authority, with filename only as supporting metadata.

Observed interim auto columns from sample:

```text
Governor ID
Name
Power
Alliance
T1-Kills
T2-Kills
T3-Kills
T4-Kills
T5-Kills
Total Kill Points
Dead Troops
Healed Troops
City Hall
Civilization
Autarch Times
Ranged Points
KvK Played
Most KvK Kill
Most KvK Dead
Most KvK Heal
Acclaim
Highest Acclaim
AOO Joined
AOO Won
AOO Avg Kill
AOO Avg Dead
AOO Avg Heal
```

Observed full fallback columns from sample:

```text
Governor ID
Name
Power
Alliance
T1-Kills
T2-Kills
T3-Kills
T4-Kills
T5-Kills
Total Kill Points
Dead Troops
Healed Troops
Rss Assistance
Alliance Helps
Rss Gathered
City Hall
Troops Power
Tech Power
Building Power
Commander Power
Civilization
Autarch Times
Ranged Points
KvK Played
Most KvK Kill
Most KvK Dead
Most KvK Heal
Acclaim
Highest Acclaim
AOO Joined
AOO Won
AOO Avg Kill
AOO Avg Dead
AOO Avg Heal
Credit / Conduct Score
```

Partial-file safety requirements:

- A partial auto file must not be rejected solely because it lacks full fallback columns.
- A partial auto file must not overwrite fields that are absent from the file with `NULL`, `0`, empty string, or stale default values.
- If a field is present but blank, keep existing import blank-handling semantics for that field.
- Store enough batch metadata to distinguish full vs interim imports in logs/audit tables.
- Consider recording `columns_present` as JSON/NVARCHAR audit metadata if the existing import audit model can support it.
- Existing downstream reports must either:
  - read only fields that were actually updated, or
  - continue using latest known values for fields absent from interim files.
- If current SQL procedures expect a fixed full schema, update staging/proc design to support partial updates safely.
- Do not duplicate the full importer into a separate, drifting auto-import implementation unless audit proves this is necessary.

Suggested SQL implementation pattern:

1. Normalize incoming rows into a canonical dictionary with field-presence metadata.
2. Load rows into staging with nullable columns and source/batch metadata.
3. Pass source type and field-presence metadata to the merge/update procedure.
4. In merge logic, update only columns that are present for the batch/source type.
5. Preserve existing values for absent columns.

Acceptance examples:

- Full fallback file with old `Credit` imports successfully.
- Full fallback file with new `Conduct Score` imports successfully.
- Interim auto file imports successfully from the same Discord folder.
- Interim auto file updates present fields such as `Power`, kills, deaths, heals, Acclaim, and AOO averages.
- Interim auto file does not erase `Rss Assistance`, `Alliance Helps`, `Rss Gathered`, `Troops Power`, `Tech Power`, `Building Power`, `Commander Power`, or Conduct Score/Credit values.

### 11.3 Player location import: add `shield_time_left`

CSV header now includes:

```text
player_id,player_name,player_power,player_kills,player_ch,player_alliance,x,y,shield_time_left
```

Requirements:

- Update `parse_output_csv` to parse `shield_time_left`.
- Keep backward compatibility with older 8-column location CSV files where the field is absent.
- Validate the field as an integer Unix timestamp.
- Treat `0` as no shield.
- Store the raw incoming value in SQL as `BIGINT` or equivalent.
- Also store or expose a UTC `DATETIME2(0)` derived value where useful:
  - `0` -> `NULL`
  - positive epoch -> UTC datetime
- Use clear domain naming internally, for example:
  - incoming CSV field: `shield_time_left`
  - canonical raw field: `ShieldEndsAtUnix`
  - canonical derived field: `ShieldEndsAtUtc`
- Update location staging table(s), final location/player table(s), procedures, views, and repository code as needed.
- Update cache warming/invalidation if profile or location caches include location records.
- Add logging/import summary evidence for shield field support, for example count of rows with active shield timestamps.
- Do not display shield data in player-facing commands unless an existing output already exposes similar location snapshot data and product approval is clear.

Suggested SQL shape:

```sql
-- Names are illustrative; audit must confirm actual object names.
ALTER TABLE dbo.<LocationStagingTable>
ADD ShieldEndsAtUnix BIGINT NULL,
    ShieldEndsAtUtc DATETIME2(0) NULL;

ALTER TABLE dbo.<PlayerLocationFinalTable>
ADD ShieldEndsAtUnix BIGINT NULL,
    ShieldEndsAtUtc DATETIME2(0) NULL;
```

Suggested conversion:

```sql
CASE
  WHEN ShieldEndsAtUnix IS NULL OR ShieldEndsAtUnix = 0 THEN NULL
  ELSE DATEADD(SECOND, ShieldEndsAtUnix, CONVERT(DATETIME2(0), '1970-01-01'))
END
```

Guard against out-of-range timestamps. Invalid values should fail the import with a clear message or be rejected row-level according to existing location-import policy.

## 12. Command Surface Governance

- [x] This task should not change top-level slash command count.
- [x] This task should not add a grouped subcommand.
- [x] No command registration baseline change is expected.
- [ ] If audit discovers command output changes are necessary, document them explicitly and update canonical command docs/tests as required.
- [ ] Run or justify skipping:
  - `scripts/validate_command_registration.py`
  - `tests/test_validate_command_registration.py`
  - `tests/test_command_inventory.py`
  - `tests/test_command_registration_smoke.py`

## 13. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| Fallback importer cannot distinguish full vs partial source files | `fix now` | Required to import interim auto files safely. |
| Header aliasing is hard-coded or fragile | `fix now` | Required for `Credit` -> `Conduct Score`. |
| Player location SQL ignores extra CSV fields | `fix now` | Required for `shield_time_left` support. |
| Import worker has duplicate parser logic | `defer unless blocking` | Capture as deferred optimisation unless it prevents safe implementation. |
| Import audit metadata lacks source type/columns-present tracking | `fix now if needed, otherwise defer` | Needed if current SQL cannot safely preserve absent partial fields. |

Deferred items must use the structured format from `docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 14. Testing Requirements

Consider each category and either cover it or explain why it does not apply.

### Parser and fixture tests

- Full fallback XLSX with `Credit` header.
- Full fallback XLSX with `Conduct Score` header.
- Failure case with both `Credit` and `Conduct Score` where values conflict.
- Interim auto partial XLSX with observed 27-column schema.
- Interim auto partial file missing one required identity column, e.g. `Governor ID`, should fail cleanly.
- Location CSV with `shield_time_left`.
- Location CSV without `shield_time_left` remains backward-compatible.
- Location CSV with `shield_time_left = 0`.
- Location CSV with invalid non-numeric shield value follows existing error policy.

### SQL contract tests

Use the project’s available SQL validation/test pattern. At minimum validate:

- Migration scripts are idempotent or safely guarded.
- Staging and final tables include required shield columns.
- Location load/replace procedure persists shield values correctly.
- Full fallback merge updates all full fields.
- Partial fallback merge updates present fields only.
- Partial fallback merge preserves absent fields from the previous known record.
- Views/procs used by profile/location outputs remain valid.

### Discord route/worker tests

- `fallback_queue_route.py` still queues supported `.xlsx`, `.xls`, and `.csv` files from monitored channels.
- Worker/importer logs detected source type for full and interim auto files.
- Location fast path still handles only `scan_1198.csv` in the player-location channel.
- SQL headroom check behavior is preserved before write-heavy imports.

### Baseline commands

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

Add focused pytest commands after audit identifies exact test modules. Likely:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests -k "fallback or import or location"
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

For broader runtime changes, also consider:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
```

Before PR handoff, include the AI-assisted review gate decision:

- Codex Security review: required.

## 15. Acceptance Criteria

- [ ] Fallback full imports work with old `Credit` header.
- [ ] Fallback full imports work with new `Conduct Score` header.
- [ ] Fallback interim auto partial imports are accepted from the same Discord monitored folder.
- [ ] Partial imports update only fields present in the source file.
- [ ] Partial imports do not erase absent full-snapshot fields.
- [ ] Import logs/audit metadata clearly identify full vs interim source type and score header alias.
- [ ] Player location import parses `shield_time_left`.
- [ ] Player location SQL staging/final storage includes the shield field.
- [ ] `shield_time_left = 0` is handled as no shield.
- [ ] Positive shield timestamps are stored raw and/or exposed as UTC datetime according to agreed schema.
- [ ] Existing location import behavior remains backward-compatible for older CSVs.
- [ ] Relevant views/procs/caches remain valid.
- [ ] No new direct SQL exists in commands or Discord route files.
- [ ] Helper reuse was checked and documented.
- [ ] Logging is adequate for changed operational paths.
- [ ] Restart safety and queue behavior are preserved.
- [ ] Tests were added/updated or a clear testing exception is documented.
- [ ] Quality gates were run or documented.
- [ ] Codex Security review was run.
- [ ] SQL deployment order and rollback are documented.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. Import Schema Decisions
7. Helpers Reused
8. Refactor Findings
9. Test Plan
10. AI Review Gates
11. Deployment Steps
12. Rollback Plan
13. Deferred Optimisations

## 17. Deployment Steps

Draft sequence; refine after audit confirms exact SQL objects.

1. Take/verify SQL backup posture according to the SQL promotion guide.
2. Deploy backward-compatible SQL migration:
   - add nullable shield columns
   - add any fallback import metadata/partial-import support needed
   - update procs/views in a backward-compatible order
3. Run SQL validation against `C:\K98-bot-SQL-Server`.
4. Deploy bot code that writes/reads the new schema.
5. In staging/dev:
   - import sanitized full fallback fixture with `Credit`
   - import sanitized full fallback fixture with `Conduct Score`
   - import sanitized interim auto fixture
   - import sanitized location fixture with `shield_time_left`
6. Validate record counts and a sample governor/location row after each import.
7. Promote to production using the normal production-before-mirror flow.
8. Run one production smoke import using current live files.
9. Monitor import logs, live queue embed updates, SQL log headroom, and location refresh signal.

## 18. Rollback Plan

- If the bot import fails before SQL writes complete:
  - disable or stop the worker if needed
  - leave SQL migration in place if it is backward-compatible and nullable
  - redeploy previous bot version
- If partial fallback import writes incorrect data:
  - stop import worker
  - restore affected records from last full fallback snapshot or SQL backup
  - rerun the latest known-good full fallback import
- If location shield migration causes issues:
  - redeploy previous location importer
  - leave nullable columns unused until fixed, or rollback migration only if no downstream object depends on it
- If `Conduct Score` alias breaks import:
  - revert parser alias change
  - temporarily require old/full file shape until fixed
- Record the incident and add regression tests before retrying.

## 19. PR Summary Template

```md
## Summary

- Added fallback import header alias support for `Credit` / `Conduct Score`.
- Added safe handling for interim auto partial fallback files in the monitored import folder.
- Added player-location `shield_time_left` parsing and SQL persistence.

## Changes

- <change item>

## Tests

- <test command or verification>

## SQL Changes

- <migration/procedure/view summary>

## AI Review Gates

- Codex Security: run

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- Main risk is partial import incorrectly overwriting absent full-snapshot fields.
- Rollback is previous bot version plus rerun latest known-good full fallback import / SQL backup restore if needed.
```
