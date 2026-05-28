# Codex Chat Starter - DL_bot Phase 6H Queue Worker Lifecycle

Use this starter to continue Phase 6 after Phase 6G scheduler/task-supervision startup was
merged, smoke-tested, pushed to production, and marked complete.

Status: implementation approved and in progress. The approved ownership model uses
`core/queue_lifecycle.py` and the `ready_queue_lifecycle` phase for queue worker registration,
live queue recovery, best-effort queue embed refresh, queue cleanup startup, connection watchdog
startup, ordering, logging, and `TaskMonitor` duplicate-prevention preservation.

Follow-up note: queue persistence hardening is intentionally not part of the Phase 6H lifecycle
extraction. Track it as an optional slice after Phase 6I, or include it in Phase 6I only if
shutdown work requires awaitable load/apply semantics or explicit queue state flush changes.
Phase 6I should fix cooperative cancellation, queue draining/state flush, and shutdown ordering.

## Copy/Paste Starter

Codex, continue Phase 6 of the DL_bot architecture optimisation programme with Phase 6H:
queue worker and live queue lifecycle.

Phase 6A, 6B, 6C, 6D, 6E, 6F, and 6G are complete:

- PR 117 (`codex/dlbot-phase-6-startup-lifecycle-1`) was merged and pushed to production.
- PR 119 (`codex/dlbot-phase-6b-runtime-services`) was merged and pushed to production.
- PR 120 (`codex/dlbot-phase-6c-usage-tracker`) was merged and pushed to production.
- PR 121 (`codex/dlbot-phase-6d-command-lifecycle`) was merged and pushed to production.
- PR 122 (`codex/dlbot-phase-6e-command-admin-tooling`) was merged and pushed to production.
- PR 123 (`codex/dlbot-phase-6f-event-rehydration`) was merged and pushed to production.
- PR 124 (`codex/dlbot-phase-6g-scheduler-lifecycle`) was merged and pushed to production.
- `core/startup_lifecycle.py` provides `StartupPhase` and `run_startup_phases()`.
- `core/command_lifecycle.py` owns startup command signature/cache/sync mechanics and shared
  `/ops` command lifecycle mechanics.
- `core/event_rehydration_lifecycle.py` owns event cache, active reminder loading, tracked view
  rehydration scheduling, and pinned calendar view rehydration scheduling.
- `core/scheduler_lifecycle.py` owns scheduler/task registration ordering, event readiness
  gating, `TaskMonitor` registration, duplicate-prevention checks, and best-effort failure
  logging.
- `bot_instance.py:on_ready()` delegates:
  - initial loop/console bootstrap through `ready_runtime_bootstrap`
  - runtime services/observability startup through `ready_runtime_services`
  - startup command signature/cache/sync through `ready_command_sync`
  - event cache/reminder/live-event readiness through `ready_event_cache_rehydration`
  - event-dependent scheduler tasks through `ready_event_scheduler_tasks`
  - long-running event cache refresh loop through `ready_event_cache_refresh_loop`
  - tracked view rehydration through `ready_view_rehydration`
  - Ark/MGE scheduler startup through `ready_domain_scheduler_tasks`
  - pinned calendar rehydration through `ready_pinned_calendar_rehydration`
  - calendar scheduler startup through `ready_calendar_scheduler_tasks`
- Production smoke logs confirmed for Phase 6G:
  - all new scheduler lifecycle phases ran in the expected order
  - event-dependent scheduler tasks started after event readiness
  - `refresh_event_cache_task` was armed before tracked view rehydration
  - Ark scheduler started and ticked
  - MGE cache warm completed and MGE scheduler ticked
  - `full_startup_sequence()` completed
  - reminder cleanup started
  - pinned calendar rehydration completed
  - daily pinned calendar refresh started
  - calendar reminder loop armed
  - no startup phase failure, `on_ready()` critical exception, scheduler registration failure,
    pinned-calendar scheduling failure, or calendar reminder loop failure was observed

This is review/scope first. Do not implement code changes until the Phase 6H scope, target
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
- `docs/task_packs/Codex Chat Starter - DL_bot Phase 6G Scheduler Task Supervision Boundary.md`

## Phase 6H Objective

Separate queue worker and live queue lifecycle responsibilities from `bot_instance.py:on_ready()`
and `full_startup_sequence()` while preserving worker startup order, live queue recovery, queue
embed refresh behavior, restart safety, and duplicate-task prevention.

The next cohesive slice after Phase 6G is the queue/live-queue block currently inside
`full_startup_sequence()`:

- queue worker startup for each `CHANNEL_IDS` entry through `queue_worker(cid)`
- `TaskMonitor.create(f"queue_worker:{cid}", ...)` task names and duplicate prevention behavior
- live queue recovery through `load_live_queue()`
- live queue embed refresh through `update_live_queue_embed(bot, NOTIFY_CHANNEL_ID)`
- queue cleanup startup through `queue_cleanup_loop`
- connection watchdog startup through `connection_watchdog(bot)`
- relationship to fallback upload queueing in `upload_routes/fallback_queue_route.py`
- shared queue state and locking through `utils.live_queue_lock`
- queue runtime state paths such as `QUEUE_CACHE_FILE`

Recommended target: keep a non-Discord lifecycle helper in `core/` or a narrowly scoped startup
module responsible for ordering, idempotency, logging, `TaskMonitor` registration, live queue
recovery outcome reporting, and best-effort queue embed refresh. Keep queue worker implementation
logic in existing modules such as `bot_helpers.py`, `utils.py`, and upload route modules unless
the audit proves a small extraction is necessary.

## In Scope

- Audit the relationship between:
  - `bot_instance.py:on_ready()`
  - `full_startup_sequence()`
  - `TaskMonitor.create()` and task names for `queue_worker:{cid}`, `queue_cleanup`, and
    `connection_watchdog`
  - `CHANNEL_IDS`
  - `queue_worker(cid)`
  - `queue_cleanup_loop`
  - `connection_watchdog(bot)`
  - `load_live_queue()`
  - `update_live_queue_embed(bot, NOTIFY_CHANNEL_ID)`
  - `utils.live_queue_lock`
  - `upload_routes/fallback_queue_route.py`
  - `QUEUE_CACHE_FILE` and related live queue persistence constants
- Define the exact startup ordering that must be preserved.
- Decide whether queue worker registration, live queue recovery, and queue cleanup/watchdog should
  be one named startup phase or split into smaller phases.
- Preserve restart safety and duplicate-task prevention.
- Preserve best-effort behavior for queue embed refresh failures.
- Add or update focused tests for worker registration, skipped duplicate registration where
  practical, live queue load/update ordering, best-effort embed refresh failure logging, and
  continued startup behavior.
- Capture shutdown/cancellation, process-entry, and broader queue persistence hardening findings
  as later work unless explicitly approved for this slice.

## Out Of Scope

- Shutdown redesign, signal handling, singleton/PID cleanup, logging shutdown order, or
  cooperative cancellation changes.
- `DL_bot.py` process-entry changes.
- Upload-route behavior changes, including fallback queue routing behavior.
- Scheduler ownership changes already completed in Phase 6G.
- Event cache load/refresh ownership changes already completed in Phase 6F and 6G.
- Command lifecycle, command sync, command cache, slash-command renaming, grouping, or retirement.
- SQL/importer/workbook/Google Sheets/ProcConfig contract changes unless unexpectedly required by
  queue validation.
- Production promotion or bot-machine deployment without `k98-promotion-check`.

## Likely Files

Review:

- `bot_instance.py`
- `core/startup_lifecycle.py`
- `core/scheduler_lifecycle.py`
- `bot_helpers.py`
- `utils.py`
- `upload_routes/fallback_queue_route.py`
- `constants.py`
- `tests/test_live_queue_persistence.py`
- `tests/test_utils_live_queue.py`
- `tests/test_fallback_queue_route.py`
- `tests/test_startup_lifecycle.py`
- `tests/test_command_registration_smoke.py`

Likely modify after approval:

- `bot_instance.py`
- one focused lifecycle helper module if the audit proves a clean extraction
- focused queue/startup lifecycle tests
- `docs/reference/runbook_startup.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/DL_bot Startup Lifecycle - Phase 6 Audit Starter.md`

Do not create a broad lifecycle orchestration module that also owns shutdown or process entry in
Phase 6H.

## Step 1 Required Output

- Audit Summary
- Current Queue Worker / Live Queue Lifecycle Map
- Current Phase 6A-G Startup Lifecycle Boundary Map
- Proposed Phase 6H Ownership Model
- Startup Ordering And Idempotency Checklist
- TaskMonitor Key And Duplicate Prevention Map
- Runtime State And Persistence Map
- Ownership Problems And Refactor Triggers
- Recommended Phase 6H Implementation Scope
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
.\.venv\Scripts\python.exe -m pytest -q tests\test_startup_lifecycle.py tests\test_live_queue_persistence.py tests\test_utils_live_queue.py tests\test_fallback_queue_route.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security review should be run before PR handoff for code changes because Phase 6H touches
Discord-facing upload queue processing, file-backed runtime state, restart-sensitive queue
recovery, and duplicate worker prevention.

## Expected Smoke / Manual Verification

After implementation and deployment, manually verify:

- normal startup still shows all Phase 6A-G startup phases
- new queue worker/live queue phase logs appear in the expected order
- queue workers start for each monitored channel in `CHANNEL_IDS`
- live queue state loads before the live queue embed refresh
- live queue embed refresh still runs best-effort and does not block later startup on failure
- queue cleanup starts once
- connection watchdog starts once
- `full_startup_sequence()` still sends startup notification and completes
- repeated `on_ready()` still skips startup work and no duplicate `queue_worker:{cid}`,
  `queue_cleanup`, or `connection_watchdog` background tasks are observed

The smoke test should not show:

```text
[STARTUP] phase failed
[CRITICAL] Exception during on_ready
Failed to update queue embed
[MONITOR] Task queue_worker
[MONITOR] Task queue_cleanup crashed
[MONITOR] Task connection_watchdog crashed
```

Known best-effort live queue embed warnings may be acceptable only when later startup still
continues and the failure is intentionally induced or otherwise understood.

## Remaining Phase 6 Slices

Recommended order after Phase 6H:

1. Phase 6I shutdown and recovery coordination, including cooperative cancellation, queue
   draining/state flush, and shutdown ordering.
2. Optional queue persistence hardening slice after Phase 6I, unless Phase 6I requires it directly.
3. Phase 6J process-entry and bot-construction cleanup.

The wider command-surface migration/renaming programme remains separate from Phase 6.

## Deferred Item Links

This starter continues the DL_bot startup/lifecycle deferred optimisation in
`docs/reference/deferred_optimisations.md` after Phase 6G completed scheduler/task-supervision
boundary extraction.

Carry forward, but do not implement unless separately approved:

- shutdown and task cancellation coordination
- process-entry and bot-construction cleanup
- queue persistence hardening after Phase 6I, unless required directly by Phase 6I shutdown work
- pinned calendar tracker persistence hardening in `event_calendar/pinned_embed.py`
