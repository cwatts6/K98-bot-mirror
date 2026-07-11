# Deferred Optimisations

Active deferred optimisation items are staged here before they are grouped, scored, or promoted
to GitHub issues/task packs.

Resolved historical notes moved to `archive/deferred_optimisations_resolved.md`.

### Deferred Optimisation
- Area: `inventory/report_image_renderer.py`, Inventory report assets, Discord desktop/mobile report presentation
- Type: consistency
- Description: GovernorOS v2 Phase 5A deliberately retains the established standalone 1400x980 Resources, Materials, and Speedups renderer while the selected-governor dashboard advances to a polished 1180x760 layout. Operator review may later find that the older Inventory cards no longer meet the GovernorOS visual-quality bar, but redesigning them during Phase 5A would mix entry-point/security integration with a material report-renderer change.
- Suggested Fix: After Phase 5A operator smoke, review representative Resources, Materials, and Speedups cards at original, Discord desktop, and mobile scales against the accepted governor dashboard. If a quality gap is confirmed, prepare a separate renderer task pack covering visual hierarchy, assets/provenance, typography, chart readability, dimensions, fallback compatibility, filenames, and regression samples without changing Inventory calculations, SQL, DAL result shapes, imports, ranges, exports, or `/myinventory` visibility behavior.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5A implementation and operator smoke; explicit visual-direction approval before changing the existing Inventory renderer or assets.

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
- Area: SQL repo `dbo.IMPORT_STAGING_PROC`, raw fallback staging, `dbo.IMPORT_STAGING_CSV`, `dbo.IMPORT_STAGING`
- Type: refactor
- Description: `dbo.IMPORT_STAGING_PROC` owns multiple responsibilities around fallback staging, raw text conversion, typed conversion, metadata-sensitive partial fallback behavior, and final staging/output handoff. Task B intentionally preserved procedure shape to reduce risk while fixing Unicode preservation.
- Suggested Fix: After durable audit hooks are deployed and fallback audit evidence is stable, split `dbo.IMPORT_STAGING_PROC` responsibilities into smaller phase procedures or clearly bounded internal sections with audit markers, preserving existing input/output contracts and rollback scripts. Keep data-contract changes out of the split unless separately approved.
- Impact: high
- Risk: high
- Dependencies: Task B raw staging path deployed; Task C Slice 2 generic batch audit and SQL validation available; production smoke baseline for full and partial fallback imports.

### Deferred Optimisation
- Area: SQL repo `dbo.UPDATE_ALL2`, SQL repo `dbo.SUMMARY_PROC`, and downstream stats/dashboard rebuild procedures
- Type: performance
- Description: Task C Slice 12 delivered durable `update_all2_*` phase audit evidence for fallback imports. The first production smoke sample showed `update_all2_summary_proc` dominating visible subphase runtime at about 78 seconds, with additional coarse-to-subphase time still outside the emitted phase rows. There are not yet enough production samples to justify decomposing `dbo.UPDATE_ALL2` or `dbo.SUMMARY_PROC`.
- Suggested Fix: Run Task C Slice 13 to collect and analyze a short production baseline of recent fallback `ImportAuditBatch`/`ImportAuditPhase` rows. Quantify per-phase duration, failures/skips, coarse `fallback_update_all2` duration, missing timing gaps, and whether `dbo.SUMMARY_PROC` consistently dominates. Only after that evidence review should a SQL-specific `SUMMARY_PROC` or `UPDATE_ALL2` performance/decomposition task pack be prepared.
- Impact: high
- Risk: high
- Dependencies: Task C Slice 12 UPDATE_ALL2 wrapper/audit outputs deployed and smoke tested; several post-rollout fallback imports with `update_all2_*` phase rows; SQL owner approval before phase procedure design, tuning, or migration work.

### Deferred Optimisation
- Area: `stats_module.py`, import service modules, import DAL modules
- Type: refactor
- Description: Task C Slice 1 extracted fallback import file orchestration and DAL helpers, and Task C Slice 12 added UPDATE_ALL2 audit-output projection, but `stats_module.py` still remains the compatibility entry point for the current worker/route/command flow and still owns mixed step sequencing around Excel processing, secondary archive, SQL execution, audit phase projection, and result aggregation.
- Suggested Fix: After Slice 13 completes the UPDATE_ALL2 evidence review and confirms the SQL instrumentation boundary is stable, continue extracting residual import orchestration from `stats_module.py` into import-specific services while keeping the module as a thin compatibility shim until route or command callers are explicitly migrated. Preserve all current caller behavior and tests during each slice.
- Impact: medium
- Risk: medium
- Dependencies: Task C Slice 1 wrappers complete; durable audit foundation complete; Task C Slice 12 UPDATE_ALL2 audit-output projection deployed; Task C Slice 13 evidence review should confirm no further tiny audit integration is needed before service extraction resumes.

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
- Area: `player_self_service/governor_dashboard_dal.py`, SQL repo `dbo.KingdomScanData4` dashboard-read indexes, optional dashboard read view
- Type: performance
- Description: Phase 3 reads one latest `KingdomScanData4` row per selected governor and joins primary-key lookup tables. The smoke review identified that the original `TRY_CONVERT` around `GovernorID` could inhibit the existing `(GovernorID, SCANORDER DESC, AsOfDate DESC, ScanDate DESC)` access path; the bot query now converts the parameter instead. The source table is approximately 387k rows and growing, but there is no representative execution-plan, logical-read, duration, or concurrency baseline demonstrating that a new view, covering index, or maintained snapshot table is required.
- Suggested Fix: Run a SQL performance evidence slice using representative early/middle/recent Governor IDs with actual execution plans plus `SET STATISTICS IO, TIME ON`. Confirm an index seek on the GovernorID/scan-order index, one-row lookup behavior, and the clustered `PlayerLocation`/`Civilization_Mapping` joins. Record warm/cold logical reads and duration under expected dashboard concurrency. Introduce a canonical view only for contract reuse, add covering includes only if key-lookup cost is evidenced, and consider a snapshot table only if measured demand justifies explicit refresh, staleness, failure, deployment, and rollback contracts.
- Impact: medium
- Risk: medium
- Dependencies: Phase 3 smoke correction deployed for representative measurement; production SQL execution-plan access; observed dashboard usage/concurrency; SQL owner approval before index, view, or maintained-table changes.

### Deferred Optimisation
- Area: `commands/me_cmds.py`, `ui/views/player_self_service_views.py`, `player_self_service/governor_dashboard_*`, `/me dashboard`, player self-service v2 docs/tests
- Type: architecture
- Description: GovernorOS v2 Phases 1-4 are complete. The remaining committed roadmap is Phase 5A direct Resources/Materials/Speedups; Phase 5B existing `/me` page presentation alignment; Phase 6 Export Stats integration after a selected-governor versus all-linked decision; Phase 7 private `/me history`; Phase 8 required permission-gated admin/leadership `/me inspect`; and Phase 9 usage-led migration review. Phase 10 sticky features are a future programme candidate rather than committed implementation. Each remaining phase has a distinct command, privacy, compatibility, or product-decision boundary and must not be collapsed into one broad PR.
- Suggested Fix: Execute Phases 5A-9 as separate task-packed slices in the authoritative programme order. Preserve the Phase 2 payload/privacy boundary, Phase 3 access/selector journey, and Phase 4 standalone renderer/delivery/navigation contract; require the documented operator checkpoint for Phase 5A private report visibility and grouped command count, Phase 5B representative page visuals, Phase 6 export scope, Phase 7 history controls, Phase 8 permissions/VIP/lookup/telemetry, and every Phase 9 migration decision. Create a new successor pack before any Phase 10 implementation.
- Impact: high
- Risk: medium
- Dependencies: Phase 1 blueprint archived; Phase 2 delivered in mirror PR #216 and production PR #523; Phase 3 delivered in mirror PR #217 and production PR #524 with automated validation and operator Discord smoke completed on 2026-07-10; Phase 4 delivered in mirror PR #218 with operator Discord smoke completed on 2026-07-11; Phase 5A task pack/starter prepared; explicit approval for each later phase gate.

### Deferred Optimisation
- Area: `player_self_service/governor_dashboard_models.py`, `player_self_service/governor_dashboard_dal.py`, `player_self_service/governor_dashboard_renderer.py`, SQL repo `dbo.KingdomScanData4`
- Type: consistency
- Description: Phase 4 operator smoke approved a visible `Last Login: TBC` placeholder on the governor card, but the current renderer-independent payload and authoritative SQL contract do not yet expose a last-login value. Guessing or deriving it in the renderer would violate the payload/DAL boundary.
- Suggested Fix: After the authoritative Last Login column and semantics are added to the SQL repo, validate its type, nullability, timezone, and freshness meaning; then extend the dashboard DAL row, payload model/service mapping, fallback embed, renderer, and complete/missing-value tests in one separately approved SQL-facing slice. Replace `TBC` only after deployment ordering and rollback are documented.
- Impact: medium
- Risk: medium
- Dependencies: Operator approval of the Phase 4 placeholder; authoritative `KingdomScanData4` SQL migration and source-population contract; `k98-sql-validation` before implementation.

### Deferred Optimisation
- Area: `ui/views/player_self_service_views.py`, `player_self_service/page_cards.py`, `player_self_service/dashboard_card.py`, Accounts/Reminders/Preferences/Inventory/Exports `/me` page delivery
- Type: consistency
- Description: Phase 4 operator smoke confirmed the governor dashboard's standalone PNG attachment is materially larger and easier to read than generated `/me` pages still delivered inside embed image containers. Accounts, Reminders, Preferences, Inventory, and Exports need the same standalone delivery, blue-primary navigation, and attachment-lifecycle consistency, while their Discord-user/all-governor semantics mean they must not display a misleading Change Governor dropdown.
- Suggested Fix: Deliver the programme's approved Phase 5B presentation-alignment slice after Phase 5A. Migrate each successful generated summary card from embed-wrapped `attachment://` presentation to standalone attachments, retain the existing private embed fallback, preserve per-page actions and disabled states, apply the blue primary top-row pattern consistently, retain selected governor context only for returning to governor-specific pages, and add page-to-page/card/fallback/timeout cleanup plus desktop/mobile smoke coverage. Do not redesign renderers or create a broad shared framework.
- Impact: medium
- Risk: medium
- Dependencies: Phase 4 operator acceptance on 2026-07-11; complete or stabilize Phase 5A governor-specific inventory controls first; Phase 5B operator scope/visual approval and smoke tests; preserve existing Accounts, Reminders, Preferences, Inventory, and Exports semantics.

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
