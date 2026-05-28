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

## Phase 6I Outcome

Phase 6I was completed in PR 126 (`codex/dlbot-phase-6i-shutdown-recovery`), merged, and pushed
to production. It routes signal shutdown through bot-side graceful teardown before `bot.close()`,
briefly waits for configured `channel_queues` including in-flight `queue.join()` work, persists
`QUEUE_CACHE_FILE` with `save_live_queue()`, then cancels supervised `TaskMonitor` tasks and stops
usage tracking.

Production `/ops force_restart` smoke confirmed restart recovery and normal Phase 6A-H startup
continuation, but it did not provide a reliable in-process graceful shutdown log trail because
`force_restart` remains a break-glass restart path. Phase 6I is therefore closed with residual
smoke risk: the in-process teardown path may need rework if Phase 6J exposes an issue while adding
a cooperative smoke-testable restart path.

Expected Phase 6I shutdown log markers when the in-process graceful path is exercised:

- `[SHUTDOWN] Graceful teardown initiated.`
- `[SHUTDOWN] Channel queues have no pending items; waiting up to ... for any in-flight queue work to finish.`
- `[SHUTDOWN] Draining ... queued message(s) across ... channel queue(s) for up to ...`
- `[SHUTDOWN] Channel queues drained before task cancellation.`
- `[SHUTDOWN] Live queue state persisted.`
- `[MONITOR] Stop requested; tasks cancelled where applicable.`
- `[SHUTDOWN] Usage tracker stopped.`

## Phase 6J Focus

Phase 6J should make the Phase 6I shutdown path categorically smoke-testable without weakening
the current break-glass restart behavior.

Approved operator model:

- `/ops graceful_restart` is the preferred safe restart path. It writes the restart marker and
  watchdog exit-code file, enters the bot-side graceful teardown path, drains queues briefly,
  persists live queue state, stops supervised tasks and usage tracking, flushes logs, then closes
  the bot so the watchdog restarts it.
- `/ops force_restart` remains the emergency break-glass path for stuck, looping, or unresponsive
  states.
- The old `/ops restart_bot` path is retired instead of kept as a compatibility alias.
- `graceful_shutdown.py` should request cooperative process teardown first and wait up to
  `GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS` seconds, defaulting to `15`, before falling back to process
  kill.

Queue persistence hardening and process-entry cleanup remain follow-up slices unless Phase 6J
smoke testing proves they are required for safe cooperative restart behavior.
