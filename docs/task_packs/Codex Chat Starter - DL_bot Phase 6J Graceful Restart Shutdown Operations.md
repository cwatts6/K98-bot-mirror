# Codex Chat Starter - DL_bot Phase 6J Graceful Restart Shutdown Operations

Status: complete. Phase 6J was delivered in PR 127
(`codex/dlbot-phase-6j-graceful-restart-starter`), merged, pushed to production, and smoke tested
successfully on 2026-05-28.

Phase 6J added `/ops graceful_restart`, retired `/ops restart_bot`, preserved `/ops force_restart`
as the emergency path, centralized restart marker writing/cooperative invocation in
`core/restart_operations.py`, and updated `graceful_shutdown.py` to request cooperative teardown
first with a configurable fallback timeout defaulting to 15 seconds.

Use `docs/task_packs/Codex Chat Starter - DL_bot Phase 6K Queue Persistence Hardening.md` for the
next optional Phase 6 slice, or continue to final process-entry/bot-construction cleanup if that
queue hardening slice is explicitly skipped.

Historical starter content follows for audit context.

## Copy/Paste Starter

Codex, continue Phase 6 of the DL_bot architecture optimisation programme with Phase 6J:
graceful restart and shutdown operations.

Phase 6A through Phase 6I are complete:

- PR 117 (`codex/dlbot-phase-6-startup-lifecycle-1`) was merged and pushed to production.
- PR 119 (`codex/dlbot-phase-6b-runtime-services`) was merged and pushed to production.
- PR 120 (`codex/dlbot-phase-6c-usage-tracker`) was merged and pushed to production.
- PR 121 (`codex/dlbot-phase-6d-command-lifecycle`) was merged and pushed to production.
- PR 122 (`codex/dlbot-phase-6e-command-admin-tooling`) was merged and pushed to production.
- PR 123 (`codex/dlbot-phase-6f-event-rehydration`) was merged and pushed to production.
- PR 124 (`codex/dlbot-phase-6g-scheduler-lifecycle`) was merged and pushed to production.
- PR 125 (`codex/dlbot-phase-6h-queue-lifecycle`) was merged and pushed to production.
- PR 126 (`codex/dlbot-phase-6i-shutdown-recovery`) was merged and pushed to production.
- `bot_instance.py:on_ready()` delegates startup to the Phase 6 lifecycle boundaries for runtime
  services, command sync, event rehydration, scheduler registration, queue lifecycle, pinned
  calendar rehydration, and calendar scheduler tasks.
- Phase 6I routed `DL_bot.py` signal shutdown through bot-side graceful teardown before
  `bot.close()`.
- Phase 6I waits briefly for configured `channel_queues`, including in-flight `queue.join()` work,
  before supervised task cancellation.
- Phase 6I snapshots and persists current live queue state before teardown continues.
- Phase 6I preserves restart/shutdown markers, shutdown heartbeat, `TaskMonitor` shutdown ordering,
  usage tracker stop, logging quiesce, and logging shutdown behavior.

Phase 6I production smoke note:

- `/ops force_restart` confirmed restart recovery and normal Phase 6A-I startup continuity.
- `/ops force_restart` did not produce a reliable in-process graceful shutdown log trail because it
  remains the break-glass restart path for stuck queues, looping workers, or other unhealthy bot
  states.
- Phase 6I is closed with the residual risk that some shutdown coordination may need rework after a
  cooperative restart/shutdown path can categorically smoke-test the new behavior.

This is review/scope first. Do not implement code changes until the Phase 6J scope, target
operator model, and first PR-sized implementation plan have each been approved.

Before implementation, read and follow:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/deferred_optimisations.md`
- `docs/reference/runbook_startup.md`
- `docs/reference/runbook_shutdown.md`
- `docs/reference/singleton_lock.md`
- `docs/reference/runbook_diagnostics.md`
- `docs/task_packs/DL_bot Startup Lifecycle - Phase 6 Audit Starter.md`
- `docs/task_packs/Codex Chat Starter - DL_bot Phase 6I Shutdown Recovery Coordination.md`

## Phase 6J Objective

Add an operator-facing cooperative restart/shutdown path that proves the Phase 6I graceful teardown
contract in production while preserving the existing break-glass restart behavior.

Explicit Phase 6J targets:

- Add `/ops graceful_restart` as the normal cooperative restart path.
- Preserve `/ops force_restart` as the emergency path for stuck, looping, or unresponsive bot states.
- Remove `/ops restart_bot` instead of keeping it as an alias, leaving one preferred safe path and
  one break-glass path.
- Review and update `graceful_shutdown.py` so weekly bot-machine restarts first request cooperative
  in-process teardown with a configurable timeout defaulting to 15 seconds, then fall back to
  external process termination.
- Produce a clear smoke-test log trail for queue drain, live queue persistence, supervised task
  cancellation, shutdown markers, logging shutdown, watchdog recovery, and startup return.

## In Scope

- Audit the current relationship between:
  - `/ops force_restart`
  - retired `/ops restart_bot` behavior
  - any admin restart buttons or shared command lifecycle helpers
  - `DL_bot.py` signal handling
  - `bot_instance.py:on_graceful_shutdown()`
  - `bot_instance.py:_graceful_teardown()` and related wrappers
  - `graceful_shutdown.py`
  - `run_bot.py` watchdog/restart behavior
  - restart/shutdown marker files, including `RESTART_FLAG_PATH`, `EXIT_CODE_FILE`,
    `LAST_RESTART_INFO`, `LAST_SHUTDOWN_INFO`, `SHUTDOWN_MARKER_FILE`, and `BOT_LOCK_PATH`
  - `TaskMonitor` cancellation and duplicate-prevention behavior
  - queue workers, `channel_queues`, `live_queue`, `QUEUE_CACHE_FILE`, and `save_live_queue()`
  - logging flush, quiesce, and shutdown ordering
- Define operator semantics for `/ops graceful_restart` versus `/ops force_restart`.
- Remove `/ops restart_bot`; do not route it as a compatibility alias.
- Add or refine a narrow helper only if it keeps marker writing, teardown invocation, timeout
  fallback, or command tests clear.
- Keep `/ops force_restart` available for recovery when graceful teardown cannot be trusted.
- Update `graceful_shutdown.py` to prefer cooperative shutdown/restart with bounded fallback.
- Add focused tests for command routing, graceful teardown invocation, force fallback preservation,
  marker handling, and timeout/fallback behavior where practical.
- Update runbooks, deferred optimisation docs, and task-pack references.
- Capture any process-entry, bot construction, or queue persistence hardening findings as later
  slices unless directly required for the cooperative restart path.

## Out Of Scope

- Broad `DL_bot.py` process-entry rewrite or bot construction cleanup.
- Removing or weakening `/ops force_restart`.
- Upload-route behavior changes, including fallback queue routing behavior.
- Queue worker processing behavior changes beyond what is required to prove graceful restart/shutdown.
- Full queue persistence hardening unless the audit proves it is required for Phase 6J.
- Scheduler ownership changes already completed in Phase 6G.
- Queue startup ownership changes already completed in Phase 6H.
- Shutdown coordination already completed in Phase 6I except where Phase 6J smoke testing proves a
  defect.
- SQL/importer/workbook/Google Sheets/ProcConfig contract changes unless unexpectedly required by
  validation.
- Production promotion or bot-machine deployment without `k98-promotion-check`.

## Likely Files

Review:

- `commands/admin_cmds.py`
- `core/restart_operations.py`
- `core/command_lifecycle.py`
- `bot_instance.py`
- `DL_bot.py`
- `graceful_shutdown.py`
- `run_bot.py`
- `constants.py`
- `logging_setup.py`
- `singleton_lock.py`
- `bot_startup_gate.py`
- `boot_safety.py`
- `startup_utils.py`
- `bot_helpers.py`
- `utils.py`
- `tests/test_startup_lifecycle.py`
- `tests/test_queue_lifecycle.py`
- `tests/test_live_queue_persistence.py`
- `tests/test_utils_live_queue.py`
- `tests/test_singleton_lock_Version2.py`
- `tests/test_process_utils.py`
- `tests/test_file_utils_lockinfo.py`
- `tests/test_file_utils.py`
- `tests/test_command_registration_smoke.py`

Likely modify after approval:

- `commands/admin_cmds.py`
- one narrow restart/shutdown helper
- `bot_instance.py`
- `graceful_shutdown.py`
- `DL_bot.py` only if the audit proves a narrow shutdown hook change is required
- one narrow restart/shutdown helper only if the audit proves it is clearer than local wiring
- focused command, shutdown, queue persistence, or process utility tests
- `docs/reference/runbook_shutdown.md`
- `docs/reference/runbook_startup.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/DL_bot Startup Lifecycle - Phase 6 Audit Starter.md`

Do not create a broad process-entry or bot-construction module in Phase 6J.

## Step 1 Required Output

- Audit Summary
- Current Restart And Shutdown Command Map
- Current `graceful_shutdown.py` Machine Restart Map
- Phase 6I Shutdown Boundary Map
- Proposed Phase 6J Operator Model
- `/ops graceful_restart` Versus `/ops force_restart` Semantics
- Shutdown Marker, Restart Marker, Exit Code, Lock, And Watchdog Map
- Queue Drain And Live Queue Persistence Smoke Map
- TaskMonitor Cancellation And Timeout/Fallback Map
- Logging Flush / Quiesce / Shutdown Smoke Map
- Ownership Problems And Refactor Triggers
- Recommended Phase 6J Implementation Scope
- Test And Validation Strategy
- Deferred Optimisation Findings
- Approval Questions
- Explicit Stop Point

## Audit / Design-Only Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

## Likely Implementation Validation After Approval

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_startup_lifecycle.py tests\test_queue_lifecycle.py tests\test_live_queue_persistence.py tests\test_utils_live_queue.py tests\test_singleton_lock_Version2.py tests\test_process_utils.py tests\test_file_utils_lockinfo.py tests\test_file_utils.py tests\test_command_registration_smoke.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security review should be run before PR handoff for code changes because Phase 6J touches
Discord admin commands, restart-sensitive persistence, file-backed runtime state, process shutdown,
watchdog behavior, queue draining, and logging shutdown.

## Expected Smoke / Manual Verification

After implementation and deployment, manually verify:

- `/ops graceful_restart` writes the expected restart marker and enters the bot-side graceful
  teardown path.
- `/ops restart_bot` is no longer registered.
- shutdown logs show queue drain/join handling before supervised task cancellation.
- live queue state is persisted before shutdown completes.
- usage tracking is stopped and flushed before process exit.
- logging is flushed before quiesce/shutdown prevents late handler failures.
- watchdog restarts the bot and startup returns through the expected Phase 6A-I phase logs.
- repeated `/ops graceful_restart` requests remain idempotent.
- `/ops force_restart` remains available and suitable for stuck or looping states.
- `graceful_shutdown.py` weekly machine restart flow requests cooperative teardown first and falls
  back within the approved timeout if the bot is unresponsive.

The graceful restart smoke test should show logs similar to:

```text
[COMMAND] /graceful_restart invoked
[SHUTDOWN] Graceful teardown initiated
[SHUTDOWN] Waiting for channel queues to drain
[SHUTDOWN] Live queue state persisted
[MONITOR] Stop requested
[SHUTDOWN] Usage tracker stopped
[STARTUP] phase started: ready_runtime_bootstrap
[STARTUP] phase completed: ready_calendar_scheduler_tasks
```

The literal `[SHUTDOWN] Logging quiesced` line was an aspirational smoke marker in the original
starter. It is not emitted by the delivered implementation because `quiesce_logging()` is silent;
use the absence of late logging handler failures plus clean watchdog/startup return as the current
logging quiesce/shutdown signal.

The smoke test should not show:

```text
[CRITICAL] Exception during on_ready
[STARTUP] phase failed
[SHUTDOWN] on_graceful_shutdown failed
[SHUTDOWN] Failed writing shutdown heartbeat
[QUEUE] Failed to save
[MONITOR] Task queue_worker
[MONITOR] Task queue_cleanup crashed
[MONITOR] Task connection_watchdog crashed
```

Known best-effort warnings may be acceptable only when intentionally induced or otherwise
understood, and only when shutdown/restart still continues cleanly.

## Phase 6J Smoke Outcome

Production `/ops graceful_restart` smoke confirmed the intended path:

- command invocation and usage telemetry flush
- graceful teardown initiation
- channel queue drain/join handling before supervised task cancellation
- live queue persistence before cancellation
- reminder task registry cancellation
- usage tracker stop before disconnect
- watchdog restart and startup return through Phase 6 lifecycle phases
- `/ops graceful_restart` and `/ops force_restart` present in command inventory
- `/ops restart_bot` absent from command inventory

The smoke log did not include a literal `[SHUTDOWN] Logging quiesced` line. This is expected: the
current `bot_instance.quiesce_logging()` helper is intentionally silent and removes console-like
stream handlers while retaining queue/file logging until final shutdown. Treat the missing literal
line as acceptable when the surrounding shutdown/startup markers are clean and no late logging
handler failures appear.

## Remaining Phase 6 Slices

Recommended order after Phase 6J:

1. Optional Phase 6K queue persistence hardening:
   - make live queue load/apply semantics clearer and explicitly awaitable where practical
   - verify atomic save behavior and stale metadata handling
   - add restart/persistence tests for load-before-embed-refresh ordering and shutdown state flush
2. Final process-entry and bot-construction cleanup:
   - audit `DL_bot.py`, `bot_loader.py`, and `bot_instance.py` ownership
   - keep upload routing and command-surface migration out of scope
   - proceed only after separate review/scope approval

The wider command-surface migration/renaming programme remains separate from Phase 6.

## Deferred Item Links

This starter continues the DL_bot startup/lifecycle deferred optimisation in
`docs/reference/deferred_optimisations.md` after Phase 6I completed shutdown and recovery
coordination with residual graceful smoke-test risk.

Carry forward, but do not implement unless separately approved:

- full queue persistence hardening as the next optional Phase 6 slice
- process-entry and bot-construction cleanup after queue persistence hardening, or next if the
  queue slice is skipped
- pinned calendar tracker persistence hardening in `event_calendar/pinned_embed.py`
