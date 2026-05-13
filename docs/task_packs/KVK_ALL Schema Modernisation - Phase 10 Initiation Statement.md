KVK_ALL Schema Modernisation — Phase 10 Initiation Statement

We are starting Phase 10 of the KVK_ALL Schema Modernisation programme.

Important local documentation note:

The Phase 9 completion update to docs/KVK_ALL Schema Modernisation - Full Optimisation Task Pack.md and this Phase 10 initiation statement were created locally after Phase 9 was completed, deployed, and smoke-tested.

Do not amend the Phase 9 PR for these documentation updates.

These local documentation changes must be included in the next PR opened for Phase 10.

Before implementation, read all required repository documents and the full task pack:

README-DEV.md
docs/templates/K98 Bot Standard Development Initiation Statement.md
docs/K98 Bot - Project Engineering Standards.md
docs/K98 Bot - Coding Execution Guidelines.md
docs/K98 Bot - Testing Standards.md
docs/K98 Bot - Skills & Refactor Triggers.md
docs/k98 Bot - Deferred Optimisation Framework.md
docs/K98 Bot Deferred Optimisation Scoring Model.md
docs/K98 Bot Codex Task Pack Generator.md
docs/KVK_ALL Schema Modernisation - Full Optimisation Task Pack.md
docs/KVK_ALL Schema Modernisation - Audit & Migration Planning Task Pack.md
docs/KVK_ALL Schema Modernisation - Phase 2 Initiation Statement.md
docs/KVK_ALL Schema Modernisation - Phase 3 Initiation Statement.md
docs/KVK_ALL Schema Modernisation - Phase 4 Initiation Statement.md
docs/KVK_ALL Schema Modernisation - Phase 4 Metric Source Rules.md
docs/KVK_ALL Schema Modernisation - Phase 5 Initiation Statement.md
docs/KVK_ALL Schema Modernisation - Phase 6 Initiation Statement.md
docs/KVK_ALL Schema Modernisation - Phase 7 Initiation Statement.md
docs/KVK_ALL Schema Modernisation - Phase 8 Initiation Statement.md
docs/KVK_ALL Schema Modernisation - Phase 9 Initiation Statement.md

Also use the deployed KVK 15 sample workbook set:

1086045_05_08_2026_02_21_38_AM.xlsx
1086045_05_09_2026_02_13_52_PM.xlsx
1086045_05_10_2026_10_06_04_PM.xlsx
1086045_05_11_2026_10_00_41_AM.xlsx

Authoritative SQL repository:

C:\K98-bot-SQL-Server

The SQL repo is authoritative for table names, column names, stored procedures, indexes, views, ProcConfig usage, staging tables, output tables, aggregate functions, diagnostic tables, retention scripts, migration scripts, and performance-sensitive query plans. Do not infer schema purely from Python usage if SQL definitions exist.

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

Phase 2 is complete and deployed.

Phase 2 delivered:

additive SQL capacity for the KVK_ALL Full Data workbook schema
nullable Full Data v2 columns on KVK.KVK_AllPlayers_Stage
nullable Full Data v2 columns on KVK.KVK_AllPlayers_Raw
queryable schema/source metadata on KVK.KVK_Scan
backward-compatible optional metadata parameters on KVK.sp_KVK_AllPlayers_Ingest
Python staging support for rank, raw min/max metric families, contribution metrics, and source metadata
focused schema/import SQL contract tests
production deployment script under sql/kvk_all_phase2_full_data_capacity.sql
non-mutating workbook/importer smoke validation
read-only SQL metadata smoke validation after deployment

Phase 3 is complete and deployed.

Phase 3 delivered:

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

Phase 4 is complete and deployed.

Phase 4 delivered:

metric source-of-truth rules documented for kill points, healed troops, raw min/max metric fields, and contribution metrics
Full Data v2 recompute precedence implemented for kill points using kill_points_diff with legacy/raw fallback
Full Data v2 recompute precedence implemented for healed troops using healed_troops with legacy/raw fallback
raw min/max fields retained as validation/reconciliation inputs and fallback inputs rather than replacing stable output semantics
additive max_contribute_gain and cur_contribute_gain outputs on KVK.KVK_Player_Windowed, KVK.KVK_Kingdom_Windowed, and KVK.KVK_Camp_Windowed
KVK.sp_KVK_Recompute_Windows updated to populate contribution gains while preserving existing KP, kills, deads, healed, DKP, baseline, kingdom, and camp outputs
KVK.sp_KVK_Get_Exports kept at 10 result sets and adjusted to keep Full export output columns explicit
Google Sheets tab names and Discord reporting display unchanged
production replication script added under sql/kvk_all_phase4_recompute_modernisation.sql
focused SQL contract tests added for source precedence, additive contribution columns, export contract preservation, and production SQL script coverage

Phase 5 is complete and deployed.

Phase 5 delivered:

stable named KVK export sections for KVK.sp_KVK_Get_Exports outputs
legacy positional export compatibility retained while current callers migrate
primary KVK Google Sheets export binding moved away from fragile fixed DataFrame index assumptions
additional PASS, ALTAR, GREATZIG, and comparison spreadsheet generation updated to use named export-section binding
compatible extra SQL result sets can be ignored when all required export sections are present
existing primary spreadsheet tab names preserved
existing additional spreadsheet names and tab names preserved
ALL_WINDOW_COMPARISON tab names preserved with no new contribution comparison tabs
max_contribute_gain and cur_contribute_gain exported in existing player, kingdom, and camp windowed/full export sections
KVK.sp_KVK_Get_Exports kept at 10 result sets with existing section order preserved
local production deployment script added under sql/kvk_all_phase5_export_contract_decoupling.sql
focused tests added for named binding, backward compatibility, compatible extra result sets, missing-section failures, tab-name stability, and contribution export behaviour
read-only SQL smoke confirmed the applied procedure contract
Google Sheets smoke confirmed stable primary/additional/comparison tab behaviour
production promotion completed after validation

Phase 6 is complete and deployed.

Phase 6 delivered:

KVK all-kingdom reporting SQL moved out of stats_alerts/allkingdoms.py
reporting data access moved into kvk/dal/kvk_reporting_dal.py
reporting block orchestration and row shaping moved into kvk/services/kvk_reporting_service.py
stats_alerts/allkingdoms.py preserved as a thin compatibility wrapper around load_allkingdom_blocks(kvk_no)
existing Discord embed display, field names, links, titles, Top 5 layout, and truncation behaviour preserved
max_contribute_gain and cur_contribute_gain made available in structured reporting rows where SQL supports them
contribution metrics intentionally not displayed in Discord embeds
focused tests added for reporting block shape, SQL placement, contribution availability, embed compatibility, and truncation stability
read-only SQL smoke confirmed structured reporting block availability
Discord test embed smoke confirmed existing display remained stable
production deployment completed after validation

Phase 7 is complete and deployed.

Phase 7 delivered:

KVK admin command SQL moved out of commands/stats_cmds.py for recompute, scan listing, and window preview workflows
KVK admin data access moved into kvk/dal/kvk_admin_dal.py
KVK admin orchestration and command-facing result shaping moved into kvk/services/kvk_admin_service.py
commands/stats_cmds.py preserved command names, permissions, defer/followup flow, output copy, export behaviour, and operator workflow
/kvk_export_all current-KVK resolution moved through the KVK admin service while preserving existing Google Sheets export execution
/kvk_export_all exception reporting hardened so export failures are visible to the operator
/kvk_window_preview SQL Server RowCount alias compatibility fixed
/kvk_window_preview output capped to Discord's 1024-character embed field limit with a truncation marker
focused tests added for DAL/service result shape, command boundary handoff, SQL alias coverage, and embed field limit behaviour
/kvk_export_all smoke completed successfully
/kvk_window_preview smoke issues were fixed in Phase 7 follow-up hotfixes

Phase 8 is complete and deployed.

Phase 8 delivered:

KVK.KVK_AllPlayers_Stage gained staged_at_utc with default and supporting age-based index
KVK.KVK_Ingest_Diagnostics was introduced for durable ingest diagnostic visibility
KVK.sp_KVK_Ingest_Cleanup was introduced with dry-run default cleanup
default retention policy is 24 hours for staged rows, 90 days for ingest diagnostics, and 365 days for negative diagnostics
cleanup validates retention values and does not run automatically during deployment or import
timestamp precheck rejections and ingest procedure failures record best-effort durable diagnostics where Phase 8 SQL is deployed
diagnostic context includes schema/source metadata, source filename, file hash, uploader ID, staged row count, error text, and context JSON where available
ingest procedure failure paths retain staged rows for operator inspection until explicit retention cleanup
coercion validation failures include structured validation context without changing Discord-facing import output
focused tests added for diagnostic shape, best-effort diagnostic writes, retained failed stage rows, and cleanup SQL policy
production deployment script added under sql/kvk_all_phase8_ingest_retention.sql
production smoke confirmed stage marker, diagnostics table, cleanup procedure, dry-run cleanup, and diagnostic insert visibility

Phase 9 is complete and deployed.

Phase 9 delivered:

KVK_ALL Full Data numeric and timestamp coercion was vectorised while preserving strict Full Data validation, Basic Data rejection, canonical staging columns, schema metadata, and legacy import return compatibility
granular local timing fields were added for prepare, stage row preparation, stage insert, KVK_Details precheck, ingest procedure execution, recompute execution, and negative diagnostic counting
read-only benchmark script added under scripts/benchmark_kvk_all_phase9.py
performance baseline recorded against the 8 May workbook sample
production smoke confirmed four KVK 15 Full Data scans ingested successfully with 20,000 raw rows and no failed/rejected ingest diagnostics
Google Sheets auto-export completed and updated established PASS4 and comparison outputs
Phase 9 smoke surfaced a recompute/window correctness bug assigned to Phase 10

Phases 1 through 9 did not introduce Basic Data ingestion, summary tab ingestion, Discord contribution display, incompatible Google Sheets tab/spreadsheet changes, KVK export result-set changes, unrelated admin command redesign, or automatic cleanup execution.

Phase 10 objective:

Run a full end-to-end diagnostic correctness pass using consecutive real workbook samples, validate all SQL outputs and spreadsheet/export calculations, and fix discovered recompute/window correctness bugs while preserving established import, recompute, export, Google Sheets, Discord reporting, admin command, and operational diagnostic contracts.

Authoritative workbook tab:

Full Data only.

Do not use Basic Data as fallback. Basic Data remains out of scope and intentionally ignored.

In scope:

review the full KVK_ALL import-to-export flow before implementation
validate all referenced raw, scan, window, baseline, diagnostic, recompute, export, reporting, and admin objects against the SQL repo
use the four deployed KVK 15 sample scans as the primary correctness dataset
create or run a full diagnostic suite that compares raw scan endpoint values to recompute outputs
validate Baseline, Full, Pass 4, and future configured window semantics
validate KVK_Player_Windowed, KVK_Kingdom_Windowed, and KVK_Camp_Windowed values against sample-derived expected calculations
validate KVK.sp_KVK_Get_Exports output values and shape after recompute fixes
validate Google Sheets output values where practical without posting unintended live output unless explicitly approved
fix the discovered Full Data v2 recompute bug where zero diff fields mask changed raw cumulative endpoint values
add focused SQL contract tests and/or diagnostic fixture tests for changed recompute behaviour
preserve existing import behaviour and return shape
preserve existing Google Sheets tab names and spreadsheet names
preserve existing Discord reporting display
capture any larger out-of-scope findings structurally
include the local Phase 9 task-pack update and this Phase 10 initiation statement in the next PR

Known bug in scope:

KVK.sp_KVK_Recompute_Windows currently can produce zero Full Data v2 window gains when diff fields such as kill_points_diff and points_difference are present but zero while raw cumulative endpoint fields move across scans.

Example from production smoke:

KVK 15
Window Pass 4
StartScanID 2
EndScanID 3
governor_id 45227155
Scan 2 max_kill_points 3,380,153,250
Scan 3 max_kill_points 3,478,156,090
Expected Pass 4 kp_gain 98,002,840
Observed Pass 4 kp_gain 0

Likely SQL objects to review and possibly update:

KVK.KVK_AllPlayers_Raw
KVK.KVK_Scan
KVK.KVK_Player_Windowed
KVK.KVK_Kingdom_Windowed
KVK.KVK_Camp_Windowed
KVK.KVK_Player_Baseline
KVK.KVK_Windows
KVK.KVK_DKPWeights
KVK.KVK_CampMap
KVK.KVK_Ingest_Negatives
KVK.KVK_Ingest_Diagnostics
KVK.sp_KVK_Recompute_Windows
KVK.sp_KVK_Get_Exports
dbo.fn_KVK_Player_Aggregated
dbo.fn_KVK_Kingdom_Aggregated
dbo.fn_KVK_Camp_Aggregated
KVK.vw_FightingDataset

Likely Python modules to review and possibly update:

kvk/dal/kvk_all_import_dal.py
kvk/services/kvk_all_import_service.py
kvk_all_importer.py
kvk/services/kvk_export_service.py
gsheet_module.py
kvk/dal/kvk_admin_dal.py
kvk/services/kvk_admin_service.py
tests/test_kvk_all_recompute_sql_contract.py
tests/test_kvk_export_service.py
tests/test_gsheet_module.py
scripts/
sql/

Out of scope for Phase 10:

Discord reporting display changes unless explicitly approved as a bug fix
new contribution fields in Discord embeds
Google Sheets tab or spreadsheet name changes
KVK export result-set count/order changes unless explicitly approved
Basic Data ingestion
summary tab ingestion
new live production imports, recomputes, exports, cleanup deletes, or reporting posts unless explicitly requested
production promotion before local validation
rewriting unrelated stats, rankings, history, reporting, personal KVK, or admin command flows
large cross-module KVK_ALL upload-route extraction unless explicitly approved as a separate task
new analytics features beyond diagnostic correctness and bug fixing

Important constraints:

Keep changes PR-sized and focused.
Preserve existing import behaviour and return shape.
Preserve existing Google Sheets export behaviour.
Preserve existing Discord embed/reporting output.
Do not silently change metric semantics.
Document source-of-truth decisions before changing formulas.
Validate all schema and procedure assumptions against the SQL repo first.
Avoid embedded SQL in command/view/presentation layers.
Prefer service and DAL boundaries.
Use additive, rollback-safe SQL changes only if SQL changes become necessary.
Do not delete diagnostics or staged rows without explicit approval and dry-run review.
Run targeted tests and validation where practical.

Expected workflow:

Step 1 must be review/scope only unless explicitly told otherwise.
Search and validate SQL repo definitions first.
Identify exact correctness risks, recompute formula issues, output-shape dependencies, and diagnostic strategy.
Present an implementation plan before code if not explicitly asked to implement in one pass.
Implement only Phase 10 full-run diagnostics and correctness bug fixes.
Run targeted validation.
Stop after Phase 10 implementation, tests, and report.

Acceptance criteria:

Full Data v2 ingest remains stable for the deployed sample workbook set.
Sample-derived expected player window values match KVK.KVK_Player_Windowed for representative players, including governor_id 45227155 Pass 4 kp_gain.
Kingdom and camp rollups match player-windowed sums.
Baseline and Full output semantics are documented and validated.
KVK.sp_KVK_Get_Exports remains at 10 result sets unless an explicit contract change is approved.
Existing Google Sheets tab names and spreadsheet names remain stable.
No Basic Data or summary tab ingestion is introduced.
No incompatible Google Sheets or export result-set changes are introduced.
Tests or repeatable diagnostic scripts cover changed recompute behaviour.
New deferred findings are captured structurally.
The programme is full-run correctness-ready, or any remaining blocker is explicitly documented with owner, risk, and next action.
