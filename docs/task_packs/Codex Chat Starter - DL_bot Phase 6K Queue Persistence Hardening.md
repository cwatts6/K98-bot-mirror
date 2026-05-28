# Codex Chat Starter - DL_bot Phase 6K Queue Persistence Hardening

Use this starter only if the optional queue persistence hardening slice is approved after Phase 6J.
If this slice is skipped, proceed instead to final process-entry and bot-construction cleanup.

## Copy/Paste Starter

Codex, continue Phase 6 of the DL_bot architecture optimisation programme with Phase 6K:
queue persistence hardening.

Phase 6A through Phase 6J are complete:

- PR 117 (`codex/dlbot-phase-6-startup-lifecycle-1`) was merged and pushed to production.
- PR 119 (`codex/dlbot-phase-6b-runtime-services`) was merged and pushed to production.
- PR 120 (`codex/dlbot-phase-6c-usage-tracker`) was merged and pushed to production.
- PR 121 (`codex/dlbot-phase-6d-command-lifecycle`) was merged and pushed to production.
- PR 122 (`codex/dlbot-phase-6e-command-admin-tooling`) was merged and pushed to production.
- PR 123 (`codex/dlbot-phase-6f-event-rehydration`) was merged and pushed to production.
- PR 124 (`codex/dlbot-phase-6g-scheduler-lifecycle`) was merged and pushed to production.
- PR 125 (`codex/dlbot-phase-6h-queue-lifecycle`) was merged and pushed to production.
- PR 126 (`codex/dlbot-phase-6i-shutdown-recovery`) was merged and pushed to production.
- PR 127 (`codex/dlbot-phase-6j-graceful-restart-starter`) was merged and pushed to production.
- Phase 6H moved queue worker startup, live queue recovery, best-effort live queue embed refresh,
  queue cleanup startup, and connection watchdog startup into `core/queue_lifecycle.py`.
- Phase 6I added bot-side graceful teardown with queue drain/join handling, live queue persistence,
  supervised task cancellation, usage tracker stop, and shutdown heartbeat preservation.
- Phase 6J added `/ops graceful_restart`, retired `/ops restart_bot`, preserved
  `/ops force_restart`, centralized restart marker/cooperative restart helpers in
  `core/restart_operations.py`, and updated `graceful_shutdown.py` with a configurable cooperative
  timeout defaulting to 15 seconds.
- Phase 6J production smoke confirmed queue drain, live queue persistence, task cancellation,
  usage tracker stop, watchdog recovery, and startup return through the Phase 6 lifecycle logs.

This is review/scope first. Do not implement code changes until the Phase 6K scope, queue
persistence target model, and first PR-sized implementation plan have each been approved.

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
- `docs/task_packs/Codex Chat Starter - DL_bot Phase 6I Shutdown Recovery Coordination.md`
- `docs/task_packs/Codex Chat Starter - DL_bot Phase 6J Graceful Restart Shutdown Operations.md`

## Phase 6K Objective

Harden live queue persistence and recovery semantics now that queue startup, graceful shutdown, and
cooperative restart have stable lifecycle boundaries.

Explicit Phase 6K targets:

- Audit `load_live_queue()`, `save_live_queue()`, `live_queue`, `live_queue_lock`,
  `channel_queues`, `QUEUE_CACHE_FILE`, and the queue lifecycle startup/shutdown call sites.
- Decide whether live queue load/apply should become explicitly awaitable, remain sync-compatible
  with a safe wrapper, or use a dual helper pattern.
- Verify live queue cache writes are atomic or move them onto the established atomic JSON helper
  pattern if the current write path is weaker than the project restart-safety standard.
- Clarify stale metadata handling and recovery behavior after restart.
- Preserve the Phase 6H startup ordering: workers register, persisted live queue state loads,
  embed refresh runs best-effort, then cleanup/watchdog tasks start.
- Preserve the Phase 6I/6J shutdown ordering: queue drain/join handling and live queue persistence
  happen before supervised task cancellation.
- Add focused restart/persistence tests for load-before-embed-refresh ordering, in-flight work
  flush, stale cache behavior, and save failure handling where practical.

## In Scope

- `utils.py` live queue persistence helpers.
- `bot_helpers.py` queue worker interactions only where required to preserve persistence semantics.
- `core/queue_lifecycle.py` startup load/apply boundaries.
- `bot_instance.py` graceful teardown queue drain and live queue save call sites.
- `constants.py` only if path ownership or naming needs documentation, not broad runtime config work.
- Focused tests in queue lifecycle, live queue persistence, utils live queue, and shutdown ordering.
- Runbook and deferred optimisation updates.

## Out Of Scope

- Upload-route behavior changes, including fallback queue routing behavior.
- Queue worker processing behavior unrelated to persistence/recovery.
- New queue features, queue prioritisation, or UI redesign.
- Scheduler ownership changes already completed in Phase 6G.
- Restart command or `graceful_shutdown.py` behavior changes already completed in Phase 6J.
- Broad `DL_bot.py` process-entry rewrite or bot construction cleanup.
- SQL/importer/workbook/Google Sheets/ProcConfig contract changes unless unexpectedly required by
  validation.
- Production promotion or bot-machine deployment without `k98-promotion-check`.

## Likely Files

Review:

- `utils.py`
- `bot_helpers.py`
- `core/queue_lifecycle.py`
- `bot_instance.py`
- `constants.py`
- `logging_setup.py`
- `tests/test_queue_lifecycle.py`
- `tests/test_live_queue_persistence.py`
- `tests/test_utils_live_queue.py`
- `tests/test_startup_lifecycle.py`
- `tests/test_command_registration_smoke.py`
- `docs/reference/runbook_startup.md`
- `docs/reference/runbook_shutdown.md`
- `docs/reference/deferred_optimisations.md`

Likely modify after approval:

- `utils.py`
- `core/queue_lifecycle.py`
- `bot_instance.py` only if the audit proves shutdown save ordering or wrapper naming needs a
  narrow adjustment
- focused live queue / queue lifecycle / shutdown tests
- startup and shutdown runbooks
- deferred optimisation docs

Do not create a broad queue subsystem rewrite in Phase 6K.

## Step 1 Required Output

- Audit Summary
- Current Live Queue Persistence Map
- Startup Load / Apply / Embed Refresh Map
- Shutdown Drain / Save / Cancellation Map
- Atomicity And Stale Cache Review
- Proposed Phase 6K Queue Persistence Model
- Ownership Problems And Refactor Triggers
- Recommended Phase 6K Implementation Scope
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
.\.venv\Scripts\python.exe -m pytest -q tests\test_queue_lifecycle.py tests\test_live_queue_persistence.py tests\test_utils_live_queue.py tests\test_startup_lifecycle.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security review should be run before PR handoff for code changes because Phase 6K touches
restart-sensitive persistence, file-backed runtime state, queue recovery, and shutdown behavior.

## Expected Smoke / Manual Verification

After implementation and deployment, manually verify:

- normal startup loads persisted live queue state before best-effort live queue embed refresh
- queue cleanup and connection watchdog still register once
- `/ops graceful_restart` still drains queues and persists live queue state before task cancellation
- watchdog restarts the bot and startup returns through `ready_queue_lifecycle`
- `/ops force_restart` remains available as break-glass
- malformed or stale queue cache state is handled according to the approved model

## Remaining Phase 6 Slices

Recommended order after Phase 6J:

1. Optional Phase 6K queue persistence hardening.
2. Final process-entry and bot-construction cleanup after the queue persistence decision.

The wider command-surface migration/renaming programme remains separate from Phase 6.

## Deferred Item Links

This starter continues the queue runtime state deferred optimisation in
`docs/reference/deferred_optimisations.md`.

Carry forward, but do not implement unless separately approved:

- process-entry and bot-construction cleanup after the queue persistence decision
- pinned calendar tracker persistence hardening in `event_calendar/pinned_embed.py`
- wider command-surface migration/renaming programme
