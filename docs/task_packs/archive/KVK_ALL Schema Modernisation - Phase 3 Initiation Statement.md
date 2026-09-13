KVK_ALL Schema Modernisation — Phase 3 Initiation Statement

We are starting Phase 3 of the KVK_ALL Schema Modernisation programme.

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

Phase 2 did not change recompute formula behaviour, export result-set order, Google Sheets tab names, Discord reporting display, admin command SQL ownership, or reporting DAL ownership.

Phase 3 objective:

Refactor the KVK_ALL importer into clear schema, service, and DAL boundaries while preserving the existing user-facing import behaviour and the Phase 2 SQL contract.

Authoritative workbook tab:

Full Data only.

Do not use Basic Data as fallback. Basic Data is out of scope and intentionally ignored.

In scope:

review current importer and SQL contract before implementation
extract workbook parsing and schema validation from kvk_all_importer.py into the KVK schema/service layer
extract Full Data v2 canonical column mapping and coercion into testable schema or service code
extract SQL staging, ingest procedure calls, recompute calls, and negative count reads into a DAL module
keep Discord objects out of services and DAL
preserve kvk_all_importer.ingest_kvk_all_excel as a compatibility wrapper or thin entrypoint
preserve existing return dictionary keys used by DL_bot.py
preserve structured validation errors introduced in Phase 1
preserve Phase 2 schema/source metadata persistence
include unknown/dropped column reporting where practical without changing user-facing Discord output
add structured import result types internally if useful
add focused tests for mapping, coercion, validation, DAL call shape, and wrapper compatibility
capture new out-of-scope findings structurally

Likely Python modules to create or update:

kvk_all_importer.py
kvk/schemas/kvk_all_schema.py
kvk/services/kvk_all_import_service.py
kvk/dal/kvk_all_import_dal.py
tests/test_kvk_all_schema.py
tests/test_kvk_all_import_service.py
tests/test_kvk_all_import_dal.py
tests/test_kvk_all_importer.py

Likely SQL objects to validate, but not redesign in this phase:

KVK.KVK_AllPlayers_Stage
KVK.KVK_AllPlayers_Raw
KVK.KVK_Scan
KVK.sp_KVK_AllPlayers_Ingest
KVK.KVK_Ingest_Negatives
KVK.sp_KVK_Recompute_Windows

Out of scope for Phase 3:

new SQL schema changes unless a Phase 2 compatibility bug is discovered
recompute formula redesign
new export result sets or export result-set reordering
Google Sheets export changes
Discord reporting display changes
admin command SQL extraction
reporting DAL refactor
summary tab ingestion
Basic Data ingestion
live ingest of production data as a test unless explicitly requested

Important constraints:

Keep changes PR-sized and focused.
Preserve existing import behaviour and return shape.
Do not change existing export tab names or result-set contracts in this phase.
Do not change Discord embed/reporting output in this phase.
Avoid embedded SQL in command/view layers.
Prefer service and DAL boundaries.
Do not silently drop Phase 2 fields from the staging contract.
Run targeted tests and validation where practical.

Expected workflow:

Step 1 must be review/scope only unless explicitly told otherwise.
Search and validate SQL repo definitions first.
Identify exact Python touchpoints and SQL contract dependencies.
Present an implementation plan before code if not explicitly asked to implement in one pass.
Implement only Phase 3 importer service/DAL refactor.
Run targeted validation.
Stop after Phase 3 implementation, tests, and report.

Acceptance criteria:

kvk_all_importer.py is a thin compatibility entrypoint or substantially reduced wrapper.
Workbook schema validation and mapping are testable outside the Discord/upload path.
SQL writes and stored procedure calls live in DAL code rather than importer orchestration.
Services and DAL do not depend on Discord types.
Phase 1 strict Full Data validation remains intact.
Phase 2 SQL metadata and Full Data capacity fields continue to be staged and passed through.
Existing legacy import path remains compatible.
Existing recompute, export, Google Sheets, and Discord reporting behaviour is unchanged.
Tests cover schema mapping, coercion, DAL call shape, wrapper compatibility, and validation failures where practical.
New deferred findings are captured structurally, but all known KVK_ALL/all-kingdom work remains assigned to later programme phases rather than left as final deferred debt.
