# Deferred Optimisations

Active deferred optimisation items are staged here before they are grouped, scored, or promoted
to GitHub issues/task packs.

Resolved historical notes moved to `archive/deferred_optimisations_resolved.md`.

### Deferred Optimisation
- Area: `event_calendar/reminder_state.py`, `player_self_service/service.py`, `event_calendar/reminder_candidates.py`
- Type: performance
- Description: Phase 5D.1 must read Calendar sent-key state to exclude already delivered alerts. The existing file-backed `CalendarReminderState` stores one global, append-only mapping and exposes only a full-file load, so each private summary request parses the complete history and the pure projection copies every sent key before applying user-scoped eligibility. Codex Security reproduced approximately linear cost with synthetic state: about 93 ms and 28 MB traced peak at 100,000 keys, and about 514 ms and 135 MB at 500,000 keys. Ordinary members cannot directly grow the state, and representative production size or material shared-service impact is not yet established, so this is not a reportable security finding or an approved Phase 5D.1 persistence change.
- Suggested Fix: First record production state byte/key count and growth rate, then run a controlled production-clone concurrency check at that observed size while measuring RSS, event-loop latency, scheduler health, and interaction failures. If evidence warrants a change, scope a separate Calendar-state lifecycle slice to define retention/pruning, user-scoped indexing or an equivalent bounded read contract, concurrency controls, restart behavior, migration/rollback, and dispatcher/projection parity without changing sent-key semantics.
- Impact: medium
- Risk: high
- Dependencies: Phase 5D.1 deployed baseline; production `event_calendar_reminder_state.json` size evidence; operator-approved controlled concurrency test; no persistence or sent-key contract change without a separate task pack.

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
- Area: remaining redirect-only account/reminder/KVK compatibility paths, `/mykvkcrystaltech`, command governance, and migration communications
- Type: cleanup
- Description: Completed Phases 5F, 5G, and 6 removed their explicitly approved Inventory, export, and `/my_stats` routes. The 2026-07-18 roadmap separately assigns `/stats player` modernisation and `/player_profile` removal to Phase 8, and closes `/me history` while preserving canonical `/kvk history`. Those decisions are no longer part of this generic deferred item. Remaining redirected account/reminder/KVK paths and `/mykvkcrystaltech` still require route-specific usage, feedback, caller, and replacement evidence.
- Suggested Fix: Use future Phase 10 for fresh qualified usage and no-feedback review. Change one remaining route at a time only after explicit operator approval, communication, command-governance updates, resync, smoke, and rollback. Do not reopen the Phase 8 `/stats player`/`/player_profile` decision or the canonical `/kvk history` placement through this generic item.
- Impact: medium
- Risk: medium
- Dependencies: Phase 7-9 roadmap approved on 2026-07-18; Phase 8 and Phase 9 have dedicated task packs; future Phase 10 evidence review.

### Deferred Optimisation
- Area: SQL repo `dbo.InventoryReportPreference`, `inventory/dal/inventory_reporting_dal.py`, `inventory/reporting_service.py`, and retired Inventory-visibility documentation/tests
- Type: cleanup
- Description: Phase 5F removed the final approved player-facing need for Inventory report visibility by retiring `/myinventory`, `/inventory_preferences`, public Inventory posting, and the Personal Settings Privacy & Sharing control. The application no longer reads or writes the preference, but the SQL table and existing rows were intentionally retained as rollback evidence. Dropping the table in the bot cleanup would have created an unnecessary irreversible SQL dependency outside the no-SQL-deployment Phase 5F boundary.
- Suggested Fix: After Phase 5F is deployed, command cache resynced, and the simplified private-only Inventory journey has completed an agreed observation period, run a SQL dependency and manual-consumer audit. If no external report, procedure, job, script, or rollback need remains, prepare a separate SQL task pack and migration to retire `dbo.InventoryReportPreference`, with production backup/evidence, deployment ordering, rollback, schema export, and bot compatibility checks. Otherwise document why the dormant table is retained.
- Impact: low
- Risk: medium
- Dependencies: Phase 5F operator smoke accepted on 2026-07-16; confirmed zero runtime reads/writes; an agreed post-release observation window; fresh SQL repository and production dependency checks; explicit destructive SQL approval.

### Deferred Optimisation
- Area: `player_self_service/governor_dashboard_dal.py`, SQL repo `dbo.KingdomScanData4` dashboard-read indexes, optional dashboard read view
- Type: performance
- Description: Phase 3 reads one latest `KingdomScanData4` row per selected governor and joins primary-key lookup tables. The smoke review identified that the original `TRY_CONVERT` around `GovernorID` could inhibit the existing `(GovernorID, SCANORDER DESC, AsOfDate DESC, ScanDate DESC)` access path; the bot query now converts the parameter instead. The source table is approximately 387k rows and growing, but there is no representative execution-plan, logical-read, duration, or concurrency baseline demonstrating that a new view, covering index, or maintained snapshot table is required.
- Suggested Fix: Run a SQL performance evidence slice using representative early/middle/recent Governor IDs with actual execution plans plus `SET STATISTICS IO, TIME ON`. Confirm an index seek on the GovernorID/scan-order index, one-row lookup behavior, and the clustered `PlayerLocation`/`Civilization_Mapping` joins. Record warm/cold logical reads and duration under expected dashboard concurrency. Introduce a canonical view only for contract reuse, add covering includes only if key-lookup cost is evidenced, and consider a snapshot table only if measured demand justifies explicit refresh, staleness, failure, deployment, and rollback contracts.
- Impact: medium
- Risk: medium
- Dependencies: Phase 3 smoke correction deployed for representative measurement; production SQL execution-plan access; observed dashboard usage/concurrency; SQL owner approval before index, view, or maintained-table changes.

### Deferred Optimisation
- Area: post-Phase-8 residual `embed_my_stats.py`, root `stats_service.py`, `stats_helpers.py`, profile cache/lookup helpers, and zero-caller leadership compatibility code
- Type: cleanup
- Description: The product decision is no longer deferred: Phase 8 will modernise the existing `/stats player`, will not create `/me inspect`, and will remove `/player_profile` with no redirect. The exact caller audit may prove that some legacy stats/profile helpers remain shared by other commands. Any such non-zero-caller helper must be retained during Phase 8 rather than deleted speculatively.
- Suggested Fix: Execute the Phase 8 task pack. Delete command-specific and zero-caller helpers in that phase. After acceptance, retain only a narrowly documented residual cleanup item for helpers that could not be removed because another live caller remains; do not use broad module cleanup to widen the Phase 8 command/data scope.
- Impact: medium
- Risk: medium
- Dependencies: Phase 8 task pack, caller graph, focused permission/rendering/command tests, coordinated command resync and rollback.

### Deferred Optimisation
- Area: SQL repo `dbo.usp_GetPersonalStatsDaily`, `dbo.KingdomScanData4`, Alliance Activity/Fort sources, and `stats/dal/personal_stats_dal.py`
- Type: performance
- Description: Phase 6 deployed one bounded set-based procedure for up to 26 deduplicated governors and 180 Stats-anchor days plus `StatsSourceRefreshedAtUtc`, calculated as the latest `KingdomScanData4.ScanDate` on the global Stats anchor. Existing indexes cover the principal Governor/date access patterns, while the bot adds a 9-second data timeout, bounded concurrency, TTL/LRU caching, and inflight deduplication. Functional production smoke passed, but no recorded representative execution plan, logical-read, duration, memory-grant, or concurrent 26-account baseline proves that a new covering index is warranted. In particular, the existing AsOfDate-leading index does not currently include `ScanDate`, so the new global freshness aggregate should be measured rather than assumed free or prematurely indexed.
- Suggested Fix: Execute the deployed procedure for single, multi, and 26-account sets at 90/180 days with actual plans plus `SET STATISTICS IO, TIME ON`, cold/warm cache, and expected concurrency. Isolate the header freshness aggregate from the daily payload cost. Add the narrowest covering include/index or procedure refinement only when the measured hotspot is identified; repeat correctness/performance tests and retain an independent rollback migration.
- Impact: high
- Risk: medium
- Dependencies: SQL PRs #43/#44 deployed and Phase 6 functional smoke accepted on 2026-07-18; representative linked Governor IDs; SQL owner-approved measurement window; separate SQL Changes review for any index/procedure follow-up.

### Deferred Optimisation
- Area: `player_self_service/governor_dashboard_models.py`, `player_self_service/governor_dashboard_dal.py`, `player_self_service/governor_dashboard_renderer.py`, SQL repo `dbo.KingdomScanData4`
- Type: consistency
- Description: Phase 4 operator smoke approved a visible `Last Login: TBC` placeholder on the governor card, but the current renderer-independent payload and authoritative SQL contract do not yet expose a last-login value. Guessing or deriving it in the renderer would violate the payload/DAL boundary.
- Suggested Fix: After the authoritative Last Login column and semantics are added to the SQL repo, validate its type, nullability, timezone, and freshness meaning; then extend the dashboard DAL row, payload model/service mapping, fallback embed, renderer, and complete/missing-value tests in one separately approved SQL-facing slice. Replace `TBC` only after deployment ordering and rollback are documented.
- Impact: medium
- Risk: medium
- Dependencies: Operator approval of the Phase 4 placeholder; authoritative `KingdomScanData4` SQL migration and source-population contract; `k98-sql-validation` before implementation.

### Deferred Optimisation
- Area: broad cross-page renderer/view framework beyond Phase 7's narrow `/me` visual contract
- Type: architecture
- Description: Phase 7 is now approved to align retained `/me` typography, colours, state pills, panel borders, alignment, dates, numbers, missing values, navigation, fallbacks, and visual testing using `/me stats` as the reference. It may extract a small proven `player_self_service/visual_contract.py`. It must keep Dashboard, Inventory, summary payloads, selectors, data ownership, dimensions, and page-specific renderers independent. A universal renderer/grid/view framework is still unproven and outside Phase 7.
- Suggested Fix: During Phase 7, measure duplicated primitives and extract only contracts with at least two identical consumers. After Phase 7 and later leadership cards are observed, reconsider a broader framework only with quantified duplication, a migration matrix, visual parity tests, lifecycle proof, and separate approval.
- Impact: low
- Risk: medium
- Dependencies: Phase 7 task pack and contact-sheet audit; accepted `/me stats` reference; no broad framework without a later explicit task pack.

### Deferred Optimisation
- Area: `services/stats_export_service.py`, `stats/dal/stats_export_dal.py`, `stats_exporter.py`, `stats_exporter_csv.py`, `player_self_service/accounts_export.py`, Inventory exports, SQL export views/tables, export docs/tests
- Type: architecture
- Description: Completed Phase 5G delivers the narrow all-linked Account Data output contract: Account-Summary-first full workbook, current snapshot CSV, raw Stats history CSV, exact windows/counts/Forts/safety/freshness, and truthful `.xlsx` Sheets compatibility. The three selected-governor Inventory report-page exports remain unchanged. Broader cross-domain export redesign is still not approved.
- Suggested Fix: Treat future changes spanning Inventory, KVK history, rankings, registry, leadership outputs, live Sheets creation, or new SQL views as a separate evidence-led export-output programme. Do not reopen Phase 5G or use Phase 6 interactive Stats as an export redesign vehicle.
- Impact: high
- Risk: high
- Dependencies: Phase 5G operator accepted after output-shape and Discord smoke on 2026-07-17; operator approval for any future cross-domain programme.

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

### Deferred Optimisation
- Area: `decoraters.py`, `commands/admin_cmds.py`, `/ops usage`, `/ops usage_detail`, leadership-role configuration and permission tests
- Type: security
- Description: The Phase 5C Codex Security repository scan validated that the shared `is_admin_or_leadership` path treats an exact configured leadership role name as an independent authorization grant when no configured stable role ID matches. Both private SQL-backed usage commands inherit that decision. Phase 8 will not reuse this broad gate for `/stats player`; it has a dedicated stable-role-ID and Leadership/Notify channel matrix. The generic decorator and other commands remain a separate low/P3 hardening item.
- Suggested Fix: In a separate permission-hardening slice, decide whether role-name compatibility must remain. Prefer configured stable role IDs as authority; if names are retained for migration, make them warning-only or require a matching approved ID. Add regression coverage for unmatched ID plus matching name, allowed/disallowed channels, Discord administrator and fixed admin paths, both usage commands, and existing leadership workflows before deployment.
- Impact: medium
- Risk: medium
- Dependencies: Production leadership role IDs are confirmed for Phase 8, but generic decorator consumers still need their own compatibility audit. Preserve intended admin/leadership access outside Phase 8; run focused permission/telemetry tests, command registration, full pytest, and operator smoke before changing the shared decorator.

### Deferred Optimisation
- Area: `DL_bot.py` fast-path attachment handlers, `upload_routes/`, `file_utils.py`, import worker admission and operational telemetry
- Type: security
- Description: The Phase 5C Codex Security repository scan validated that eight attachment fast paths can hand overlapping work directly to workbook parsing, worker subprocesses, audit writes, and SQL-backed imports without one shared in-flight bound, cooldown, or backpressure control. A bounded local harness observed two concurrent real-route importer handoffs. Discord limits and unknown production channel ACLs reduce likelihood, but they do not cap bot-side in-flight work; final severity is low/P3.
- Suggested Fix: Scope a dedicated upload-admission slice. Measure normal import duration and host/SQL headroom, then place every fast path behind a small shared semaphore or bounded queue with explicit busy/backpressure messaging, per-channel or import-key deduplication where safe, cancellation/timeout cleanup, and metrics for active, queued, rejected, and timed-out work. Preserve importer semantics and validate concurrency limits with deterministic two/many-task tests before live smoke.
- Impact: medium
- Risk: high
- Dependencies: Production upload-channel ACL review; measured host/process/SQL capacity and acceptable queue depth; coordinate with the existing queue-domain deferred item without broad redesign; no live load test without explicit operator approval.

### Deferred Optimisation
- Area: `DL_bot.py::_offload_callable`, `file_utils.py` callable offload backends, `upload_routes/mge_results_route.py`, importer failure tests
- Type: reliability
- Description: The same security scan reproduced a bounded correctness defect: for the production four-argument MGE importer shape, the first compatible thread backend can execute a side-effecting callable and propagate its exception, after which `_offload_callable` treats that callable exception as a backend-start failure and invokes the callable once more through `asyncio.to_thread`. The demonstrated consequence is repeated failed-import audit/parsing/database work, not a reportable security impact after policy calibration.
- Suggested Fix: Separate backend-start/transport failures from exceptions raised after callable entry, and never retry a non-idempotent callable merely because it failed. Add a focused regression test asserting one invocation when the callable raises after entry, retain coverage for genuine backend-unavailable fallback, and audit other helper call shapes before claiming they share the same behavior.
- Impact: medium
- Risk: medium
- Dependencies: Preserve current offload preference and route-level error messaging; define once-only versus explicitly retryable callable contracts; run MGE upload, offload, failure/audit, pre-commit, and full regression tests.
