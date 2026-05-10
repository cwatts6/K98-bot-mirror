KVK_ALL Schema Modernisation — Phase 2 Initiation Statement

We are starting Phase 2 of the KVK_ALL Schema Modernisation programme.

Before implementation, read all required repository documents and the full task pack:

README-DEV.md
docs/K98 Bot — Standard Development Initiation Statement.md
docs/K98 Bot — Project Engineering Standards.md
docs/K98 Bot — Coding Execution Guidelines.md
docs/K98 Bot — Testing Standards.md
docs/K98 Bot — Skills & Refactor Triggers.md
docs/k98 Bot — Deferred Optimisation Framework.md
docs/K98 Bot Deferred Optimisation Scoring Model.md
docs/K98 Bot Codex Task Pack Generator.md
docs/KVK_ALL Schema Modernisation — Full Optimisation Task Pack.md
docs/KVK_ALL Schema Modernisation — Audit & Migration Planning Task Pack.md

Also read the uploaded workbook sample:

downloads/kvk_all_sample_file/1086045_05_08_2026,_02_21_38_AM.xlsx

Authoritative SQL repository:

C:\K98-bot-SQL-Server

The SQL repo is authoritative for table names, column names, stored procedures, indexes, views, ProcConfig usage, staging tables, output tables, and migration scripts. Do not infer schema purely from Python usage if SQL definitions exist.

Phase 1 is complete and deployed.

Phase 1 delivered:

strict Full Data workbook detection
Full Data tab required
Basic Data ignored and never used as fallback
fallback-to-second-sheet behaviour removed for KVK_ALL imports
all expected Full Data columns validated before legacy coercion
schema version kvk_all_full_data_v2 returned in import results
structured validation errors for schema failures
focused schema tests for valid schema, missing Full Data, missing required columns, and Basic Data ignored

Phase 1 did not change SQL schema, SQL procedures, recompute, export, Google Sheets, or Discord reporting behaviour.

Phase 2 objective:

Add SQL capacity for the full KVK_ALL Full Data workbook schema without breaking existing ingest, recompute, export, Google Sheets, or Discord reporting behaviour.

Authoritative workbook tab:

Full Data only.

Do not use Basic Data as fallback. Basic Data is out of scope and intentionally ignored.

In scope:

review SQL repo objects before implementation
design additive SQL migration for Full Data fields
add nullable columns to existing KVK stage/raw tables or introduce versioned v2 tables if justified
update ingest stored procedure/stage flow additively
persist schema/source metadata needed by the programme
preserve existing legacy import/export/recompute compatibility
add SQL scripts in the SQL repo using project naming standards
add or update focused Python/SQL contract tests where practical
capture new out-of-scope findings structurally

Required persisted fields to support:

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

Likely SQL objects to review/update:

KVK.KVK_AllPlayers_Stage
KVK.KVK_AllPlayers_Raw
KVK.KVK_Scan or a new ingest metadata table
KVK.sp_KVK_AllPlayers_Ingest
KVK.KVK_Ingest_Negatives

Out of scope for Phase 2:

Discord reporting display changes
Google Sheets export changes
recompute formula redesign
admin command SQL extraction
reporting DAL refactor
importer service/DAL refactor unless a minimal Python compatibility change is required for SQL contract tests

Important constraints:

Keep changes PR-sized and focused.
Use additive, rollback-safe SQL changes.
Do not make destructive SQL changes.
Do not change existing export tab names or result-set contracts in this phase.
Do not change Discord embed/reporting output in this phase.
Preserve existing ingest behaviour for currently mapped legacy fields.
Avoid embedded SQL in command/view layers.
Prefer service and DAL boundaries where practical.
Run targeted tests and validation where practical.

Expected workflow:

Step 1 must be review/scope only unless explicitly told otherwise.
Search and validate SQL repo definitions first.
Identify exact SQL objects and Python touchpoints.
Present an implementation plan before code if not explicitly asked to implement in one pass.
Implement only Phase 2 additive SQL capacity.
Run targeted validation.
Stop after Phase 2 implementation, tests, and report.

Acceptance criteria:

existing legacy import path remains compatible
new Full Data fields have additive SQL capacity
ingest metadata is queryable
SQL scripts are additive and rollback-safe
no SQL/export/reporting behaviour outside Phase 2 is changed
tests or validation cover the SQL contract and compatibility path where practical
new deferred findings are captured structurally
