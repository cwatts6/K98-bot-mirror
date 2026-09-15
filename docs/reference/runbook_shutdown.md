# Shutdown Runbook

## Current status — S10D SQL merged; S10E scope next, 2026-09-15

SQL #87 is merged and locally pulled at `80353a6280e523f30c27e724f71e7b47dadadd16`.
Bot main/origin main remains `bf3eccf964601e2975dd86eefe96f7b0153be3bb`; production/main remains
`aa1821adbde9ccda47797caa83b5d5a9958bfce9`. **No changes have been pulled to the bot machine.**
S10D authoring, offline checks and Changes security review are complete; SQL installation and
provider/Discord execution are not established. S10C remains source/static SQL evidence too.
See [S10D closeout and exact carry-forward manifests](kvk_source_migration/s10d_closeout_and_s10e_handoff.md).

Next: **S10E Export Operator UX and Rollover, initial review/scope only**:
[task pack](../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md) and [starter](../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md).
The eventual authorized S10E Bot implementation PR MUST include every pending Bot document in
that closeout, this pack/starter and all required archive identities. Verify filename AND
previous_filename, or exact merged/content and absent-at-base proof. No standalone docs PR,
repository mixing, manufactured implementation or renewed predecessor/grouping approval.
Both SQL documents were delivered in #87; their new closeout edits stay in SQL for the next
actual authorized SQL implementation PR. S10E scope must assess any genuine SQL delta separately.

Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and every retained database/file.
S8A six scripts, S8B 50 cases/actual restore versus offline history, and S8C seven local checks
remain distinct; none is new live Discord or deployment evidence. Shutdown stops admission and
drains owned delivery; uncertainty retains claims. No lease-age/job-state release.
This documentation closeout authorizes no implementation, Git publication, SQL/provider/Discord
execution, real import/export, bot-machine action, deployment, activation, predecessor rerun or
new task. Earlier dated checkpoints are historical; the current closeout controls the next step.

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
- `bot_loader.py` owns bot singleton construction and is not part of shutdown coordination.
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

## Phase 6J Outcome

Phase 6J was completed in PR 127 (`codex/dlbot-phase-6j-graceful-restart-starter`), merged, pushed
to production, and smoke tested successfully. It makes the Phase 6I graceful teardown path directly
testable from normal operator tooling while keeping the existing emergency restart route.

Delivered operator model:

- `/ops graceful_restart` is the preferred safe restart path. It writes the restart marker and
  watchdog exit-code file through `core/restart_operations.py`, enters the bot-side graceful
  teardown path, drains queues briefly, persists live queue state, stops supervised tasks and usage
  tracking, flushes logs, then closes the bot so the watchdog restarts it. If `bot.close()` times
  out after markers are written, the restart helper forces process exit with the restart exit code
  so the watchdog is not left blocked waiting for a still-running child process.
- `/ops force_restart` remains the emergency break-glass path for stuck, looping, or unresponsive
  states.
- `/ops restart_bot` is retired and is no longer registered.
- `graceful_shutdown.py` now requests cooperative process teardown first and waits up to
  `GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS`, defaulting to `15`, before falling back to process kill.
  Invalid or non-positive timeout values fall back to `15` instead of aborting the helper at import
  time.
- Restart audit CSV writes are best-effort. Marker and exit-code writes remain the restart control
  path; a locked or unavailable restart log must not prevent teardown.
- Cooperative `bot.close()` is bounded so a Discord close stall does not leave the watchdog waiting
  indefinitely after restart markers have been written.
- Live queue shutdown persistence uses the explicit async live queue save helper and only reports
  success after the atomic JSON write completes.

Production `/ops graceful_restart` smoke on 2026-05-28 confirmed:

- command invocation and usage telemetry flush
- graceful teardown initiation
- channel queue drain/join handling before supervised task cancellation
- live queue persistence before cancellation
- reminder task registry cancellation
- usage tracker stop before disconnect
- watchdog restart and singleton lock reacquisition
- startup return through Phase 6 lifecycle logs, including `ready_runtime_bootstrap`,
  `ready_queue_lifecycle`, and `ready_calendar_scheduler_tasks`
- command inventory containing `/ops graceful_restart` and `/ops force_restart`, with
  `/ops restart_bot` absent

The smoke log did not include a literal `[SHUTDOWN] Logging quiesced` line. That is expected with
the current implementation: `bot_instance.quiesce_logging()` is intentionally silent and removes
console-like stream handlers while keeping queue/file logging alive. Treat the absence of that
exact line as acceptable when the surrounding shutdown and startup markers are clean and there are
no late logging handler failures.

## Phase 6K Outcome

Phase 6K was completed in PR 128 (`codex/dlbot-phase-6k-queue-persistence`), merged, pushed to
production, and smoke tested successfully. It hardened the file-backed live queue persistence model
without changing upload-route behavior or queue worker processing.

Delivered persistence and restart model:

- Startup awaits persisted live queue load/apply before best-effort live queue embed refresh.
- Live queue shutdown persistence uses the explicit async save helper and reports success only
  after the atomic JSON write completes.
- Sync/offloaded queue saves remain thread-safe by snapshotting without awaiting the Discord
  main-loop `live_queue_lock`.
- Stale persisted queue embed metadata is cleared/replaced during embed refresh while preserving
  startup continuity.
- Cooperative `bot.close()` timeout after restart markers are written forces process exit with the
  restart code, preventing the watchdog from waiting indefinitely on a still-running child.

Production `/ops graceful_restart` smoke on 2026-05-28 confirmed queue drain, live queue
persistence, task cancellation, usage tracker stop, watchdog restart, singleton lock reacquisition,
`ready_queue_lifecycle` startup return, stale queue embed metadata replacement, queue cleanup and
connection watchdog registration, and startup continuation through `ready_calendar_scheduler_tasks`.

## Phase 6L Outcome

Phase 6L closed the DL_bot startup/lifecycle separation programme. `DL_bot.py` remains the
process-entry and signal owner, `bot_loader.py` remains the construction owner, and
`bot_instance.py` remains the bot-side lifecycle and teardown owner. The Phase 6L runtime cleanup
only names the child PID write and process signal registration helpers in `DL_bot.py`; it does not
change shutdown marker writing, bot-side graceful teardown, `bot.close()` ordering, singleton lock
release, restart exit-code handling, queue drain, or live queue persistence.

Do not weaken `/ops force_restart`; it remains the recovery route when cooperative teardown cannot
be trusted. Future lifecycle-adjacent work should be scoped as new deferred optimisation tasks, not
as additional Phase 6 slices.

## S10B shared export shutdown boundary

Graceful teardown first stops new export admission. The worker checks the stop signal before discovery and each account admission. An already claimed delivery drains through request pacing, cooldown waits, full readback and confirmation; the admission stop event does not interrupt its requests or budget waits. Every request still checks durable ownership before and after reservation and records its completion. Cancellation waits for the offloaded thread, including repeated cancellation; it never detaches the thread to make a replacement eligible. Request budget waits occur outside SQL transactions.

A durable attempt precedes provider mutation. Interrupted/ambiguous attempts retain their resources, owner/fence and complete part records, with quarantine and an uncertain outcome. Even a process exit cannot establish remote absence. Authoritative reconciliation belongs to the later recovery workflow; do not release resources from job state alone, clear attempts, restart a blind write or delete retained files. A proved pre-attempt failure can release via the owned CAS and requires an explicit audited safe-retry request.
