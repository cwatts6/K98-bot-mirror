# Deferred Optimisations

Active deferred optimisation items are staged here before they are grouped, scored, or promoted
to GitHub issues/task packs.

Resolved historical notes were moved to `archive/deferred_optimisations_resolved.md`.

Last reviewed after the slow-pytest optimisation production release. PR 107
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
separation is now the active DL_bot architecture batch. Phase 6A startup lifecycle boundary work
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
cooperative fallback timeout defaulting to 15 seconds.

The next coherent major architecture batch should be scoped as fresh work around `DL_bot.py`
startup/lifecycle ownership, not as a continuation of upload routing. If the optional queue
persistence slice is taken, continue from
`docs/task_packs/Codex Chat Starter - DL_bot Phase 6K Queue Persistence Hardening.md`; otherwise
continue toward final process-entry and bot-construction cleanup from
`docs/task_packs/DL_bot Startup Lifecycle - Phase 6 Audit Starter.md`, with this backlog and the
current `K98-bot-mirror` GitHub issues list as supporting context.

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
- Description: Batch 1 of the command-surface balancing audit grouped admin-heavy `/ops` and `/mge` commands, reducing the primary Discord application-command set from 100 to 82 top-level commands. Future standalone slash commands can still erode this buffer and eventually break startup sync with Discord error 30032 unless additional command-surface consolidation remains planned.
- Suggested Fix: Continue the command-surface programme through the staged follow-up batches below. Group related commands by domain where user experience allows, identify stale/low-use admin commands for consolidation or retirement, update docs for renamed paths, and keep `scripts/validate_command_registration.py` enforcing the 100-command ceiling with a warning at 90+.
- Impact: high
- Risk: medium
- Dependencies: Batch 1 `/ops` and `/mge` grouping validation remains clean; coordinate with bot operators before renaming public command paths; preserve admin-only permission checks when commands move into groups.

### Deferred Optimisation
- Area: `commands/ark_cmds.py`, `docs/ark/`, Ark command tests
- Type: architecture
- Description: Ark still exposes many top-level commands (`/ark_create_match`, `/ark_force_announce`, `/ark_amend_match`, `/ark_cancel_match`, `/ark_set_preference`, `/ark_clear_preference`, `/ark_ban_add`, `/ark_ban_revoke`, `/ark_ban_list`, `/ark_set_result`, `/ark_generate_draft`, `/create_ark_team`, plus public `/ark_reminder_prefs` and `/ark_report_players`). These are a natural `/ark` command group and could recover another large block of top-level command headroom, but several docs and public/operator workflows reference the flat paths.
- Suggested Fix: Prepare a second command-surface migration batch that groups Ark commands under `/ark`, preserving `is_admin_or_leadership_only`, `channel_only`, public reminder/report behavior, autocomplete/options, and interaction responses. Coordinate operator communication for public path changes before implementation and update Ark docs/tests to the new paths.
- Impact: high
- Risk: medium
- Dependencies: Batch 1 `/ops` and `/mge` grouping deployed cleanly; operators approve public Ark path migration and announcement timing.

### Deferred Optimisation
- Area: `commands/stats_cmds.py`, `commands/registry_cmds.py`, `commands/inventory_cmds.py`, `commands/calendar_cmds.py`, `commands/subscriptions_cmds.py`, user-facing command docs/tests
- Type: architecture
- Description: Public/player-facing command domains still use many top-level paths that could be grouped later (`/kvk`, `/registry`, `/inventory`, `/calendar`, `/subscriptions`). These commands are more discoverability-sensitive than admin-only surfaces and include heavily documented player workflows, so moving them without coordination could confuse users even though it would reduce startup sync risk further.
- Suggested Fix: Scope a later public command-path migration with operator-approved UX rules, aliases/transition messaging if feasible, and focused docs/test updates. Prioritise admin-heavy subcommands inside each domain first, then evaluate whether player paths should remain flat for discoverability.
- Impact: medium
- Risk: medium
- Dependencies: Operator approval for public command rename policy; updated command reference/announcement plan; Batch 1 validation remains below the warning threshold.

### Deferred Optimisation
- Area: `cogs/commands.py`, `subscribe.py`, `scripts/validate_command_registration.py`, startup command audit docs
- Type: cleanup
- Description: Disabled secondary command surfaces still declare duplicate command names (`/summary`, `/weeksummary`, `/history`, `/failures`, `/ping`, `/subscribe`). The validator reports these duplicates, but the output does not clearly separate intentionally disabled legacy surfaces from active startup-sync risk.
- Suggested Fix: Decide whether to retire the disabled secondary cogs or enhance validator output to classify duplicates by active vs disabled registration path. If the files are retained, document the environment gating and keep duplicate warnings informational; if retired, remove or archive the dead command declarations with smoke/import coverage.
- Impact: medium
- Risk: low
- Dependencies: Confirm secondary cogs remain disabled by default in production and no operator workflow depends on loading them.

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
- Suggested Fix: After the current upload-routing phase set is complete, use `C:\Users\cwatt\Downloads\sql_deploy_route_task_pack.md` to create a PR-based SQL promotion workflow with guarded deploy scripts, migration history, a safe production schema export branch, `migrations/` conventions, and `docs/SQL_PROMOTION_GUIDE.md`.
- Impact: high
- Risk: medium
- Dependencies: Complete the active DL_bot upload-routing phases first; preserve current production schema export as a drift/safety mechanism while preventing direct overwrite of `main`.

### Deferred Optimisation
- Area: `DL_bot.py`, `bot_instance.py` startup and lifecycle
- Type: architecture
- Description: Startup and lifecycle responsibilities remain spread across `DL_bot.py` and `bot_instance.py`, including interpreter/startup checks, bot construction/import wiring, event registration, singleton/runtime concerns, signal/shutdown handling, cache warming, startup notifications, and lifecycle coordination for the wider bot. Phase 5 completed upload-route separation, Phase 6A introduced the first named startup lifecycle boundary for the initial `on_ready()` runtime bootstrap, Phase 6B extracted runtime services/observability startup into `ready_runtime_services`, Phase 6C consolidated usage tracker lifecycle ownership, Phase 6D extracted startup command signature/cache/sync handling into `core/command_lifecycle.py` and `ready_command_sync`, Phase 6E converged command lifecycle admin tooling onto the same lifecycle owner, Phase 6F extracted event cache, reminder loading, tracked view rehydration, and pinned calendar view rehydration behind named lifecycle boundaries, Phase 6G extracted scheduler/task-supervision startup into `core/scheduler_lifecycle.py`, Phase 6H extracted queue worker/live queue startup into `core/queue_lifecycle.py`, Phase 6I added bot-side graceful teardown coordination for queue drain/state flush before supervised task cancellation, and Phase 6J added cooperative restart/shutdown operations. Remaining lifecycle work should address the optional queue persistence hardening slice first if desired, then process-entry/bot-construction cleanup.
- Suggested Fix: Continue Phase 6 incrementally from `docs/task_packs/DL_bot Startup Lifecycle - Phase 6 Audit Starter.md`. If approved, run the optional queue persistence hardening slice from `docs/task_packs/Codex Chat Starter - DL_bot Phase 6K Queue Persistence Hardening.md`; otherwise proceed to final process-entry and bot-construction cleanup as a later approval-gated slice.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5 upload routing and Phase 6A through Phase 6J lifecycle slices are complete, merged, production-pushed, and locally validated; Phase 6J production smoke proved the cooperative restart path and left broader queue persistence hardening as optional follow-up before process-entry cleanup.

### Deferred Optimisation
- Area: `utils.py`, `bot_helpers.py`, `core/queue_lifecycle.py`, queue runtime state
- Type: refactor
- Description: Phase 6H separated queue lifecycle startup, but broader queue persistence hardening remains out of scope. `load_live_queue()` is synchronous while scheduling an async state apply when an event loop is running, and queue draining/state flush semantics are coupled to later shutdown behavior.
- Suggested Fix: Add a dedicated queue persistence hardening slice now that Phase 6J has proven the cooperative shutdown path. Make live queue load/apply explicitly awaitable where practical, preserve sync test compatibility or add a safe wrapper, verify atomic save behavior and stale metadata handling, and add restart/persistence tests for load-before-embed-refresh ordering and state flush after queue cancellation.
- Impact: medium
- Risk: medium
- Dependencies: Phase 6H lifecycle extraction, Phase 6I shutdown coordination, and Phase 6J graceful restart/shutdown operations are complete and production-pushed.

### Deferred Optimisation
- Area: `bot_helpers.py`, `utils.py`, `core/queue_lifecycle.py`, `upload_routes/fallback_queue_route.py`, queue runtime state
- Type: architecture
- Description: Phase 6K is intentionally limited to live queue persistence hardening. A fuller queue-domain redesign remains separate, including clearer ownership for queued message/job lifecycle, worker status transitions, display state, processing state, retry/drop semantics, and the boundary between fallback upload routing, `channel_queues`, and live queue UI state.
- Suggested Fix: After Phase 6K and final lifecycle cleanup are stable, scope a dedicated queue-domain redesign audit. Map queue state sources, worker lifecycle, status transitions, user-visible embed updates, failure modes, and restart behavior before proposing any code movement. Keep upload-route behavior unchanged unless a later approved task explicitly includes it.
- Impact: medium
- Risk: medium
- Dependencies: Phase 6K live queue persistence hardening should complete first; coordinate with any later process-entry/bot-construction cleanup.

### Deferred Optimisation
- Area: queue persistence model, SQL repo `C:\K98-bot-SQL-Server`
- Type: architecture
- Description: Live queue persistence remains file-backed through `QUEUE_CACHE_FILE`. SQL-backed queue persistence may eventually provide a stronger source of truth for queued work, in-flight state, and recovery after crashes, but it would require a separate schema and contract design rather than being folded into Phase 6K.
- Suggested Fix: If file-backed queue state proves insufficient after Phase 6K, scope a SQL-backed queue persistence design task. Validate table/procedure/index needs against `C:\K98-bot-SQL-Server`, define migration and rollback plans, preserve existing operator behavior, and add restart/recovery tests before any implementation.
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
