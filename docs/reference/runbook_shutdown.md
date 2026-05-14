# Shutdown Runbook

Purpose: describe graceful shutdown, state persistence, lock cleanup, and recovery checks.

## Shutdown Sequence

High-level flow:

1. Signal, admin command, or watchdog request starts shutdown.
2. Process-level guard prevents duplicate shutdown work.
3. Bot stops accepting new work.
4. Background tasks are cancelled cooperatively.
5. Runtime queues/state are flushed.
6. Logs are flushed.
7. External resources are closed.
8. Singleton locks and PID/marker files are cleared or updated.
9. Process exits with normal or restart code.

## Main Files

- `DL_bot.py` handles process-level startup/shutdown wiring and signals.
- `bot_instance.py` handles bot/client lifecycle and task supervision.
- `logging_setup.py` provides `flush_logs()` and `shutdown_logging()`.
- `singleton_lock.py` owns lock acquisition/release.
- `constants.py` defines lock, PID, shutdown, queue, and log paths.

## State To Preserve

Depending on active features, shutdown may need to preserve:

- `QUEUE_CACHE_FILE`
- `COMMAND_CACHE_FILE`
- `LAST_SHUTDOWN_INFO`
- event/reminder state files
- subscription reminder trackers
- event calendar cache/reminder state
- offload registry state

Use existing atomic file helpers where possible.

## Recovery After Hard Crash

1. Check `logs/crash.log`.
2. Check `logs/error_log.txt`.
3. Confirm no bot process is still running.
4. Inspect `BOT_LOCK_PATH` and watchdog lock state.
5. Preserve suspicious JSON state files before editing.
6. Start through the normal watchdog path.
7. Verify startup logs and admin notification.

## Checklist For Shutdown-Related Changes

- Shutdown remains idempotent.
- Tasks handle `asyncio.CancelledError` correctly.
- Blocking cleanup is offloaded or bounded.
- Logs are flushed before logging shutdown.
- Critical state is persisted atomically.
- Tests cover lock release, task cancellation, or state persistence where practical.
