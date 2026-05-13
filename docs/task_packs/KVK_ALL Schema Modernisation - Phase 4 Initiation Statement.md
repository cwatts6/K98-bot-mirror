KVK_ALL Schema Modernisation — Phase 4 Initiation Statement

We are starting Phase 4 of the KVK_ALL Schema Modernisation programme.

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

Phases 1 through 3 did not change recompute formula behaviour, export result-set order, Google Sheets tab names, Discord reporting display, admin command SQL ownership, or reporting DAL ownership.

Phase 4 objective:

Modernise KVK_ALL recompute behaviour to support the Full Data v2 schema where appropriate, decide and document source-of-truth metric rules, and reduce recompute performance risk while preserving existing downstream export, Google Sheets, and Discord reporting contracts.

Authoritative workbook tab:

Full Data only.

Do not use Basic Data as fallback. Basic Data is out of scope and intentionally ignored.

In scope:

review current recompute SQL and downstream aggregate dependencies before implementation
validate all recompute input columns against the SQL repo
decide and document the source of truth for points_difference vs kill_points_diff
decide and document the source of truth for max_units_healed_diff vs healed_troops
decide and document the source of truth for raw min/max metric fields vs legacy diff fields
evaluate whether contribution metrics should be recomputed into output tables in this phase
add contribution recompute outputs if required and safe
preserve existing KP, kills, deads, healed, DKP, baseline, kingdom, and camp outputs
review current full-refresh recompute behaviour
measure or smoke-check recompute performance risk where practical
add additive SQL changes in the SQL repo if output table capacity or indexes are required
add representative SQL contract or fixture-style tests where practical
keep Python changes limited to any service/DAL contract adjustments needed for recompute support
capture new out-of-scope findings structurally

Likely SQL objects to review and possibly update:

KVK.sp_KVK_Recompute_Windows
KVK.KVK_Player_Windowed
KVK.KVK_Kingdom_Windowed
KVK.KVK_Camp_Windowed
KVK.KVK_AllPlayers_Raw
KVK.KVK_Player_Baseline
KVK.KVK_Windows
KVK.KVK_CampMap
dbo.fn_KVK_Player_Aggregated
dbo.fn_KVK_Kingdom_Aggregated
dbo.fn_KVK_Camp_Aggregated
KVK.vw_FightingDataset

Likely Python modules to review, but not redesign unless required:

kvk/dal/kvk_all_import_dal.py
kvk/services/kvk_all_import_service.py
kvk_all_importer.py
gsheet_module.py
stats_alerts/allkingdoms.py
stats_alerts/embeds/kvk.py
commands/stats_cmds.py
tests/test_kvk_all_import_dal.py
tests/test_kvk_all_import_service.py

Out of scope for Phase 4:

new export result sets or export result-set reordering unless strictly required by recompute compatibility
Google Sheets export changes
Discord reporting display changes
admin command SQL extraction
reporting DAL refactor
export contract decoupling
summary tab ingestion
Basic Data ingestion
live ingest of production data as a test unless explicitly requested
production promotion before local validation

Important constraints:

Keep changes PR-sized and focused.
Preserve existing import behaviour and return shape.
Do not change existing export tab names or result-set contracts in this phase unless explicitly approved.
Do not change Discord embed/reporting output in this phase.
Use additive, rollback-safe SQL changes only.
Do not silently change metric semantics.
Document source-of-truth decisions before changing formulas.
Avoid embedded SQL in command/view layers.
Prefer service and DAL boundaries.
Run targeted tests and validation where practical.

Expected workflow:

Step 1 must be review/scope only unless explicitly told otherwise.
Search and validate SQL repo definitions first.
Identify exact recompute SQL dependencies and downstream contracts.
Present an implementation plan before code if not explicitly asked to implement in one pass.
Implement only Phase 4 recompute modernisation.
Run targeted validation.
Stop after Phase 4 implementation, tests, and report.

Acceptance criteria:

Current recompute inputs and outputs are mapped against authoritative SQL definitions.
Metric source-of-truth decisions are documented.
Existing KP, kills, deads, healed, DKP, baseline, kingdom, and camp outputs remain stable.
Contribution metrics are recomputed or explicitly excluded by documented rule.
Any SQL changes are additive and rollback-safe.
Export result-set order and Google Sheets tab names remain unchanged unless explicitly approved.
Discord reporting display remains unchanged.
Representative recompute tests or SQL contract validations cover changed formulas where practical.
Performance risk is measured, smoke-checked, or explicitly documented.
New deferred findings are captured structurally, but all known KVK_ALL/all-kingdom work remains assigned to later programme phases rather than left as final deferred debt.
