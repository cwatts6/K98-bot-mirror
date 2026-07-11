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

KVK_ALL Schema Modernisation status:

- The KVK_ALL Schema Modernisation programme is complete through Phase 11 and archived. Phase 11
  Acclaim Output Contract Polish was smoke tested successfully: KVK.vw_FightingDataset exposes
  acclaim_gain, Google Sheets exports expose acclaim_gain without Highest Acclaim gain, and KVK_ALL
  imports plus export completed successfully.
- KVK_ALL records are archived under `archive/`:
  - `archive/KVK_ALL Schema Modernisation - Full Optimisation Task Pack.md`
  - `archive/KVK_ALL Schema Modernisation - Audit & Migration Planning Task Pack.md`
  - `archive/KVK_ALL Schema Modernisation - Phase 4 Metric Source Rules.md`
  - `archive/KVK_ALL Schema Modernisation - Phase 10 Metric Source Correction.md`
  - `archive/KVK_ALL Schema Modernisation - Phase 11 Initiation Statement.md`
- The Phase 4 metric source rules and Phase 10 metric source correction docs also remain mirrored
  at their active `docs/task_packs/` paths because SQL contract tests assert those references.
- Future KVK_ALL work should start from a fresh task pack rather than continuing the schema
  modernisation programme as Phase 12.

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
- Task C Slice 12 UPDATE_ALL2 Wrapper Audit Outputs is delivered in mirror PR #215, production PR
  #522, and SQL PR #41. SQL deployment and bot restart completed on 2026-07-09. Production smoke
  confirmed fallback batch 67 recorded the existing `fallback_update_all2` coarse phase plus 13
  durable `update_all2_*` subphase rows, with structured details and no
  `_update_all2_phase_results` leakage after the review-fix restart.
- Task C Slice 12 records are archived under `archive/`:
  - `archive/Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 12 UPDATE_ALL2 Wrapper Audit Outputs.md`
  - `archive/Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 12 UPDATE_ALL2 Wrapper Audit Outputs.md`
- Active Task C Slice 13 files:
  - `Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 13 UPDATE_ALL2 Phase Evidence Review and SUMMARY_PROC Scope Audit.md`
  - `Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 13 UPDATE_ALL2 Phase Evidence Review and SUMMARY_PROC Scope Audit.md`
- Task C Slice 13 is the next import architecture cleanup slice. It starts with audit/scope and
  evidence review over the new `update_all2_*` phase rows, quantifies whether
  `update_all2_summary_proc` consistently dominates runtime, identifies any coarse-to-subphase
  timing gap, validates `dbo.SUMMARY_PROC` and helper-procedure boundaries, and recommends the
  next implementation slice. `dbo.IMPORT_STAGING_PROC` decomposition, `dbo.UPDATE_ALL2`
  decomposition, `dbo.SUMMARY_PROC` tuning/decomposition, residual `stats_module.py` cleanup,
  legacy PreKvK SQL cleanup, weekly cumulative view cleanup, and inventory view-orchestration
  extraction remain separate later slices unless explicitly approved.

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
- Phase 9A Optional Survey Questions is delivered in mirror PR #201, production PR #509, and SQL
  PR #31. SQL deployment completed before bot rollout. Operator smoke testing on 2026-07-04
  confirmed optional unanswered questions submit successfully when required questions are answered,
  mixed required/optional question counts are displayed, raw text/details remain private, and
  existing survey/vote behavior remains compatible.
- Phase 9 audit and Phase 9A records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 9 Advanced Survey Question Types Audit and Design.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 9 Advanced Survey Question Types Audit and Design.md`
- Phase 9B Rating Survey Questions is delivered in mirror PR #203, production PR #510, and SQL PR
  #32. SQL deployment completed before bot runtime smoke. Operator smoke testing on 2026-07-04
  confirmed rating-question creation, disabled option/detail controls for ratings, required and
  optional rating submission, optional rating skip behavior, average-rating public display, and
  compatibility for existing choice/text/detail/optional surveys, multi-select votes, and
  one-choice votes.
- Phase 9B records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 9B Rating Survey Questions.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 9B Rating Survey Questions.md`
- Phase 9C Ranking Survey Questions is delivered in mirror PR #204, production promotion branch
  `prod/phase-9c-ranking-survey`, and SQL PR #33. SQL deployment completed before bot runtime
  smoke. Operator smoke testing on 2026-07-04 confirmed ranking survey creation, required ranking
  response flow, optional ranking skip/clear behavior, ranking update/regression behavior,
  aggregate-only public ranking cards, and compatibility for existing choice/text/detail/optional
  surveys, fixed 1-5 rating surveys, multi-select votes, and one-choice votes.
- Phase 9C records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 9C Ranking Survey Questions.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 9C Ranking Survey Questions.md`
- Phase 10 Survey Export v2 and Reporting Readiness is delivered in mirror PR #205, production PR
  #512, and SQL PR #35. SQL deployment completed before bot runtime smoke. Operator smoke testing
  on 2026-07-05 confirmed the report bundle creates a private multi-CSV bundle, opens cleanly,
  contains expected rows, and preserves regression behavior.
- Phase 10 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 10 Survey Export v2 and Reporting Readiness Audit and Design.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 10 Survey Export v2 and Reporting Readiness Audit and Design.md`
- Phase 11 Private Dashboard Reporting Runtime is delivered in mirror PR #206 and production PR
  #513. Operator smoke and regression testing on 2026-07-06 confirmed the private aggregate
  dashboard-safe reporting runtime contract and preserved regression behavior. Phase 11 delivered
  vote/survey summary contracts for admin/leadership reporting without Discord identity, per-user
  rows, raw text answers, or choice details in dashboard-safe payloads, and without adding
  dashboard UI, new commands, cross-survey/workbook exports, retention/redaction behavior changes,
  command reshaping, public detail posting, or new SQL objects.
- Phase 11 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 11 Private Dashboard Reporting Runtime Audit and Design.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 11 Private Dashboard Reporting Runtime Audit and Design.md`
- Phase 12 Survey Draft Resume is delivered in mirror PR #207, production PR #514, and SQL PR #36.
  SQL deployment completed before bot runtime smoke. Operator smoke and regression testing on
  2026-07-06 confirmed persisted survey drafts/resume for surveys only, automatic and explicit
  draft save, restart-safe resume, duplicate stale-panel protection, answer-type coverage, final
  submit validation, draft exclusion from public/private result and export surfaces, and preserved
  existing vote/submitted-survey behavior.
- Phase 12 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 12 Survey Draft Resume Audit and Design.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 12 Survey Draft Resume Audit and Design.md`
- Phase 13 Private Dashboard UI is delivered in mirror PR #208 and production PR #515. Operator
  smoke and regression testing on 2026-07-07 confirmed private aggregate dashboard pages for votes
  and surveys, Refresh, Next, Previous, Close, Open and Closed filters, admin/leadership access
  control, private delivery, and no raw details or Discord names visible.
- Phase 13 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 13 Private Dashboard UI Audit and Design.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 13 Private Dashboard UI Audit and Design.md`
- Phase 14 Rating Scale Extensions is delivered in mirror PR #209, production PR #516, and SQL PR
  #37. SQL migration `20260707_001_add_survey_rating_scales` was deployed before bot rollout.
  Operator smoke/regression testing on 2026-07-07 confirmed normal fixed 1-5 rating surveys,
  1-10 rating surveys, custom min/max scales, scale endpoint labels, named rating choices,
  save/draft/resume, `/vote_admin dashboard`, export, repost, status, and other regressions.
- Phase 14 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 14 Rating Scale Extensions Audit and Design.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 14 Rating Scale Extensions Audit and Design.md`
- Phase 15 Emoji/Icon Support and Visual Polish is delivered in mirror PR #210, production PR #517,
  and SQL PR #38. SQL deployment completed before bot rollout. Operator smoke/regression testing
  on 2026-07-07 confirmed vote and survey emoji behavior, Unicode emoji, custom Discord emoji,
  animated custom Discord emoji in Discord/status/dashboard, expected generated-card custom emoji
  text fallback, guided option-polish controls, SQL production rollout, and existing regression
  behavior.
- Phase 15 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 15 Emoji Icon Support and Visual Polish Audit and Design.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 15 Emoji Icon Support and Visual Polish Audit and Design.md`
- Phase 16 Survey Authoring Edit Controls is delivered in mirror PR #211 and production PR #518.
  Operator smoke/regression testing on 2026-07-07 confirmed pre-publish survey review, edit,
  delete, and reorder; post-publish updates; survey update locks after response submission;
  closed-survey locks; and existing regression behavior.
- Phase 16 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 16 Survey Authoring Edit Controls Audit and Design.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 16 Survey Authoring Edit Controls Audit and Design.md`
- Phase 17 Vote Admin Reshaping Audit and Design is complete and closed with no runtime command
  change. Operator decision D keeps `/vote_admin` as-is because the commands work, leadership is
  comfortable with the naming convention, and only a small operator set creates or updates
  votes/surveys. No aliases, new top-level commands, help/launch panels, command-registration
  changes, SQL/DAL changes, export/report/dashboard changes, public rendering changes, rollout, or
  operator retraining are required.
- Phase 17 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 17 Vote Admin Reshaping Audit and Design.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 17 Vote Admin Reshaping Audit and Design.md`
- Phase 18 Cross Survey Workbook Export Redesign Audit and Design is complete and closed with no
  runtime export change and no documentation-guidance change. Existing private exports and report
  bundles are well received and understood by leadership. Single-survey private workbook output
  and cross-survey private aggregate workbook/report output are not required now.
- Phase 18 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 18 Cross Survey Workbook Export Redesign Audit and Design.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 18 Cross Survey Workbook Export Redesign Audit and Design.md`
- Phase 19 Leadership Engagement Summary Reporting is complete, review-hardened, smoke/regression
  tested, and archived. It delivered the private `/vote_admin dashboard` engagement mode with
  compact `Total Polls`, `Total Users`, `Participation levels`, `Monthly Snapshots`, best/worst
  single poll, role-filtered eligibility, fixed rolling windows, one-Discord-user counting
  regardless of governor IDs, raw-answer exclusion, no public reporting, no export schema changes,
  and no SQL-native combined reporting.
- Phase 19 records are archived under `archive/`:
  - `archive/Codex Task Pack - Discord Voting Post Framework Phase 19 Leadership Engagement Summary Reporting Audit and Design.md`
  - `archive/Codex Chat Starter - Discord Voting Post Framework Phase 19 Leadership Engagement Summary Reporting Audit and Design.md`
- Discord Voting Post Framework is complete and archived through Phase 22. The programme pack
  remains as the closed record:
  - `Discord Voting Post Framework - Programme Pack.md`
- Phase 20 Per-User Engagement Export List and Graph Audit and Design is complete, smoke tested,
  and archived. It delivered the private CSV export under `/vote_admin engagement`.
- Phase 21 Private Engagement Graph Assessment Audit and Design is audit-closed as not required now
  and archived. The Phase 20 CSV export remains the data path; any future graph work needs a fresh
  concrete leadership requirement.
- Phase 22 Vote Survey Retention Redaction Policy is complete, deployed, and smoke tested. It
  delivered SQL-only
  `dbo.VoteSurveyDeletionAudit` and `dbo.usp_VoteSurveyAdminDelete` through SQL migration
  `20260709_001_add_vote_survey_admin_delete`, with dry-run/readback, closed-item enforcement,
  explicit confirmation, mandatory reason/operator identity, local audit summary capture,
  dependency-order hard deletes, break-glass production support, and no bot-side delete command,
  Discord UI, dashboard control, scheduled job, public output, or runtime code change.
  SQL PR #39 plus follow-up SQL PR #40 were merged, pushed to production, and smoke tested
  successfully on 2026-07-09. No Discord Voting Post Framework deferred optimisations remain
  active; future voting enhancements must start in a new programme pack.

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
  - `Codex Task Pack - Player Self-Service Command Centre v2 Phase 5A Direct Inventory Reports and Governor Context.md`
  - `Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5A Direct Inventory Reports and Governor Context.md`
- GovernorOS v2 Phases 1-4 are complete. Their reports/task packs/chat starters are archived under
  `archive/`. Phase 2 delivered in mirror PR #216 and production PR #523, Phase 3 delivered in
  mirror PR #217 and production PR #524, and Phase 4 delivered in mirror PR #218. Phase 4 operator
  smoke on 2026-07-11 accepted the materially wider standalone card and gated Change Governor
  dropdown. Phase 5A is the next approval-gated implementation slice; Phase 5B owns standalone
  presentation alignment for the existing Accounts, Reminders, Preferences, Inventory, and Exports
  summary pages.
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

Import Pipeline Deferred Optimisation Task C Slice 13 UPDATE_ALL2 Phase Evidence Review and
SUMMARY_PROC Scope Audit is the next prepared import pipeline slice. It starts with audit/scope
and evidence review over recent fallback `ImportAuditBatch`/`ImportAuditPhase` rows now that Slice
12 has delivered durable `update_all2_*` phase markers. The slice should quantify
`SUMMARY_PROC`/downstream timing evidence before any later SQL tuning or decomposition work.
Fallback, player-location, Honor, PreKvK, weekly activity, MGE, inventory, KVK_ALL, and Rally Forts
durable audit adoption is complete, Slice 11 normalized generic `ImportAuditPhase` timestamps, and
Slice 12 delivered UPDATE_ALL2 audit-output observability. Route UX changes, queue embed changes,
`dbo.IMPORT_STAGING_PROC` decomposition, `dbo.UPDATE_ALL2` decomposition, `dbo.SUMMARY_PROC`
tuning/decomposition, residual `stats_module.py` cleanup, legacy PreKvK SQL cleanup, weekly
cumulative view cleanup, and inventory view-orchestration extraction remain separate later slices
unless explicitly approved.

Player Self-Service Command Centre v2 Phase 5A Direct Inventory Reports and Governor Context is the
next prepared player self-service slice. It proposes private `/me resources`, `/me materials`, and
`/me speedups`, matching dashboard actions, no/one/multiple governor resolution, and the accepted
paged Change Governor dropdown while reusing the existing standalone inventory renderer and
service/DAL contracts. Phase 5B page-presentation alignment, export integration, history, inspect,
migration decisions, renderer redesign, SQL changes, and legacy behavior changes remain outside
Phase 5A.
Final removal of temporary deprecated command paths remains captured as deferred cleanup for
execution only after player communication, no-feedback monitoring, production usage review, and
operator approval.

Discord Voting Post Framework is closed after Phase 22. Future voting enhancements should start in
a new programme pack rather than continuing this programme as Phase 23.
