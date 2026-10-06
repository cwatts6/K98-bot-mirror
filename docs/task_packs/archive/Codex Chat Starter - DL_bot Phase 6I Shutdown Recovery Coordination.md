# Codex Chat Starter - DL_bot Phase 6I Shutdown Recovery Coordination

Status: complete. Phase 6I was delivered in PR 126
(`codex/dlbot-phase-6i-shutdown-recovery`), merged, and pushed to production.

Phase 6I added bot-side graceful teardown coordination before `bot.close()`, brief channel queue
drain handling including in-flight `queue.join()` work, live queue snapshot persistence, supervised
task cancellation ordering, shutdown heartbeat writing, usage tracker stop, and logging
quiesce/shutdown ordering. Production `/ops force_restart` smoke confirmed restart recovery and
startup continuity, but it did not provide a reliable in-process graceful shutdown log trail because
`/ops force_restart` remains the break-glass restart path.

Phase 6J was subsequently completed in PR 127 and proved the cooperative restart path in
production. Phase 6K was subsequently completed in PR 128 and hardened live queue persistence.
Phase 6L subsequently closed process-entry and bot-construction cleanup. This starter is retained
as historical context for the archived DL_bot programme.

Historical starter retained below.

## Copy/Paste Starter

Codex, continue Phase 6 of the DL_bot architecture optimisation programme with Phase 6I:
shutdown and recovery coordination.

Phase 6A, 6B, 6C, 6D, 6E, 6F, 6G, and 6H are complete:

- PR 117 (`codex/dlbot-phase-6-startup-lifecycle-1`) was merged and pushed to production.
- PR 119 (`codex/dlbot-phase-6b-runtime-services`) was merged and pushed to production.
- PR 120 (`codex/dlbot-phase-6c-usage-tracker`) was merged and pushed to production.
- PR 121 (`codex/dlbot-phase-6d-command-lifecycle`) was merged and pushed to production.
- PR 122 (`codex/dlbot-phase-6e-command-admin-tooling`) was merged and pushed to production.
- PR 123 (`codex/dlbot-phase-6f-event-rehydration`) was merged and pushed to production.
- PR 124 (`codex/dlbot-phase-6g-scheduler-lifecycle`) was merged and pushed to production.
- PR 125 (`codex/dlbot-phase-6h-queue-lifecycle`) was merged and pushed to production.
- `core/startup_lifecycle.py` provides `StartupPhase` and `run_startup_phases()`.
- `core/command_lifecycle.py` owns startup command signature/cache/sync mechanics and shared
  `/ops` command lifecycle mechanics.
- `core/event_rehydration_lifecycle.py` owns event cache, active reminder loading, tracked view
  rehydration scheduling, and pinned calendar view rehydration scheduling.
- `core/scheduler_lifecycle.py` owns scheduler/task registration ordering, event readiness
  gating, `TaskMonitor` registration, duplicate-prevention checks, and best-effort failure
  logging.
- `core/queue_lifecycle.py` owns queue worker registration, live queue recovery, best-effort queue
  embed refresh, queue cleanup startup, connection watchdog startup, ordering, logging, and
  `TaskMonitor` duplicate-prevention preservation.
- `bot_instance.py:on_ready()` delegates:
  - initial loop/console bootstrap through `ready_runtime_bootstrap`
  - runtime services/observability startup through `ready_runtime_services`
  - startup command signature/cache/sync through `ready_command_sync`
  - event cache/reminder/live-event readiness through `ready_event_cache_rehydration`
  - event-dependent scheduler tasks through `ready_event_scheduler_tasks`
  - long-running event cache refresh loop through `ready_event_cache_refresh_loop`
  - tracked view rehydration through `ready_view_rehydration`
  - Ark/MGE scheduler startup through `ready_domain_scheduler_tasks`
  - queue worker/live queue startup through `ready_queue_lifecycle`
  - pinned calendar rehydration through `ready_pinned_calendar_rehydration`
  - calendar scheduler startup through `ready_calendar_scheduler_tasks`
- Production smoke logs confirmed for Phase 6H:
  - `ready_queue_lifecycle` ran after `ready_domain_scheduler_tasks`
  - queue workers started for the configured monitored channels
  - live queue state loaded before live queue embed refresh
  - live queue embed refresh completed
  - queue cleanup started once
  - connection watchdog started once
  - `full_startup_sequence()` completed
  - reminder cleanup, pinned calendar rehydration, and calendar scheduler tasks continued normally
  - no startup phase failure, `on_ready()` critical exception, queue embed refresh failure,
    `queue_worker` monitor crash, `queue_cleanup` crash, or `connection_watchdog` crash was
    observed

This is review/scope first. Do not implement code changes until the Phase 6I scope, target
ownership model, and first PR-sized implementation plan have each been approved.

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
- `docs/task_packs/Codex Chat Starter - DL_bot Phase 6H Queue Worker Lifecycle.md`

## Phase 6I Objective

Separate and harden shutdown/recovery coordination while preserving current operator behavior,
restart safety, singleton/runtime file handling, queue state persistence, task supervision, and
logging shutdown order.

Explicit Phase 6I fix target:

- Handle cooperative cancellation, queue draining/state flush, and shutdown ordering.

The next cohesive slice after Phase 6H is the shutdown/recovery block currently spread across
`DL_bot.py`, `bot_instance.py`, `TaskMonitor`, queue worker helpers, singleton/runtime files, and
logging setup:

- signal/admin/watchdog shutdown entry points
- `on_graceful_shutdown()` and `_graceful_teardown()`
- `TaskMonitor` cancellation/listing/restart behavior during shutdown
- queue workers, queue cleanup loop, connection watchdog, and `QUEUE_CACHE_FILE` state flush
- shutdown marker and restart marker handling, including `LAST_SHUTDOWN_INFO`,
  `LAST_RESTART_INFO`, `RESTART_FLAG_PATH`, `EXIT_CODE_FILE`, and related runtime files
- singleton lock and PID cleanup behavior
- logging flush/quiesce/shutdown behavior
- recovery verification through startup logs and persisted state

Recommended target: keep process-entry behavior in place for this slice, but introduce or refine a
narrow lifecycle helper/boundary only if the audit proves it makes shutdown ordering and tests
clearer. Avoid a broad process-entry rewrite. Keep queue worker implementation logic in existing
modules unless the audit proves a small extraction is necessary for cooperative cancellation or
state flush.

## In Scope

- Audit the relationship between:
  - `DL_bot.py` signal handling and graceful shutdown helpers
  - `bot_instance.py:on_graceful_shutdown()`
  - `bot_instance.py:_graceful_teardown()`
  - `TaskMonitor` task listing, active flag, cancellation, and restart behavior
  - queue lifecycle tasks: `queue_worker:{cid}`, `queue_cleanup`, `connection_watchdog`
  - `queue_worker(cid)`, `queue_cleanup_loop`, `connection_watchdog(bot)`
  - shared queue state and locking through `utils.live_queue_lock`
  - `QUEUE_CACHE_FILE`, `save_live_queue()`, and live queue recovery expectations
  - shutdown/restart marker files such as `LAST_SHUTDOWN_INFO`, `LAST_RESTART_INFO`,
    `RESTART_FLAG_PATH`, `EXIT_CODE_FILE`, `SHUTDOWN_MARKER_FILE`, and `BOT_LOCK_PATH`
  - `logging_setup.flush_logs()`, `quiesce_logging()`, and `shutdown_logging()`
  - watchdog and bot-machine restart behavior
- Define the exact shutdown ordering that must be preserved or intentionally corrected.
- Decide whether shutdown coordination should be one helper/boundary or multiple smaller helpers.
- Preserve restart safety, idempotency, and duplicate-shutdown prevention.
- Preserve existing operator-facing restart/shutdown notifications unless explicitly approved.
- Add or update focused tests for cooperative task cancellation, queue state flush, shutdown marker
  writing, idempotency, and continued clean restart behavior where practical.
- Decide whether queue persistence hardening is required inside Phase 6I or should remain a
  separate follow-up slice after shutdown ordering is settled.
- Capture process-entry and broader bot-construction cleanup findings as Phase 6K work unless
  explicitly approved for this slice.

## Out Of Scope

- Broad `DL_bot.py` process-entry rewrite or bot construction cleanup.
- Upload-route behavior changes, including fallback queue routing behavior.
- Queue worker processing behavior changes beyond what is needed for cooperative cancellation,
  queue draining, or state flush.
- Scheduler ownership changes already completed in Phase 6G.
- Queue startup ownership changes already completed in Phase 6H.
- Event cache load/refresh ownership changes already completed in Phase 6F and 6G.
- Command lifecycle, command sync, command cache, slash-command renaming, grouping, or retirement.
- SQL/importer/workbook/Google Sheets/ProcConfig contract changes unless unexpectedly required by
  shutdown validation.
- Production promotion or bot-machine deployment without `k98-promotion-check`.

## Likely Files

Review:

- `DL_bot.py`
- `bot_instance.py`
- `core/startup_lifecycle.py`
- `core/scheduler_lifecycle.py`
- `core/queue_lifecycle.py`
- `bot_helpers.py`
- `utils.py`
- `constants.py`
- `logging_setup.py`
- `singleton_lock.py`
- `bot_startup_gate.py`
- `boot_safety.py`
- `startup_utils.py`
- `run_bot.py`
- `tests/test_singleton_lock_Version2.py`
- `tests/test_live_queue_persistence.py`
- `tests/test_utils_live_queue.py`
- `tests/test_queue_lifecycle.py`
- `tests/test_startup_lifecycle.py`
- `tests/test_process_utils.py`
- `tests/test_file_utils_lockinfo.py`
- `tests/test_file_utils.py`
- `tests/test_command_registration_smoke.py`

Likely modify after approval:

- `bot_instance.py`
- `DL_bot.py` only if the audit proves a narrow shutdown hook change is required
- one focused shutdown lifecycle helper if the audit proves a clean extraction
- focused shutdown/queue persistence tests
- `docs/reference/runbook_shutdown.md`
- `docs/reference/runbook_startup.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/DL_bot Startup Lifecycle - Phase 6 Audit Starter.md`

Do not create a broad process-entry or bot-construction module in Phase 6I.

## Step 1 Required Output

- Audit Summary
- Current Shutdown / Recovery Lifecycle Map
- Current Phase 6A-H Startup Lifecycle Boundary Map
- Proposed Phase 6I Ownership Model
- Shutdown Ordering And Idempotency Checklist
- TaskMonitor Cancellation And Duplicate-Prevention Map
- Queue Draining And State Flush Map
- Runtime State, Marker, Lock, And Persistence Map
- Logging Flush / Quiesce / Shutdown Map
- Ownership Problems And Refactor Triggers
- Recommended Phase 6I Implementation Scope
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
.\.venv\Scripts\python.exe -m pytest -q tests\test_startup_lifecycle.py tests\test_queue_lifecycle.py tests\test_live_queue_persistence.py tests\test_utils_live_queue.py tests\test_singleton_lock_Version2.py tests\test_process_utils.py tests\test_file_utils_lockinfo.py tests\test_file_utils.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security review should be run before PR handoff for code changes because Phase 6I touches
shutdown, file-backed runtime state, queue recovery, task cancellation, singleton locks, logging,
watchdog/restart behavior, and restart-sensitive persistence.

## Expected Smoke / Manual Verification

After implementation and deployment, manually verify:

- normal startup still shows all Phase 6A-H startup phases
- graceful shutdown or `/ops force_restart` writes expected restart/shutdown markers
- queue workers cancel cooperatively or drain according to the approved design
- live queue state is flushed before shutdown completes
- `QUEUE_CACHE_FILE` remains readable and startup can reload it
- singleton lock/PID state is cleaned or preserved according to existing watchdog expectations
- logs are flushed before logging shutdown/quiesce prevents late handler failures
- restart returns through the expected startup notification path
- repeated shutdown requests remain idempotent
- repeated `on_ready()` still skips startup work and no duplicate background tasks are observed

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

## Remaining Phase 6 Slices

Recommended order after Phase 6K:

1. Final process-entry and bot-construction cleanup.

The wider command-surface migration/renaming programme remains separate from Phase 6.

## Deferred Item Links

This starter continues the DL_bot startup/lifecycle deferred optimisation in
`docs/reference/deferred_optimisations.md` after Phase 6H completed queue worker/live queue
lifecycle extraction.

Carry forward, but do not implement unless separately approved:

- process-entry and bot-construction cleanup, completed in Phase 6L
- pinned calendar tracker persistence hardening in `event_calendar/pinned_embed.py`
