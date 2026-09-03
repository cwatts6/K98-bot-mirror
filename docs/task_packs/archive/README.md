# Archived Task Packs

This folder keeps completed task packs and chat starters for historical reference.

Discord Embed Payload Safety Phase 2D Operator Diagnostics Convergence completed implementation,
review remediation, automated validation, final Changes-only security review, production-candidate
deployment, and operator smoke on 2026-09-03. Focused review verification passed `64`, the complete
suite passed `3172 passed, 2 skipped`, pre-commit passed, and scan
`984d93ff-29b1-4dd3-b681-a9830d01a1c4` covered the exact production runtime range with Deep off,
all 11 runtime files covered, and zero findings. SQL was a no-diff skip. Restart, queue persistence
and rehydration, `/ops logs` and component interactions, `/ops show_logs`,
`/ops view_restart_log`, `/ops last_errors`, and the representative command set passed without
`File.to_dict`, Discord `50035`, traceback, command error, or error/critical entry. Mirror PR #255
and production PR #562 are ready for manual merge; final production-main verification remains
operator-owned. Phase 2E Ark Persistence Orchestration and Delivery Observability is prepared as
the next audit-first task.

Discord Embed Payload Safety Phase 2C Player-Facing Rankings and History Convergence completed its
evidence-led tests/documentation-only implementation, review, candidate deployment, and operator
smoke on 2026-09-03 through mirror PR #254 and production PR #561. Authoritative contracts proved
every live rankings/history payload safe, so no runtime correction was required. Focused validation
passed `79`; the full suite passed `3104 passed, 2 skipped`; Changes-only scan
`25a90732-3ad2-4ee0-9138-d1f4f11bbf36` covered all nine changed files with Deep off and zero
findings; SQL was a no-diff skip. Both PRs await manual merge and final production-main
verification. Phase 2D Operator Diagnostics Convergence is prepared as the next review-first slice.

Discord Embed Payload Safety Phase 2B Evidence-Led Ark Payload Hardening completed implementation,
validation, Changes-only security review, production-candidate promotion, and operator candidate
smoke on 2026-09-02. Mirror PR #253's delivered tree is present on mirror `main`; production PR
#560 is merged in production commit `6da1c083`. The full suite passed `3090 passed, 2 skipped`; scan
`79603f53-69f8-4586-9296-760385dd9420` ran over the exact approved bot runtime range with Deep off,
complete coverage, and zero reportable findings; SQL was a no-diff skip. Smoke built a four-field,
346-character registration payload with no compaction/omission, retained `should_announce=False`,
and edited the existing message reference without state/identity change, duplication, or `50035`.
Phase 2C rankings/history is archived above as delivered and operator smoke accepted. Diagnostics,
Ark persistence and delivery observability, active-reminder atomicity, and atomic Pre-KVK
reservation remain assigned to Phases 2D through 2G rather than left unowned.

Discord Embed Payload Safety Phase 2A Event and Calendar Convergence completed implementation,
review, promotion preparation, and representative production smoke on 2026-09-02 through mirror
PR #252 and production PR #559, pending the operator's manual merges. Final automated validation
passed `3078 passed, 2 skipped`; the applicable Changes-only reviews ran with Deep off and found no
reportable issues. Restart smoke rehydrated the persistent pinned view, armed the reminder and
daily-refresh tasks, and edited message `1488086669876920341` in place for 27 events. Payload
metrics were `fields=15`, `chars=4789`, `max_field_value=533`, `compacted_events=0`, and
`omitted_events=0`, with no duplicate or Discord `50035`. Public/DM reminders and an omission marker
were not naturally forced during smoke; their unchanged behavior and boundary cases retain
automated coverage. Phase 2B is now archived above as delivered and candidate-smoke accepted.

Discord Embed Payload Safety Phase 1 completed implementation, review, promotion preparation, and
operator edit-path smoke on 2026-09-02 through mirror PR #251 and production PR #558, pending the
operator's manual merges. It delivered `core/discord_embed_limits.py`, the exact 1,029-character
Pre-KVK regression and complete-event packing, shared-sender overflow repair, and sole Pre-KVK
ownership of `prekvk_daily`. Focused validation passed `40` tests and the full/log-noise suites
passed `3059 passed, 2 skipped`; two Changes-only reviews ran with Deep off and zero reportable
findings. Live smoke validated 13 fields, 1,847 aggregate characters, a 530-character largest
field, and an in-place edit of message `1544617668999381044` with matching persisted state and no
duplicate or `50035`. The archived task pack, starter, and findings record preserve the delivery.
Phase 2A event/calendar convergence and Phase 2B Ark hardening are archived as delivered.
Rankings/history, diagnostics, Ark persistence/observability, active-reminder atomicity, and atomic
Pre-KVK reservation retain the named Phase 2C-2G follow-up sequence.

Pinned Calendar Tracker Atomic Persistence completed implementation, validation, Changes-only
security review, production deployment, and operator restart smoke on 2026-09-01 through mirror
PR #250 and production PR #557. The existing pinned message was rehydrated and edited in place
with unchanged channel/message identity, the tracker remained valid JSON with an advanced
`updated_at_utc`, no duplicate or stale temporary file remained, and the daily refresh scheduled
normally. Its task pack and chat starter are archived here as the completed execution record. No
SQL, config, dependency, command, permission, cache, reminder, scheduler, or user-facing behavior
change was delivered.

DL_bot Offload Callable Once-Only Failure Semantics completed implementation, production review,
automated validation, and operator Discord smoke on 2026-09-01 through mirror PR #248 and
production PR #555, pending manual merge. The smoke confirmed that a duplicate MGE import failed
as expected and that a standard scan import completed successfully with its route unaffected. Its
task pack and chat starter are archived here; upload admission/backpressure and the separate
once-only audits for `stats_module.py` and `ui/views/kvk_history_view.py` remain active deferred
items.

KingdomScanData4 Phase 5.2 Post-Stabilisation Cleanup completed through mirror PR #246 without a
runtime or SQL behaviour change. Its task pack and chat starter are archived here. The separate
MINI_AMD transaction-log backup cadence policy question remains active in the deferred register;
it is not unfinished Phase 5.2 work.

GovernorOS Phase 8.1 Leadership Player Review Visual Hierarchy, Presence and Performance completed
and was operator accepted on 2026-07-23. Mirror PR #231 and production PR #538 carry the bot
delivery; SQL PRs #58 and #59 supplied the additive rank and exact-ID existence support. Its task
pack and chat starter are archived here, while representative delivered-path performance evidence
remains separately deferred.

MGE Process Polish Phase 2 completed in mirror PR #75, then was production deployed and smoke
tested through production PR #386. Its initiation/delivery record is archived here as historical
service-boundary evidence; it is not an active MGE implementation pack.

King of All Britain KVK Card Background completed implementation, review, and operator visual smoke
on 2026-08-28 through mirror PR #244 and production PR #551, pending manual merge. Both KVK Stats
and Targets renderers select the pinned `1180 × 640` RGB production backdrop through the existing
normalised fixed mapping and unchanged fallback chain. Focused renderer coverage passes 32 tests,
the mirror and production Changes reviews ran with Deep Off and returned zero findings, and the
operator confirmed the live Stats and Targets cards display the backdrop correctly and look
perfect. Local Stats, More Stats, active Targets, and exempt Targets artifacts are retained under
`smoke_artifacts/king_of_all_britain/`. No SQL, command, payload, publication, permission,
persistence, or registration contract changed; deployment requires only the normal bot rollout and
restart. The archived task pack and starter are the historical completion records.

KVK Target Publication State Separation Phase 1 was deployed and operator accepted on 2026-08-26
through mirror PR #235, production PR #542, and SQL PR #73. The import-path transaction follow-up
was deployed through mirror PR #236 and production PR #543. Production publication metadata,
source-scan, row-count, cache rebuild, and Discord smoke checks passed. Its task pack and chat
starter are archived here.

KVK Targets Quality Phase 2 completed the deferred target-architecture programme through mirror
PRs #237-#242, production PRs #544-#549, and Phase 2A SQL PR #74. The six independently gated
slices delivered immutable typed target rows, one service-owned presentation-input path, a bounded
crash-recoverable target cache repository, explicit fighting-lifecycle terminology, lifecycle DAL
ownership, history rank result-set hardening, and final target interaction cleanup. Phase 2F
production smoke on 2026-08-28 passed history, targets, stats, CrystalTech, and shared account-picker
flows with clear logs. Its task pack and chat starter are archived here; the final follow-up review
found no new Phase 2 requirement or active target-subsystem deferred optimisation.

CrystalTech Path Refresh and Config Corrections completed operator smoke and acceptance on
2026-08-25 in mirror PR #234 and production PR #541, pending manual merge. The archived bundle
records the 404-step source contract, the 11 approved follow-up image/spelling corrections,
focused regression coverage, final security Changes review, clean-rollover/no-extant-progress
precondition, successful validate/reload checks, and two-user progression/reset smoke evidence.

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
here. The original programme is complete; its closed programme pack remains in `docs/task_packs/`.

Player Self-Service Command Centre v2 / GovernorOS completed Phases 1 through 8. The archived
records cover the dashboard blueprint/data foundation, governor selector and premium dashboard,
direct Inventory reports and visual alignment, Accounts, Reminders, and the authoritative shared
KVK/Calendar next-alert projection. Phase 5D.1 delivered in mirror PR #223 and production PR #530;
operator smoke accepted the final `/me reminders` presentation on 2026-07-15. Phase 5E Preferences
delivered in mirror PR #224 and production PR #531 and was deployed on 2026-07-16; its archived
records capture the accepted top-left-avatar Personal Settings card, local-time/UTC fallback,
regional profile, Inventory privacy flow, one Manage Settings journey, and Accounts-owned Update
VIP migration with no SQL deployment. The active v2 programme pack remains in `docs/task_packs/`.
Phase 5F Inventory Surface Consolidation and Legacy Retirement delivered in mirror PR #225, was
promoted at production-branch commit `89f7da16`, and was operator accepted after final Discord smoke
on 2026-07-16. Its archived records capture retirement of `/me inventory`, `/myinventory`,
`/inventory_preferences`, `/export_inventory`, public/combined Inventory viewing and the combined
export; preservation of the selected-governor reports and their three exports; the profile-first
Personal Settings reflow; final 39 top-level/8 `/me` command baselines; zero SQL change; and the
dormant rollback table. Phase 5G Account Data Export Consolidation completed final review,
deployment/resync, and operator Discord smoke on 2026-07-17 through mirror PR #227 and production
PR #534. Its archived task pack and starter record the canonical Account Summary Download data
journey, retirement of `/me exports` and `/my_stats_export`, the `38 / 7 / 2` command surface, all
three private output contracts, corrected workbook/history semantics, no SQL change, and the Phase 6
interactive Stats handoff. Phase 6 Interactive Period Performance completed final production Discord
smoke on 2026-07-18 through mirror PR #228 and production PR #535 after SQL PRs #43/#44 deployed.
Its archived task pack and starter record private-anywhere `/me stats`, the accepted 1702x924
Overview/Activity/Combat format, opaque paged governor selection plus explicit All Linked, exact
periods and coverage, source-refresh semantics, `/my_stats` retirement, preserved `/stats player`,
the `37 / 100 / 8 / 2` command surface, zero unresolved bot/SQL Changes findings, and final operator
acceptance. Phase 7 completed the retained `/me` visual/content closeout on 2026-07-19 through
mirror PR #229 and production PR #536. Phase 8 completed the one private `/stats player` leadership
journey, global canonical combat alignment, bounded source/audit/history contracts and
`/player_profile` retirement on 2026-07-21 through mirror PR #230 and production PR #537 after the
SQL migration series and merged follow-up SQL PR #53 deployed. Its archived records preserve the
accepted `36 / 100 / 8 / 1 / 2` command surface and production smoke evidence. The living v2
programme pack remains in `docs/task_packs/`; Phase 8.1 is complete and its execution records are
archived here. Phase 9 `/stats kingdom` remains separately proposed and gated.

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

Task C Slice 12 is complete and archived. The active import follow-up is Task C Slice 13, whose
July evidence/object map must be refreshed against the post-August KingdomScanData4 tree before
execution:

`../Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 13 UPDATE_ALL2 Phase Evidence Review and SUMMARY_PROC Scope Audit.md`.

The DL_bot upload-routing and startup/lifecycle optimisation programme is complete through
Phase 6L:

- `DL_bot.py` remains process-entry, command-registration, signal, and message/upload owner.
- `bot_loader.py` remains bot construction owner.
- `bot_instance.py` remains lifecycle event, startup phase, task-supervision, and bot-side graceful
  teardown owner.

Remaining related work is tracked in `docs/reference/deferred_optimisations.md` as separate future
programmes, including command-surface migration, queue-domain redesign, optional SQL-backed queue
persistence, and disabled secondary command-surface cleanup. Pinned calendar tracker atomic-write
hardening is complete and recorded in `docs/reference/archive/deferred_optimisations_resolved.md`.
