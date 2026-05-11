KVK_ALL Schema Modernisation — Phase 6 Initiation Statement

We are starting Phase 6 of the KVK_ALL Schema Modernisation programme.

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

Phases 1 through 5 did not introduce Basic Data ingestion, summary tab ingestion, Discord reporting display changes, reporting DAL ownership changes, admin command SQL extraction, or incompatible Google Sheets tab/spreadsheet changes.

Phase 6 objective:

Move KVK all-kingdom reporting SQL out of presentation modules into clear DAL/service boundaries and expose Phase 4/5 contribution metrics in structured reporting rows while preserving the existing Discord reporting display.

Authoritative workbook tab:

Full Data only.

Do not use Basic Data as fallback. Basic Data remains out of scope and intentionally ignored.

In scope:

review current reporting SQL and embed dependencies before implementation
validate aggregate functions and windowed table columns against the SQL repo
move KVK reporting SQL out of stats_alerts/allkingdoms.py into a KVK DAL module
add a reporting service that returns structured rows/blocks for existing KVK all-kingdom reporting
preserve existing stats_alerts.embeds.kvk Discord display and field layout
preserve existing daily KVK embed behaviour, links, titles, field names, and truncation behaviour unless a bug fix is required
make max_contribute_gain and cur_contribute_gain available in structured reporting rows where SQL already supports them
do not display contribution metrics in Discord embeds in this phase unless explicitly approved
keep all Discord-facing copy unchanged where practical
add focused tests for DAL/service row shape, embed compatibility, contribution-field availability, and formatting/truncation stability
capture new out-of-scope findings structurally

Likely SQL objects to review:

dbo.fn_KVK_Player_Aggregated
dbo.fn_KVK_Kingdom_Aggregated
dbo.fn_KVK_Camp_Aggregated
KVK.KVK_Player_Windowed
KVK.KVK_Kingdom_Windowed
KVK.KVK_Camp_Windowed
KVK.KVK_DKPWeights
KVK.KVK_Windows
KVK.KVK_CampMap

Likely Python modules to review and possibly update:

stats_alerts/allkingdoms.py
stats_alerts/embeds/kvk.py
kvk/dal/kvk_reporting_dal.py
kvk/services/kvk_reporting_service.py
tests/test_kvk_reporting_service.py
tests/test_kvk_embed.py

Likely modules to review for downstream contract awareness, but not redesign unless required:

commands/stats_cmds.py
gsheet_module.py
kvk/services/kvk_export_service.py
build_KVKrankings_embed.py
ui/views/kvk_personal_views.py

Out of scope for Phase 6:

Discord reporting display changes unless explicitly approved
new contribution fields in Discord embeds
admin command SQL extraction
Google Sheets export contract changes
KVK export result-set changes
Basic Data ingestion
summary tab ingestion
new live production reporting posts unless explicitly requested
production promotion before local validation
rewriting unrelated stats, rankings, history, or personal KVK flows

Important constraints:

Keep changes PR-sized and focused.
Preserve existing import behaviour and return shape.
Preserve existing Google Sheets export behaviour.
Preserve existing Discord embed/reporting output.
Do not silently change reporting metric semantics.
Avoid embedded SQL in command/view/presentation layers.
Prefer service and DAL boundaries.
Use additive, rollback-safe SQL changes only if SQL changes become necessary.
Run targeted tests and validation where practical.

Expected workflow:

Step 1 must be review/scope only unless explicitly told otherwise.
Search and validate SQL repo definitions first.
Identify exact reporting SQL dependencies and Discord embed contracts.
Present an implementation plan before code if not explicitly asked to implement in one pass.
Implement only Phase 6 reporting DAL/service extraction and structured contribution availability.
Run targeted validation.
Stop after Phase 6 implementation, tests, and report.

Acceptance criteria:

KVK all-kingdom reporting SQL no longer lives in stats_alerts/allkingdoms.py.
Reporting data access lives in a DAL module.
Reporting orchestration and row/block shaping live in a service module.
stats_alerts/embeds/kvk.py keeps the existing Discord display contract.
Existing top player, kingdom, camp, own kingdom, and own camp reporting blocks remain stable.
Contribution metrics are available in structured reporting rows or explicitly excluded by documented rule.
No Discord reporting display changes are made.
Tests cover reporting row shape, service block shape, embed compatibility, and truncation/formatting stability where practical.
New deferred findings are captured structurally, but all known KVK_ALL/all-kingdom work remains assigned to later programme phases rather than left as final deferred debt.
