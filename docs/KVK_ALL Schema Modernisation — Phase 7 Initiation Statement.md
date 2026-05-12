KVK_ALL Schema Modernisation — Phase 7 Initiation Statement

We are starting Phase 7 of the KVK_ALL Schema Modernisation programme.

Important local documentation note:

The Phase 6 completion update to docs/KVK_ALL Schema Modernisation — Full Optimisation Task Pack.md and this Phase 7 initiation statement were created locally after Phase 6 was completed and deployed.

Do not amend the Phase 6 PR for these documentation updates.

These local documentation changes must be included in the next PR opened for Phase 7.

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
docs/KVK_ALL Schema Modernisation — Phase 2 Initiation Statement.md
docs/KVK_ALL Schema Modernisation — Phase 3 Initiation Statement.md
docs/KVK_ALL Schema Modernisation — Phase 4 Initiation Statement.md
docs/KVK_ALL Schema Modernisation - Phase 4 Metric Source Rules.md
docs/KVK_ALL Schema Modernisation — Phase 5 Initiation Statement.md
docs/KVK_ALL Schema Modernisation — Phase 6 Initiation Statement.md

Also read the uploaded workbook sample:

downloads/kvk_all_sample_file/1086045_05_08_2026,_02_21_38_AM.xlsx

Authoritative SQL repository:

C:\K98-bot-SQL-Server

The SQL repo is authoritative for table names, column names, stored procedures, indexes, views, ProcConfig usage, staging tables, output tables, aggregate functions, and migration scripts. Do not infer schema purely from Python usage if SQL definitions exist.

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

Phases 1 through 6 did not introduce Basic Data ingestion, summary tab ingestion, Discord contribution display, incompatible Google Sheets tab/spreadsheet changes, KVK export result-set changes, or admin command SQL extraction.

Phase 7 objective:

Move KVK admin command SQL out of commands/stats_cmds.py into clear DAL/service boundaries while preserving existing command permissions, defer/response behaviour, output copy, export behaviour, and operator workflow.

Authoritative workbook tab:

Full Data only.

Do not use Basic Data as fallback. Basic Data remains out of scope and intentionally ignored.

In scope:

review current KVK admin commands and embedded SQL before implementation
validate all referenced SQL objects against the SQL repo
move KVK admin SQL out of commands/stats_cmds.py into a KVK DAL module
add a KVK admin service for orchestration and command-facing results
keep command handlers thin and focused on permission/defer/input/response flow
preserve existing command names, permissions, response copy, and user-facing output where practical
preserve existing import, recompute, export, Google Sheets, and reporting behaviour
preserve Phase 5 named export binding and Phase 6 reporting service boundaries
add focused tests for service/DAL result shape and command handoff where practical
capture new out-of-scope findings structurally
include the local Phase 6 task-pack update and this Phase 7 initiation statement in the next PR

Likely SQL objects to review:

dbo.KVK_Details
KVK.KVK_Scan
KVK.KVK_Windows
KVK.KVK_DKPWeights
KVK.KVK_CampMap
KVK.sp_KVK_Recompute_Windows
KVK.sp_KVK_Get_Exports
KVK.KVK_AllPlayers_Stage
KVK.KVK_AllPlayers_Raw

Likely Python modules to review and possibly update:

commands/stats_cmds.py
kvk/dal/kvk_admin_dal.py
kvk/services/kvk_admin_service.py
kvk/dal/kvk_all_import_dal.py
kvk/services/kvk_export_service.py
gsheet_module.py
tests/test_kvk_admin_service.py
tests/test_stats_cmds.py

Likely modules to review for downstream contract awareness, but not redesign unless required:

kvk/dal/kvk_reporting_dal.py
kvk/services/kvk_reporting_service.py
stats_alerts/allkingdoms.py
stats_alerts/embeds/kvk.py
DL_bot.py
kvk_all_importer.py

Out of scope for Phase 7:

Discord reporting display changes
new contribution fields in Discord embeds
Google Sheets export contract changes
KVK export result-set changes
Basic Data ingestion
summary tab ingestion
new live production imports, recomputes, exports, or reporting posts unless explicitly requested
production promotion before local validation
rewriting unrelated stats, rankings, history, reporting, or personal KVK flows
operational cleanup and retention work assigned to Phase 8
end-to-end performance and restart hardening assigned to Phase 9

Important constraints:

Keep changes PR-sized and focused.
Preserve existing import behaviour and return shape.
Preserve existing Google Sheets export behaviour.
Preserve existing Discord embed/reporting output.
Do not silently change command response copy or admin workflow semantics.
Avoid embedded SQL in command/view/presentation layers.
Prefer service and DAL boundaries.
Use additive, rollback-safe SQL changes only if SQL changes become necessary.
Run targeted tests and validation where practical.

Expected workflow:

Step 1 must be review/scope only unless explicitly told otherwise.
Search and validate SQL repo definitions first.
Identify exact admin command SQL dependencies and response contracts.
Present an implementation plan before code if not explicitly asked to implement in one pass.
Implement only Phase 7 admin command SQL extraction and service/DAL boundary cleanup.
Run targeted validation.
Stop after Phase 7 implementation, tests, and report.

Acceptance criteria:

KVK admin SQL no longer lives in commands/stats_cmds.py for the in-scope commands.
KVK admin data access lives in a DAL module.
KVK admin orchestration lives in a service module.
commands/stats_cmds.py remains thin and preserves existing user-facing behaviour.
Existing recompute, scan listing, window preview, and export command workflows remain stable.
No Discord reporting display changes are made.
No Google Sheets export contract changes are made.
Tests cover service/DAL result shape and command handoff where practical.
The local Phase 6 task-pack update and this Phase 7 initiation statement are included in the Phase 7 PR.
New deferred findings are captured structurally, but all known KVK_ALL work remains assigned to later programme phases rather than left as final deferred debt.
