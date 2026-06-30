# Archived Task Packs

This folder keeps completed task packs and chat starters for historical reference.

Player Self-Service Command Centre completed Phase 1 audit/design, Phase 2 `/me` shell
foundation, Phase 3 Modern Account Centre, Phase 4 Modern Reminder Centre, Phase 5 Visual
Dashboard Card and Preferences Hub, Phase 6 Guided Management Cards and Workflow Simplification,
and Phase 7 Unified Reminder Centre and Dashboard Card Alignment execution records are archived
here. The active programme pack and next-phase task pack remain in `docs/task_packs/`.

Archived packs include completed registry/account-resolution, telemetry, stats, pytest
log-isolation and original slow-pytest optimisation, high-priority KVK state, MGE Phase 1 polish,
PreKvK schema standardisation, completed KVK Player Experience Redesign execution phases,
completed KVK_ALL phase initiation statements, and the DL_bot upload-routing and startup/lifecycle
programmes.

Import pipeline archives include Task A Import Process Schema Resilience and Shield Time Support,
which delivered fallback `Credit` / `Conduct Score` compatibility, interim auto partial fallback
overlay support, player-location shield timestamp persistence, and the temporary ASCII-safe SQL
bulk CSV hotfix. Task B Unicode Import Contract replaced the temporary ASCII fallback with raw text
SQL staging plus explicit typed conversion. Task C Slice 1 Import Architecture and Service/DAL
Wrappers extracted fallback import file orchestration and DAL helpers while preserving current
route, command, SQL, and import output behavior. Task C Slice 2 Durable Batch Audit Foundation
added SQL-owned durable import batch/phase audit tables and stored procedure writers, bot audit
DAL/service wrappers, and fallback-first audit wiring correlated to `dbo.FallbackImportBatchControl`
without changing route, command, queue, staging, SQL procedure, or import output behavior. Task C
Slice 3 Non-Fallback Audit Adoption mapped location, Honor, PreKvK, weekly activity, MGE, and
inventory import state surfaces, then wired player-location generic audit for the auto
`scan_1198.csv` route and `/location import` command merge path. Task C Slice 3A Import Audit
Batch Counter Normalization added optional `RowsInSource` support to SQL-owned terminal audit
writer procedures, threaded it through bot DAL/service wrappers, and smoke tested normalized
fallback and player-location batch counters without historical backfill.
Task C Slice 4 Honor Import Audit Adoption wired the KVK Honor upload/import path to generic
durable audit with `honor_xlsx_parse`, `honor_sql_ingest`, and `honor_post_import_refresh` phases,
correlated completed batches to `dbo.KVK_Honor_Scan`, preserved user-facing route/import behavior,
and smoke tested a completed Honor batch with 562 source/staged/written rows.
Task C Slice 5 PreKvK Import Audit Adoption wired the PreKvK upload/import path to generic durable
audit with `prekvk_xlsx_parse`, `prekvk_sql_ingest`, and `prekvk_post_import_refresh` phases,
correlated accepted batches to `dbo.PreKvk_Scan`, correlated duplicate/rejected batches to
`dbo.PreKvk_ImportHistory` when available, preserved user-facing route/import behavior, and smoke
tested accepted, duplicate, and rejected PreKvK outcomes.
Task C Slice 6 Weekly Activity Import Audit Adoption wired the weekly activity upload/import path
to generic durable audit with `weekly_activity_xlsx_parse`, `weekly_activity_sql_ingest`, and
`weekly_activity_post_import_backup` phases, correlated accepted batches to
`dbo.AllianceActivitySnapshotHeader`, left duplicate and failed-without-snapshot outcomes
uncorrelated, preserved user-facing route/import behavior, and smoke tested completed and duplicate
weekly activity outcomes.
Task C Slice 7 MGE Results Import Audit Adoption wired the MGE results upload/manual import path
to generic durable audit with `mge_results_xlsx_parse`, `mge_results_sql_ingest`, and
`mge_results_post_import_backup` phases, correlated accepted and post-domain-row failed outcomes
to `dbo.MGE_ResultImports`, left duplicate/pre-domain outcomes uncorrelated, preserved route,
manual overwrite, report, and importer behavior, resolved review hardening feedback, and was
reported smoke tested successfully on 2026-06-30.
Task C Slice 8 Inventory Import Audit Adoption wired inventory image uploads, command-session
imports, additional-material continuation, approval/reject/cancel/timeout/failure outcomes, admin
debug, and original-upload cleanup into generic durable audit while preserving inventory's domain
audit/history model and route UX. Accepted lifecycle outcomes correlate to
`dbo.InventoryImportBatch`. Operator smoke testing on 2026-06-30 confirmed resources, speedups,
materials, failure, and cancel audit outcomes, including a three-file material continuation with
`RowsInSource=3`, `RowsStaged=3`, and `RowsWritten=25`.

The active import follow-up is Task C Slice 9 in
`../Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 9 KVK_ALL and Rally Forts Import Audit Adoption.md`.

The DL_bot upload-routing and startup/lifecycle optimisation programme is complete through
Phase 6L:

- `DL_bot.py` remains process-entry, command-registration, signal, and message/upload owner.
- `bot_loader.py` remains bot construction owner.
- `bot_instance.py` remains lifecycle event, startup phase, task-supervision, and bot-side graceful
  teardown owner.

Remaining related work is tracked in `docs/reference/deferred_optimisations.md` as separate future
programmes, including command-surface migration, queue-domain redesign, optional SQL-backed queue
persistence, disabled secondary command-surface cleanup, and pinned calendar tracker atomic-write
hardening.
