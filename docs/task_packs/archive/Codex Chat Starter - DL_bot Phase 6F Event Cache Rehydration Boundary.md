# Codex Chat Starter - DL_bot Phase 6F Event Cache Rehydration Boundary

Status: complete. PR 123 (`codex/dlbot-phase-6f-event-rehydration`) was merged, smoke-tested,
and pushed to production on 2026-05-28. This starter is retained as historical context for Phase
6F.

Use `docs/task_packs/Codex Chat Starter - DL_bot Phase 6G Scheduler Task Supervision Boundary.md`
for the next Phase 6 slice.

Delivered outcome:

- `core/event_rehydration_lifecycle.py` now owns event cache/reminder/view rehydration startup
  ordering, readiness gating, and best-effort scheduling boundaries.
- `bot_instance.py:on_ready()` delegates through `ready_event_cache_rehydration`,
  `ready_view_rehydration`, and `ready_pinned_calendar_rehydration`.
- The current event-dependent scheduler bundle was deliberately preserved and deferred to Phase 6G.
- Production smoke confirmed clean startup phases, event cache ready count, active reminder
  rehydration, tracked view scheduling, pinned calendar rehydration scheduling, later scheduler
  continuation, full startup completion, and no Phase 6F error signatures.

Approved Phase 6F scope decision: extract event cache, reminder loading, tracked view rehydration,
and pinned calendar rehydration behind explicit startup lifecycle boundaries. Preserve the current
event-dependent scheduler bundle as a compatibility path and defer scheduler/task-supervision
ownership to Phase 6G so that work is not lost.

## Copy/Paste Starter

Codex, continue Phase 6 of the DL_bot architecture optimisation programme with Phase 6F:
event cache, reminder loading, and rehydration boundary.

Phase 6A, 6B, 6C, 6D, and 6E are complete:

- PR 117 (`codex/dlbot-phase-6-startup-lifecycle-1`) was merged and pushed to production.
- PR 119 (`codex/dlbot-phase-6b-runtime-services`) was merged and pushed to production.
- PR 120 (`codex/dlbot-phase-6c-usage-tracker`) was merged and pushed to production.
- PR 121 (`codex/dlbot-phase-6d-command-lifecycle`) was merged and pushed to production.
- PR 122 (`codex/dlbot-phase-6e-command-admin-tooling`) was merged and pushed to production.
- `core/startup_lifecycle.py` provides `StartupPhase` and `run_startup_phases()`.
- `core/command_lifecycle.py` owns startup command signature/cache/sync mechanics and the shared
  command lifecycle mechanics used by `/ops` admin tooling.
- `bot_instance.py:on_ready()` delegates:
  - initial loop/console bootstrap through `ready_runtime_bootstrap`
  - runtime services/observability startup through `ready_runtime_services`
  - startup command signature/cache/sync through `ready_command_sync`
- Production smoke logs confirmed for Phase 6E:
  - `/ops show_command_versions` loaded and executed
  - `/ops validate_command_cache` loaded and executed
  - `/ops resync_commands` completed scoped sync successfully
  - command usage telemetry flushed normally for all three commands
  - no command sync timeout, failure, startup phase failure, or `on_ready()` critical exception was
    observed

This is review/scope first. Do not implement code changes until the Phase 6F scope, target
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
- `docs/task_packs/Codex Chat Starter - DL_bot Phase 6E Command Lifecycle Admin Tooling.md`

## Phase 6F Objective

Separate the event cache, reminder loading, and rehydration portion of `bot_instance.py:on_ready()`
behind an explicit startup lifecycle boundary while preserving current startup order and runtime
behaviour.

The next cohesive slice is the block after `ready_command_sync` and before scheduler/task
supervision cleanup. Phase 6F should audit and, after approval, extract ownership for:

- active reminder state loading through `load_active_reminders(bot)`
- event cache load/stale/empty handling through `load_event_cache()`, `is_cache_stale()`,
  `get_all_upcoming_events()`, and `refresh_event_cache()`
- background one-shot event cache refresh scheduling
- event cache readiness gating through `wait_for_events(10)`
- event-dependent startup work currently grouped under `_start_event_dependent_tasks()`
- tracked view rehydration through `rehydrate_tracked_views(bot)`
- pinned calendar view rehydration through `rehydrate_pinned_calendar_view(bot)`

Recommended target: keep a non-Discord lifecycle helper in `core/` or a narrowly scoped startup
module responsible for ordering, logging, timeouts, and outcome reporting. Keep Discord-specific
view/event helpers in their existing modules, and keep actual scheduler ownership for a later
Phase 6G slice.

## In Scope

- Audit the relationship between:
  - `bot_instance.py:on_ready()`
  - `_start_event_dependent_tasks()`
  - `schedule_bg()`
  - `_with_timeout()`
  - `event_cache.py`
  - `event_scheduler.load_active_reminders()`
  - `event_scheduler.refresh_reminder_format()`
  - `event_embed_manager.rehydrate_live_event_views()`
  - `rehydrate_views.rehydrate_tracked_views()`
  - `event_calendar.pinned_embed.rehydrate_pinned_calendar_view()`
  - `event_calendar.pinned_embed.update_calendar_embed()`
  - `REMINDER_TRACKING_FILE`
  - event/reminder/view tracker persisted state files
- Define the exact startup ordering that must be preserved.
- Decide whether this should be one named startup phase or two smaller phases.
- Preserve restart safety and duplicate-task prevention.
- Add or update focused tests for success, stale/empty cache handling, failure logging, and
  idempotent/safe scheduling where practical.
- Capture scheduler/task-supervision, queue-worker, shutdown, and process-entry findings as later
  Phase 6 work.

## Out Of Scope

- Ark, MGE, event reminder, calendar reminder, subscription, maintenance, or daily pinned refresh
  scheduler ownership changes.
- Queue worker startup, live queue rehydration, queue embed refresh, or queue persistence changes.
- Shutdown redesign, signal handling, singleton/PID cleanup, or logging shutdown order.
- `DL_bot.py` process-entry changes.
- Command lifecycle, command sync, command cache, slash-command renaming, grouping, or retirement.
- Upload-route behaviour changes.
- SQL/importer/workbook/Google Sheets/ProcConfig contract changes unless unexpectedly required by
  event/reminder state validation.
- Production promotion or bot-machine deployment without `k98-promotion-check`.

## Likely Files

Review:

- `bot_instance.py`
- `core/startup_lifecycle.py`
- `event_cache.py`
- `event_scheduler.py`
- `event_embed_manager.py`
- `rehydrate_views.py`
- `event_calendar/pinned_embed.py`
- `event_calendar/reminders.py`
- `constants.py`
- `tests/test_mge_startup_hook_invoked.py`
- `tests/test_mge_rehydrate_and_regression.py`
- `tests/test_rehydrate_views.py`
- `tests/test_rehydrate_views_and_localtime.py`
- `tests/test_rehydrate_sanitize_and_fileio.py`
- `tests/test_event_cache.py`
- `tests/test_calendar_pinned_embed.py`
- `tests/test_calendar_reminders.py`
- `tests/test_calendar_reminders_dispatch.py`
- `tests/test_command_registration_smoke.py`

Likely modify after approval:

- `bot_instance.py`
- one focused lifecycle helper module if the audit proves a clean extraction
- focused startup/rehydration tests
- `docs/reference/runbook_startup.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/DL_bot Startup Lifecycle - Phase 6 Audit Starter.md`

Do not create a broad lifecycle orchestration module that also owns schedulers, queue workers, or
shutdown in Phase 6F.

## Step 1 Required Output

- Audit Summary
- Current Event Cache / Reminder / Rehydration Map
- Current Phase 6A-E Startup Lifecycle Boundary Map
- Proposed Phase 6F Ownership Model
- Startup Ordering And Idempotency Checklist
- Runtime State And Persistence Map
- Ownership Problems And Refactor Triggers
- Recommended Phase 6F Implementation Scope
- Test And Validation Strategy
- Deferred Optimisation Findings
- Approval Questions
- Explicit Stop Point

## Audit / Design-Only Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
```

## Likely Implementation Validation After Approval

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_event_cache.py tests\test_rehydrate_views.py tests\test_rehydrate_views_and_localtime.py tests\test_rehydrate_sanitize_and_fileio.py tests\test_calendar_pinned_embed.py tests\test_calendar_reminders.py tests\test_calendar_reminders_dispatch.py tests\test_mge_startup_hook_invoked.py tests\test_mge_rehydrate_and_regression.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security review should be run before PR handoff for code changes because Phase 6F touches
Discord event/view rehydration, user-facing reminder state, file-backed runtime state, and
restart-sensitive persistence.

## Expected Smoke / Manual Verification

After implementation and deployment, manually verify:

- normal startup still shows `ready_runtime_bootstrap`, `ready_runtime_services`, and
  `ready_command_sync`
- event reminder state loads from `REMINDER_TRACKING_FILE`
- event cache loads from disk or refreshes when stale/empty
- event cache ready count is logged
- event-dependent live views rehydrate successfully
- tracked views are scheduled for rehydration
- pinned calendar view rehydration is scheduled
- later schedulers still start after the rehydration boundary
- no duplicate background task starts are observed after a repeated `on_ready()` call

The smoke test should not show:

```text
[STARTUP] phase failed
[CRITICAL] Exception during on_ready
[STARTUP] Failed to load or refresh event cache
[BOOT] Failed to start rehydrate_live_event_views
[BOOT] Failed to start rehydrate_tracked_views
[BOOT] failed to schedule pinned calendar rehydration
```

Warnings around stale or empty event cache may be expected only when followed by a successful
refresh and ready event count.

## Remaining Phase 6 Slices

Recommended order after Phase 6E:

1. Phase 6F event cache, reminder loading, and rehydration boundary.
2. Phase 6G scheduler and task-supervision boundary.
3. Phase 6H queue worker and live queue lifecycle.
4. Phase 6I shutdown and recovery coordination.
5. Phase 6J process-entry and bot-construction cleanup.

The wider command-surface migration/renaming programme remains separate from Phase 6.

## Deferred Item Link

This starter continues the DL_bot startup/lifecycle deferred optimisation in
`docs/reference/deferred_optimisations.md` after Phase 6E completed command lifecycle admin tooling
convergence.
