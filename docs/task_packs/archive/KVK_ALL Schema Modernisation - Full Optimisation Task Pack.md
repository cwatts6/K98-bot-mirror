KVK_ALL Schema Modernisation — Full Optimisation Task Pack

Status: archived completed programme. Phases 1 through 11 are complete, deployed or represented
in the SQL source-of-truth, smoke tested, and closed. This file is retained as the final programme
record and should not be used as an active task pack.

Objective
Modernise the full KVK_ALL pipeline around the new workbook schema.

This is a multi-phase optimisation and migration programme covering:

workbook schema validation
Python ingestion
SQL schema and stored procedures
recompute logic
export generation
Google Sheets output
Discord reporting
admin commands
operational diagnostics
restart and performance hardening
The authoritative workbook source is:

Full Data

Basic Data is out of scope and must not be used for ingestion, validation, or fallback behaviour. The additional rows in Basic Data are not required for the modernised pipeline.

Programme Status
Phase 1 is complete and deployed.

Phase 2 is complete and deployed.

Phase 3 is complete and deployed.

Phase 4 is complete and deployed.

Phase 5 is complete and deployed.

Phase 6 is complete and deployed.

Phase 7 is complete and deployed.

Phase 8 is complete and deployed.

Phase 9 is complete and deployed.

Phase 10 is complete and smoke-tested.

Phase 11 is complete and smoke-tested.

The KVK_ALL Schema Modernisation programme is closed. Future KVK_ALL work should start from a
fresh task pack rather than continuing this programme as Phase 12.

Completed Phase 1 scope:

strict Full Data workbook detection
Full Data tab is required
Basic Data is ignored and never used as fallback
fallback-to-second-sheet behaviour removed for KVK_ALL imports
all expected Full Data columns are validated before legacy coercion
schema version kvk_all_full_data_v2 is returned in import results
structured validation errors are returned for schema failures
focused tests cover valid schema, missing Full Data, missing required columns, and Basic Data ignored

Phase 1 changed Python-side workbook validation only. No SQL schema, stored procedure, recompute, export, Google Sheets, or Discord reporting behaviour was changed.

Completed Phase 2 scope:

additive SQL capacity added for Full Data v2 fields
nullable Full Data columns added to KVK.KVK_AllPlayers_Stage
nullable Full Data columns added to KVK.KVK_AllPlayers_Raw
schema/source metadata added to KVK.KVK_Scan
KVK.sp_KVK_AllPlayers_Ingest updated additively with optional metadata parameters
Full Data v2 fields are staged from Python without changing recompute/export/reporting contracts
source metadata is staged and passed into ingest
KVK_Ingest_Negatives can capture negative contribution deltas
production deployment SQL script added under sql/
focused schema/import contract tests added
deployment smoke confirmed DB columns and ingest metadata parameters exist

Phase 2 did not change recompute formula behaviour, export result-set order, Google Sheets tabs, Discord reporting display, admin command SQL ownership, or reporting DAL ownership.

Completed Phase 3 scope:

kvk_all_importer.py reduced to a compatibility wrapper around service and DAL layers
workbook parsing, Full Data selection, aliasing, schema validation, canonical mapping, coercion, and source metadata moved into kvk/services/kvk_all_import_service.py
stage column ordering, SQL staging, stage schema preflight, ingest procedure call, recompute call, KVK timestamp precheck, diagnostic writing, and negative count reads moved into kvk/dal/kvk_all_import_dal.py
Full Data v2 canonical mapping constants moved into kvk/schemas/kvk_all_schema.py
structured schema and coercion failures preserved
legacy import return dictionary shape preserved for DL_bot.py
Phase 2 schema/source metadata staging and ingest parameters preserved
unknown column reporting retained in schema metadata without changing Discord output
focused tests added for service mapping/validation, DAL call shape, wrapper compatibility, and existing schema behaviours
non-mutating workbook/service smoke validation completed against the uploaded sample workbook

Phase 3 did not change SQL schema, recompute formulas, export result-set order, Google Sheets tab names, Discord reporting display, admin command SQL ownership, or reporting DAL ownership.

Completed Phase 7 scope:

KVK admin SQL moved out of commands/stats_cmds.py for the Phase 7 in-scope admin workflows
KVK admin data access added in kvk/dal/kvk_admin_dal.py
KVK admin orchestration and command-facing result shaping added in kvk/services/kvk_admin_service.py
/kvk_recompute delegates recompute execution through the KVK admin service and DAL
/kvk_list_scans delegates recent scan loading and response table formatting through the KVK admin service and DAL
/kvk_window_preview delegates window preview loading through the KVK admin service and DAL
/kvk_export_all current-KVK resolution delegates through the KVK admin service and preserves existing Google Sheets export execution
command names, permissions, defer/followup behaviour, output copy, and operator workflow were preserved
SQL Server RowCount alias compatibility was fixed with [RowCount]
window preview embed output was capped to Discord's 1024-character field limit with a truncation marker
focused tests added for DAL/service result shape, command boundary handoff, SQL alias coverage, and window preview embed field limit
local smoke confirmed /kvk_export_all completes successfully
/kvk_window_preview smoke issues found during validation were fixed in follow-up PRs
the unrelated /my_stats_export direct SQL finding was captured structurally in docs/deferred_optimisations.md

Phase 7 did not change SQL schema, import behaviour, recompute semantics, export result-set contracts, Google Sheets tab names, Discord reporting display, Basic Data ingestion, summary tab ingestion, or Phase 5/6 service boundaries.

Completed Phase 8 scope:

KVK.KVK_AllPlayers_Stage gained an additive staged_at_utc retention marker for failed/stale stage row cleanup
KVK.KVK_Ingest_Diagnostics was introduced for durable ingest diagnostic visibility
KVK.sp_KVK_Ingest_Cleanup was introduced with dry-run default cleanup for stale stage rows, old ingest diagnostics, and old negative diagnostics
default retention policy documented and implemented as 24 hours for staged rows, 90 days for ingest diagnostics, and 365 days for negative diagnostics
cleanup refuses unsafe sub-1-hour or sub-1-day retention settings
cleanup does not run automatically during deployment or import
Python KVK_ALL ingest now records best-effort durable diagnostics for timestamp precheck rejections and ingest procedure failures where Phase 8 SQL is deployed
diagnostic context includes schema/source metadata, source filename, file hash, uploader ID, staged row count, and error/context payload where available
failed ingest procedure paths intentionally retain staged rows for inspection until explicit retention cleanup
coercion validation failures include structured validation context without changing Discord-facing import output
focused DAL/importer/SQL contract tests were added for diagnostic shape, best-effort diagnostic writes, retained failed stage rows, and cleanup SQL policy
production deployment script added under sql/kvk_all_phase8_ingest_retention.sql
production SQL smoke confirmed stage marker, diagnostics table, cleanup procedure, dry-run cleanup, and diagnostic insert visibility
the KVK_ALL upload routing follow-up was captured structurally in docs/deferred_optimisations.md

Phase 8 did not introduce Basic Data ingestion, summary tab ingestion, Discord reporting display changes, Google Sheets export contract changes, KVK export result-set changes, admin command redesign, automatic cleanup execution, or Phase 9 performance/restart hardening.

Programme closure:

Phase 11 Acclaim Output Contract Polish completed the final open KVK_ALL output-contract items.
No further KVK_ALL Schema Modernisation phase is planned.

Completion Rule
This work is not complete until all items previously identified as deferred optimisations are implemented or explicitly resolved inside this programme.

No remaining KVK_ALL pipeline debt should be left as deferred unless a new blocker is discovered and documented.

Required Reading
Before starting any phase, read:

README-DEV.md
docs/templates/Codex Task Pack Template.md
docs/K98 Bot - Project Engineering Standards.md
docs/K98 Bot - Coding Execution Guidelines.md
docs/K98 Bot - Testing Standards.md
docs/K98 Bot - Skills & Refactor Triggers.md
docs/k98 Bot - Deferred Optimisation Framework.md
docs/K98 Bot Deferred Optimisation Scoring Model.md
This task pack
The uploaded workbook sample:
downloads/kvk_all_sample_file/1086045_05_08_2026,_02_21_38_AM.xlsx
SQL repository:
C:\K98-bot-SQL-Server
SQL repo is authoritative for all SQL object validation.

Current Audit Summary
Workbook
The uploaded workbook contains:

Basic Data
Full Data
Summary
Summary Full
Only Full Data is authoritative for this migration.

Full Data contains 43 columns:

rank
governor_id
name
kingdom
campid
max_units_healed_difference
max_contribute_diff
minkill_points
minpower
mindead
mintroop_power
minmax_units_healed
minkills_iv
minkills_v
max_contribute_min
maxkill_points
maxpower
maxdead
maxtroop_power
maxmax_units_healed
maxkills_iv
maxkills_v
max_contribute_max
min_points
max_points
points_difference
min_power
max_power
cur_contribute_min
cur_contribute_max
power_difference
first_update
last_update
latest_power
kill_points_diff
power_diff
dead_diff
troop_power_diff
max_units_healed_diff
kills_iv_diff
kills_v_diff
cur_contribute_diff
healed_troops
Current Python Pipeline
Current path:

DL_bot.py
  -> kvk_all_importer.ingest_kvk_all_excel
      -> KVK.KVK_AllPlayers_Stage
      -> KVK.sp_KVK_AllPlayers_Ingest
      -> KVK.sp_KVK_Recompute_Windows
      -> optional gsheet_module.run_kvk_proc_exports_with_alerts
Current importer:

requires Full Data
rejects fallback sheets
maps legacy fields and Phase 2 Full Data capacity fields into stage rows
stages rank, raw min/max metric families, and contribution fields
returns schema version in the import result
persists schema/source metadata through the SQL ingest flow
does not warn on ignored known columns
Current SQL Pipeline
Reviewed SQL objects:

KVK.KVK_AllPlayers_Stage
KVK.KVK_AllPlayers_Raw
KVK.KVK_Player_Windowed
KVK.KVK_Kingdom_Windowed
KVK.KVK_Camp_Windowed
KVK.KVK_Scan
KVK.KVK_Player_Baseline
KVK.KVK_Ingest_Negatives
KVK.KVK_Windows
KVK.KVK_CampMap

KVK.sp_KVK_AllPlayers_Ingest
KVK.sp_KVK_Recompute_Windows
KVK.sp_KVK_Get_Exports

dbo.fn_KVK_Player_Aggregated
dbo.fn_KVK_Kingdom_Aggregated
dbo.fn_KVK_Camp_Aggregated
KVK.vw_FightingDataset
Current SQL supports legacy fields plus Phase 2 Full Data capacity fields:

points_difference
kill_points_diff
power_diff
dead_diff
troop_power_diff
max_units_healed_diff
healed_troops
kills_iv_diff
kills_v_diff
latest_power
rank
min_kill_points
max_kill_points
min_power_raw
max_power_raw
min_dead
max_dead
min_troop_power
max_troop_power
min_units_healed
max_units_healed
min_kills_iv
max_kills_iv
min_kills_v
max_kills_v
min_max_contribute
max_max_contribute
min_cur_contribute
max_cur_contribute
max_contribute_diff
cur_contribute_diff
schema_version
source_sheet_name
source_column_hash
source_column_count
source_row_count

It does not support:

summary tab reconciliation
Current Export/Reporting Coupling
gsheet_module.py currently assumes:

KVK.sp_KVK_Get_Exports returns exactly 10 result sets
result-set order is fixed
tab names are fixed
additional spreadsheets use hardcoded DataFrame indexes
comparison sheets assume fixed metric names
stats_alerts/allkingdoms.py contains direct SQL and assumes existing aggregate function output.

stats_alerts/embeds/kvk.py displays:

kills
KP
deads
DKP
healed
It does not display contribution metrics.

commands/stats_cmds.py contains direct SQL for KVK admin operations.

Canonical Schema Proposal
Canonical Source
Only Full Data should be accepted.

The importer should reject workbooks that do not contain a valid Full Data sheet matching the expected schema version.

Schema Version
Introduce a schema identifier:

kvk_all_full_data_v2
Persist at minimum:

schema_version
source_sheet_name
source_file_name
source_file_hash
source_column_hash
source_column_count
source_row_count
parsed_at_utc
uploader_discord_id
Naming Standard
Use snake_case canonical names.

Examples:

minkill_points          -> min_kill_points
maxkill_points          -> max_kill_points
minpower                -> min_power_raw
maxpower                -> max_power_raw
mindead                 -> min_dead
maxdead                 -> max_dead
mintroop_power          -> min_troop_power
maxtroop_power          -> max_troop_power
minmax_units_healed     -> min_units_healed
maxmax_units_healed     -> max_units_healed
minkills_iv             -> min_kills_iv
maxkills_iv             -> max_kills_iv
minkills_v              -> min_kills_v
maxkills_v              -> max_kills_v
max_contribute_min      -> min_max_contribute
max_contribute_max      -> max_max_contribute
cur_contribute_min      -> min_cur_contribute
cur_contribute_max      -> max_cur_contribute
Keep existing legacy fields during compatibility:

min_points
max_points
points_difference
min_power
max_power
power_difference
latest_power
kill_points_diff
power_diff
dead_diff
troop_power_diff
max_units_healed_diff
kills_iv_diff
kills_v_diff
cur_contribute_diff
healed_troops
Required Target Architecture
Python
Importer code should be split into:

kvk/
  schemas/
    kvk_all_schema.py
  services/
    kvk_all_import_service.py
    kvk_recompute_service.py
    kvk_export_service.py
    kvk_reporting_service.py
  dal/
    kvk_all_import_dal.py
    kvk_admin_dal.py
    kvk_reporting_dal.py
Exact paths may follow existing repo conventions, but responsibilities must be separated.

SQL
SQL changes belong in:

C:\K98-bot-SQL-Server\sql_schema
Use:

KVK.<ObjectName>.Table.sql
KVK.<ProcedureName>.StoredProcedure.sql
dbo.<FunctionName>.UserDefinedFunction.sql
KVK.<ViewName>.View.sql
Commands
Commands must remain thin.

commands/stats_cmds.py should not own SQL for:

recompute
scan listing
window preview
export orchestration details
Reporting
Reporting SQL should move out of stats_alerts/allkingdoms.py into DAL/service code.

Implementation Phases
Phase 1 — Schema Detection & Validation
Status
Complete and deployed.

Goal
Introduce strict Full Data schema detection before changing SQL behaviour.

In Scope
Detect workbook tabs.
Require Full Data.
Reject missing Full Data.
Reject fallback to second sheet.
Validate all expected Full Data columns.
Record schema version in import result.
Warn or fail on unknown columns depending on configured strictness.
Confirm Basic Data is ignored.
Add tests for valid and invalid workbook schemas.
Out of Scope
SQL schema migration.
New metric persistence.
Export changes.
Likely Files
kvk_all_importer.py
tests/test_kvk_all_importer.py
Potential new files:

kvk/schemas/kvk_all_schema.py
tests/test_kvk_all_schema.py
Acceptance Criteria
Importer only accepts Full Data.
Basic Data is never used.
Schema validation returns clear errors.
Tests cover valid full schema, missing sheet, missing required columns, and ignored basic data.

Completion Notes
Implemented in Python only:

kvk/schemas/kvk_all_schema.py
kvk_all_importer.py
tests/test_kvk_all_schema.py

Validation completed:

targeted schema tests passed
import smoke passed
command registration validation passed
architecture boundary validation passed
deferred item validation passed

No SQL, export, recompute, or reporting changes were made in Phase 1.
Phase 2 — Additive SQL Schema Migration
Status
Complete and deployed.

Goal
Add SQL capacity for the full workbook schema without breaking existing ingest/export behaviour.

In Scope
Add nullable columns to stage/raw or introduce versioned v2 tables.

Required persisted fields:

rank
min_kill_points
max_kill_points
min_power_raw
max_power_raw
min_dead
max_dead
min_troop_power
max_troop_power
min_units_healed
max_units_healed
min_kills_iv
max_kills_iv
min_kills_v
max_kills_v
min_max_contribute
max_max_contribute
min_cur_contribute
max_cur_contribute
max_contribute_diff
cur_contribute_diff
schema_version
source_sheet_name
source_column_hash
source_column_count
source_row_count
Update:

KVK.KVK_AllPlayers_Stage
KVK.KVK_AllPlayers_Raw
KVK.KVK_Scan or new ingest metadata table
KVK.sp_KVK_AllPlayers_Ingest
KVK.KVK_Ingest_Negatives
Out of Scope
Reporting display changes.
Discord embed changes.
Acceptance Criteria
Existing legacy import still works if required by compatibility tests.
New Full Data fields are persisted.
Ingest metadata is queryable.
SQL scripts are additive and rollback-safe.

Completion Notes
Implemented:

sql/kvk_all_phase2_full_data_capacity.sql
kvk_all_importer.py
tests/test_kvk_all_schema.py
docs/task_packs/archive/KVK_ALL Schema Modernisation - Phase 2 Initiation Statement.md

SQL deployment delivered:

nullable Full Data capacity columns on KVK.KVK_AllPlayers_Stage
nullable Full Data capacity columns on KVK.KVK_AllPlayers_Raw
schema_version, source_sheet_name, source_column_hash, source_column_count, and source_row_count on KVK.KVK_Scan
backward-compatible optional metadata parameters on KVK.sp_KVK_AllPlayers_Ingest
raw persistence of rank, min/max metrics, contribution metrics, and source metadata
negative diagnostics extended to max_contribute_diff and cur_contribute_diff

Python delivery:

Full Data v2 workbook columns are mapped into canonical stage column names.
schema/source metadata is added to staged rows.
ingest call passes schema/source metadata to SQL.
legacy import return fields and user-facing import behaviour are preserved.

Validation completed:

python -m pytest -q tests\test_kvk_all_schema.py
python scripts\validate_architecture_boundaries.py
python scripts\validate_deferred_items.py
python scripts\smoke_imports.py
python scripts\validate_command_registration.py
python -m black --check kvk_all_importer.py tests\test_kvk_all_schema.py
python -m pyright kvk_all_importer.py tests\test_kvk_all_schema.py
non-mutating workbook/importer smoke against downloads/kvk_all_sample_file/1086045_05_08_2026,_02_21_38_AM.xlsx
read-only SQL metadata smoke confirming deployed columns and ingest metadata parameters

No recompute, export, Google Sheets, Discord reporting display, admin command SQL extraction, or reporting DAL refactor changes were made in Phase 2.
Phase 3 — Importer Service/DAL Refactor
Status
Complete and deployed.

Goal
Resolve importer architecture debt and support the full schema cleanly.

In Scope
Extract workbook parsing/schema mapping from kvk_all_importer.py.
Extract SQL writes to DAL.
Keep Discord objects out of services/DAL.
Add structured import result object.
Include dropped/unknown column reporting.
Include source metadata.
Preserve existing user-facing import result fields.
Out of Scope
Recompute formula redesign.
Acceptance Criteria
kvk_all_importer.py becomes a compatibility wrapper or thin entrypoint.
SQL write logic lives in DAL.
Schema mapping is metadata-driven.
Tests cover mapping, coercion, validation, and DAL call shape.

Completion Notes
Implemented:

kvk_all_importer.py
kvk/schemas/kvk_all_schema.py
kvk/services/kvk_all_import_service.py
kvk/dal/kvk_all_import_dal.py
tests/test_kvk_all_schema.py
tests/test_kvk_all_import_service.py
tests/test_kvk_all_import_dal.py
tests/test_kvk_all_importer.py

Python delivery:

kvk_all_importer.ingest_kvk_all_excel remains the compatibility entrypoint.
Services and DAL do not depend on Discord types.
Workbook schema validation and mapping are testable outside the Discord/upload path.
SQL writes and stored procedure calls live in DAL code.
Phase 1 strict Full Data validation remains intact.
Basic Data remains intentionally ignored and is not used as fallback.
Phase 2 SQL metadata and Full Data capacity fields continue to be staged and passed through.
Existing legacy import return keys used by DL_bot.py remain compatible.
Unknown column reporting is available in schema metadata without changing user-facing Discord output.

Validation completed:

python -m pytest -q tests\test_kvk_all_schema.py tests\test_kvk_all_import_service.py tests\test_kvk_all_import_dal.py tests\test_kvk_all_importer.py
python -m black --check kvk_all_importer.py kvk\schemas\kvk_all_schema.py kvk\services\kvk_all_import_service.py kvk\dal\kvk_all_import_dal.py tests\test_kvk_all_schema.py tests\test_kvk_all_import_service.py tests\test_kvk_all_import_dal.py tests\test_kvk_all_importer.py
python -m ruff check kvk_all_importer.py kvk\schemas\kvk_all_schema.py kvk\services\kvk_all_import_service.py kvk\dal\kvk_all_import_dal.py tests\test_kvk_all_schema.py tests\test_kvk_all_import_service.py tests\test_kvk_all_import_dal.py tests\test_kvk_all_importer.py
python -m py_compile kvk_all_importer.py kvk\schemas\kvk_all_schema.py kvk\services\kvk_all_import_service.py kvk\dal\kvk_all_import_dal.py
python scripts\validate_architecture_boundaries.py
python scripts\validate_deferred_items.py
python scripts\smoke_imports.py
python scripts\validate_command_registration.py
python -m pyright kvk_all_importer.py kvk\schemas\kvk_all_schema.py kvk\services\kvk_all_import_service.py kvk\dal\kvk_all_import_dal.py tests\test_kvk_all_schema.py tests\test_kvk_all_import_service.py tests\test_kvk_all_import_dal.py tests\test_kvk_all_importer.py
non-mutating workbook/service smoke against downloads/kvk_all_sample_file/1086045_05_08_2026,_02_21_38_AM.xlsx

Pyright completed with 0 errors and local dependency-resolution warnings for pandas, pytest, pyodbc, and numpy in the sandboxed invocation.

No SQL, recompute formula, export, Google Sheets, Discord reporting display, admin command SQL extraction, or reporting DAL refactor changes were made in Phase 3.

Phase 4 — Recompute Modernisation
Status
Complete and deployed.

Goal
Modernise recompute to support new metrics and reduce performance risk.

In Scope
Add contribution metrics to recompute outputs if required:
max_contribute_gain
cur_contribute_gain
Decide and document source of truth for:
points_difference vs kill_points_diff
max_units_healed_diff vs healed_troops
raw min/max fields vs legacy diff fields
Review full-refresh behaviour.
Benchmark current recompute.
Add indexes where needed.
Consider incremental/window-aware recompute.
Keep existing output fields compatible.
SQL Objects
KVK.sp_KVK_Recompute_Windows
KVK.KVK_Player_Windowed
KVK.KVK_Kingdom_Windowed
KVK.KVK_Camp_Windowed
dbo.fn_KVK_Player_Aggregated
dbo.fn_KVK_Kingdom_Aggregated
dbo.fn_KVK_Camp_Aggregated
KVK.vw_FightingDataset
Acceptance Criteria
New contribution metrics are recomputed or explicitly excluded by rule.
Existing KP/kills/deads/healed outputs remain stable.
Recompute performance risk is measured.
Indexing plan is implemented or documented.
Tests cover recompute formulas using representative fixture data.

Completion Notes
Implemented:

docs/task_packs/archive/KVK_ALL Schema Modernisation - Phase 4 Metric Source Rules.md
sql/kvk_all_phase4_recompute_modernisation.sql
tests/test_kvk_all_recompute_sql_contract.py

SQL delivery:

Full Data v2 recompute precedence uses kill_points_diff for kill points with legacy/raw fallback.
Full Data v2 recompute precedence uses healed_troops for healed troops with legacy/raw fallback.
Raw min/max fields are retained as validation, reconciliation, and fallback inputs.
KVK.KVK_Player_Windowed, KVK.KVK_Kingdom_Windowed, and KVK.KVK_Camp_Windowed include max_contribute_gain and cur_contribute_gain.
KVK.sp_KVK_Recompute_Windows populates contribution gains while preserving existing KP, kills, deads, healed, DKP, baseline, kingdom, and camp output semantics.
KVK.sp_KVK_Get_Exports remained at 10 result sets.

No Google Sheets tab changes, Discord reporting display changes, admin command SQL extraction, reporting DAL refactor, Basic Data ingestion, or summary-tab ingestion were included in Phase 4.
Phase 5 — Export Contract Decoupling
Status
Complete and deployed.

Goal
Remove fragile coupling between SQL result-set order and Google Sheets output.

In Scope
Replace fixed result-set order assumptions.
Introduce named export sections or metadata result set.
Update gsheet_module.py to bind exports by name.
Keep current tab names stable unless deliberately versioned.
Add contribution fields to relevant exports.
Update additional spreadsheets:
PASS outputs
ALTAR outputs
ALL_WINDOW_COMPARISON
Likely Files
gsheet_module.py
KVK.sp_KVK_Get_Exports.StoredProcedure.sql
tests/test_gsheet_module.py
Acceptance Criteria
Export does not fail solely because a new result set is added.
Existing tabs still export.
New contribution columns export where applicable.
Tests cover result-set name binding and backward compatibility.

Completion Notes
Implemented:

kvk/services/kvk_export_service.py
gsheet_module.py
tests/test_kvk_export_service.py
tests/test_gsheet_module.py
tests/test_kvk_all_recompute_sql_contract.py
sql/kvk_all_phase5_export_contract_decoupling.sql
docs/task_packs/archive/KVK_ALL Schema Modernisation - Phase 5 Initiation Statement.md

SQL delivery:

KVK.sp_KVK_Get_Exports keeps the existing 10 result sets and existing section order.
Existing player, kingdom, and camp windowed/full result sets now include max_contribute_gain and cur_contribute_gain.
No new export result sets or Google Sheets tab names were introduced.
The local deployment script mirrors the SQL repo procedure change.

Python delivery:

KVK export result sets are bound to stable named sections before Google Sheets writing.
The current positional result-set contract remains supported as a compatibility path.
Compatible extra result sets can be ignored when all required named sections are present.
Primary KVK export tabs, PASS/ALTAR additional spreadsheets, and ALL_WINDOW_COMPARISON continue to use established spreadsheet and tab names.
Contribution metrics are exported through existing player, kingdom, and camp detail/full sections only.
No Discord reporting display changes were made.

Validation completed:

python -m pytest -q tests/test_kvk_export_service.py tests/test_gsheet_module.py tests/test_kvk_all_recompute_sql_contract.py
python -m black --check gsheet_module.py kvk/services/kvk_export_service.py tests/test_gsheet_module.py tests/test_kvk_export_service.py tests/test_kvk_all_recompute_sql_contract.py
python -m ruff check gsheet_module.py kvk/services/kvk_export_service.py tests/test_gsheet_module.py tests/test_kvk_export_service.py tests/test_kvk_all_recompute_sql_contract.py
python -m py_compile gsheet_module.py kvk/services/kvk_export_service.py
python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py
python scripts/select_tests.py
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
python -m pyright gsheet_module.py kvk/services/kvk_export_service.py tests/test_gsheet_module.py tests/test_kvk_export_service.py tests/test_kvk_all_recompute_sql_contract.py

Pyright completed with 0 errors and local dependency-resolution warnings for optional/runtime dependencies in the sandboxed invocation.

Post-deployment smoke completed:

KVK.sp_KVK_Get_Exports SQL script was applied.
Read-only SQL smoke confirmed the export procedure returns the expected 10 result sets.
Existing result-set order and section meaning were preserved.
Player, kingdom, and camp windowed/full export result sets include max_contribute_gain and cur_contribute_gain.
No 11th result set was introduced.
Google Sheets smoke confirmed existing primary tabs, additional PASS/ALTAR spreadsheets, and comparison tab names remain stable.
ALL_WINDOW_COMPARISON did not gain new contribution tabs.
Production promotion completed after local validation and smoke testing.

No Discord reporting change, admin command SQL extraction, reporting DAL refactor, Basic Data ingestion, or summary-tab ingestion was included in Phase 5.
Phase 6 — Reporting DAL & Discord Integration
Status
Complete and deployed.

Goal
Move reporting SQL into DAL/service and expose new metrics cleanly.

In Scope
Move SQL out of stats_alerts/allkingdoms.py.
Add reporting service for KVK all-kingdom blocks.
Add contribution metrics to reporting rows.
Decide where contribution metrics appear in Discord embeds.
Keep embed field lengths safe.
Preserve existing daily KVK embed behaviour.
Likely Files
stats_alerts/allkingdoms.py
stats_alerts/embeds/kvk.py
kvk/dal/kvk_reporting_dal.py
kvk/services/kvk_reporting_service.py
tests/test_kvk_reporting_service.py
tests/test_kvk_embed.py
Acceptance Criteria
No direct SQL remains in reporting presentation module.
Existing KVK embed still works.
Contribution metrics are available in structured rows.
Tests cover formatting and truncation.

Completion Notes
Implemented:

stats_alerts/allkingdoms.py
kvk/dal/kvk_reporting_dal.py
kvk/services/kvk_reporting_service.py
tests/test_kvk_reporting_service.py
tests/test_kvk_embed.py
docs/task_packs/archive/KVK_ALL Schema Modernisation - Phase 6 Initiation Statement.md

Python delivery:

KVK all-kingdom reporting SQL was moved out of stats_alerts/allkingdoms.py.
Reporting data access now lives in kvk/dal/kvk_reporting_dal.py.
Reporting block orchestration and row shaping now live in kvk/services/kvk_reporting_service.py.
stats_alerts/allkingdoms.py remains as a thin compatibility wrapper around load_allkingdom_blocks(kvk_no).
Existing Discord embed display, field names, links, titles, Top 5 layout, and truncation behaviour were preserved.
max_contribute_gain and cur_contribute_gain are available in structured reporting rows where SQL supports them.
Contribution metrics are not displayed in Discord embeds.

Validation completed:

python -m pytest -q tests/test_kvk_reporting_service.py tests/test_kvk_embed.py
python -m py_compile kvk/dal/kvk_reporting_dal.py kvk/services/kvk_reporting_service.py stats_alerts/allkingdoms.py tests/test_kvk_reporting_service.py tests/test_kvk_embed.py
python -m black --check kvk/dal/kvk_reporting_dal.py kvk/services/kvk_reporting_service.py stats_alerts/allkingdoms.py tests/test_kvk_reporting_service.py tests/test_kvk_embed.py
python -m ruff check kvk/dal/kvk_reporting_dal.py kvk/services/kvk_reporting_service.py stats_alerts/allkingdoms.py tests/test_kvk_reporting_service.py tests/test_kvk_embed.py
python -m pyright kvk/dal/kvk_reporting_dal.py kvk/services/kvk_reporting_service.py tests/test_kvk_reporting_service.py tests/test_kvk_embed.py
python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py
python scripts/select_tests.py
python scripts/smoke_imports.py
python scripts/validate_command_registration.py

Post-deployment smoke completed:

Read-only SQL smoke confirmed the service can load all expected reporting blocks for a known KVK.
Structured player, kingdom, camp, own kingdom, and own camp rows include max_contribute_gain and cur_contribute_gain.
Discord test embed smoke confirmed the existing display remains stable and contribution metrics are not rendered.
Production deployment completed after local validation and smoke testing.

No SQL schema changes, Google Sheets export contract changes, admin command SQL extraction, Basic Data ingestion, summary-tab ingestion, or unrelated rankings/history/personal KVK redesign were included in Phase 6.
Phase 7 — Admin Command SQL Extraction
Status
Complete and deployed.

Goal
Remove KVK admin SQL from command modules.

In Scope
Move SQL for:

/kvk_recompute
/kvk_list_scans
/kvk_window_preview
/kvk_export_all orchestration where appropriate
Into service/DAL modules.

Likely Files
commands/stats_cmds.py
kvk/dal/kvk_admin_dal.py
kvk/services/kvk_admin_service.py
tests/test_kvk_admin_service.py
Acceptance Criteria
Commands are thin.
Direct SQL is removed from command handlers.
Permission/defer/response behaviour remains unchanged.
Tests cover service handoff and core service logic.

Completion Notes
Implemented:

commands/stats_cmds.py
kvk/dal/kvk_admin_dal.py
kvk/services/kvk_admin_service.py
tests/test_kvk_admin_service.py
tests/test_stats_cmds.py
docs/task_packs/archive/KVK_ALL Schema Modernisation - Phase 7 Initiation Statement.md

Python delivery:

KVK admin command SQL for recompute, recent scan listing, and window preview was moved out of commands/stats_cmds.py.
KVK admin data access now lives in kvk/dal/kvk_admin_dal.py.
KVK admin orchestration and command-facing result shaping now lives in kvk/services/kvk_admin_service.py.
commands/stats_cmds.py remains responsible for Discord permissions, safe defer/followup flow, command inputs, and response rendering.
/kvk_export_all keeps the existing Google Sheets export execution path and delegates current-KVK resolution through the KVK admin service.
/kvk_export_all now reports export exceptions back to the operator instead of failing silently.
/kvk_window_preview preserves the existing embed/table shape and caps the field value to Discord's 1024-character embed field limit, appending a truncation marker when needed.
SQL Server compatibility for the window preview row-count alias was fixed by bracketing [RowCount].

Validation completed:

python -m pytest -q tests/test_kvk_admin_service.py tests/test_stats_cmds.py
python -m pytest -q tests/test_kvk_admin_service.py tests/test_stats_cmds.py tests/test_stats_service.py tests/test_mykvkstats.py
python -m black --check commands/stats_cmds.py kvk/dal/kvk_admin_dal.py kvk/services/kvk_admin_service.py tests/test_kvk_admin_service.py tests/test_stats_cmds.py
python -m ruff check commands/stats_cmds.py kvk/dal/kvk_admin_dal.py kvk/services/kvk_admin_service.py tests/test_kvk_admin_service.py tests/test_stats_cmds.py
python -m py_compile commands/stats_cmds.py kvk/dal/kvk_admin_dal.py kvk/services/kvk_admin_service.py tests/test_kvk_admin_service.py tests/test_stats_cmds.py
python -m pyright kvk/dal/kvk_admin_dal.py kvk/services/kvk_admin_service.py tests/test_kvk_admin_service.py tests/test_stats_cmds.py
python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py
python scripts/select_tests.py
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
git diff --check

Smoke validation completed:

/kvk_export_all completed successfully after Phase 7 deployment.
/kvk_window_preview initially surfaced a SQL Server RowCount alias issue; fixed in the Phase 7 follow-up hotfix.
/kvk_window_preview then surfaced a Discord 1024-character embed field limit issue; fixed in the Phase 7 follow-up hotfix.

No SQL schema changes, Google Sheets export contract changes, KVK export result-set changes, Discord reporting display changes, Basic Data ingestion, summary tab ingestion, operational retention cleanup, or end-to-end performance/restart hardening were included in Phase 7.

Phase 8 — Operational Cleanup & Retention
Status
Complete and deployed.

Goal
Make ingest diagnostics and failed stage rows operationally safe.

In Scope
Define retention policy for failed stage rows.
Add cleanup stored procedure or script.
Add ingest audit visibility.
Include schema metadata in diagnostics.
Include failed column validation context.
Avoid unbounded growth of diagnostic data.
SQL / Script Candidates
KVK.KVK_AllPlayers_Stage
KVK.KVK_Ingest_*
scripts/
Acceptance Criteria
Failed ingest diagnostics are inspectable.
Old diagnostics can be cleaned safely.
Cleanup does not remove active ingest tokens.
Runbook notes exist.

Completion Notes
Implemented:

sql/kvk_all_phase8_ingest_retention.sql
kvk/dal/kvk_all_import_dal.py
kvk_all_importer.py
tests/test_kvk_all_import_dal.py
tests/test_kvk_all_importer.py
tests/test_kvk_all_recompute_sql_contract.py
docs/task_packs/archive/KVK_ALL Schema Modernisation - Phase 8 Initiation Statement.md

SQL delivery:

KVK.KVK_AllPlayers_Stage gained staged_at_utc with a sysutcdatetime() default and supporting age-based index.
KVK.KVK_Ingest_Diagnostics was added for durable ingest diagnostic visibility.
KVK.sp_KVK_Ingest_Cleanup was added with dry-run default cleanup.
Default retention policy is 24 hours for staged rows, 90 days for ingest diagnostics, and 365 days for negative diagnostics.
Cleanup validates retention values before deleting and does not run automatically during deployment.

Python delivery:

KVK_ALL timestamp precheck rejections record best-effort durable diagnostics where Phase 8 SQL is deployed.
KVK_ALL ingest procedure failures record best-effort durable diagnostics while retaining staged rows for operator inspection.
Diagnostic payloads include schema/source metadata, source filename, file hash, uploader ID, staged row count, error text, and context JSON where available.
Coercion validation failures include structured validation context without changing Discord-facing import output.
Diagnostic writes are best-effort and do not make imports fail harder if the Phase 8 SQL table is unavailable.

Validation completed:

python -m pytest -q tests
python -m pytest -q tests/test_kvk_all_import_dal.py tests/test_kvk_all_importer.py tests/test_kvk_all_schema.py tests/test_kvk_all_import_service.py tests/test_kvk_all_recompute_sql_contract.py
python -m black --check kvk/dal/kvk_all_import_dal.py kvk_all_importer.py tests/test_kvk_all_import_dal.py tests/test_kvk_all_importer.py tests/test_kvk_all_recompute_sql_contract.py
python -m ruff check kvk/dal/kvk_all_import_dal.py kvk_all_importer.py tests/test_kvk_all_import_dal.py tests/test_kvk_all_importer.py tests/test_kvk_all_recompute_sql_contract.py
python -m py_compile kvk/dal/kvk_all_import_dal.py kvk_all_importer.py tests/test_kvk_all_import_dal.py tests/test_kvk_all_importer.py tests/test_kvk_all_recompute_sql_contract.py
python -m pyright kvk/dal/kvk_all_import_dal.py kvk_all_importer.py tests/test_kvk_all_import_dal.py tests/test_kvk_all_importer.py tests/test_kvk_all_recompute_sql_contract.py
python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py
python scripts/select_tests.py
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
git diff --check

Production smoke completed:

staged_at_utc column exists on KVK.KVK_AllPlayers_Stage.
KVK.KVK_Ingest_Diagnostics exists and accepts insert smoke rows.
KVK.sp_KVK_Ingest_Cleanup exists.
Dry-run cleanup returned stale counts without deleting rows.
Diagnostic audit visibility was confirmed with a phase8_smoke row.

No Discord reporting display changes, Google Sheets export contract changes, KVK export result-set changes, Basic Data ingestion, summary tab ingestion, automatic cleanup execution, or Phase 9 restart/performance hardening were included in Phase 8.

Phase 9 — End-to-End Performance & Restart Safety Hardening
Status
Complete and deployed.

Goal
Final optimisation and validation pass.

In Scope
Benchmark workbook parse time.
Benchmark stage insert.
Benchmark ingest proc.
Benchmark recompute.
Benchmark export.
Review transaction log impact.
Validate bot restart behaviour during:
upload
stage insert
proc ingest
recompute
export
Verify no critical state exists only in process memory.
Run targeted and architectural validations.
Required Commands
Where practical:

python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py
python scripts/select_tests.py
python -m pytest -q tests
python -m pyright
python -m ruff check .
Acceptance Criteria
Performance baseline recorded.
Restart risks documented or fixed.
No unresolved required optimisation items remain.
Full pipeline is migration-ready.
Testing Requirements
Each phase must include targeted tests.

Minimum categories to consider:

happy path
negative path
regression
schema validation
SQL contract
export shape
reporting shape
restart/persistence
performance where practical
Recommended focused tests:

tests/test_kvk_all_schema.py
tests/test_kvk_all_importer.py
tests/test_kvk_all_import_service.py
tests/test_kvk_admin_service.py
tests/test_kvk_reporting_service.py
tests/test_gsheet_module.py
tests/test_kvk_embed.py
Required Output Per Phase
Each implementation phase must end with:

Summary
Files changed
SQL changes
Behaviour changes
Backward compatibility notes
Tests run
Restart safety notes
Performance notes
Remaining risks
Deferred Optimisations
For this programme, Deferred Optimisations should usually be:

None. Required optimisation item completed in this phase.

Completion Notes

Implemented:

kvk/services/kvk_all_import_service.py
kvk/dal/kvk_all_import_dal.py
kvk_all_importer.py
scripts/benchmark_kvk_all_phase9.py
tests/test_kvk_all_import_service.py
tests/test_kvk_all_import_dal.py
tests/test_kvk_all_importer.py
docs/task_packs/archive/KVK_ALL Schema Modernisation - Phase 9 Initiation Statement.md

Python delivery:

KVK_ALL Full Data numeric and timestamp coercion was vectorised while preserving strict Full Data validation, Basic Data rejection, canonical staging columns, schema metadata, and legacy import return compatibility.
Granular local timing fields were added for prepare, stage row preparation, stage insert, KVK_Details precheck, ingest procedure execution, recompute execution, and negative diagnostic counting.
The existing Discord-facing import output was not changed; added timing fields are returned for diagnostics and future operator analysis.
A read-only Phase 9 benchmark script was added under scripts/ for repeatable workbook parsing, coercion, metadata, full preparation, and stage-row preparation timing against local workbook samples.

Performance baseline:

Sample workbook:
downloads/kvk_all_sample_file/1086045_05_08_2026,_02_21_38_AM.xlsx

Workbook shape:
Full Data, 5,000 rows, 43 columns, schema hash f885b1c7c5e36516697b05acbb0499a8969bb7571d3fc67546f7f9358124c7b8.

Pre-change local baseline from Phase 9 audit:
read_full_data_workbook median 1552.25ms
coerce_full_data_frame median 1967.53ms
attach_source_metadata median 1.44ms
prepare_kvk_all_import total median 3642.55ms
rows_for_stage median 79.91ms

Post-change local baseline:
read_full_data_workbook median 1637.91ms
coerce_full_data_frame median 24.87ms
attach_source_metadata median 6.30ms
prepare_kvk_all_import total median 1616.97ms
rows_for_stage median 72.25ms

Live SQL timing notes:

KVK.sp_KVK_AllPlayers_Ingest live timing was not run during local validation because it mutates KVK.KVK_Scan, KVK.KVK_AllPlayers_Raw, KVK.KVK_Player_Baseline, KVK.KVK_Ingest_Negatives, and clears staged rows.
KVK.sp_KVK_Recompute_Windows live timing was not run during local validation because it deletes and rebuilds KVK windowed output tables for the target KVK.
KVK.sp_KVK_Get_Exports / Google Sheets export posting was not run during local validation to avoid unintended live spreadsheet writes.
The Python path now returns timing fields for the live ingest/recompute/export-adjacent phases when normal operator workflows run them.

Restart and state assessment:

Before stage insert, no critical KVK_ALL state exists only in process memory; retrying the upload is safe.
After stage insert and before ingest procedure execution, staged rows are durable by IngestToken and inspectable until explicit Phase 8 retention cleanup.
If KVK_Details timestamp precheck rejects an upload, the importer attempts targeted staged-row cleanup and records a best-effort durable diagnostic where Phase 8 SQL is deployed.
If KVK.sp_KVK_AllPlayers_Ingest fails, SQL transaction rollback preserves staged rows for inspection and the Python DAL records a best-effort durable diagnostic.
After ingest succeeds and before recompute completes, KVK.KVK_Scan and KVK.KVK_AllPlayers_Raw are durable and /kvk_recompute can rebuild windowed outputs.
After recompute succeeds and before Google Sheets export completes, SQL outputs are durable and /kvk_export_all can be rerun.
Automatic Google Sheets export remains an in-process convenience task; the recovery contract is the existing admin export command. Broader durable upload/export route extraction remains outside Phase 9 scope.
Phase 8 cleanup remains dry-run by default and no staged rows or diagnostics are deleted automatically by the import path.

Validation completed:

python -m pytest -q tests/test_kvk_all_import_service.py tests/test_kvk_all_import_dal.py tests/test_kvk_all_importer.py tests/test_kvk_all_schema.py tests/test_kvk_all_recompute_sql_contract.py tests/test_kvk_export_service.py tests/test_gsheet_module.py tests/test_kvk_admin_service.py tests/test_kvk_reporting_service.py

No SQL schema changes, Discord reporting display changes, Google Sheets tab/spreadsheet changes, KVK export result-set changes, Basic Data ingestion, summary tab ingestion, automatic cleanup execution, live production import, live recompute, or live export posting were included in Phase 9.

Production smoke completed after deployment:

Four KVK_ALL Full Data workbooks were uploaded and ingested for KVK 15:

Scan 1: 1086045_05_08_2026_02_21_38_AM.xlsx, 5,000 rows.
Scan 2: 1086045_05_09_2026_02_13_52_PM.xlsx, 5,000 rows.
Scan 3: 1086045_05_10_2026_10_06_04_PM.xlsx, 5,000 rows.
Scan 4: 1086045_05_11_2026_10_00_41_AM.xlsx, 5,000 rows.

KVK.KVK_Scan confirmed all four scans with schema_version kvk_all_full_data_v2 and source_sheet_name Full Data.
KVK.KVK_AllPlayers_Raw confirmed 20,000 rows for KVK 15, matching 4 scans x 5,000 rows.
KVK.KVK_Ingest_Diagnostics contained only the prior phase8_smoke diagnostic and no failed/rejected diagnostics from these uploads.
SQL log headroom checks passed before each ingest with reuse_wait=NOTHING and low log usage.
Google Sheets auto-export completed and updated PASS4 and ALL_WINDOW_COMPARISON outputs without changing established tab names.

Phase 9 deployment smoke also surfaced a Phase 10 correctness finding:

Full Data v2 recompute window calculations can incorrectly return zero gains when diff fields such as kill_points_diff and points_difference are present but zero while raw cumulative endpoint fields change across scans. Example: governor_id 45227155 has max_kill_points increasing from 3,380,153,250 at Scan 2 to 3,478,156,090 at Scan 3, so Pass 4 kp_gain should be 98,002,840, but current KVK.sp_KVK_Recompute_Windows output shows zero. This is assigned to Phase 10.

Phase 10 — Full Run Diagnostics, Output Correctness & Recompute Bug Fixing
Goal
Run a full end-to-end diagnostic correctness pass using consecutive real workbook samples, validate all SQL outputs and spreadsheet/export calculations, and fix discovered recompute/window correctness bugs while preserving the established Phase 1-9 import, export, Google Sheets, Discord reporting, admin command, and diagnostic contracts.

In Scope
Use the deployed KVK 15 sample scans from 8 May, 9 May, 10 May, and 11 May 2026 as the primary diagnostic dataset.
Validate KVK.KVK_Scan, KVK.KVK_AllPlayers_Raw, KVK.KVK_Windows, KVK.KVK_Player_Windowed, KVK.KVK_Kingdom_Windowed, KVK.KVK_Camp_Windowed, KVK.KVK_Player_Baseline, KVK.KVK_Ingest_Negatives, KVK.KVK_Ingest_Diagnostics, and KVK export result sets against expected sample-derived calculations.
Validate source-of-truth semantics for Full Data v2 cumulative endpoint columns versus diff columns.
Fix KVK.sp_KVK_Recompute_Windows so Full Data v2 window calculations use the correct endpoint deltas when diff columns are zero or non-authoritative.
Validate player, kingdom, and camp rollups after recompute.
Validate Baseline, Full, Pass 4, and any configured future windows using sample-derived expected values.
Validate KVK.sp_KVK_Get_Exports result-set shape and values after recompute fixes.
Validate Google Sheets output values where practical without changing spreadsheet names, tab names, or result-set contracts.
Add diagnostic SQL scripts or Python scripts where useful for repeatable comparison of raw scans to recompute outputs.
Add SQL contract tests and/or fixture-style tests for the discovered zero-diff/nonzero-endpoint bug.
Capture any larger analytics or redesign findings structurally.

Known Phase 10 Bug In Scope
Area: KVK.sp_KVK_Recompute_Windows
Description: Full Data v2 scans can persist diff fields as zero while raw cumulative endpoint fields such as max_kill_points, max_kills_iv, max_kills_v, max_dead, max_units_healed, and contribution endpoint fields move between scans. Current recompute precedence can select the zero diff value before using raw endpoint fields, producing zero window gains.
Expected Fix: For schema_version kvk_all_full_data_v2, compute window deltas from raw cumulative endpoint fields across StartScanID and EndScanID where those fields are available. Preserve legacy compatibility for older rows that depend on diff fields.
Example: KVK 15, governor_id 45227155, Pass 4 window StartScanID=2 and EndScanID=3 should produce kp_gain 98,002,840 from max_kill_points delta.

Out of Scope
Basic Data ingestion.
Summary tab ingestion.
Discord reporting display changes unless explicitly approved as a bug fix.
New contribution fields in Discord embeds.
Google Sheets spreadsheet or tab name changes.
KVK export result-set count/order changes unless explicitly approved.
Unrelated stats, rankings, history, reporting, personal KVK, or admin command redesign.
Large upload-route extraction from DL_bot.py unless separately approved.
Automatic diagnostic cleanup deletes without explicit dry-run review.
Production promotion before local validation.

Acceptance Criteria
Full Data v2 ingest remains stable for the sample workbooks.
Expected sample-derived player window values match KVK.KVK_Player_Windowed for representative players, including the known governor_id 45227155 Pass 4 kp_gain case.
Kingdom and camp rollups match player-windowed sums.
Baseline and Full outputs have documented and validated semantics.
Export result sets remain at 10 and preserve existing section meanings.
Google Sheets tab names and spreadsheet names remain stable.
No Basic Data or summary tab ingestion is introduced.
Tests or repeatable diagnostic scripts cover changed recompute behaviour.
Any remaining correctness blocker is explicitly documented with owner, risk, and next action.

Completion Notes

Implemented:

C:\K98-bot-SQL-Server\sql_schema\KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql
sql/kvk_all_phase10_recompute_correctness.sql
scripts/diagnose_kvk_all_phase10.py
tests/test_kvk_all_recompute_sql_contract.py
docs/task_packs/archive/KVK_ALL Schema Modernisation - Phase 10 Metric Source Correction.md
docs/task_packs/archive/KVK_ALL Schema Modernisation - Phase 10 Initiation Statement.md

SQL delivery:

KVK.sp_KVK_Recompute_Windows was corrected so Full Data v2 configured windows use cumulative endpoint deltas when start and end endpoint values are available.
Legacy diff-field compatibility was preserved for older 22-column Full Data rows that do not contain endpoint families.
Baseline rows remain zero-gain validation rows.
Full rows now use baseline-to-latest endpoint deltas when Full Data v2 endpoint values are available, with legacy latest-snapshot diff fallback when endpoints are unavailable.
The production deployment script was added under sql/kvk_all_phase10_recompute_correctness.sql using the same GO-batched procedure deployment pattern as prior KVK SQL scripts.

Diagnostic delivery:

scripts/diagnose_kvk_all_phase10.py was added for repeatable, read-only derivation of expected endpoint deltas from the four KVK 15 sample workbooks.
The diagnostic confirmed the known Pass 4 case for governor_id 45227155 should produce kp_gain 98,002,840 for Scan 2 to Scan 3.
Post-deployment smoke confirmed the output now shows 98,002,840 for that case.

Validation completed:

python scripts/diagnose_kvk_all_phase10.py
python -m pytest -q tests/test_kvk_all_recompute_sql_contract.py
python -m pytest -q tests/test_kvk_all_import_service.py tests/test_kvk_all_import_dal.py tests/test_kvk_all_importer.py tests/test_kvk_all_schema.py tests/test_kvk_all_recompute_sql_contract.py tests/test_kvk_export_service.py tests/test_gsheet_module.py tests/test_kvk_admin_service.py tests/test_kvk_reporting_service.py
python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py
python scripts/select_tests.py
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
python -m ruff check scripts/diagnose_kvk_all_phase10.py tests/test_kvk_all_recompute_sql_contract.py
python -m black --check scripts/diagnose_kvk_all_phase10.py tests/test_kvk_all_recompute_sql_contract.py
git diff --check

No Basic Data ingestion, summary tab ingestion, Discord reporting display changes, Google Sheets spreadsheet or tab name changes, KVK export result-set count/order changes, automatic cleanup execution, unrelated admin command redesign, or unrelated analytics features were introduced in Phase 10.

Phase 11 — Acclaim Output Contract Polish
Goal
Polish KVK contribution/acclaim output semantics by removing low-value Highest Acclaim gain output while exposing current Acclaim gain using player-facing terminology, without changing internal storage, import behaviour, recompute correctness, Discord reporting display, or established spreadsheet/tab names unless explicitly approved.

In Scope
Keep max_contribute_gain stored internally for diagnostic and future analysis purposes.
Remove max_contribute_gain from player, kingdom, and camp export/Google Sheets outputs where it is currently surfaced as an output metric.
Preserve max_contribute_gain in SQL windowed tables unless a separate explicit schema-removal decision is approved.
Expose cur_contribute_gain in outputs as acclaim_gain, matching the in-game player-facing name Acclaim.
Validate whether the alias applies to KVK.sp_KVK_Get_Exports result-set column names, Google Sheets outputs, comparison outputs, and structured reporting rows.
Convert KVK.vw_FightingDataset from SELECT * to an explicit player-facing projection that exposes acclaim_gain and does not expose max_contribute_gain.
Preserve current KVK export result-set count and order unless explicitly approved.
Preserve existing Google Sheets spreadsheet names and tab names.
Preserve Discord reporting display; do not add Acclaim to Discord embeds unless explicitly approved.
Update named export-section binding and tests for the new output contract.
Add focused tests for removed Highest Acclaim output, Acclaim aliasing, Sheets tab-name stability, and export section shape.

Source Deferred Items

### Deferred Optimisation
- Area: KVK exports / Google Sheets output
- Type: consistency
- Description: max_contribute_gain is technically stored correctly but has low player-facing value because Highest Acclaim is an all-time peak; the gain is not a meaningful performance signal.
- Suggested Fix: Keep storing max_contribute_gain internally, but remove it from player/kingdom/camp export and Sheets outputs.
- Impact: medium
- Risk: low
- Dependencies: none

### Deferred Optimisation
- Area: KVK exports / Google Sheets output
- Type: consistency
- Description: cur_contribute_gain is valuable but player-facing terminology is Acclaim.
- Suggested Fix: Expose cur_contribute_gain as acclaim_gain in outputs while preserving internal storage/SQL semantics.
- Impact: medium
- Risk: low
- Dependencies: confirm whether aliasing applies to SQL export result sets, Google Sheets tabs, comparison outputs, and structured reporting rows.

Out of Scope
Removing max_contribute_gain from internal SQL storage.
Changing KVK import behaviour or return shape.
Changing recompute formulas beyond output alias/removal needs.
Discord reporting display changes or new contribution fields in Discord embeds.
Google Sheets spreadsheet or tab name changes unless explicitly approved.
KVK export result-set count/order changes unless explicitly approved.
Basic Data ingestion.
Summary tab ingestion.
Unrelated stats, rankings, history, reporting, personal KVK, admin command, or upload-route redesign.

Acceptance Criteria
max_contribute_gain remains stored internally but is no longer surfaced in the in-scope export/Sheets outputs.
cur_contribute_gain is surfaced as acclaim_gain in the in-scope outputs.
Existing spreadsheet names and tab names remain stable.
KVK.sp_KVK_Get_Exports remains at 10 result sets unless an explicit contract change is approved.
Existing Discord reporting display remains unchanged.
No Basic Data or summary tab ingestion is introduced.
Focused tests cover the output removal/aliasing contract and tab/result-set stability.

Completion Notes

Implemented:

sql/kvk_all_phase11_acclaim_output_contract.sql
KVK.sp_KVK_Get_Exports.StoredProcedure.sql in the SQL source-of-truth
KVK.vw_FightingDataset.View.sql in the SQL source-of-truth
kvk/services/kvk_export_service.py
gsheet_module.py
kvk/dal/kvk_reporting_dal.py
kvk/services/kvk_reporting_service.py
tests/test_kvk_all_recompute_sql_contract.py
tests/test_kvk_export_service.py
tests/test_kvk_reporting_service.py
tests/test_gsheet_module.py

SQL/output delivery:

KVK.sp_KVK_Get_Exports still returns the established 10 result sets in the same order.
Player, kingdom, and camp export result sets no longer surface max_contribute_gain.
cur_contribute_gain is surfaced as acclaim_gain in player, kingdom, camp, full, windowed, Google
Sheets, comparison, and structured reporting output contracts where applicable.
KVK.vw_FightingDataset now uses an explicit player-facing projection and exposes acclaim_gain
without exposing max_contribute_gain.
max_contribute_gain remains stored internally in the SQL windowed tables for diagnostics and
future analysis.
Existing Google Sheets spreadsheet names and tab names were preserved.
Existing Discord reporting display was preserved; Acclaim was not added to Discord embeds.

Smoke evidence:

KVK.vw_FightingDataset was updated and returned the expected player-facing acclaim_gain column.
Observed smoke row:

KVK_NO=15, WindowName=Pass 9, governor_id=44452, name=执政官44452, kingdom=1058, campid=4,
kp_gain=0, kp_gain_recalc=0, kills_gain=0, t4_kills=0, t5_kills=0, kp_loss=0,
healed_troops=0, deads=0, starting_power=6331190, dkp=0, last_scan_id=63,
computed_at_utc=2026-06-30 16:12:54, acclaim_gain=0.

Google Sheets export showed the expected acclaim_gain output column and no Highest Acclaim gain
output in the player-facing export shape. Observed smoke row:

KVK_NO=15, WindowName=3rd Altar, camp_name=Earth, kp_gain=1161500598,
kills_gain=63365241, t4_kills=10732871, t5_kills=52632370, kp_loss=520370720,
healed_troops=26018536, deads=235140, acclaim_gain=14518423, dkp=1169381710,
last_scan_id=49, computed_at_utc=2026-06-30 16:12:57.

KVK_ALL imports and export completed successfully after the Phase 11 output-contract changes.

Validation completed:

python -m pytest -q tests/test_kvk_all_recompute_sql_contract.py tests/test_kvk_export_service.py tests/test_kvk_reporting_service.py tests/test_gsheet_module.py

No Basic Data ingestion, summary tab ingestion, import return-shape changes, recompute formula
changes beyond already completed Phase 10 semantics, KVK export result-set count/order changes,
Google Sheets spreadsheet or tab name changes, Discord embed contribution display changes,
internal SQL storage removals, automatic cleanup execution, or unrelated admin/reporting redesigns
were introduced in Phase 11.

Deferred Optimisations

None for the KVK_ALL Schema Modernisation programme. The two Phase 11 source deferred items were
resolved by preserving internal max_contribute_gain storage, removing Highest Acclaim gain from
player-facing outputs, and exposing current Acclaim as acclaim_gain.

Archive Notes

The full optimisation pack, audit and migration planning pack, Phase 4 metric source rules,
Phase 10 metric source correction, and Phase 11 initiation statement are archived under
docs/task_packs/archive/ as completed KVK_ALL programme records.
