# 🔻 Shutdown Runbook – Graceful Exit & State Persistence

File: `docs/runbook_shutdown.md`  
Audience: Developers & maintainers of the K98 Discord Bot  
Last Updated: 2025-10-19

---

Purpose
- Explain how the bot shuts down cleanly, what is persisted, and how to recover after a crash.
- Reference repository helpers and constants so operators can find artifacts and expected behavior.

One-line sequence
- Signal or admin command → idempotent shutdown guard → set is_closing → cancel TaskMonitor tasks → flush queues & logs → persist runtime state atomically → close external resources → clear locks → exit (or write restart exit code).

Entry points (repo)
- OS signals wired in DL_bot.py (SIGINT, SIGTERM, SIGBREAK on Windows).
- Admin-only command or watchdog triggers.
- Programmatic shutdown via bot_instance.on_graceful_shutdown / shutdown coroutine.

Shutdown contract (idempotent)
- DL_bot.py and bot_instance implement a single-run guard to avoid double-cancel and duplicated writes.
- Both sides cooperate: DL_bot.py handles process-level markers, locks and final logging shutdown; bot_instance handles in-memory persistence, TaskMonitor cancellation, usage flushes and client quiescing.

Step-by-step (repo-aware)

1) ID guard + optional EXIT marker
- Top-level guard ensures shutdown sequence runs once.
- DL_bot.py may write EXIT_CODE / EXIT marker early so watchdog can decide restart policy.

2) Stop accepting work
- bot_instance sets self.is_closing = True. Producers must check this flag and avoid enqueueing new jobs.

3) Cancel TaskMonitor tasks
- Call task_monitor.stop() / task_monitor.cancel_all() (repo names) to cancel periodic and background tasks.
- Await cancellation with a sensible per-task timeout.
- Ensure all tasks properly handle asyncio.CancelledError.

4) Flush logs & queues
- Call logging_setup.flush_logs() to ensure the logging queue is drained.
- Flush CSV and JSON writers, and call handler.flush() on file handlers.

5) Persist runtime state (atomic writes)
- Persist these artifacts:
  - QUEUE_CACHE_FILE — live queue state
  - REMINDER_TRACKING_FILE, DM_SCHEDULED_TRACKER_FILE
  - COMMAND_CACHE_FILE (if mutated during runtime)
  - LAST_SHUTDOWN_INFO (summary JSON)
- Use atomic writes: write to tmp, fsync, os.replace.

6) Close external resources
- Close DB pools and await closure.
- await aiohttp_session.close() (if used).
- Close any other connections or file descriptors.

7) Release singleton lock and write last-shutdown summary
- Write LAST_SHUTDOWN_INFO (constants.LAST_SHUTDOWN_INFO) with timestamp, reason, pending_jobs, and task summary.
- Remove BOT_LOCK_PATH as the last step.
- If the process crashed earlier, boot_safety will detect stale locks on next boot.

8) Stop QueueListener & exit
- After persistence and resource closure: call logging_setup.shutdown_logging() (idempotent), then exit with appropriate code (0 for normal, RESTART_EXIT_CODE to request restart).

Troubleshooting (repo-specific)
- Hangs: check tasks ignoring CancelledError and long blocking I/O.
- Corrupted JSON: ensure atomic writes (tmp+replace+fsync).
- Stale locks: remove BOT_LOCK_PATH manually if no process is running.
- Missing final logs: call logging_setup.flush_logs() before shutdown_logging().

Recovery steps after hard crash
1) Check LOG_DIR/crash.log and log.txt for cause.
2) Check BOT_LOCK_PATH and any WATCHDOG lock; remove stale locks if safe.
3) Rehydrate using the repo helpers:
   - load_event_cache(), rehydrate_live_event_views(), refresh_event_cache()
   - load QUEUE_CACHE_FILE and re-queue safe jobs after validating timestamps and uniqueness.
4) If rehydration fails, archive the persisted JSON files (add .broken.TIMESTAMP) and restart.

Appendix: helpers & constants to use
- logging_setup.flush_logs(), logging_setup.shutdown_logging()
- constants.QUEUE_CACHE_FILE, constants.COMMAND_CACHE_FILE, constants.LAST_SHUTDOWN_INFO, constants.BOT_LOCK_PATH, constants.RESTART_EXIT_CODE

Checklist before merging shutdown-related code
- Add unit/integration tests that simulate SIGTERM and assert persisted files and lock removal.
- Confirm that TaskMonitor tasks cancel under test harness and that logging queue drains fully.
