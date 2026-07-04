# Deferred Optimisations

Active deferred optimisation items are staged here before they are grouped, scored, or promoted
to GitHub issues/task packs.

Resolved historical notes moved to `archive/deferred_optimisations_resolved.md`.

### Deferred Optimisation
- Area: `voting/`, future survey response UX, SQL repo survey response tables
- Type: architecture
- Description: Phase 7 delivered choice-only surveys without persisted partial player response drafts. This keeps privacy and restart behavior simple, but longer surveys may eventually need SQL-backed draft responses, resume after timeout/restart, expiry/cleanup rules, and clearer abandoned-draft retention. Phase 9A delivered optional-question completion semantics without adding persisted drafts.
- Suggested Fix: Keep draft/resume as a separate later slice after advanced question-type work is stable. Add explicit draft status, partial answer storage, cleanup/expiry policy, resume UX, optional-question interaction rules using the delivered Phase 9A semantics, and tests for restart, timeout, close, stale draft, and export exclusion behavior.
- Impact: medium
- Risk: high
- Dependencies: Phase 7 choice-only surveys delivered and smoke tested on 2026-07-03; Phase 8 text/details delivered and smoke tested on 2026-07-04; Phase 9A optional-question semantics delivered and smoke tested on 2026-07-04; privacy approval for storing unsubmitted answers; SQL repo validation; restart and cleanup tests.

### Deferred Optimisation
- Area: `voting/`, future survey rating and ranking question types, SQL repo survey answer tables
- Type: architecture
- Description: Phase 9 audit designed rating and ranking question directions and Phase 9A delivered the optional-question foundation. Rating still needs a dedicated scalar answer contract, aggregate average/distribution behavior, and response-detail columns. Ranking still needs a dedicated ranked-option answer contract, duplicate-rank prevention, clearer Discord entry/edit UX, and conservative aggregate semantics.
- Suggested Fix: Use `docs/task_packs/Codex Task Pack - Discord Voting Post Framework Phase 9B Rating Survey Questions.md` for the next approval packet. Implement rating questions first with a fixed 1-5 scale and `dbo.SurveyRatingAnswers`, then prepare Phase 9C ranking questions using existing `SurveyQuestionOptions` plus `dbo.SurveyRankingAnswers` with uniqueness constraints for rank and option per response/question. Keep public output aggregate-only and private response-detail exports closed-only/admin-leadership-only.
- Impact: high
- Risk: high
- Dependencies: Phase 9A optional-question semantics delivered and smoke tested on 2026-07-04; SQL repo migration approval; export shape approval; focused service/DAL/view/export tests; Discord smoke testing for prefill/update/close/restart behavior.

### Deferred Optimisation
- Area: `voting/`, `/vote_admin`, voting policy and identity future scope
- Type: architecture
- Description: Role-restricted voting, governor-linked voting/reporting, saved vote/survey templates, public voter-level/detail export posting, and `/vote_admin` command reshaping remain outside Phase 9. They are product-policy and command-surface changes, not prerequisites for optional/rating/ranking survey answers, and each can change privacy, permissions, exports, or command governance.
- Suggested Fix: Keep these as separate approval-gated policy/design task packs. Each future pack should validate command-surface fit, permission/privacy model, SQL identity/template storage, export/reporting implications, public posting rules, tests, smoke plan, and promotion posture before implementation.
- Impact: medium
- Risk: high
- Dependencies: Explicit operator approval; canonical command reference updates if command paths change; SQL repo validation for identity/template storage; Codex Security review before runtime PR handoff.

### Deferred Optimisation
- Area: `voting/export_service.py`, future survey export services, SQL repo survey reporting views/procedures
- Type: architecture
- Description: Phase 7 delivered first-slice survey summary/detail CSV exports only for one closed survey at a time. Phase 8 added approved text/detail response-detail columns and aggregate text-question rows without broadening into richer reporting. Richer survey export/reporting work remains out of scope, including cross-survey exports, workbook-style exports, longitudinal reporting, and private reporting views/procedures.
- Suggested Fix: After Phase 9B/9C advanced question-type shape is settled, scope a Survey Export v2 and reporting-readiness task. Validate consumer needs, define SQL views/procedures or service-owned queries, preserve private delivery by default, and add output-shape regression tests before changing export/report formats.
- Impact: medium
- Risk: medium
- Dependencies: Phase 7 survey data model delivered; Phase 8 text/detail export behavior delivered and smoke tested; Phase 9A optional export behavior delivered and smoke tested; Phase 9B/9C advanced question-type export decisions; reporting consumer requirements; SQL repo validation; no public reporting without separate approval.

### Deferred Optimisation
- Area: `voting/discord_presentation.py`, `voting/render_service.py`, `ui/views/vote_post_view.py`, SQL repo `dbo.VotePostOptions`
- Type: consistency
- Description: Per-option emoji/icon support is approved for future scope because it makes public votes and surveys more readable and engaging. Current options have labels and nullable `ButtonStyle`, but no emoji/icon metadata. Adding emoji has Discord button UX, CSV/export, and generated-card font/glyph implications. This remains a later polish slice and should not be bundled into Phase 9 advanced question types unless the operator explicitly reorders the roadmap.
- Suggested Fix: Prepare a focused polish slice that adds approved option emoji/icon metadata, validates Unicode or custom emoji input, uses Discord button emoji support where practical, updates card rendering with glyph fallback checks, and preserves existing label-length/export behavior.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5 hidden-until-close, Phase 6 MultiSelect, and Phase 7 choice-only surveys are delivered; renderer visual QA with representative emoji/custom emoji cases; operator approval for whether emoji applies to one-choice only, MultiSelect, survey options, or all option-bearing voting surfaces.

### Deferred Optimisation
- Area: `voting/`, `/vote_admin status`, SQL repo vote reporting views/procedures
- Type: architecture
- Description: Dashboard/reporting readiness is approved for future scope. Current vote tables can support basic closed-vote summaries, Phase 6 added stable `OneChoice`/`MultiSelect` mode dimensions, Phase 7 added separate survey question/answer dimensions, and Phase 8 added text/detail answer dimensions, but there are no dedicated reporting views/procedures for combined vote/survey reporting.
- Suggested Fix: Scope a private reporting-readiness slice after Phase 9B/9C advanced question-type shape is settled. Define SQL views or procedures for vote/survey summaries, participation, outcomes/top selections, export/audit history, result visibility, mode dimensions, text/detail exclusion or redaction policy, optional/rating/ranking dimensions, and any approved long-form export/reporting variants. Keep public website work out of scope unless separately approved.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5 result visibility, Phase 6 vote-mode/cardinality SQL, Phase 7 survey SQL, Phase 8 text/details, and Phase 9A optional questions are delivered; Phase 9B/9C rating/ranking decisions; operator approval for private versus public reporting consumers.

### Deferred Optimisation
- Area: `ui/views/inventory_views.py`, `inventory/inventory_service.py`, inventory import lifecycle callbacks
- Type: architecture
- Description: Inventory import lifecycle coordination remains intentionally view-heavy. `ui/views/inventory_views.py` routes upload-first messages, command-session continuations, multi-governor selection, review interactions, correction modals, additional-material continuation, approval, rejection, cancellation, timeout, admin-debug posting, and original-upload cleanup. Task C Slice 8 adopted generic audit without redesigning this workflow and smoke testing confirmed the behavior-preserving audit contract.
- Suggested Fix: In a later inventory-only orchestration slice, audit inventory import view callbacks for service-extraction opportunities. Move only stable lifecycle transitions, admin-debug/reference updates, material-continuation coordination, and original-upload cleanup orchestration behind service helpers with focused interaction tests, preserving `/inventory import`, upload-first, correction, materials, admin debug, audit metadata, and user-facing behavior.
- Impact: medium
- Risk: medium
- Dependencies: Task C Slice 8 inventory generic audit adoption delivered and smoke tested on 2026-06-30; existing inventory route/view/service/DAL tests; no command UX or SQL schema changes without a separate approved slice.

### Deferred Optimisation
- Area: SQL repo `dbo.vAllianceActivity_WeeklyCumulative`
- Type: cleanup
- Description: Weekly activity SQL validation during Task C Slice 6 found that `dbo.vAllianceActivity_WeeklyCumulative` appears to reference columns not exposed by `dbo.vAllianceActivity_WeeklyDelta`. Current bot searches did not find active usage, so fixing or dropping the view is outside the weekly activity audit-adoption slice.
- Suggested Fix: Run a later SQL cleanup audit to confirm whether any reports, manual queries, or downstream exports still use `dbo.vAllianceActivity_WeeklyCumulative`. If unused, retire or correct the view through the SQL repo migration process with validation and rollback notes.
- Impact: low
- Risk: medium
- Dependencies: SQL repo validation in `C:\K98-bot-SQL-Server`; operator approval before changing reporting view semantics or retiring the view.

### Deferred Optimisation
- Area: SQL repo `dbo.UPDATE_ALL2`, `update_all2_log_manager.py`, `stats/dal/fallback_import_dal.py`, `stats_module.py`
- Type: architecture
- Description: `dbo.UPDATE_ALL2` remains a broad downstream rebuild procedure, and Python currently observes completion through `SP_TaskStatus` counter/status polling. There is not yet a durable per-phase audit output that explains which downstream phase failed or dominated runtime.
- Suggested Fix: After Task C Slice 2's generic batch audit foundation is deployed, add a wrapper or non-invasive audit output around `dbo.UPDATE_ALL2` that records start/end, status, duration, and phase-level markers without changing output tables or player-visible behavior. Use the resulting baseline before deciding whether to split the procedure.
- Impact: high
- Risk: medium
- Dependencies: Task C Slice 2 generic import batch audit foundation; Task C Slice 11 timestamp normalization delivered and smoke tested; SQL validation in `C:\K98-bot-SQL-Server`; no wholesale `UPDATE_ALL2` replacement in this slice. Promoted into the prepared Task C Slice 12 task pack for audit/scope and SQL implementation-boundary confirmation.

### Deferred Optimisation
- Area: SQL repo `dbo.IMPORT_STAGING_PROC`, raw fallback staging, `dbo.IMPORT_STAGING_CSV`, `dbo.IMPORT_STAGING`
- Type: refactor
- Description: `dbo.IMPORT_STAGING_PROC` owns multiple responsibilities around fallback staging, raw text conversion, typed conversion, metadata-sensitive partial fallback behavior, and final staging/output handoff. Task B intentionally preserved procedure shape to reduce risk while fixing Unicode preservation.
- Suggested Fix: After durable audit hooks are deployed and fallback audit evidence is stable, split `dbo.IMPORT_STAGING_PROC` responsibilities into smaller phase procedures or clearly bounded internal sections with audit markers, preserving existing input/output contracts and rollback scripts. Keep data-contract changes out of the split unless separately approved.
- Impact: high
- Risk: high
- Dependencies: Task B raw staging path deployed; Task C Slice 2 generic batch audit and SQL validation available; production smoke baseline for full and partial fallback imports.

### Deferred Optimisation
- Area: SQL repo `dbo.UPDATE_ALL2` and downstream stats/dashboard rebuild procedures
- Type: performance
- Description: `dbo.UPDATE_ALL2` may eventually need decomposition, but there is not yet durable evidence showing which phase fails most often or dominates runtime. Decomposing it before instrumentation risks optimizing or changing the wrong boundary.
- Suggested Fix: Use audit data from the `UPDATE_ALL2` wrapper/audit-output slice to identify phase boundaries and runtime/failure hotspots. Only then prepare a SQL-specific decomposition task pack that splits the procedure into phase procedures with compatibility wrappers, migration order, rollback scripts, and before/after runtime validation.
- Impact: high
- Risk: high
- Dependencies: `UPDATE_ALL2` wrapper/audit outputs deployed long enough to gather baseline evidence; SQL owner approval for phase procedure design and migration plan.

### Deferred Optimisation
- Area: `stats_module.py`, import service modules, import DAL modules
- Type: refactor
- Description: Task C Slice 1 extracted fallback import file orchestration and DAL helpers, but `stats_module.py` still remains the compatibility entry point for the current worker/route/command flow and still owns mixed step sequencing around Excel processing, secondary archive, SQL execution, and result aggregation.
- Suggested Fix: After durable audit and SQL instrumentation are stable, continue extracting residual import orchestration from `stats_module.py` into import-specific services while keeping the module as a thin compatibility shim until route or command callers are explicitly migrated. Preserve all current caller behavior and tests during each slice.
- Impact: medium
- Risk: medium
- Dependencies: Task C Slice 1 wrappers complete; durable audit foundation and route/worker adoption sequence agreed.

### Deferred Optimisation
- Area: `commands/stats_cmds.py`, `commands/telemetry_cmds.py`, `commands/prekvk_cmds.py`, `scripts/validate_command_registration.py`, `docs/reference/canonical_command_reference.md`
- Type: cleanup
- Description: Phase 7 converted `/mykvkstats`, `/mykvktargets`, `/mykvkhistory`, `/kvk_rankings`, `/honor_rankings`, and `/prekvk report` into tested deprecated redirect/help responses. The old command paths remain registered temporarily so players receive migration guidance, which means the command baseline, redirect helpers/tests, and compatibility docs still carry legacy surface area after the first deprecation rollout.
- Suggested Fix: After the agreed no-feedback window and operator approval, remove the deprecated command registrations and redirect-only tests, update `scripts/validate_command_registration.py::APPROVED_TOP_LEVEL_COMMANDS`, update `docs/reference/canonical_command_reference.md` and player/operator docs, and run command inventory, registration, focused KVK command tests, pre-commit, and full pytest before merge.
- Impact: medium
- Risk: medium
- Dependencies: Phase 7 redirect PR merged and deployed; player briefing posted; no actionable player feedback during the monitoring window; operator approval for final removal.

### Deferred Optimisation
- Area: `tests/test_ark_preference_service.py`, `tests/test_ark_bans_enforcement.py`, `tests/test_lock_timeout.py`, `tests/test_calendar_service.py`, `tests/test_calendar_pipeline.py`, remaining slow full-suite pytest paths
- Type: performance
- Description: After PR 107 resolved the original slow pytest offenders, the new duration audit `C:\Users\cwatt\Downloads\.codex_pytest_audit-new.log` shows the remaining full-suite outliers are concentrated in Ark preference/ban negative paths, lock-timeout coverage, calendar failure-path retries, live queue persistence, maintenance subprocess timeout/success coverage, and one inventory vision import case. The slowest current timings are `tests/test_ark_preference_service.py::test_set_preference_rejects_unknown_governor` at 7.33s, `tests/test_ark_bans_enforcement.py::test_admin_add_allows_when_override_on` at 5.23s, `tests/test_lock_timeout.py::test_remove_view_tracker_entry_returns_false_when_locked` at 5.06s, `tests/test_lock_timeout.py::test_save_view_tracker_raises_on_lock` at 5.06s, `tests/test_calendar_service.py::test_refresh_full_stops_on_sync_failure` at 3.02s, and `tests/test_calendar_pipeline.py::test_pipeline_stops_on_sync_failure` at 3.01s.
- Suggested Fix: Start a fresh audit from `.codex_pytest_audit-new.log` and classify each remaining slow path as intentional timeout coverage, missing test boundary, live dependency leakage, retry/backoff, or genuine defect. Preserve lock-timeout and subprocess timeout coverage, but replace real multi-second waits with patched timeout constants, fake clocks, controlled retry policies, or explicit service/DAL boundary fakes where safe. Keep the scope separate from PR 107 and validate with `pytest -vv tests --durations=30 --durations-min=1.0`, focused subsystem tests, `scripts/analyse_pytest_log_noise.py`, and `python -m pytest -q tests`.
- Impact: medium
- Risk: medium
- Dependencies: Use the post-PR-107 audit baseline (`1450 passed, 2 skipped, 19 warnings in 54.86s`); preserve genuine timeout, subprocess, lock, negative-path, and log-noise coverage.

### Deferred Optimisation
- Area: `commands/ark_cmds.py`, `ark/registration_flow.py`, `ark/confirmation_flow.py`, `ark/reminders.py`, `ark/dal/ark_dal.py`
- Type: refactor
- Description: The Ark create, amend, and cancel command handlers still contain substantial workflow orchestration, including config parsing, match validation, registration embed edits, JSON state lookup, reminder rescheduling/cancellation, audit logging, and cancel-DM dispatch coordination. Phase 4 intentionally preserved these bodies while moving command paths under `/ark` to avoid mixing command-surface migration with service extraction.
- Suggested Fix: Scope a follow-up Ark command orchestration extraction that moves create/amend/cancel workflow coordination into Ark services while leaving command handlers responsible for permissions, deferral, input collection, and response rendering. Preserve existing DAL contracts, restart-sensitive message/reminder state behavior, and modal/view callback behavior with focused regression tests.
- Impact: medium
- Risk: medium
- Dependencies: Phase 4 Ark command grouping is complete and smoke tested; validate service boundaries against existing Ark registration, confirmation, reminder, cancel, and audit tests.

### Deferred Optimisation
- Area: `commands/registry_cmds.py`, `commands/telemetry_cmds.py`, `commands/stats_cmds.py`, `commands/inventory_cmds.py`, `commands/subscriptions_cmds.py`, `commands/calendar_cmds.py`, player self-service command docs/tests
- Type: cleanup
- Description: Player Self-Service Command Centre Phase 13 converted the explicitly approved legacy self-service entry points to lightweight private redirects: `/register_governor`, `/modify_registration`, `/my_registrations`, and `/mygovernorid` to `/me accounts`; `/subscribe`, `/modify_subscription`, `/unsubscribe`, and `/calendar_reminder_config` to `/me reminders`; `/inventory_preferences` to `/me preferences`; and `/my_stats_export` plus `/export_inventory` to `/me exports`. The old command registrations remain temporarily so players receive guidance. `/myinventory`, `/my_stats`, `/mykvkcrystaltech`, `/player_profile`, and `/stats player` remain live.
- Suggested Fix: After player communication and the agreed no-feedback monitoring window, review production `/ops usage_detail` or `dbo.BotCommandUsage` evidence for the redirected paths. Remove only the operator-approved command registrations and redirect-only tests, update `scripts/validate_command_registration.py::APPROVED_TOP_LEVEL_COMMANDS`, canonical docs, briefing docs, and focused command tests, and preserve the v2-scoped stats/profile/inventory paths unless separately approved.
- Impact: medium
- Risk: medium
- Dependencies: Phase 12B delivered and smoke tested successfully on 2026-06-27; Phase 13 audit/scope drafted using supplied SQL extract and dated JSONL evidence; Phase 13 redirect slice approved by the operator, delivered in production PR #486, and smoke tested successfully on 2026-06-27; requires player communication, no-feedback monitoring, production usage review, and operator approval before final command-registration removal.

### Deferred Optimisation
- Area: `commands/stats_cmds.py`, `commands/inventory_cmds.py`, `/my_stats_export`, `/export_inventory`, player self-service docs/tests
- Type: cleanup
- Description: Phase 13 explicitly approved lightweight redirects for `/my_stats_export` and `/export_inventory` to `/me exports`. The redirect slice intentionally preserves the existing stats and inventory export services, schemas, formats, option-window behavior, and file delivery through `/me exports`; only the old flat command entry points stop producing files directly.
- Suggested Fix: After the export redirect no-feedback window, review production command usage and player feedback. Remove the flat export command registrations only with explicit operator approval, keep export schema/format redesign out of this cleanup, and update command registration baselines, canonical command reference, player briefing, and focused export redirect tests for the approved removal slice.
- Impact: medium
- Risk: medium
- Dependencies: Phase 9 `/me exports` option windows smoke tested; Phase 13 audit/scope drafted; operator approved export entry-point redirects; production PR #486 delivered and smoke tested the redirects successfully on 2026-06-27; player communication and no-feedback monitoring before final removal.

### Deferred Optimisation
- Area: `commands/stats_cmds.py`, `commands/inventory_cmds.py`, `commands/telemetry_cmds.py`, `/my_stats`, `/stats player`, `/player_profile`, `/myinventory`, player self-service v2 programme docs/tests
- Type: architecture
- Description: The full player self-service modernisation still has larger personal stats, leadership/profile, and detailed inventory report surfaces outside Phase 13. `/my_stats`, `/stats player`, and `/player_profile` are too large for the first programme pack and need a Player Self-Service v2 scope; `/myinventory` remains valuable but needs product/design alignment with the new command group model; `/mykvkcrystaltech` is a unique channel-gated personal workflow and is not included in the immediate v2 redirect cleanup.
- Suggested Fix: Use `docs/task_packs/Player Self-Service Command Centre v2 - Programme Pack.md` and `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 1 Stats Profile Inventory Audit and Design.md` to run an audit-only v2 slice. The audit should classify stats report, leadership/profile lookup, and detailed inventory report journeys, define whether they stay flat/channel-gated or gain `/me`/grouped entry points, preserve public/private channel rules, and avoid folding CrystalTech into the same implementation slice until its product fit is decided.
- Impact: high
- Risk: medium
- Dependencies: Original Player Self-Service Command Centre programme completed in production PR #486; v2 programme pack and Phase 1 audit starter prepared; operator approval to start the v2 audit; production usage evidence for `/my_stats`, `/stats player`, `/player_profile`, `/myinventory`, and `/mykvkcrystaltech` before any command-surface changes.

### Deferred Optimisation
- Area: `services/stats_export_service.py`, `stats/dal/stats_export_dal.py`, `stats_exporter.py`, `stats_exporter_csv.py`, `inventory/export_service.py`, `inventory/dal/`, SQL repo export views/tables, export docs/tests
- Type: architecture
- Description: Phase 8 and Phase 9 intentionally reuse existing stats and inventory export schemas and file formats so `/me exports` can safely launch current service-backed private exports. A fuller export schema and format redesign would need to decide whether exports should stay raw, add curated summary sheets, change CSV/XLSX headers, add new formats, split personal versus leadership exports, or introduce new SQL views/contracts.
- Suggested Fix: Treat export schema and format redesign as a separate export-output programme, not as another phase of the Player Self-Service Command Centre. Start with a dedicated audit of current stats, inventory, KVK history, rankings, and registry export consumers; validate SQL contracts in `C:\K98-bot-SQL-Server`; define backwards-compatibility and migration expectations for file consumers; then implement schema or format changes in controlled slices with export-file regression tests.
- Impact: high
- Risk: high
- Dependencies: Phase 8 confirms launchpad requirements without changing file contracts; operator approval for a dedicated export-output programme; SQL validation and downstream consumer review before any schema/format changes.

### Deferred Optimisation
- Area: `commands/calendar_cmds.py`, `commands/events_cmds.py`, `ui/views/calendar.py`, `ui/views/events_views.py`, public calendar/KVK calendar docs/tests
- Type: architecture
- Description: Generic public calendar and KVK calendar commands have inconsistent naming, visibility, scope, and interaction behavior. `/calendar` is an ephemeral calendar overview; `/calendar_next_event` is ephemeral and shows one next calendar event; `/next_kvk_fight` is public and shows one fight with controls for the next three fights; `/next_kvk_event` is public and shows one event with controls for the next five events. There is also no clearly named `/kvk_calendar` or equivalent KVK calendar overview, so grouping these commands now would tidy paths without resolving the user-facing model.
- Suggested Fix: Scope a dedicated public calendar/KVK calendar UX redesign outside the command-count programme. Review whether the end state should use grouped paths such as `/calendar overview`, `/calendar kvk_overview`, `/calendar next_event`, `/calendar next_kvk_fight`, and `/calendar next_kvk_event`; decide whether all public information commands should post publicly; define the missing KVK calendar overview behavior; align button counts and visibility; update docs/smoke references; and add focused command/view tests before implementation.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5A admin/leadership/operator grouping is complete; requires operator approval for public visibility changes and a fresh task pack. Phase 5A moved calendar admin/operator commands under existing `/ops calendar_*` paths so the flat public `/calendar` command remains untouched until this redesign.

### Deferred Optimisation
- Area: SQL repo legacy PreKvK phase object retirement
- Type: cleanup
- Description: After Phase 2B compatibility wrappers remove active scan-window logic, `dbo.PreKvk_Phases` and any compatibility-only phase objects may remain as unused legacy SQL surface.
- Suggested Fix: Run a later Option C retirement audit after at least one production cycle, re-check live SQL dependencies and manual/report usage, then prepare a SQL-repo-only drop plan with rollback scripts if no consumers remain.
- Impact: low
- Risk: medium
- Dependencies: Phase 2B compatibility wrapper deployment completed and smoke tested; live dependency checks confirm no references beyond the objects being retired; production owner approves destructive SQL cleanup.

### Deferred Optimisation
- Area: `C:\K98-bot-SQL-Server` SQL development and deployment workflow
- Type: architecture
- Description: SQL schema changes can now be developed through Git PRs, but the existing production export routine can still overwrite Git-driven SQL changes because it syncs production schema back to the repository as the main routine.
- Suggested Fix: Use `C:\Users\cwatt\Downloads\sql_deploy_route_task_pack.md` to create a PR-based SQL promotion workflow with guarded deploy scripts, migration history, a safe production schema export branch, `migrations/` conventions, and `docs/SQL_PROMOTION_GUIDE.md`.
- Impact: high
- Risk: medium
- Dependencies: DL_bot upload-routing and Phase 6 lifecycle work are complete; preserve current production schema export as a drift/safety mechanism while preventing direct overwrite of `main`.

### Deferred Optimisation
- Area: `bot_helpers.py`, `utils.py`, `core/queue_lifecycle.py`, `upload_routes/fallback_queue_route.py`, queue runtime state
- Type: architecture
- Description: Phase 6K is intentionally limited to live queue persistence hardening. A fuller queue-domain redesign remains separate, including clearer ownership for queued message/job lifecycle, worker status transitions, display state, processing state, retry/drop semantics, and the boundary between fallback upload routing, `channel_queues`, and live queue UI state.
- Suggested Fix: Scope a dedicated queue-domain redesign audit as a new deferred optimisation batch. Map queue state sources, worker lifecycle, status transitions, user-visible embed updates, failure modes, and restart behavior before proposing any code movement. Keep upload-route behavior unchanged unless a later approved task explicitly includes it.
- Impact: medium
- Risk: medium
- Dependencies: Phase 6K live queue persistence hardening and Phase 6L lifecycle closure are complete; coordinate as a separate post-Phase 6 programme.

### Deferred Optimisation
- Area: queue persistence model, SQL repo `C:\K98-bot-SQL-Server`
- Type: architecture
- Description: Live queue persistence remains file-backed through `QUEUE_CACHE_FILE` after Phase 6K hardened the file-backed model. SQL-backed queue persistence may eventually provide a stronger source of truth for queued work, in-flight state, and recovery after crashes, but it requires a separate schema and contract design rather than being folded into Phase 6.
- Suggested Fix: If the hardened file-backed queue state proves insufficient in production, scope a SQL-backed queue persistence design task. Validate table/procedure/index needs against `C:\K98-bot-SQL-Server`, define migration and rollback plans, preserve existing operator behavior, and add restart/recovery tests before any implementation.
- Impact: medium
- Risk: high
- Dependencies: Requires explicit approval, `k98-sql-validation`, SQL repo changes, and production migration planning.

### Deferred Optimisation
- Area: `event_calendar/pinned_embed.py`
- Type: refactor
- Description: Pinned calendar tracker persistence currently uses direct `Path.write_text()` JSON writes in `_save_tracker()`, unlike other restart-sensitive tracker files that use atomic JSON helpers and clearer failure boundaries.
- Suggested Fix: Move pinned calendar tracker persistence to the established atomic JSON helper pattern, preserve tracker shape and missing-message recovery behavior, and add focused tests for successful save, failed/partial write protection, missing tracker, and rehydration after restart.
- Impact: medium
- Risk: low
- Dependencies: Keep this separate from Phase 6F unless a later pinned-calendar persistence task is approved.
