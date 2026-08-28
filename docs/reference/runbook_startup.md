# Startup Runbook

Purpose: describe the bot startup sequence, guardrails, logging setup, and common failures.

## High-Level Startup Flow

1. `DL_bot.py` starts.
2. `logging_setup.py` initializes queue/file logging.
3. Environment and watchdog checks run.
4. Singleton lock and PID file are created.
5. The configured bot instance is imported.
6. Commands are registered locally.
7. Discord client starts.
8. `bot_instance.on_ready()` runs the full startup sequence.
   - `ready_runtime_bootstrap` installs the running-loop exception handler and final console
     handler cleanup.
   - `ready_runtime_services` starts heartbeat, health dashboard, offload monitor, image-show
     safety patching, legacy lock cleanup, the shared usage tracker and usage JSONL prune loop,
     daily summary, activity tracking, and server status channel loops.
   - `ready_command_sync` owns slash-command signature inventory, command-cache comparison,
     scoped command sync when signatures change, timeout telemetry, and loaded-command logging.
     Phase 6E also converged `/ops` command lifecycle admin tooling onto the same command
     lifecycle helpers while keeping Discord admin UX in `commands/admin_cmds.py`.
   - `ready_event_cache_rehydration` owns active reminder loading, event cache disk load,
     stale/empty cache refresh, and one-shot refresh scheduling.
   - `ready_event_scheduler_tasks` owns event-readiness-gated startup for live event embed
     updates, daily KVK overview updates, event reminders, reminder format refresh,
     live-event view rehydration, and event embed expiry.
   - `ready_event_cache_refresh_loop` starts the long-running event cache refresh loop at the
     existing point before tracked view rehydration.
   - `ready_view_rehydration` schedules tracked persistent view rehydration.
   - `ready_domain_scheduler_tasks` starts the Ark lifecycle scheduler, MGE cache warm, and MGE
     lifecycle scheduler.
   - `ready_queue_lifecycle` starts queue workers, awaits persisted live queue state load/apply,
     refreshes the live queue embed best-effort, and starts queue cleanup/watchdog tasks at the
     existing `full_startup_sequence()` point.
   - `ready_pinned_calendar_rehydration` schedules pinned calendar view rehydration at the
     existing later startup point after `full_startup_sequence()`.
   - `ready_calendar_scheduler_tasks` starts the daily pinned calendar refresh and calendar
     reminder loop after pinned calendar rehydration.
9. Caches, rehydration, background tasks, heartbeat, and admin notification start.

## Main Files

- `DL_bot.py` - process entrypoint, logging/env/watchdog guards, child singleton/PID setup,
  authoritative command registration, upload/message listener ownership, process signal wiring,
  and `bot.run()`.
- `bot_loader.py` - sole owner of bot singleton construction and Discord intents.
- `bot_instance.py` - lifecycle event owner for `on_ready()`, reconnect/disconnect events,
  interaction usage listening, named startup phases, task supervision, and bot-side graceful
  teardown.
- `bot_startup_gate.py`
- `boot_safety.py`
- `startup_utils.py`
- `logging_setup.py`
- `singleton_lock.py`
- `Commands.py`
- `core/command_lifecycle.py`
- `core/queue_lifecycle.py`
- `core/scheduler_lifecycle.py`

## Startup Guards

Important checks include:

- `WATCHDOG_RUN=1` for normal supervised startup
- `DISCORD_BOT_TOKEN` presence
- Windows virtualenv executable checks
- singleton lock acquisition
- PID file write
- Discord UI shadowing check
- smoke/import flags that suppress side effects during validation

## Logging

`logging_setup.py` configures:

- `logs/log.txt`
- `logs/error_log.txt`
- `logs/crash.log`
- `logs/telemetry_log.jsonl`
- `flush_logs()`
- `shutdown_logging()`

`LOG_TO_CONSOLE=1` adds console output for local debugging.

## Rehydration And Background Work

Startup may rehydrate or start:

- named lifecycle phases from `core/startup_lifecycle.py`
- command signature cache
- live queue state
- event views
- event calendar cache/runtime state
- subscription reminder tasks
- maintenance/health tasks
- heartbeat file updates

Phase 6A and 6B introduced named `on_ready()` startup phases for initial runtime bootstrap and
runtime services/observability startup. Phase 6C consolidated usage tracking onto the shared
`usage_tracker.py` singleton, with tracker startup and usage JSONL pruning owned by
`ready_runtime_services`. The unified tracker intentionally uses the previous command/decorator
cadence of a 5-second flush interval or 20-event batch size for command, component, metric, and
alert usage events. Phase 6D moved startup command signature/cache/sync handling behind
`ready_command_sync` and `core/command_lifecycle.py`. Phase 6E reused that lifecycle owner from
`/ops resync_commands`, `/ops validate_command_cache`, and `/ops show_command_versions`; production
smoke on 2026-05-28 confirmed those commands loaded, executed, flushed usage telemetry, and manual
scoped command resync completed successfully. Phase 6F completed in PR 123
(`codex/dlbot-phase-6f-event-rehydration`), was smoke tested cleanly, merged, and pushed to
production: event cache, reminder loading, tracked view rehydration, and pinned calendar
rehydration now have explicit startup lifecycle boundaries. Phase 6G completed in PR 124
(`codex/dlbot-phase-6g-scheduler-lifecycle`), was smoke tested cleanly, merged, and pushed to
production: scheduler and task-supervision startup now runs through `core/scheduler_lifecycle.py`
while preserving event readiness gating, task names, duplicate prevention, and the existing
Ark/MGE/calendar ordering. Review follow-up kept `refresh_event_cache_task` at its prior point
before tracked view rehydration via `ready_event_cache_refresh_loop` and changed Ark scheduler
registration failures to `logger.exception()` for traceback parity. Production smoke confirmed all
new scheduler phases, Ark/MGE scheduler ticks, `full_startup_sequence()`, reminder cleanup, pinned
calendar rehydration, daily pinned refresh, and calendar reminder loop startup with no startup
phase failure or `on_ready()` critical exception. Phase 6H completed in PR 125
(`codex/dlbot-phase-6h-queue-lifecycle`), was smoke tested cleanly, merged, and pushed to
production: queue worker/live queue startup now runs through `core/queue_lifecycle.py` and the
`ready_queue_lifecycle` phase while preserving the existing `full_startup_sequence()` ordering,
`TaskMonitor` duplicate prevention, live queue recovery, best-effort queue embed refresh, queue
cleanup startup, and connection watchdog startup. Production smoke confirmed the new queue phase
ran after `ready_domain_scheduler_tasks`, started workers for configured monitored channels, loaded
live queue state before embed refresh, started queue cleanup and connection watchdog once, and
allowed `full_startup_sequence()`, reminder cleanup, pinned calendar rehydration, and calendar
scheduler startup to continue normally. Phase 6I completed in PR 126
(`codex/dlbot-phase-6i-shutdown-recovery`), was merged and pushed to production: shutdown now
routes through bot-side graceful teardown before `bot.close()`, briefly drains configured
`channel_queues`, persists live queue state, cancels supervised tasks, and stops usage tracking.
Production `/ops force_restart` smoke confirmed restart recovery and startup continuity, but it did
not prove the in-process graceful shutdown log trail because `force_restart` remains a break-glass
path. Phase 6J completed in PR 127 (`codex/dlbot-phase-6j-graceful-restart-starter`), was merged,
pushed to production, and smoke tested successfully: `/ops graceful_restart` is now the preferred
safe restart path, `/ops force_restart` remains the emergency path, `/ops restart_bot` is retired,
restart marker writing and cooperative restart invocation are centralized in
`core/restart_operations.py`, and `graceful_shutdown.py` now uses a configurable cooperative
fallback timeout that defaults to 15 seconds. The 2026-05-28 smoke log confirmed queue drain, live
queue persistence, task cancellation, usage tracker stop, watchdog recovery, and startup return
through `ready_calendar_scheduler_tasks`. Phase 6K completed in PR 128
(`codex/dlbot-phase-6k-queue-persistence`), was merged, pushed to production, and smoke tested
successfully: `ready_queue_lifecycle` now awaits persisted live queue load/apply before best-effort
embed refresh, queue cache writes use the established atomic JSON helper, sync/offloaded queue
saves remain thread-safe without awaiting the main-loop lock, stale queue message metadata is
cleared/replaced during startup embed refresh, and later startup phases continue normally.
Phase 6L closed the startup/lifecycle programme by confirming the final ownership model:
`DL_bot.py` remains the process-entry and message/upload owner, `bot_loader.py` remains the bot
construction owner, and `bot_instance.py` remains the lifecycle owner. The Phase 6L code cleanup is
intentionally narrow: process PID publication and signal registration in `DL_bot.py` are wrapped in
named helpers without changing startup order, command registration, event registration, shutdown
semantics, or `bot.run()` flow.

When changing startup, verify restart safety and avoid duplicate task creation. Live queue startup
must keep the Phase 6K ordering contract: workers register first, persisted state is applied before
the embed refresh runs, and cleanup/watchdog tasks start after the best-effort refresh.

## Phase 6 Closure

The DL_bot upload-routing and startup/lifecycle optimisation programme is complete after Phase 6L.
Historical task packs and chat starters live under `docs/task_packs/archive/`. The current
post-Phase 6 programmes are the wider command-surface migration, queue-domain redesign, optional
SQL-backed queue persistence, disabled secondary command-surface cleanup, SQL deployment workflow,
and pinned calendar tracker atomic-write hardening; each needs its own scope and validation plan.

## Common Startup Failures

| Symptom | Check |
|---------|-------|
| exits immediately | `WATCHDOG_RUN`, `DISCORD_BOT_TOKEN`, venv path |
| duplicate process warning | `BOT_LOCK_PATH`, process list |
| no command sync | `GUILD_ID`, command cache, registration logs |
| no logs | `LOG_DIR`, permissions, `DISABLE_FILE_LOGGING`, smoke flags |
| rehydration fails | persisted JSON state, message/channel permissions |

## Validation

```powershell
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
python scripts/config_self_test.py
```
