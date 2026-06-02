# Deferred Optimisations

Active deferred optimisation items are staged here before they are grouped, scored, or promoted
to GitHub issues/task packs.

Resolved historical notes were moved to `archive/deferred_optimisations_resolved.md`.

Last reviewed after Command Platform Phase 5, Public Domain Grouping Design. PR 131
(`codex/command-platform-phase-1-permission-decorators`) was smoke tested successfully, merged,
and pushed to production on 2026-06-01. Phase 1 standardised active command permission gates onto
decorators, added focused decorator tests, preserved command paths and registration count, and kept
the command-platform baseline at
`primary=82 grouped_subcommands_detected=21 secondary_cogs=5 secondary_subscribe=1 total_unique=82`.
Phase 2 of the command-platform programme then retired the unused disabled secondary command
declarations in `cogs/commands.py` and root `subscribe.py`, updated validator terminology for
active versus disabled legacy surfaces, and detected helper-attached grouped subcommands including
`/prekvk import_history`. The active command baseline after Phase 2 is
`primary=82 grouped_subcommands_detected=22 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=82`.
PR 132 (`codex/command-platform-phase-2-validator-inventory`) was smoke tested successfully,
merged, and pushed to production on 2026-06-01. Phase 3 grouped the approved low-risk
operational/reporting commands under `/ops`, aligned startup command-audit logging, confirmed the
stale `primary=0 ... total_unique=0` startup summary was gone, and passed production smoke via
restart plus `/ops validate_command_cache`. PR 133
(`codex/command-platform-phase-3-ops-startup-audit`) was smoke tested successfully, merged, and
pushed to production on 2026-06-01. The active command baseline after Phase 3 is
`primary=75 grouped_subcommands_detected=29 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=75`.
Phase 4 then grouped all 14 Ark commands under `/ark`, including the public reminder preferences
and player report commands after approval, added a post-merge Discord briefing note, and reduced
the active command baseline to
`primary=62 grouped_subcommands_detected=43 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=62`.
PR 134 (`codex/command-platform-phase-4-ark-grouping`) was smoke tested successfully, merged, and
pushed to production on 2026-06-01.
Phase 5 then approved Phase 5A as the admin/leadership/operator implementation slice, captured
player self-service workflow redesign and public calendar/KVK calendar redesign as separate
deferred optimisations, and left the command baseline unchanged at
`primary=62 grouped_subcommands_detected=43 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=62`.
PR 135 (`codex/command-platform-phase-5a-design-docs`) was merged and pushed to production in
production PR 444 on 2026-06-01.
Phase 5A grouped the approved admin, leadership, and operator paths under domain command groups
and reduced the active command baseline to
`primary=39 grouped_subcommands_detected=76 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=39`.
Earlier review history: after the slow-pytest optimisation production
release, PR 107
(`pytest-log-delivery-docs`) resolved the high-impact pytest duration outliers found after the
pytest log-isolation production smoke audit, reducing the duration audit from `1450 passed, 2
skipped, 19 warnings in 638.91s` to `1450 passed, 2 skipped, 19 warnings in 54.86s`; it was smoke
tested successfully and deployed to production. PR 96
(`import-locations-command-orchestration-cleanup`) was smoke tested successfully and deployed to
production. PR 97 (`dlbot-player-location-upload-route`) was smoke tested successfully and
promoted to production. The governor fuzzy/name/partial-ID lookup standardisation item,
profile/location profile-cache lookup item, `/import_locations` command orchestration item, DL_bot
player location auto-import route/signal coupling item, and DL_bot PreKvK upload route extraction
item from PR 98 (`dlbot-prekvk-upload-route`) are complete, smoke tested successfully, and
promoted to production. Phase 2B PreKvK SQL compatibility cleanup was deployed and smoke tested
successfully. Phase 2C delivered the public read-only `/prekvk report` image report, was smoke
tested successfully, and was pushed to production. Phase 2D refactored the scheduled PreKvK
stats-alert path onto the Phase 2C report service architecture while preserving scheduled embed,
guard/state, and upload-refresh behaviour; it was smoke tested successfully and pushed to
production. Phase 3 local validation blockers were audited on 2026-05-20 and closed as a no-op:
the focused DB/non-DB blocker tests, full suite, and pytest log-noise validation all passed under
the documented `.venv` workflow without `RUN_DB_TESTS=1`. Phase 4 KVK_ALL upload-route extraction
was completed in PR 110 (`codex/kvk-all-upload-route`), smoke tested successfully on 2026-05-26,
and promoted to production: KVK_ALL now delegates through `upload_routes/kvk_all_route.py` while
preserving multi-attachment handling, SQL preflight behaviour, Discord output, sheet link button
behaviour, and non-blocking auto-export scheduling. Phase 5A MGE results and KVK Honor upload-route
extraction was completed in PR 113 (`codex/dlbot-upload-routing-phase-5a`), smoke tested
successfully on 2026-05-26, deployed to production, and closed: `DL_bot.py` now delegates those
routes through `upload_routes/mge_results_route.py` and `upload_routes/honor_route.py`, with shared
route helpers in `upload_routes/common.py` for notify-channel fallback, source/uploader embed
fields, and best-effort background task scheduling. Phase 5B inventory and weekly activity route
extraction was completed in PR 114 (`codex/dlbot-upload-routing-phase-5b`), smoke tested
successfully on 2026-05-26 with inventory and alliance weekly uploads, deployed to production, and
closed: `DL_bot.py` now delegates those routes through `upload_routes/inventory_route.py` and
`upload_routes/weekly_activity_route.py`. Phase 5C Rally Forts upload-route extraction was
completed in PR 115 (`codex/dlbot-upload-routing-phase-5c`), smoke tested successfully, merged,
deployed to production, and pushed to production: `DL_bot.py` now delegates Rally Forts handling
through `upload_routes/rally_forts_route.py` while preserving filename matching, local download
staging, lazy importer loading, SQL preflight, offload dispatch, aggregate Discord output,
safe filename rejection, disabled-channel fall-through, and best-effort log-backup scheduling.
Phase 5D fallback queue route extraction was completed in PR 116
(`codex/dlbot-upload-routing-phase-5d`), smoke tested successfully on 2026-05-26, closed, and
pushed to production: `DL_bot.py` now delegates the monitored-channel fallback queue path through
`upload_routes/fallback_queue_route.py` while preserving route order, `.xlsx/.xls/.csv` fallback
attachment handling, worker queue handoff, `QueueFull` drop behaviour, live queue bookkeeping,
queue embed updates, shared `utils.live_queue_lock` usage, command fall-through, and best-effort
log-backup scheduling. Phase 5 upload-routing consolidation is complete. Phase 6 startup/lifecycle
separation is complete. Phase 6A startup lifecycle boundary work
was completed in PR 117 (`codex/dlbot-phase-6-startup-lifecycle-1`), smoke tested successfully on
2026-05-27, merged, and pushed to production: `bot_instance.py:on_ready()` now routes its initial
runtime bootstrap through `core.startup_lifecycle.run_startup_phases()` with a named
`ready_runtime_bootstrap` phase, preserving startup order while adding phase start/completion and
failure attribution logs. Phase 6B runtime services extraction was completed in PR 119
(`codex/dlbot-phase-6b-runtime-services`), smoke tested successfully on 2026-05-27, merged, and
pushed to production: `bot_instance.py:on_ready()` now routes heartbeat, health dashboard, offload
monitor, PIL safety patch, lock-file cleanup, usage tracker startup, daily summary, activity
tracking, UTC clock, and member-count status loops through the named `ready_runtime_services`
phase while preserving startup order and behaviour. Phase 6C usage tracker lifecycle ownership
then consolidated command/component/metric usage logging onto the shared `usage_tracker.py`
singleton and moved usage JSONL prune startup into `ready_runtime_services`, leaving
`full_startup_sequence()` free of usage observability startup. Phase 6D command sync lifecycle
ownership was completed in PR 121 (`codex/dlbot-phase-6d-command-lifecycle`), smoke tested with
unchanged, changed, and post-cache-update restart paths, merged, and pushed to production:
`bot_instance.py:on_ready()` now delegates startup command signature/cache/sync handling through
`core/command_lifecycle.py` and the named `ready_command_sync` phase while preserving scoped sync,
timeout telemetry, command-cache writes, and loaded-command logging. Phase 6E command lifecycle
admin tooling convergence was completed in PR 122
(`codex/dlbot-phase-6e-command-admin-tooling`), merged, smoke tested, and pushed to production on
2026-05-28: `/ops resync_commands`, `/ops validate_command_cache`, and
`/ops show_command_versions` now reuse `core/command_lifecycle.py` for manual scoped sync,
signature inventory, version display, cache update, and cache validation while preserving admin
permissions, ephemeral responses, operation locking, embeds, timeout behaviour, and grouped command
names. Production smoke confirmed both command execution and usage telemetry flushes, including a
successful manual command resync. Phase 6F event cache/reminder/view rehydration was completed in
PR 123 (`codex/dlbot-phase-6f-event-rehydration`), merged, smoke tested, and pushed to production
on 2026-05-28. Phase 6G scheduler/task-supervision startup was completed in PR 124
(`codex/dlbot-phase-6g-scheduler-lifecycle`), merged, smoke tested, and pushed to production on
2026-05-28: `core/scheduler_lifecycle.py` now owns scheduler/task registration ordering, event
readiness gating, `TaskMonitor` registration, duplicate-prevention checks, and best-effort logging;
`bot_instance.py:on_ready()` delegates through `ready_event_scheduler_tasks`,
`ready_event_cache_refresh_loop`, `ready_domain_scheduler_tasks`, and
`ready_calendar_scheduler_tasks`. Production smoke confirmed event-dependent schedulers,
`refresh_event_cache_task`, tracked view rehydration, Ark/MGE schedulers, `full_startup_sequence()`,
reminder cleanup, pinned calendar rehydration, daily pinned refresh, and calendar reminder loop all
started in the expected order with no startup phase failure or `on_ready()` critical exception.
Phase 6H queue worker/live queue lifecycle moved queue worker registration, live queue recovery,
best-effort queue embed refresh, queue cleanup startup, and connection watchdog startup into
`core/queue_lifecycle.py` and the `ready_queue_lifecycle` startup phase while preserving the
existing `full_startup_sequence()` ordering. PR 125
(`codex/dlbot-phase-6h-queue-lifecycle`) was merged, smoke tested cleanly, pushed to production,
and confirmed the new queue lifecycle phase ran in order with queue workers, live queue recovery,
queue cleanup, connection watchdog, and later startup phases continuing normally. Phase 6I shutdown
and recovery coordination was completed in PR 126
(`codex/dlbot-phase-6i-shutdown-recovery`), merged, and pushed to production: signal shutdown now
routes through bot-side graceful teardown before `bot.close()`, `bot_instance.py` briefly waits for
configured `channel_queues` including in-flight `queue.join()` work, persists `QUEUE_CACHE_FILE`
through `save_live_queue()`, then cancels supervised tasks and stops usage tracking. Validation
passed locally, and production `/ops force_restart` smoke confirmed restart recovery and all
Phase 6A-H startup phases continued normally. Because `/ops force_restart` intentionally remains a
break-glass path and Windows/process termination did not expose a reliable in-process graceful
shutdown log trail, Phase 6I was closed with residual smoke risk. Phase 6J graceful restart and
shutdown operations was completed in PR 127 (`codex/dlbot-phase-6j-graceful-restart-starter`),
merged, pushed to production, and smoke tested successfully on 2026-05-28: `/ops graceful_restart`
is now the preferred cooperative restart path, `/ops force_restart` remains the break-glass path,
`/ops restart_bot` is retired, restart marker writing and cooperative restart invocation are
centralized in `core/restart_operations.py`, and `graceful_shutdown.py` uses a configurable
cooperative fallback timeout defaulting to 15 seconds. Phase 6K queue persistence hardening was
completed in PR 128 (`codex/dlbot-phase-6k-queue-persistence`), merged, pushed to production, and
smoke tested successfully on 2026-05-28: live queue startup now awaits persisted state load/apply
before best-effort embed refresh, live queue saves use the established atomic JSON helper,
sync/offloaded queue saves remain thread-safe without awaiting the main-loop `live_queue_lock`,
stale queue message metadata is cleared/replaced during embed refresh, graceful restart still
persists live queue state before task cancellation, and cooperative `bot.close()` timeout now
forces process exit with the restart code so the watchdog cannot wait indefinitely. Phase 6L
closed the programme by confirming the final ownership model: `DL_bot.py` remains process-entry
and message/upload owner, `bot_loader.py` remains bot construction owner, and `bot_instance.py`
remains lifecycle owner. Phase 6L also wrapped child PID publication and process signal
registration in named `DL_bot.py` helpers without changing startup, shutdown, restart, command
registration, upload-route, or queue-persistence behavior. The completed DL_bot task packs and
chat starters are archived under `docs/task_packs/archive/`. The remaining related programmes are
the command-surface migration, queue-domain redesign, optional SQL-backed queue persistence,
disabled secondary command-surface cleanup, SQL deployment workflow, and pinned calendar tracker
atomic-write hardening; each requires a fresh scope instead of an additional Phase 6 slice.

### Deferred Optimisation
- Area: `tests/test_ark_preference_service.py`, `tests/test_ark_bans_enforcement.py`, `tests/test_lock_timeout.py`, `tests/test_calendar_service.py`, `tests/test_calendar_pipeline.py`, remaining slow full-suite pytest paths
- Type: performance
- Description: After PR 107 resolved the original slow pytest offenders, the new duration audit `C:\Users\cwatt\Downloads\.codex_pytest_audit-new.log` shows the remaining full-suite outliers are concentrated in Ark preference/ban negative paths, lock-timeout coverage, calendar failure-path retries, live queue persistence, maintenance subprocess timeout/success coverage, and one inventory vision import case. The slowest current timings are `tests/test_ark_preference_service.py::test_set_preference_rejects_unknown_governor` at 7.33s, `tests/test_ark_bans_enforcement.py::test_admin_add_allows_when_override_on` at 5.23s, `tests/test_lock_timeout.py::test_remove_view_tracker_entry_returns_false_when_locked` at 5.06s, `tests/test_lock_timeout.py::test_save_view_tracker_raises_on_lock` at 5.06s, `tests/test_calendar_service.py::test_refresh_full_stops_on_sync_failure` at 3.02s, and `tests/test_calendar_pipeline.py::test_pipeline_stops_on_sync_failure` at 3.01s.
- Suggested Fix: Start a fresh audit from `.codex_pytest_audit-new.log` and classify each remaining slow path as intentional timeout coverage, missing test boundary, live dependency leakage, retry/backoff, or genuine defect. Preserve lock-timeout and subprocess timeout coverage, but replace real multi-second waits with patched timeout constants, fake clocks, controlled retry policies, or explicit service/DAL boundary fakes where safe. Keep the scope separate from PR 107 and validate with `pytest -vv tests --durations=30 --durations-min=1.0`, focused subsystem tests, `scripts/analyse_pytest_log_noise.py`, and `python -m pytest -q tests`.
- Impact: medium
- Risk: medium
- Dependencies: Use the post-PR-107 audit baseline (`1450 passed, 2 skipped, 19 warnings in 54.86s`); preserve genuine timeout, subprocess, lock, negative-path, and log-noise coverage.

### Deferred Optimisation
- Area: `commands/`, `scripts/validate_command_registration.py`
- Type: architecture
- Description: Batch 1 of the command-surface balancing audit grouped admin-heavy `/ops` and `/mge` commands, reducing the primary Discord application-command set from 100 to 82 top-level commands. Phase 3 later moved approved low-risk ops/reporting commands under `/ops`, reducing the primary set to 75. Future standalone slash commands can still erode this buffer and eventually break startup sync with Discord error 30032 unless additional command-surface consolidation remains planned.
- Suggested Fix: Continue the command-platform programme through staged follow-up batches. Group related commands by domain where user experience allows, identify stale/low-use admin commands for consolidation or retirement, update docs for renamed paths, and keep `scripts/validate_command_registration.py` enforcing the 100-command ceiling with a warning at 90+.
- Impact: high
- Risk: medium
- Dependencies: Batch 1 `/ops` and `/mge` grouping and Phase 1 permission decorator standardisation remain deployed cleanly; coordinate with bot operators before renaming public command paths; preserve standard decorator permission checks when commands move into groups.

### Phase 4 Completed Item
- Area: `commands/ark_cmds.py`, `docs/ark/`, Ark command tests
- Type: architecture
- Description: Phase 4 grouped all Ark commands under `/ark`, including `/ark reminder_prefs` and `/ark report_players`, while preserving permissions, options, versions, usage tracking, response visibility, modal/view flows, and command-cache semantics.
- Resolution: Added the `/ark` command group, updated Ark command docs/tests and command-platform docs, and added a post-merge Discord briefing note.
- Validation: Command registration reports `primary=62 grouped_subcommands_detected=43 disabled_legacy=0 secondary_cogs=0 secondary_subscribe=0 total_unique=62` in implementation validation.

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
- Type: architecture
- Description: Player self-service commands are still split across development-era entry points instead of being designed as complete user workflows. The affected paths include `/register_governor`, `/modify_registration`, `/my_registrations`, `/mygovernorid`, `/mykvkstats`, `/my_stats`, `/my_stats_export`, `/mykvkhistory`, `/mykvktargets`, `/mykvkcrystaltech`, `/myinventory`, `/inventory_preferences`, `/export_inventory`, `/subscribe`, `/modify_subscription`, `/unsubscribe`, and `/calendar_reminder_config`. These are high-discoverability, likely high-traffic commands that players use for critical self-service tasks, and simple path grouping could preserve a fragmented user model while still forcing players to relearn command names.
- Suggested Fix: Scope a dedicated player self-service workflow redesign outside the command-count programme. Review each block as a user journey before choosing command paths. For registry/account flows, specifically evaluate whether lookup, register, review, and modify should be consolidated into a coherent Governor ID/account command surface rather than four separate commands. Review SQL-backed command usage, transition/announcement needs, Discord alias limitations, docs/smoke references, permission and channel behavior, and focused regression tests before any implementation.
- Impact: high
- Risk: medium
- Dependencies: Phase 5A admin/leadership/operator grouping is complete; requires operator approval, SQL-backed usage review, user-facing briefing, and a fresh task pack.

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
- Area: `commands/`, command documentation, `scripts/validate_command_registration.py`
- Type: architecture
- Description: The wider command-surface end state remains separate from startup lifecycle ownership. Grouping or retiring slash-command surfaces can reduce Discord's 100-command sync risk, but it affects public/operator command paths, documentation, tests, and rollout communication.
- Suggested Fix: Scope a standalone command-surface optimisation programme after the Phase 6 lifecycle slices. Group or retire command paths by domain only with operator-approved UX rules, update docs and tests for renamed paths, preserve permissions and autocomplete behaviour, and keep `scripts/validate_command_registration.py` enforcing command-count guardrails. Treat this as a separate wider task, not a startup lifecycle PR.
- Impact: high
- Risk: medium
- Dependencies: Operator approval for command path changes; command lifecycle admin tooling convergence can happen first but is not required for command-surface grouping.
