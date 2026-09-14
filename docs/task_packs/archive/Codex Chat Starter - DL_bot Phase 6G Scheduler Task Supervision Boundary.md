# Codex Chat Starter - DL_bot Phase 6G Scheduler Task Supervision Boundary

Status: complete. PR 124 (`codex/dlbot-phase-6g-scheduler-lifecycle`) was merged,
smoke-tested, and pushed to production on 2026-05-28. This starter is retained as historical
context for Phase 6G.

Use `docs/task_packs/Codex Chat Starter - DL_bot Phase 6H Queue Worker Lifecycle.md` for the next
Phase 6 slice.

Delivered outcome:

- `core/scheduler_lifecycle.py` now owns scheduler/task registration ordering, readiness gating,
  `TaskMonitor` registration, duplicate-prevention checks, and best-effort failure logging.
- `bot_instance.py:on_ready()` delegates event-dependent schedulers through
  `ready_event_scheduler_tasks`, the long-running event cache refresh loop through
  `ready_event_cache_refresh_loop`, Ark/MGE schedulers through `ready_domain_scheduler_tasks`, and
  calendar schedulers through `ready_calendar_scheduler_tasks`.
- Review feedback restored `refresh_event_cache_task.start()` to its prior ordering before tracked
  view rehydration by giving it the dedicated `ready_event_cache_refresh_loop` phase.
- Review feedback also changed Ark scheduler registration failure logging to `logger.exception()`
  so it retains tracebacks like the other scheduler registration paths.
- Production smoke confirmed all new scheduler lifecycle phases ran in order, event readiness
  gating succeeded, event-dependent schedulers started, the event cache refresh loop was armed
  before tracked view rehydration, Ark and MGE schedulers ticked, `full_startup_sequence()`
  completed, reminder cleanup started, pinned calendar rehydration completed, daily pinned
  calendar refresh started, and the calendar reminder loop armed.
- No startup phase failure, `on_ready()` critical exception, scheduler registration failure,
  pinned-calendar scheduling failure, or calendar reminder loop failure was observed.

## Copy/Paste Starter

Codex, continue Phase 6 of the DL_bot architecture optimisation programme with Phase 6G:
scheduler and task-supervision boundary.

Phase 6A, 6B, 6C, 6D, 6E, and 6F are complete:

- PR 117 (`codex/dlbot-phase-6-startup-lifecycle-1`) was merged and pushed to production.
- PR 119 (`codex/dlbot-phase-6b-runtime-services`) was merged and pushed to production.
- PR 120 (`codex/dlbot-phase-6c-usage-tracker`) was merged and pushed to production.
- PR 121 (`codex/dlbot-phase-6d-command-lifecycle`) was merged and pushed to production.
- PR 122 (`codex/dlbot-phase-6e-command-admin-tooling`) was merged and pushed to production.
- PR 123 (`codex/dlbot-phase-6f-event-rehydration`) was merged and pushed to production.
- `core/startup_lifecycle.py` provides `StartupPhase` and `run_startup_phases()`.
- `core/command_lifecycle.py` owns startup command signature/cache/sync mechanics and shared
  `/ops` command lifecycle mechanics.
- `core/event_rehydration_lifecycle.py` owns event cache, active reminder loading, event readiness
  gating, tracked view rehydration scheduling, and pinned calendar view rehydration scheduling.
- `bot_instance.py:on_ready()` delegates:
  - initial loop/console bootstrap through `ready_runtime_bootstrap`
  - runtime services/observability startup through `ready_runtime_services`
  - startup command signature/cache/sync through `ready_command_sync`
  - event cache/reminder/live-event readiness through `ready_event_cache_rehydration`
  - tracked view rehydration through `ready_view_rehydration`
  - pinned calendar rehydration through `ready_pinned_calendar_rehydration`
- Production smoke logs confirmed for Phase 6F:
  - event reminder state loaded from `REMINDER_TRACKING_FILE`
  - event cache loaded from disk and one-shot refresh completed
  - event cache ready count was logged
  - event-dependent live views rehydrated
  - tracked view rehydration was scheduled
  - pinned calendar view rehydration was scheduled and completed
  - Ark/MGE schedulers, `full_startup_sequence()`, reminder cleanup, daily pinned calendar refresh,
    and calendar reminder loop still started afterward
  - no startup phase failure, event cache failure, tracked-view scheduling failure,
    pinned-calendar scheduling failure, or `on_ready()` critical exception was observed

This is review/scope first. Do not implement code changes until the Phase 6G scope, target
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
- `docs/reference/events_and_dm_reminders.md`
- `docs/task_packs/DL_bot Startup Lifecycle - Phase 6 Audit Starter.md`
- `docs/task_packs/Codex Chat Starter - DL_bot Phase 6F Event Cache Rehydration Boundary.md`

## Phase 6G Objective

Separate scheduler and task-supervision startup responsibilities from `bot_instance.py:on_ready()`
and from the current event-dependent compatibility bundle while preserving startup order,
readiness gating, best-effort failure boundaries, and duplicate-task prevention.

The next cohesive slice is scheduler/task registration after Phase 6F:

- event-dependent scheduler bundle currently grouped in `_start_event_dependent_tasks()`
- long-running event cache refresh loop startup through `refresh_event_cache_task`
- Ark lifecycle scheduler startup through `schedule_ark_lifecycle(bot)`
- MGE cache warm and lifecycle scheduler startup through `_refresh_mge_caches_on_startup()` and
  `schedule_mge_lifecycle(bot)`
- legacy reminder cleanup loop startup through `reminder_cleanup_loop`
- daily pinned calendar refresh startup through `schedule_daily_pinned_calendar_refresh`
- calendar reminder loop startup through `calendar_reminder_task()` and `run_calendar_reminder_loop(bot)`
- related `TaskMonitor.create()` keys, `replace=False` behavior, and `is_running()` checks

Recommended target: keep a non-Discord lifecycle helper in `core/` or a narrowly scoped startup
module responsible for ordering, idempotency, logging, `TaskMonitor` registration, and outcome
reporting. Keep scheduler implementation logic in existing domain modules such as `ark/`,
`mge/`, `event_scheduler.py`, and `event_calendar/`.

## In Scope

- Audit the relationship between:
  - `bot_instance.py:on_ready()`
  - `_start_event_dependent_tasks()`
  - `schedule_bg()`
  - `_with_timeout()`
  - `TaskMonitor.create()`, `TaskMonitor.is_running()`, and task names
  - `refresh_event_cache_task`
  - `periodic_live_embed_update()`
  - `schedule_daily_KVK_overview()`
  - `schedule_event_reminders()`
  - `refresh_reminder_format()`
  - `rehydrate_live_event_views()`
  - `schedule_event_embed_expiry()`
  - `schedule_ark_lifecycle(bot)`
  - `_refresh_mge_caches_on_startup()`
  - `schedule_mge_lifecycle(bot)`
  - `reminder_cleanup_loop`
  - `schedule_daily_pinned_calendar_refresh()`
  - `calendar_reminder_task()`
  - `run_calendar_reminder_loop(bot)`
- Define the exact startup ordering that must be preserved.
- Decide whether this should be one named startup phase or two smaller scheduler phases.
- Preserve event readiness gating from Phase 6F.
- Preserve restart safety and duplicate-task prevention.
- Preserve best-effort behavior for non-critical scheduler registration failures.
- Add or update focused tests for successful registration, skipped duplicate registration,
  best-effort failure logging, and continued startup behavior where practical.
- Capture queue-worker, shutdown, process-entry, and pinned-calendar persistence findings as later
  work unless explicitly approved for this slice.

## Out Of Scope

- Queue worker startup, live queue rehydration, queue embed refresh, or queue persistence changes.
- Shutdown redesign, signal handling, singleton/PID cleanup, or logging shutdown order.
- `DL_bot.py` process-entry changes.
- Command lifecycle, command sync, command cache, slash-command renaming, grouping, or retirement.
- Event cache load/refresh ownership changes already completed in Phase 6F.
- View rehydration ownership changes already completed in Phase 6F.
- Scheduler implementation behavior changes inside Ark, MGE, legacy reminders, or event calendar
  modules unless needed to preserve current startup behavior.
- Pinned calendar tracker persistence hardening. This remains a deferred optimisation:
  `event_calendar/pinned_embed.py` should later replace raw `Path.write_text()` tracker writes with
  established atomic JSON helper usage.
- Upload-route behaviour changes.
- SQL/importer/workbook/Google Sheets/ProcConfig contract changes unless unexpectedly required by
  scheduler validation.
- Production promotion or bot-machine deployment without `k98-promotion-check`.

## Likely Files

Review:

- `bot_instance.py`
- `core/startup_lifecycle.py`
- `core/event_rehydration_lifecycle.py`
- `ark/ark_scheduler.py`
- `mge/mge_scheduler.py`
- `mge/mge_cache.py`
- `event_scheduler.py`
- `event_embed_manager.py`
- `event_calendar/reminders.py`
- `event_calendar/pinned_embed.py`
- `event_calendar/scheduler.py`
- `constants.py`
- `tests/test_startup_lifecycle.py`
- `tests/test_event_rehydration_lifecycle.py`
- `tests/test_mge_startup_hook_invoked.py`
- `tests/test_mge_rehydrate_and_regression.py`
- `tests/test_calendar_pinned_embed.py`
- `tests/test_calendar_reminders.py`
- `tests/test_calendar_reminders_dispatch.py`
- `tests/test_calendar_scheduler.py`
- `tests/test_ark_scheduler.py`
- `tests/test_ark_scheduler_post_start.py`
- `tests/test_command_registration_smoke.py`

Likely modify after approval:

- `bot_instance.py`
- one focused lifecycle helper module if the audit proves a clean extraction
- focused scheduler/startup lifecycle tests
- `docs/reference/runbook_startup.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/DL_bot Startup Lifecycle - Phase 6 Audit Starter.md`

Do not create a broad lifecycle orchestration module that also owns queue workers, shutdown, or
process entry in Phase 6G.

## Step 1 Required Output

- Audit Summary
- Current Scheduler / Task Supervision Map
- Current Phase 6A-F Startup Lifecycle Boundary Map
- Proposed Phase 6G Ownership Model
- Startup Ordering And Idempotency Checklist
- TaskMonitor Key And Duplicate Prevention Map
- Runtime State And Persistence Map
- Ownership Problems And Refactor Triggers
- Recommended Phase 6G Implementation Scope
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
.\.venv\Scripts\python.exe -m pytest -q tests\test_startup_lifecycle.py tests\test_event_rehydration_lifecycle.py tests\test_mge_startup_hook_invoked.py tests\test_mge_rehydrate_and_regression.py tests\test_calendar_pinned_embed.py tests\test_calendar_reminders.py tests\test_calendar_reminders_dispatch.py tests\test_calendar_scheduler.py tests\test_ark_scheduler.py tests\test_ark_scheduler_post_start.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security review should be run before PR handoff for code changes because Phase 6G touches
Discord-facing schedulers, reminder state, restart-sensitive task supervision, file-backed runtime
state, and duplicate-action prevention.

## Expected Smoke / Manual Verification

After implementation and deployment, manually verify:

- normal startup still shows all Phase 6A-F startup phases
- new scheduler/task-supervision phase logs appear in the expected order
- event-dependent scheduler tasks still start only after event readiness
- live embed update, daily KVK overview, event reminders, reminder format refresh, live event view
  rehydration, and event embed expiry still start or complete as before
- Ark scheduler still starts
- MGE cache warm and MGE lifecycle scheduler still start
- `full_startup_sequence()` still runs after scheduler startup
- reminder cleanup still starts
- daily pinned calendar refresh still starts after pinned calendar rehydration
- calendar reminder loop still starts once
- repeated `on_ready()` still skips startup work and no duplicate background tasks are observed

The smoke test should not show:

```text
[STARTUP] phase failed
[CRITICAL] Exception during on_ready
[BOOT] Failed to start schedule_event_reminders
[BOOT] Failed to start event_embed_expiry task
[BOOT] Failed to start Ark scheduler
[BOOT] Failed to start MGE scheduler
[BOOT] failed to start daily pinned calendar refresh
[BOOT] failed to start calendar reminder loop
```

Known best-effort scheduler warnings may be acceptable only when later startup still continues and
the failure is intentionally induced or otherwise understood.

## Remaining Phase 6 Slices

Recommended order after Phase 6F:

1. Phase 6G scheduler and task-supervision boundary.
2. Phase 6H queue worker and live queue lifecycle.
3. Phase 6I shutdown and recovery coordination.
4. Phase 6J process-entry and bot-construction cleanup.

The wider command-surface migration/renaming programme remains separate from Phase 6.

## Deferred Item Links

This starter continues the DL_bot startup/lifecycle deferred optimisation in
`docs/reference/deferred_optimisations.md` after Phase 6F completed event cache/reminder/view
rehydration boundary extraction.

Carry forward, but do not implement unless separately approved:

- scheduler/task-supervision split from the current `_start_event_dependent_tasks()` bundle
- pinned calendar tracker persistence hardening in `event_calendar/pinned_embed.py`
