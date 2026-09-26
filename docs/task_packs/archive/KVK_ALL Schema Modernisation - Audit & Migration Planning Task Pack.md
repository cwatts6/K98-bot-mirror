KVK_ALL Schema Modernisation — Audit & Migration Planning Task Pack

Status: archived completed audit pack. The KVK_ALL Schema Modernisation programme is complete
through Phase 11 and this audit/planning pack is retained as historical planning context only.

Objective

Perform a full end-to-end audit and migration assessment of the KVK_ALL ingestion, recompute, export, reporting, and downstream analytics pipeline following the introduction of the new KVK_ALL workbook schema.

This is an audit-first task only.

DO NOT implement changes in this task.

The goal is to:

fully understand the new workbook schema
identify every impacted Python module and SQL object
identify schema mismatches and technical debt
define a phased migration plan
define backward compatibility strategy
define required SQL schema changes
define required reporting/export changes
identify restart/performance risks
prepare implementation-ready phased task packs
Required Reading Order

Read in this exact order before starting:

Uploaded workbook sample:
1086045_05_08_2026,_02_21_38_AM.xlsx
Uploaded Python modules:
kvk_all_importer.py
DL_bot.py
allkingdoms.py
gsheet_module.py
Engineering standards:
docs/templates/Codex Task Pack Template.md
K98 Bot - Project Engineering Standards.md
K98 Bot - Coding Execution Guidelines.md
K98 Bot - Testing Standards.md
K98 Bot - Skills & Refactor Triggers.md
k98 Bot - Deferred Optimisation Framework.md
SQL repository:
cwatts6/K98-bot-SQL-Server
Critical Scope Rules
This is NOT an implementation task

You MUST NOT:

modify code
create PRs
change SQL
refactor modules
change exports
alter Google Sheets outputs

You MUST ONLY:

audit
analyse
map dependencies
identify risks
define phases
define migration approach
Mandatory Audit Areas
1. Workbook Schema Audit

Fully analyse:

all tabs
all columns
tab purposes
duplicate/redundant metrics
min/max/current field patterns
contribution metrics
rank metrics
derived fields
summary tabs

Identify:

newly introduced columns
renamed columns
removed columns
obsolete legacy assumptions

Document:

canonical schema proposal
recommended naming standards
versioning strategy
2. Python Import Pipeline Audit

Audit ALL Python touchpoints including but not limited to:

Import path
DL_bot.py
kvk_all_importer.py
Export/reporting
gsheet_module.py
stats_alerts/allkingdoms.py
Search for additional dependencies:
KVK references
Windowed reporting
Player aggregation
Camp aggregation
Kingdom aggregation
Google Sheet exports
stats alerts
telemetry
caches
views
embeds
helper utilities

You MUST identify:

direct dependencies
implicit dependencies
assumptions about result-set counts
assumptions about column names
assumptions about fixed schemas
hardcoded tabs/order logic
export formatting dependencies
restart/state risks
scaling/performance concerns
3. SQL Audit (MANDATORY)

Search the SQL repository thoroughly.

At minimum audit:

Tables
KVK.KVK_AllPlayers_Stage
KVK.KVK_AllPlayers_Raw
KVK.KVK_Player_Windowed
KVK.KVK_Kingdom_Windowed
KVK.KVK_Camp_Windowed
KVK.KVK_Scan
KVK.KVK_Player_Baseline
KVK.KVK_Ingest_Negatives
Stored procedures
KVK.sp_KVK_AllPlayers_Ingest
KVK.sp_KVK_Recompute_Windows
KVK.sp_KVK_Get_Exports
Functions/views
dbo.fn_KVK_Player_Aggregated
dbo.fn_KVK_Kingdom_Aggregated
dbo.fn_KVK_Camp_Aggregated
KVK.vw_FightingDataset

Also search for:

any references to:
points_difference
kills_iv_diff
kills_v_diff
dead_diff
max_units_healed_diff
kill_points_diff
latest_power

Identify:

downstream dependencies
computed assumptions
cumulative assumptions
schema coupling
export coupling
indexing concerns
recompute bottlenecks
Required Deliverables
1. Current Architecture Map

Include:

ingestion flow
SQL flow
recompute flow
export flow
reporting flow
Discord/reporting dependencies
Google Sheets dependencies

Use clear structured sections.

2. Schema Delta Report

Create a detailed mapping:

New Workbook Column	Existing Equivalent	Current Usage	Proposed Usage	Required SQL Changes	Notes

Include ALL columns.

3. Risk Assessment

Assess:

backward compatibility
recompute performance
table growth
indexing
export instability
result-set coupling
Google Sheets scaling
Discord embed impacts
restart risks
transaction log impact
future schema evolution risks
4. Migration Strategy

Recommend:

phased migration plan
rollout order
compatibility approach
dual-schema support strategy
schema version detection approach
validation strategy
rollback strategy
5. Proposed Future Architecture

Recommend:

canonical schema layer
importer abstraction improvements
schema-version handling
metadata-driven mapping
export decoupling
recompute modularisation
reporting abstraction
audit logging improvements

DO NOT implement.

6. Deferred Optimisations (MANDATORY)

Capture ALL findings using the required structured format.

Expected Output Format
Executive Summary
Current Pipeline Architecture
Workbook Schema Audit
SQL Dependency Audit
Python Dependency Audit
Export/Reporting Dependency Audit
Schema Delta Mapping
Risks
Recommended Phases
Migration Strategy
Deferred Optimisations
Suggested Follow-On Task Packs
Success Criteria

Task is complete ONLY if:

all dependencies are mapped
all impacted SQL objects are identified
all impacted Python modules are identified
workbook schema fully analysed
migration phases clearly defined
risks documented
future architecture recommendations provided
deferred optimisations documented
Important Constraints

DO NOT:

start implementation
make assumptions about unused columns
remove fields without documenting rationale
simplify scope
ignore downstream exports/reporting

DO:

assume future workbook schemas may evolve again
optimise for maintainability
optimise for restart safety
optimise for schema evolution
optimise for long-term reporting flexibility
Suggested Future Follow-On Tasks (Do NOT Implement Now)

Potential future phases likely include:

Schema abstraction layer
SQL schema migration
Importer refactor
Recompute modularisation
Export decoupling
Reporting enhancements
Historical analytics expansion
Contribution metrics integration
Summary-tab ingestion
Performance/indexing optimisation
