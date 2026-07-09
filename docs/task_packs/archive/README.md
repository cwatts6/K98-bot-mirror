# Archived Task Packs

This folder keeps completed task packs and chat starters for historical reference.

Discord Voting Post Framework Phase 1 through Phase 22 execution records are archived here. The
programme delivered SQL-backed vote posts, button voting, one-vote-per-Discord-user enforcement,
vote changes, live Pillow result cards, scheduler reminders, automatic close, manual close,
persistent views, mention safety, guided admin UX, private totals-only export, private
admin/leadership voter-audit export, hidden-until-close result visibility, single-question
multi-select voting, choice-only multi-question surveys, private survey response-detail export,
SQL audit logging, free-text survey questions, choice-question details, optional survey questions,
fixed 1-5 rating survey questions, rollout-safe rating migration guards, production promotion, and
complete ranking survey questions, plus Phase 10 private Survey Export v2 report-bundle CSV output
and SQL survey reporting views/procedure, and Phase 11 private admin/leadership aggregate
dashboard-safe reporting contracts, and Phase 12 persisted survey drafts/resume with draft
exclusion from public results, private dashboard summaries, status totals, and existing export
profiles until final submit, Phase 13 private aggregate dashboard UI, and Phase 14 configurable
rating scales with fixed 1-5 compatibility, fixed 1-10 ratings, custom min/max scales, endpoint
labels, named rating choices, draft/resume compatibility, and private/public aggregate reporting
compatibility, plus Phase 15 per-option Unicode/custom Discord emoji support, guided option-polish
controls, Discord/status/dashboard emoji display including animated custom emoji, generated-card
custom emoji text fallback, and narrow dense-summary readability polish, plus Phase 16 guided
survey builder review/edit/delete/reorder controls and `/vote_admin survey_update` for safe
open-survey metadata updates with response-sensitive and closed-survey locks, plus Phase 17
`/vote_admin` command-surface audit closure with no runtime command change, plus Phase 18
cross-survey/workbook export redesign audit closure with no runtime export or documentation
guidance change because the current private exports are sufficient and understood, plus Phase 19
private leadership engagement dashboard delivery with compact top-level engagement metrics,
role-filtered eligibility, fixed rolling windows, best/worst single poll, one-Discord-user
counting regardless of governor IDs, raw-answer exclusion, and graceful dashboard timeout handling,
plus Phase 20 private per-user engagement CSV export delivery under `/vote_admin engagement`, and
Phase 21 private engagement graph assessment audit closure with no runtime graph implementation
because the CSV export remains sufficient until leadership defines a concrete graph requirement,
plus Phase 22 final retention/redaction policy and SQL-only admin delete delivery through
`dbo.VoteSurveyDeletionAudit` and `dbo.usp_VoteSurveyAdminDelete` with no bot runtime/UI changes.
Operator smoke/regression testing is complete through 2026-07-08, and SQL-only Phase 22 deployment
and smoke testing completed successfully on 2026-07-09 after SQL PR #39 and follow-up SQL PR #40
were merged and pushed to production.
The closed programme pack remains in `../`.

Player Self-Service Command Centre completed Phase 1 audit/design, Phase 2 `/me` shell
foundation, Phase 3 Modern Account Centre, Phase 4 Modern Reminder Centre, Phase 5 Visual
Dashboard Card and Preferences Hub, Phase 6 Guided Management Cards and Workflow Simplification,
and Phase 7 Unified Reminder Centre and Dashboard Card Alignment execution records are archived
here. The active programme pack and next-phase task pack remain in `docs/task_packs/`.

Archived packs include completed registry/account-resolution, telemetry, stats, pytest
log-isolation and original slow-pytest optimisation, high-priority KVK state, MGE Phase 1 polish,
PreKvK schema standardisation, completed KVK Player Experience Redesign execution phases,
completed KVK_ALL phase initiation statements, the completed KVK_ALL Schema Modernisation
programme pack and supporting metric/source references, and the DL_bot upload-routing and
startup/lifecycle programmes.

KVK_ALL Schema Modernisation is complete through Phase 11. Phase 11 Acclaim Output Contract Polish
closed the final output-contract items by keeping max_contribute_gain internal, exposing
cur_contribute_gain as acclaim_gain in player-facing outputs, preserving the 10-result-set export
contract, preserving Google Sheets spreadsheet and tab names, and leaving Discord embeds unchanged.
Operator smoke evidence confirmed KVK.vw_FightingDataset now exposes acclaim_gain, Google Sheets
exports show acclaim_gain without Highest Acclaim gain, and KVK_ALL imports plus export completed
successfully. Future KVK_ALL work should start from a fresh task pack rather than continuing the
schema modernisation programme as Phase 12.

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
Task C Slice 9 KVK_ALL Import Audit Adoption delivered the KVK_ALL half of the split
KVK_ALL/Rally Forts audit-adoption scope in mirror PR #190 and production PR #498. It wired the
KVK_ALL upload route to generic durable audit while preserving route UX, embed text, importer
contracts, SQL ingest/recompute behavior, Google Sheet link behavior, and auto-export scheduling.
Accepted imports correlate to `KVK.KVK_Scan` using `ExternalBatchId=<KVK_NO>:<ScanID>`, and
KVK-details timestamp rejections correlate to `KVK.KVK_Ingest_Diagnostics` when a diagnostic id
exists. Operator smoke testing on 2026-06-30 confirmed completed batch 23 with `ExternalBatchId=15:83`
and 9194 source/staged/written rows, plus failed diagnostic batch 22 with `ExternalBatchId=2` and
9194 staged/skipped rows. Rally Forts was split into Task C Slice 10 and later delivered in
mirror PR #191 and production PR #499.

Task C Slice 10 Rally Forts Import Audit Adoption delivered generic durable audit for Rally Forts
uploads, correlated successful daily/all-time imports to `dbo.IngestionLog/<IngestionID>`, kept
duplicate/no-row/unrecognized/preflight/failure outcomes externally uncorrelated, and was reported
smoke tested successfully on 2026-07-01.

Task C Slice 11 Import Audit Phase Timestamp Normalization normalized generic
`ImportAuditPhase` timestamp handling in bot service and SQL writer boundaries, preserving
duration semantics, audit best-effort behavior, route/importer contracts, batch counters, external
correlation, SQL import behavior, user-facing behavior, and historical rows. Production smoke
testing on 2026-07-01 confirmed new fallback batch 27 and player-location batch 28 phase rows no
longer show `CompletedAtUtc < StartedAtUtc`.

The active import follow-up is Task C Slice 12 in
`../Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 12 UPDATE_ALL2 Wrapper Audit Outputs.md`.

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
