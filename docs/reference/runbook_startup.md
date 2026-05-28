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
   - `ready_queue_lifecycle` starts queue workers, loads persisted live queue state, refreshes the
     live queue embed best-effort, and starts queue cleanup/watchdog tasks at the existing
     `full_startup_sequence()` point.
   - `ready_pinned_calendar_rehydration` schedules pinned calendar view rehydration at the
     existing later startup point after `full_startup_sequence()`.
   - `ready_calendar_scheduler_tasks` starts the daily pinned calendar refresh and calendar
     reminder loop after pinned calendar rehydration.
9. Caches, rehydration, background tasks, heartbeat, and admin notification start.

## Main Files

- `DL_bot.py`
- `bot_instance.py`
- `bot_loader.py`
- `bot_startup_gate.py`
- `boot_safety.py`
- `startup_utils.py`
- `logging_setup.py`
- `singleton_lock.py`
- `Commands.py`
- `core/command_lifecycle.py`
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
phase failure or `on_ready()` critical exception. Phase 6H moved queue worker/live queue startup
into `core/queue_lifecycle.py` and the `ready_queue_lifecycle` phase while preserving the existing
`full_startup_sequence()` ordering. Remaining lifecycle cleanup continues with shutdown
coordination and final process-entry/bot-construction cleanup.

When changing startup, verify restart safety and avoid duplicate task creation.

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
