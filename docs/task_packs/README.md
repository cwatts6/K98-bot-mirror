# Task Packs

Active task packs live in this folder. Completed DL_bot upload-routing, startup/lifecycle, and
completed command-platform programme packs were moved to `archive/` to keep the active task-pack
list focused.

Do not continue the completed DL_bot programme as Phase 6M. Open a fresh task pack for the
queue-domain redesign, optional SQL-backed queue persistence, SQL deployment workflow, or pinned
calendar tracker atomic-write hardening when one of those programmes is approved.

The Command Platform Audit & Optimisation Programme is complete. Its programme pack, phase packs,
and chat starters are archived under `archive/`.

Phase 1, Phase 2, Phase 3, Phase 4, Phase 5, Phase 5A, Phase 6, Phase 7, the programme pack, and
the superseded command-surface balancing audit pack are archived as execution records.

Phase 7 was completed in PR 139 (`codex/command-platform-phase-7-governance`), merged, and pushed
to production on 2026-06-02. It closed the Command Platform Audit & Optimisation Programme by
adding command-registration validator baseline enforcement, JSON/Markdown inventory artifact
output, pre-commit validation, focused command-governance CI, and command-change checklist
material.

Player self-service workflow redesign and public calendar/KVK calendar UX redesign remain separate
deferred optimisation programmes, not additional command-platform phases.

Import pipeline status:

- Task A Import Process Schema Resilience and Shield Time Support is delivered in mirror PR #179,
  production PR #487, and SQL PR #21, with SQL deployment and operator smoke testing completed on
  2026-06-28.
- Task A records are archived under `archive/`:
  - `archive/Codex Task Pack - Import Process Schema Resilience and Shield Time Support.md`
- Task B Import Pipeline Deferred Optimisation Unicode Import Contract is delivered in mirror PR
  #180, production PR #488, and SQL PR #22. SQL deployment completed before bot rollout. Smoke
  testing confirmed full fallback with `Credit`, full fallback with `Conduct Score`, interim auto
  partial fallback with non-ASCII names, and existing location shield import unchanged.
- Task B records are archived under `archive/`:
  - `archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task B.md`
  - `archive/Codex Chat Starter - Import Pipeline Deferred Optimisation Task B Unicode Import Contract.md`
- Task C Slice 1 Import Architecture and Service/DAL Wrappers is delivered in mirror PR #181 and
  production PR #489. It extracted fallback import file orchestration into
  `services/fallback_import_service.py`, extracted fallback import SQL/data-access helpers into
  `stats/dal/fallback_import_dal.py`, kept `stats_module.py` as the compatibility entry point, and
  made no SQL, upload route, or Discord command behavior changes. Smoke testing completed
  successfully.
- Task C Slice 1 records are archived under `archive/`:
  - `archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Import Architecture and Service DAL Wrappers.md`
  - `archive/Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Import Architecture and Durable Audit.md`
- Task C Slice 2 Durable Batch Audit Foundation is delivered in mirror PR #182 and SQL PR #23. It
  added `dbo.ImportAuditBatch`, `dbo.ImportAuditPhase`, SQL-owned audit writer procedures, bot
  DAL/service wrappers, and fallback-first audit wiring correlated to
  `dbo.FallbackImportBatchControl`. Smoke testing on 2026-06-29 confirmed full fallback and interim
  auto partial fallback produce completed audit batches and phase rows while preserving existing
  import output behavior.
- Task C Slice 2 records are archived under `archive/`:
  - `archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 2 Durable Batch Audit Foundation.md`
  - `archive/Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 2 Durable Batch Audit Foundation.md`
- Task C Slice 3 Non-Fallback Audit Adoption is delivered in mirror PR #183 and production PR
  #491. It mapped current non-fallback import state surfaces, then wired player-location generic
  audit for the auto `scan_1198.csv` route and `/location import` command merge path while
  preserving user-visible route, command, queue, embed, file, staging, cache refresh, SQL
  procedure, and output behavior. Production smoke testing on 2026-06-29 confirmed a completed
  `player_location` audit batch with 301 staged/written rows and a skipped no-valid-row batch.
- Task C Slice 3 records are archived under `archive/`:
  - `archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3 Non-Fallback Audit Adoption.md`
  - `archive/Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 3 Non-Fallback Audit Adoption.md`
- Task C Slice 3A Import Audit Batch Counter Normalization is delivered in mirror PR #184,
  production PR #492, and SQL PR #24. SQL deployment completed before bot rollout. Production smoke
  testing on 2026-06-29 confirmed fallback batch 5 completed with `RowsInSource=374` and
  player-location batch 6 completed with `RowsInSource=302`; earlier pre-update rows retained
  `RowsInSource=NULL`, confirming no historical backfill.
- Task C Slice 3A records are archived under `archive/`:
  - `archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 3A Import Audit Batch Counter Normalization.md`
  - `archive/Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 3A Import Audit Batch Counter Normalization.md`
- Task C Slice 4 Honor Import Audit Adoption is delivered in mirror PR #185 and production PR
  #493. Production smoke testing on 2026-06-29 confirmed Honor audit batch 7 completed with
  `RowsInSource=562`, `RowsStaged=562`, `RowsWritten=562`, `RowsSkipped=0`,
  `ExternalBatchTable=dbo.KVK_Honor_Scan`, and `ExternalBatchId=15:92`.
- Task C Slice 4 records are archived under `archive/`:
  - `archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 4 Honor Import Audit Adoption.md`
  - `archive/Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 4 Honor Import Audit Adoption.md`
- Task C Slice 5 PreKvK Import Audit Adoption is delivered in mirror PR #186 and production PR
  #494. Production smoke testing on 2026-06-29 confirmed accepted PreKvK batch 8 completed with
  `ExternalBatchTable=dbo.PreKvk_Scan`, `ExternalBatchId=15:1095`, `RowsInSource=1`,
  `RowsStaged=1`, `RowsWritten=1`, `RowsSkipped=0`; duplicate batch 9 completed with
  `ExternalBatchTable=dbo.PreKvk_ImportHistory`, `ExternalBatchId=17`, `RowsSkipped=1`; and
  rejected batch 10 failed with `ErrorType=MissingColumns`,
  `ExternalBatchTable=dbo.PreKvk_ImportHistory`, and `ExternalBatchId=18`.
- Task C Slice 5 records are archived under `archive/`:
  - `archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 5 PreKvK Import Audit Adoption.md`
  - `archive/Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 5 PreKvK Import Audit Adoption.md`
- Task C Slice 6 Weekly Activity Import Audit Adoption is delivered in mirror PR #187 and
  production PR #495. Production smoke testing on 2026-06-29 confirmed two completed weekly
  activity batches correlated to `dbo.AllianceActivitySnapshotHeader` and one duplicate batch with
  `RowsSkipped=816` and no external correlation.
- Task C Slice 6 records are archived under `archive/`:
  - `archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 6 Weekly Activity Import Audit Adoption.md`
  - `archive/Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 6 Weekly Activity Import Audit Adoption.md`
- Task C Slice 7 MGE Results Import Audit Adoption is delivered in mirror PR #188 and production
  PR #496. Operator smoke testing was reported successful on 2026-06-30. Accepted and
  post-domain-row failed MGE outcomes correlate to `dbo.MGE_ResultImports`; duplicate/pre-domain
  outcomes remain uncorrelated; manual command/overwrite imports are audited through the importer.
- Task C Slice 7 records are archived under `archive/`:
  - `archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 7 MGE Results Import Audit Adoption.md`
  - `archive/Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 7 MGE Results Import Audit Adoption.md`
- Task C Slice 8 Inventory Import Audit Adoption is delivered in mirror PR #189 and production
  PR #497. Operator smoke testing on 2026-06-30 confirmed completed resources, speedups,
  materials, failure, and cancel outcomes. The three-file material continuation smoke now records
  `RowsInSource=3`, `RowsStaged=3`, `RowsWritten=25`, and correlation to
  `dbo.InventoryImportBatch`.
- Task C Slice 8 records are archived under `archive/`:
  - `archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 8 Inventory Import Audit Adoption.md`
  - `archive/Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 8 Inventory Import Audit Adoption.md`
- Task C Slice 9 KVK_ALL Import Audit Adoption is delivered in mirror PR #190 and production
  PR #498. Production smoke testing on 2026-06-30 confirmed completed KVK_ALL batch 23 correlated
  to `KVK.KVK_Scan` with `ExternalBatchId=15:83`, `RowsInSource=9194`, `RowsStaged=9194`,
  `RowsWritten=9194`, and `RowsSkipped=0`; KVK-details rejection batch 22 failed as
  `KvkDetailsTimestampRejected` and correlated to `KVK.KVK_Ingest_Diagnostics` with
  `ExternalBatchId=2`, `RowsStaged=9194`, and `RowsSkipped=9194`.
- Task C Slice 9 records are archived under `archive/`:
  - `archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 9 KVK_ALL and Rally Forts Import Audit Adoption.md`
  - `archive/Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 9 KVK_ALL and Rally Forts Import Audit Adoption.md`
- Task C Slice 10 Rally Forts Import Audit Adoption is delivered in mirror PR #191 and production
  PR #499. Operator smoke testing was reported successful on 2026-07-01. Successful daily/all-time
  Rally imports now correlate to `dbo.IngestionLog/<IngestionID>`; duplicate/no-row/unrecognized,
  unsafe filename, SQL preflight, and importer/offload failure outcomes remain externally
  uncorrelated. Review follow-ups sanitized audit source filenames, populated source-file hashes
  for saved workbooks, and aligned backup-schedule failure metrics with other upload routes by
  recording `RowsOut=NULL`.
- Task C Slice 10 records are archived under `archive/`:
  - `archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 10 Rally Forts Import Audit Adoption.md`
  - `archive/Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 10 Rally Forts Import Audit Adoption.md`
- Task C Slice 11 Import Audit Phase Timestamp Normalization is delivered in mirror PR #192,
  production PR #500, and SQL PR #25. SQL deployment completed before bot rollout. Production smoke
  testing on 2026-07-01 confirmed new fallback batch 27 and player-location batch 28 phase rows no
  longer show `CompletedAtUtc < StartedAtUtc`; earlier historical rows remain unchanged by design.
- Task C Slice 11 records are archived under `archive/`:
  - `archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 11 Import Audit Phase Timestamp Normalization.md`
  - `archive/Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 11 Import Audit Phase Timestamp Normalization.md`
- Active Task C Slice 12 files:
  - `Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 12 UPDATE_ALL2 Wrapper Audit Outputs.md`
  - `Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 12 UPDATE_ALL2 Wrapper Audit Outputs.md`
- Task C Slice 12 is the next import architecture cleanup slice. It starts with audit/scope and
  SQL implementation-boundary confirmation for a non-invasive `dbo.UPDATE_ALL2` wrapper or
  audit-output layer that can record durable downstream rebuild timing/status evidence before any
  later procedure decomposition. `dbo.IMPORT_STAGING_PROC` decomposition, `dbo.UPDATE_ALL2`
  decomposition, residual `stats_module.py` cleanup, legacy PreKvK SQL cleanup, weekly cumulative
  view cleanup, and inventory view-orchestration extraction remain separate later slices unless
  explicitly approved.

Discord Voting Post Framework status:

- Phase 1 SQL-Backed Live Voting is delivered in mirror PR #193, production PR #501, and SQL PR
  #26. SQL deployment completed on 2026-07-01. Operator smoke testing confirmed vote creation,
  button voting, vote changes, configured `@everyone` launch behavior, SQL record updates, manual
  close, timer close, and disabled buttons after close.
- Phase 1 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 1 SQL Backed Live Voting.md`
- Phase 2 Guided Admin UX and Results Polish is delivered in mirror PR #194 and production PR
  #502. Operator smoke testing on 2026-07-01 confirmed guided create, configurable 20-character
  option labels, vote lookup choices for status/update/close, the guided update follow-up menu,
  clear manual close results, disabled buttons after close, and restart-safe open vote buttons.
- Phase 2 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 2 Guided Admin UX and Results Polish.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 2 Guided Admin UX and Results Polish.md`
- Phase 3 Admin Export and Audit Hardening is delivered in mirror PR #195. Operator smoke testing
  on 2026-07-02 confirmed `/vote_admin export` looks good, the export response posts
  ephemerally/private as expected, and existing vote buttons work after restart and deployment.
  Phase 3 delivered totals-only CSV export for one closed vote at a time and intentionally
  deferred voter-level audit export to a privacy/access-control slice.
- Phase 3 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 3 Admin Export and Audit Hardening.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 3 Admin Export and Audit Hardening.md`
- Phase 4 Voter-Level Audit Export Privacy and Access Controls is delivered in mirror PR #196 and
  production PR #504. Operator smoke testing on 2026-07-02 confirmed private/ephemeral
  voter-audit export, spreadsheet-safe `DiscordUserID`, resolved `DiscordName`, governor identity
  exclusion, correct `VoteChanged`, SQL `VoterAuditExported` metadata, and regression-test success.
- Phase 4 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 4 Voter-Level Audit Export Privacy and Access Controls.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 4 Voter-Level Audit Export Privacy and Access Controls.md`
- Phase 5 Advanced Voting Modes Audit and Hidden-Until-Close Results is delivered in mirror PR
  #197, production PR #505, and SQL PR #27. Operator smoke testing on 2026-07-02 confirmed
  hidden-until-close votes can be created and voted on through the normal public vote post, open
  hidden-result votes do not leak interim public totals or outcome state, closing reveals final
  totals/results/outcome, result visibility is shown clearly, and existing button, close, and
  export behavior remains compatible.
- Phase 5 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 5 Advanced Voting Modes Audit and Slice Planning.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 5 Advanced Voting Modes Audit and Slice Planning.md`
- Phase 6 Multi-Select / Survey Voting Audit and Design is delivered in mirror PR #198,
  production PR #506, and SQL PR #28. SQL deployment completed on 2026-07-02. Operator smoke
  testing confirmed multi-select create/vote/update/close/status paths, allowed/blocked changes,
  selection limits, restart-safe opener behavior, existing-selection prefill when reopening the
  selector, successful amendments, and one-choice regression compatibility.
- Phase 6 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 6 Multi-Select Survey Voting Audit and Design.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 6 Multi-Select Survey Voting Audit and Design.md`
- Phase 7 Choice-Only Survey Builder is delivered in mirror PR #199 and production PR #507. SQL
  migration `20260702_003_add_survey_post_framework.sql` was deployed. Operator smoke testing on
  2026-07-03 confirmed survey creation with single-choice and multi-select questions, response
  submission, response updates after submit, PublicLive and HiddenUntilClose behavior, manual
  close, automatic close, and the polished guided builder flow.
- Phase 7 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 7 Survey Builder Audit and Design.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 7 Survey Builder Audit and Design.md`
- Phase 8 Survey Free Text and Add Details is delivered in mirror PR #200, production PR #508,
  and SQL PR #30. SQL deployment completed before bot rollout. Operator smoke testing on
  2026-07-04 confirmed free-text survey questions, one details capture per choice question,
  text/detail guidance copy, submit gating, successful submit closeout, PublicLive and
  HiddenUntilClose privacy behavior, private exports, and existing survey/vote behavior.
- Phase 8 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 8 Survey Free Text and Add Details.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 8 Survey Free Text and Add Details.md`
- Active Discord Voting Post Framework files:
  - `Discord Voting Post Framework - Programme Pack.md`
  - `Codex Task Pack - Discord Voting Post Framework Phase 9 Advanced Survey Question Types Audit and Design.md`
  - `Codex Chat Starter - Discord Voting Post Framework Phase 9 Advanced Survey Question Types Audit and Design.md`
- Phase 9 is the next prepared voting slice. It starts with audit/scope only for optional survey
  questions and rating/ranking question types. It should decide completion semantics, SQL storage,
  validation, builder/player UX, PublicLive/HiddenUntilClose aggregate behavior, private export
  shape, tests, smoke plan, migration order, rollback posture, and remaining deferred work before
  any runtime implementation. Persisted partial drafts/resume, emoji/icon support,
  dashboard/reporting, richer exports, role-restricted voting, governor-linked voting, saved
  templates, and public voter-level/detail export posting remain separate later slices unless
  explicitly approved.

Player Self-Service Command Centre status:

- Phase 1 audit/design is complete and archived.
- Phase 2 `/me` Command Shell and Navigation Foundation is delivered in mirror PR #164 and
  production PR #472 and smoke tested successfully.
- Phase 3 Modern Account Centre is delivered in mirror PR #165, smoke tested successfully by the
  operator on 2026-06-22.
- Phase 4 Modern Reminder Centre is delivered in mirror PR #166 and production PR #474, smoke
  tested successfully by the operator.
- Phase 5 Visual Dashboard Card and Preferences Hub is delivered in production PR #475 and smoke
  tested successfully on desktop, mobile, and iPad.
- Phase 6 Guided Management Cards and Workflow Simplification is delivered in mirror PR #168 and
  smoke tested successfully by the operator on 2026-06-24.
- Phase 7 Unified Reminder Centre and Dashboard Card Alignment is delivered in production PR #477
  and smoke tested successfully by the operator on 2026-06-25.
- Phase 8 Exports Launchpad is delivered in production PR #478 and smoke tested successfully by
  the operator on 2026-06-25.
- Phase 9 Quick Launch Expansion and Legacy Export Rollout is delivered in production PR #479 and
  smoke tested successfully by the operator on 2026-06-25.
- Phase 10 Inventory Summary Card is delivered in production PR #480 and smoke tested
  successfully by the operator on 2026-06-26.
- Phase 11A Shared Visual-Card Renderer Consolidation is delivered in mirror PR #173 and
  production PR #481 and smoke tested successfully by the operator on 2026-06-26.
- Phase 11B KVK Renderer Migration is delivered in production PR #482, smoke tested successfully
  by the operator on 2026-06-26, and migrated the KVK renderer family away from the old PreKvK
  helper path. KVK stats, targets, rankings, history, and special-character governor names were
  smoke tested successfully.
- Phase 11C Inventory Renderer Migration is delivered in production PR #483, smoke tested
  successfully by the operator on 2026-06-26, and migrates
  `inventory/report_image_renderer.py` text primitives to `core.visual_text` while preserving
  Inventory report output contracts. Phase 11 is complete.
- Phase 11 records are archived under `archive/`.
- Phase 12 Preferences Hub Expansion Slice 1 is delivered in mirror PR #176 and smoke tested
  successfully by the operator on 2026-06-26. It keeps `/me preferences` focused on the existing
  service-backed Inventory Preferences controls for report visibility and Inventory VIP.
- Phase 12B Discord User Preference Profile Store is delivered in mirror PR #177, SQL PR #20,
  and production PR #485, and smoke tested successfully by the operator on 2026-06-27. It adds
  SQL-backed Discord-user-level timezone, location country, and preferred language preferences,
  guided dropdown controls, and in-place replacement of the private Manage Profile child window.
- Phase 12 and Phase 12B records are archived under `archive/`.
- Phase 13 Legacy Redirect Planning is delivered in production PR #486 and smoke tested
  successfully by the operator on 2026-06-27. Approved legacy account, reminder, preference, and
  export paths now return private guidance to the matching `/me` centre; no command registrations
  were removed.
- The original Player Self-Service Command Centre programme is complete and archived under
  `archive/`.
- Active Player Self-Service v2 files:
  - `Player Self-Service Command Centre v2 - Programme Pack.md`
  - `Codex Task Pack - Player Self-Service Command Centre v2 Phase 1 Stats Profile Inventory Audit and Design.md`
  - `Codex Chat Starter - Player Self-Service Command Centre v2 Phase 1 Stats Profile Inventory Audit and Design.md`
- Completed Phase 1 through Phase 13 execution records are archived under `archive/`.

KVK Player Experience Redesign Phase 7 redirect/deprecation rollout is complete and awaiting PR
merge/promotion. Phase 1 audit/design, Phase 2A
Admin Collision Resolution, Phase 2B Player `/kvk` Scaffold, Phase 3 Modern `/kvk stats` Visual
Card, Phase 3B Stats Card Polish and Secondary Cards, Phase 3C Overall Rank and Card Polish,
Phase 4A Modern `/kvk targets`, the full Phase 4B modern `/kvk history` rollout, and Phase 5A
through Phase 5H unified `/kvk rankings` delivery, and Phase 6 admin command hardening are
complete.
Phase 2A moved admin/operator commands from `/kvk ...` to `/kvk_admin ...` in PR 140. Phase 2B
added the player `/kvk stats`, `/kvk targets`, `/kvk history`, and `/kvk rankings` scaffold in PR
141, then was promoted to production. Phase 3, Phase 3B, and Phase 3C delivered the modern
`/kvk stats` image-card rollout, mode-specific card backgrounds, secondary More Stats and History
cards, SQL-backed KVK overall rank context, and production promotion in PRs 142, 143, and 144.
Phase 4A delivered the modern `/kvk targets` card, target service/DAL/payload boundary, fallback
handling, and production promotion in PR 145. Phase 4Bi/4Bii/4Biii delivered the modern
`/kvk history` card journey: Last 3 History, Summary, Trends, CSV export controls, `/kvk stats`
History-button removal, and the retained legacy `/mykvkhistory` graph/table/CSV path. Phase 4Biv
removed the stale command-level selector option, preserved explicit governor lookup, polished CSV
export data with healed, KillPoints, PreKVK, Honor, and derived `TankingScorePct`, and passed
production smoke testing. Phase 5A delivered the `/kvk rankings type:records` KD98 Hall of Fame
Top 10 single-KVK records foundation, shared rankings payload/DAL/service/rendering pieces,
Top 10/25/50 primary control policy, command reference updates, and review hardening in mirror
PR 152 and production PR 461. Phase 5A was smoke tested successfully and pushed to production.
Phase 5B delivered the shared `/kvk rankings` current-browser foundation for KVK, Honor, and
PreKvK in mirror PR 153 and production PR 462, including mode/metric selectors, Top 10/25/50
controls, no primary Top 100, PreKvK unified embed output under `/kvk rankings`, preservation of
the image-based legacy `/prekvk report`, Honor mode guard hardening, and production smoke-tested
table layout polish.
Phase 5C delivered the current KVK Top 10 visual ranking card in mirror PR 154 and production PR
463, including Kills default, KVK card metrics for Kills, % Kill Target, Deads, DKP, Acclaim, and
Tanking Score, embed fallback, Top 25/50 compact browser preservation, Top 100 exclusion, legacy
command preservation, image-based legacy `/prekvk report` preservation, production smoke testing,
and visual polish.
Phase 5D delivered the Hall of Fame records Top 10 visual cards in mirror PR 155 and production PR
464, including all existing records metrics, single-KVK record wording, metric-specific qualifying
record counts, records Top 10-only controls, embed fallback, repeated-governor preservation,
missing historical metric exclusion, production smoke testing, and visual polish.
Phase 5E delivered Honor and PreKvK Top 10 visual cards in mirror PR 156 and production PR 465,
preserving current KVK cards, Hall of Fame cards, Top 25/50 compact browser output, records Top
10-only controls, Honor channel gating, legacy commands, and image-based legacy `/prekvk report`.
Phase 5F-1 delivered private My Rank / Find Me in mirror PR 158 and production PR 466 for current
KVK, Honor, and PreKvK rankings, with single-account, multi-account, not-ranked, no-account, and
missing-data paths smoke tested successfully in production.
Phase 5F-2 delivered private Full List CSV export in mirror PR 159 and production PR 467 for
current KVK, Honor, and PreKvK rankings, with clean leaderboard-only CSV columns, formula-leading
cell escaping, private error handling, no primary Top 100 reintroduction, restored KVK `Kill
Points` and `Healed` metric selection, and successful production smoke testing.
Phase 5G delivered rankings wrap-up polish for Honor Top 25/50 compact values, PreKvK Top 25/50
compact alignment, near-billion value unit preservation, display-width-aware rows for
wide/special-character governor names, and current KVK Top 10 podium centering, while preserving
My Rank, Full List CSV, Top 10 cards, Top 25/50 controls, Top 100 exclusion, records Top 10-only
behavior, Honor gating, legacy ranking commands, and image-based legacy `/prekvk report`.
Phase 5H delivered ranking-card render/load performance optimisation for current KVK, Honor,
PreKvK, and Hall of Fame records Top 10 visual cards. Smoke testing confirmed the improvement was
solid and noticeable across all visual cards. No active Phase 5 delivery deferred optimisations
remain. The retained legacy-ranking consolidation/deprecation item is future Phase 7 rollout work,
not a Phase 5 closure blocker.
Phase 6 delivered `/kvk_admin` operator hardening in mirror PR 162 and production PR 470,
preserving the existing seven subcommands, permissions, channel restrictions, command
registration, service/DAL boundaries, SQL/import/recompute/export semantics, stats cache
behaviour, and Google Sheets contracts. Manual smoke testing completed successfully, and no active
Phase 6 admin/operator deferred optimisations remain. The retained legacy-ranking
consolidation/deprecation item has now been promoted into the Phase 7 task pack.
Phase 7 delivered tested deprecated redirects for `/mykvkstats`, `/mykvktargets`,
`/mykvkhistory`, `/kvk_rankings`, `/honor_rankings`, and `/prekvk report`, plus channel-limit
consistency for the canonical `/kvk` commands. Final removal of the deprecated command paths is
tracked in `docs/reference/deferred_optimisations.md` after the agreed no-feedback window.

Completed KVK Player Experience Redesign Phase 1 through Phase 7 execution records are archived
under `archive/`. The programme pack remains active until the Phase 7 PRs are merged and the
later final-removal cleanup is explicitly approved.
The Phase 4B task pack remains as the history delivery record in the archive:

`archive/Codex Task Pack - KVK Player Experience Redesign Phase 4B History Audit and Optioneering.md`

Latest completed starter:

`archive/Codex Chat Starter - KVK Player Experience Redesign Phase 5H Ranking Card Performance Optimisation.md`

Next active work:

Import Pipeline Deferred Optimisation Task C Slice 12 UPDATE_ALL2 Wrapper Audit Outputs is the next
prepared import pipeline slice. It starts with audit/scope and SQL implementation-boundary
confirmation for a non-invasive wrapper or audit-output layer around `dbo.UPDATE_ALL2`, so fallback
SQL rebuild work can gain durable phase-level timing/status evidence before any later procedure
decomposition. Fallback, player-location, Honor, PreKvK, weekly activity, MGE, inventory, KVK_ALL,
and Rally Forts durable audit adoption is complete, and Slice 11 has normalized generic
`ImportAuditPhase` timestamps. Route UX changes, queue embed changes, `dbo.IMPORT_STAGING_PROC`
decomposition, `dbo.UPDATE_ALL2` decomposition, residual `stats_module.py` cleanup, legacy PreKvK
SQL cleanup, weekly cumulative view cleanup, and inventory view-orchestration extraction remain
separate later slices unless explicitly approved.

Player Self-Service Command Centre v2 Phase 1 Stats, Profile, and Inventory Audit and Design is
the next prepared player self-service slice. It starts with audit/scope only for `/my_stats`,
`/stats player`, `/player_profile`, `/myinventory`, and the product fit of `/mykvkcrystaltech`.
Final removal of temporary deprecated command paths remains captured as deferred cleanup for
execution only after player communication, no-feedback monitoring, production usage review, and
operator approval.

Discord Voting Post Framework Phase 8 Survey Free Text and Add Details is the next prepared voting
slice. It starts with audit/scope only and should decide the safest way to add free-text survey
questions and optional choice-question detail notes while keeping all Phase 1 through Phase 7
behaviour unchanged.
