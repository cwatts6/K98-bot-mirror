KVK_ALL Schema Modernisation — Phase 8 Initiation Statement

We are starting Phase 8 of the KVK_ALL Schema Modernisation programme.

Important local documentation note:

The Phase 7 completion update to docs/KVK_ALL Schema Modernisation - Full Optimisation Task Pack.md and this Phase 8 initiation statement were created locally after Phase 7 was completed and deployed.

Do not amend the Phase 7 PR or Phase 7 follow-up hotfix PR for these documentation updates.

These local documentation changes must be included in the next PR opened for Phase 8.

Before implementation, read all required repository documents and the full task pack:

README-DEV.md
docs/templates/Codex Task Pack Template.md
docs/K98 Bot - Project Engineering Standards.md
docs/K98 Bot - Coding Execution Guidelines.md
docs/K98 Bot - Testing Standards.md
docs/K98 Bot - Skills & Refactor Triggers.md
docs/k98 Bot - Deferred Optimisation Framework.md
docs/K98 Bot Deferred Optimisation Scoring Model.md
docs/KVK_ALL Schema Modernisation - Full Optimisation Task Pack.md
docs/KVK_ALL Schema Modernisation - Audit & Migration Planning Task Pack.md
docs/KVK_ALL Schema Modernisation - Phase 2 Initiation Statement.md
docs/KVK_ALL Schema Modernisation - Phase 3 Initiation Statement.md
docs/KVK_ALL Schema Modernisation - Phase 4 Initiation Statement.md
docs/KVK_ALL Schema Modernisation - Phase 4 Metric Source Rules.md
docs/KVK_ALL Schema Modernisation - Phase 5 Initiation Statement.md
docs/KVK_ALL Schema Modernisation - Phase 6 Initiation Statement.md
docs/KVK_ALL Schema Modernisation - Phase 7 Initiation Statement.md

Also read the uploaded workbook sample:

downloads/kvk_all_sample_file/1086045_05_08_2026,_02_21_38_AM.xlsx

Authoritative SQL repository:

C:\K98-bot-SQL-Server

The SQL repo is authoritative for table names, column names, stored procedures, indexes, views, ProcConfig usage, staging tables, output tables, aggregate functions, diagnostic tables, retention scripts, and migration scripts. Do not infer schema purely from Python usage if SQL definitions exist.

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

Phases 1 through 7 did not introduce Basic Data ingestion, summary tab ingestion, Discord contribution display, incompatible Google Sheets tab/spreadsheet changes, KVK export result-set changes, or unrelated admin command redesign.

Phase 8 objective:

Make KVK_ALL ingest diagnostics and failed stage rows operationally safe by defining retention, cleanup, and audit visibility for diagnostic data while preserving import, recompute, export, reporting, and admin command behaviour.

Authoritative workbook tab:

Full Data only.

Do not use Basic Data as fallback. Basic Data remains out of scope and intentionally ignored.

In scope:

review current KVK ingest diagnostic and staging failure behaviour before implementation
validate all referenced diagnostic, stage, ingest, scan, and metadata objects against the SQL repo
define a retention policy for failed stage rows and diagnostic records
add cleanup capability for stale failed stage rows or diagnostics if needed
ensure cleanup does not remove active ingest tokens or recent actionable diagnostics
make ingest audit visibility clearer where practical
include schema/source metadata in diagnostics where supported by existing Phase 2/3 metadata
include failed column validation context where practical without changing Discord import output unless required for error clarity
avoid unbounded growth of diagnostic data
keep changes PR-sized and rollback-safe
add focused tests or validation for retention/cleanup selection logic and diagnostic shape where practical
capture new out-of-scope findings structurally
include the local Phase 7 task-pack update and this Phase 8 initiation statement in the next PR

Likely SQL objects to review:

KVK.KVK_AllPlayers_Stage
KVK.KVK_AllPlayers_Raw
KVK.KVK_Scan
KVK.KVK_Ingest_Negatives
KVK.sp_KVK_AllPlayers_Ingest
dbo.KVK_Details
any KVK.KVK_Ingest_* diagnostic objects or scripts found in the SQL repo

Likely Python modules to review and possibly update:

kvk/dal/kvk_all_import_dal.py
kvk/services/kvk_all_import_service.py
kvk_all_importer.py
DL_bot.py
tests/test_kvk_all_import_dal.py
tests/test_kvk_all_import_service.py
tests/test_kvk_all_importer.py
scripts/
sql/

Likely modules to review for downstream contract awareness, but not redesign unless required:

commands/stats_cmds.py
kvk/dal/kvk_admin_dal.py
kvk/services/kvk_admin_service.py
kvk/services/kvk_export_service.py
kvk/dal/kvk_reporting_dal.py
kvk/services/kvk_reporting_service.py
gsheet_module.py
stats_alerts/allkingdoms.py
stats_alerts/embeds/kvk.py

Out of scope for Phase 8:

Discord reporting display changes
new contribution fields in Discord embeds
Google Sheets export contract changes
KVK export result-set changes
Basic Data ingestion
summary tab ingestion
admin command SQL extraction beyond Phase 7 follow-up fixes
new live production imports, recomputes, exports, cleanup, or reporting posts unless explicitly requested
production promotion before local validation
rewriting unrelated stats, rankings, history, reporting, personal KVK, or admin command flows
end-to-end performance and restart hardening assigned to Phase 9

Important constraints:

Keep changes PR-sized and focused.
Preserve existing import behaviour and return shape.
Preserve existing Google Sheets export behaviour.
Preserve existing Discord embed/reporting output.
Do not silently change diagnostic retention semantics.
Do not delete diagnostics or staged rows without a clear retention rule.
Avoid embedded SQL in command/view/presentation layers.
Prefer service and DAL boundaries.
Use additive, rollback-safe SQL changes only if SQL changes become necessary.
Run targeted tests and validation where practical.

Expected workflow:

Step 1 must be review/scope only unless explicitly told otherwise.
Search and validate SQL repo definitions first.
Identify exact diagnostic/staging data dependencies and retention risks.
Present an implementation plan before code if not explicitly asked to implement in one pass.
Implement only Phase 8 operational cleanup and retention work.
Run targeted validation.
Stop after Phase 8 implementation, tests, and report.

Acceptance criteria:

Failed ingest diagnostics are inspectable.
Old diagnostics or failed staged rows can be cleaned safely according to a documented rule.
Cleanup does not remove active ingest tokens or recent actionable diagnostics.
Diagnostic context includes schema/source metadata where supported by the current pipeline.
Failed column validation context is preserved or improved where practical.
Existing import, recompute, export, Google Sheets, admin command, and Discord reporting behaviour remains stable.
No Basic Data or summary tab ingestion is introduced.
Tests or validation cover retention/cleanup selection and diagnostic shape where practical.
New deferred findings are captured structurally, but all known KVK_ALL work remains assigned to later programme phases rather than left as final deferred debt.
