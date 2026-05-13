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

- command signature cache
- live queue state
- event views
- event calendar cache/runtime state
- subscription reminder tasks
- maintenance/health tasks
- heartbeat file updates

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
