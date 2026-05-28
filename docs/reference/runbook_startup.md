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
`ready_command_sync` and `core/command_lifecycle.py`. Remaining lifecycle cleanup after that
starts with command lifecycle admin tooling convergence, then continues into rehydration and
scheduler boundaries, queue worker lifecycle, and shutdown coordination.

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
