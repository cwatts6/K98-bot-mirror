KVK_ALL Schema Modernisation — Full Optimisation Task Pack
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

Next phase:

Phase 2 — Additive SQL Schema Migration

Completion Rule
This work is not complete until all items previously identified as deferred optimisations are implemented or explicitly resolved inside this programme.

No remaining KVK_ALL pipeline debt should be left as deferred unless a new blocker is discovered and documented.

Required Reading
Before starting any phase, read:

README-DEV.md
docs/K98 Bot — Standard Development Initiation Statement.md
docs/K98 Bot — Project Engineering Standards.md
docs/K98 Bot — Coding Execution Guidelines.md
docs/K98 Bot — Testing Standards.md
docs/K98 Bot — Skills & Refactor Triggers.md
docs/k98 Bot — Deferred Optimisation Framework.md
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
maps only legacy/stage columns
drops new contribution fields
drops raw min/max metric families
returns schema version in the import result
does not persist source sheet metadata
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
Current SQL supports legacy fields only:

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
It does not support:

rank
raw min/max kill points
raw min/max power
raw min/max dead
raw min/max troop power
raw min/max healed
max contribution metrics
current contribution metrics
schema version metadata
source workbook metadata
source sheet metadata
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
Phase 3 — Importer Service/DAL Refactor
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
Phase 4 — Recompute Modernisation
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
Phase 5 — Export Contract Decoupling
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
Phase 6 — Reporting DAL & Discord Integration
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
Phase 7 — Admin Command SQL Extraction
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
Phase 8 — Operational Cleanup & Retention
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
Phase 9 — End-to-End Performance & Restart Safety Hardening
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
