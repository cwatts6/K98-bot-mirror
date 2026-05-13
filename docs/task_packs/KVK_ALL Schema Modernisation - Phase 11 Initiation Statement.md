KVK_ALL Schema Modernisation — Phase 11 Initiation Statement

We are starting Phase 11 of the KVK_ALL Schema Modernisation programme.

Important local documentation note:

The Phase 10 completion update to docs/KVK_ALL Schema Modernisation - Full Optimisation Task Pack.md and this Phase 11 initiation statement were created locally after Phase 10 was completed and smoke-tested.

Do not amend the Phase 10 PR for these documentation updates.

These local documentation changes must be included in the next PR opened for Phase 11.

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
docs/KVK_ALL Schema Modernisation - Phase 8 Initiation Statement.md
docs/KVK_ALL Schema Modernisation - Phase 9 Initiation Statement.md
docs/KVK_ALL Schema Modernisation - Phase 10 Initiation Statement.md
docs/KVK_ALL Schema Modernisation - Phase 10 Metric Source Correction.md

Authoritative SQL repository:

C:\K98-bot-SQL-Server

The SQL repo is authoritative for table names, column names, stored procedures, indexes, views, ProcConfig usage, staging tables, output tables, aggregate functions, diagnostic tables, retention scripts, migration scripts, and performance-sensitive query plans. Do not infer schema purely from Python usage if SQL definitions exist.

Phase 10 is complete and smoke-tested.

Phase 10 delivered:

Full Data v2 recompute window correctness fixed for cumulative endpoint fields
configured windows now use endpoint deltas when both start and end endpoint values are available
legacy diff-field compatibility preserved for older 22-column Full Data rows
Baseline rows remain zero-gain validation rows
Full rows use baseline-to-latest endpoint deltas when Full Data v2 endpoints are available
production deployment script added under sql/kvk_all_phase10_recompute_correctness.sql
read-only diagnostic script added under scripts/diagnose_kvk_all_phase10.py
known KVK 15 Pass 4 governor_id 45227155 case validated at kp_gain 98,002,840
KVK export result-set count/order preserved
Google Sheets spreadsheet names and tab names preserved
Discord reporting display preserved

Phases 1 through 10 did not introduce Basic Data ingestion, summary tab ingestion, Discord contribution display, incompatible Google Sheets tab/spreadsheet changes, KVK export result-set count/order changes, unrelated admin command redesign, or automatic cleanup execution.

Phase 11 objective:

Polish KVK contribution/acclaim output semantics by removing low-value Highest Acclaim gain output while exposing current Acclaim gain using player-facing terminology, without changing internal storage, import behaviour, recompute correctness, Discord reporting display, or established spreadsheet/tab names unless explicitly approved.

Terminology:

max_contribute_gain maps to Highest Acclaim gain. Highest Acclaim is an all-time peak score, so the gain value has low player-facing value and can mislead if a player scores below a previous peak.

cur_contribute_gain maps to Acclaim gain. This value is player-facing and useful, but should be labelled as acclaim_gain in outputs.

In scope:

review current export, Google Sheets, comparison, and structured reporting output contracts before implementation
validate all referenced export/result-set objects against the SQL repo
keep max_contribute_gain stored internally for diagnostic and future analysis purposes
remove max_contribute_gain from player, kingdom, and camp export/Google Sheets outputs where it is currently surfaced as an output metric
preserve max_contribute_gain in SQL windowed tables unless a separate explicit schema-removal decision is approved
expose cur_contribute_gain in outputs as acclaim_gain
validate whether the alias applies to KVK.sp_KVK_Get_Exports result-set column names, Google Sheets outputs, comparison outputs, and structured reporting rows
convert KVK.vw_FightingDataset from SELECT * to an explicit player-facing projection that exposes acclaim_gain and does not expose max_contribute_gain
preserve current KVK export result-set count and order unless explicitly approved
preserve existing Google Sheets spreadsheet names and tab names
preserve Discord reporting display
update named export-section binding and tests for the new output contract
add focused tests for removed Highest Acclaim output, Acclaim aliasing, Sheets tab-name stability, and export section shape
capture new out-of-scope findings structurally
include the local Phase 10 task-pack update and this Phase 11 initiation statement in the next PR

Likely SQL objects to review and possibly update:

KVK.sp_KVK_Get_Exports
KVK.KVK_Player_Windowed
KVK.KVK_Kingdom_Windowed
KVK.KVK_Camp_Windowed
dbo.fn_KVK_Player_Aggregated
dbo.fn_KVK_Kingdom_Aggregated
dbo.fn_KVK_Camp_Aggregated
KVK.vw_FightingDataset

Likely Python modules to review and possibly update:

kvk/services/kvk_export_service.py
gsheet_module.py
kvk/dal/kvk_reporting_dal.py
kvk/services/kvk_reporting_service.py
tests/test_kvk_export_service.py
tests/test_gsheet_module.py
tests/test_kvk_reporting_service.py
tests/test_kvk_all_recompute_sql_contract.py
sql/

Likely modules to review for downstream contract awareness, but not redesign unless required:

commands/stats_cmds.py
kvk/dal/kvk_admin_dal.py
kvk/services/kvk_admin_service.py
stats_alerts/allkingdoms.py
stats_alerts/embeds/kvk.py
DL_bot.py
kvk_all_importer.py

Out of scope for Phase 11:

removing max_contribute_gain from internal SQL storage
changing KVK import behaviour or return shape
changing recompute formulas beyond output alias/removal needs
Discord reporting display changes or new contribution fields in Discord embeds
Google Sheets spreadsheet or tab name changes unless explicitly approved
KVK export result-set count/order changes unless explicitly approved
Basic Data ingestion
summary tab ingestion
new live production imports, recomputes, exports, cleanup deletes, or reporting posts unless explicitly requested
production promotion before local validation
rewriting unrelated stats, rankings, history, reporting, personal KVK, admin command, or upload-route flows

Important constraints:

Keep changes PR-sized and focused.
Preserve existing import behaviour and return shape.
Preserve existing recompute correctness.
Preserve existing Google Sheets spreadsheet and tab names.
Preserve existing Discord embed/reporting output.
Do not silently change metric semantics.
Document source-of-truth/output-label decisions before changing formulas or column names.
Validate all schema and procedure assumptions against the SQL repo first.
Avoid embedded SQL in command/view/presentation layers.
Prefer service and DAL boundaries.
Use additive, rollback-safe SQL changes only if SQL changes become necessary.
Do not delete diagnostics or staged rows without explicit approval and dry-run review.
Run targeted tests and validation where practical.

Expected workflow:

Step 1 must be review/scope only unless explicitly told otherwise.
Search and validate SQL repo definitions first.
Identify exact output-shape dependencies and alias/removal strategy.
Present an implementation plan before code if not explicitly asked to implement in one pass.
Implement only Phase 11 Acclaim output contract polish.
Run targeted validation.
Stop after Phase 11 implementation, tests, and report.

Acceptance criteria:

max_contribute_gain remains stored internally but is no longer surfaced in the in-scope export/Sheets outputs.
cur_contribute_gain is surfaced as acclaim_gain in the in-scope outputs.
Existing spreadsheet names and tab names remain stable.
KVK.sp_KVK_Get_Exports remains at 10 result sets unless an explicit contract change is approved.
Existing Discord reporting display remains unchanged.
No Basic Data or summary tab ingestion is introduced.
No incompatible Google Sheets or export result-set count/order changes are introduced.
Tests cover the output removal/aliasing contract and tab/result-set stability.
New deferred findings are captured structurally.
