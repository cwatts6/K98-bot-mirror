KVK_ALL Schema Modernisation — Phase 5 Initiation Statement

We are starting Phase 5 of the KVK_ALL Schema Modernisation programme.

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

Phase 4 is complete and dev-validated.

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
non-mutating workbook/service smoke validation completed against the uploaded sample workbook
read-only dev SQL metadata smoke confirmed all six contribution columns and recompute/export procedure markers

Phases 1 through 4 did not introduce Basic Data ingestion, summary tab ingestion, Discord reporting display changes, admin command SQL extraction, reporting DAL ownership changes, or production promotion without validation.

Phase 5 objective:

Decouple KVK export handling from fragile fixed SQL result-set ordering while preserving existing Google Sheets tab names, current spreadsheet workflows, and downstream Discord reporting contracts.

Authoritative workbook tab:

Full Data only.

Do not use Basic Data as fallback. Basic Data remains out of scope and intentionally ignored.

In scope:

review current export SQL and Google Sheets export dependencies before implementation
validate KVK.sp_KVK_Get_Exports result sets against the SQL repo
map every current result set to an explicit export section name
replace or wrap fixed DataFrame index assumptions in gsheet_module.py with named export-section binding
preserve existing primary spreadsheet tab names
preserve existing additional spreadsheet names and tab names unless explicitly approved
preserve current export result data for existing KP, kills, deads, healed, DKP, baseline, kingdom, camp, scan log, windows, weights, and negative diagnostics outputs
decide where Phase 4 contribution columns should appear in exports
add contribution columns to relevant exports if safe and contract-compatible
keep Discord reporting display unchanged
avoid live production data export as a test unless explicitly requested
add focused tests for result-set name binding, backward compatibility with positional results where needed, tab-name stability, and contribution-column export behaviour
capture new out-of-scope findings structurally

Likely SQL objects to review and possibly update:

KVK.sp_KVK_Get_Exports
KVK.KVK_Player_Windowed
KVK.KVK_Kingdom_Windowed
KVK.KVK_Camp_Windowed
KVK.KVK_Ingest_Negatives
KVK.KVK_Scan
KVK.KVK_Windows
KVK.KVK_DKPWeights

Likely Python modules to review and possibly update:

gsheet_module.py
tests/test_gsheet_module.py
tests/test_kvk_all_recompute_sql_contract.py
kvk/dal/kvk_all_import_dal.py
kvk_all_importer.py

Likely modules to review for downstream contract awareness, but not redesign unless required:

stats_alerts/allkingdoms.py
stats_alerts/embeds/kvk.py
commands/stats_cmds.py

Out of scope for Phase 5:

Discord reporting display changes
reporting DAL refactor
admin command SQL extraction
Basic Data ingestion
summary tab ingestion
new live production export runs unless explicitly requested
production promotion before local validation
changing established Google Sheets tab names unless explicitly approved
changing spreadsheet names unless explicitly approved
removing current positional export compatibility before all callers are migrated

Important constraints:

Keep changes PR-sized and focused.
Preserve existing import behaviour and return shape.
Do not change Discord embed/reporting output in this phase.
Do not change existing Google Sheets tab names unless explicitly approved.
Do not silently change export metric semantics.
Use additive, rollback-safe SQL changes only.
Avoid embedded SQL in command/view layers.
Prefer service and DAL boundaries.
Run targeted tests and validation where practical.

Expected workflow:

Step 1 must be review/scope only unless explicitly told otherwise.
Search and validate SQL repo definitions first.
Identify exact export SQL dependencies and downstream Google Sheets contracts.
Present an implementation plan before code if not explicitly asked to implement in one pass.
Implement only Phase 5 export contract decoupling.
Run targeted validation.
Stop after Phase 5 implementation, tests, and report.

Acceptance criteria:

Current KVK export result sets are mapped to stable named export sections.
Google Sheets export no longer fails solely because a new SQL result set is added in a compatible way.
Existing primary tab names remain stable.
Existing additional spreadsheet and comparison tab names remain stable unless explicitly approved.
Existing KP, kills, deads, healed, DKP, baseline, kingdom, camp, scan log, windows, weights, and negative diagnostic exports remain stable.
Contribution columns are exported where safe or explicitly excluded by documented rule.
Representative tests cover named binding, backward compatibility, tab-name stability, and contribution export behaviour.
No Discord reporting display changes are made.
New deferred findings are captured structurally, but all known KVK_ALL/all-kingdom work remains assigned to later programme phases rather than left as final deferred debt.