# Codex Chat Starter - DL_bot Phase 6C Usage Tracker Ownership

Use this starter to continue Phase 6 after Phase 6B runtime services extraction was merged,
smoke-tested, pushed to production, and marked complete.

## Copy/Paste Starter

Codex, continue Phase 6 of the DL_bot architecture optimisation programme with Phase 6C:
usage tracker lifecycle ownership and `full_startup_sequence()` observability cleanup.

Phase 6A and 6B are complete:

- PR 117 (`codex/dlbot-phase-6-startup-lifecycle-1`) was merged and pushed to production.
- PR 119 (`codex/dlbot-phase-6b-runtime-services`) was merged and pushed to production.
- `core/startup_lifecycle.py` provides `StartupPhase` and `run_startup_phases()`.
- `bot_instance.py:on_ready()` now delegates:
  - initial loop/console bootstrap through `ready_runtime_bootstrap`
  - runtime services/observability startup through `ready_runtime_services`
- Production smoke logs confirmed:
  - `[STARTUP] phase started: ready_runtime_bootstrap`
  - `[STARTUP] phase completed: ready_runtime_bootstrap`
  - `[STARTUP] phase started: ready_runtime_services`
  - heartbeat, health dashboard, offload monitor, usage tracker, daily summary, activity tracking,
    UTC clock, and member-count status loops started
  - `[STARTUP] phase completed: ready_runtime_services`
  - command cache, event cache, rehydration, schedulers, queue workers, and
    `full_startup_sequence()` continued afterward.

This is review/scope first. Do not implement code changes until the Phase 6C scope, target
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
- `docs/task_packs/DL_bot Startup Lifecycle - Phase 6 Audit Starter.md`

## Phase 6C Objective

Audit and consolidate usage tracker lifecycle ownership now that Phase 6B made the runtime services
phase explicit.

The current production-smoke-tested behaviour is intentionally preserved, but ownership remains
split:

- `_run_ready_runtime_services()` starts the decorator-level `usage_tracker()` singleton.
- `full_startup_sequence()` later calls `start_usage_tracker()` and starts the
  `usage_jsonl_prune` TaskMonitor task.
- `on_graceful_shutdown()` stops the decorator-level `usage_tracker()` singleton.

Recommended target: one explicit startup lifecycle owner for usage tracking and usage JSONL prune
startup, with shutdown ownership documented and preserved.

## In Scope

- Audit the relationship between:
  - `decoraters.usage_tracker()`
  - `usage_tracker.start_usage_tracker()`
  - `usage_tracker.usage_jsonl_prune_loop`
  - `bot_instance.py:_run_ready_runtime_services()`
  - `bot_instance.py:full_startup_sequence()`
  - `bot_instance.py:on_graceful_shutdown()`
- Decide whether usage tracker startup and prune-loop startup should remain in
  `ready_runtime_services`, move into a dedicated named phase, or be otherwise made explicit.
- Preserve usage event capture for commands, components, autocomplete, denied-command logging, SQL
  flush behaviour, JSONL writes, and JSONL retention pruning.
- Preserve startup order enough that command/interactions do not lose usage logging after ready.
- Preserve shutdown flushing/stopping behaviour.
- Add or update focused lifecycle tests.
- Capture any broader `full_startup_sequence()` cleanup that exceeds this slice.

## Out Of Scope

- Command sync/cache extraction.
- Event cache refresh, reminder loading, view rehydration, scheduler registration, and MGE/Ark
  lifecycle extraction.
- Queue worker startup, live queue rehydration, or queue persistence changes.
- Shutdown redesign beyond preserving usage tracker stop/flush behaviour.
- `DL_bot.py` process-entry changes.
- Upload-route behaviour changes.
- SQL/importer/workbook/Google Sheets/ProcConfig contract changes.
- Production promotion or bot-machine deployment without `k98-promotion-check`.

## Likely Files

Review:

- `bot_instance.py`
- `decoraters.py`
- `usage_tracker.py`
- `core/startup_lifecycle.py`
- `tests/test_startup_lifecycle.py`
- `tests/test_usage_tracker.py`
- `docs/reference/runbook_startup.md`
- `docs/reference/runbook_shutdown.md`

Likely modify after approval:

- `bot_instance.py`
- `tests/test_startup_lifecycle.py`
- possibly `tests/test_usage_tracker.py`

Do not create a new lifecycle module unless the audit finds `core/startup_lifecycle.py` is no
longer sufficient.

## Step 1 Required Output

- Audit Summary
- Current Usage Tracker Lifecycle Map
- Current Phase 6A/6B Boundary Map
- Proposed Phase 6C Ownership Model
- Behaviour Preservation Checklist
- Ownership Problems And Refactor Triggers
- Recommended Phase 6C Implementation Scope
- Test And Validation Strategy
- Deferred Optimisation Findings
- Approval Questions
- Explicit Stop Point

## Audit / Design-Only Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

## Likely Implementation Validation After Approval

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_startup_lifecycle.py tests\test_usage_tracker.py tests\test_mge_startup_hook_invoked.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security review should be run before PR handoff for code changes because Phase 6 touches
startup, file handling, network calls, Discord runtime behaviour, usage telemetry, and
restart-sensitive persistence.

## Expected Smoke Log Signals

After implementation and deployment, expected startup logs should still include:

```text
[STARTUP] phase started: ready_runtime_bootstrap
[STARTUP] phase completed: ready_runtime_bootstrap
[STARTUP] phase started: ready_runtime_services
[BOOT] Usage tracker started.
[STARTUP] phase completed: ready_runtime_services
```

If the implementation introduces a dedicated usage phase, the smoke expectations should include
the new phase start/completion lines and should still show usage JSONL prune startup once.

The smoke test should not show:

```text
[STARTUP] phase failed
[CRITICAL] Exception during on_ready
[BOOT] Failed to start usage tracker.
```

## Deferred Item Link

This starter continues the usage tracker ownership deferred optimisation in
`docs/reference/deferred_optimisations.md`.

---

## Phase 6C Is Complete

**Status**: Merged via PR codex/dlbot-phase-6c-usage-tracker (commit d39f5b0) and pushed to production.

**What Changed**:

- `decoraters.usage_tracker()` now delegates to the shared `usage_tracker.get_usage_tracker()` singleton.
- `usage_tracker.py` owns the shared tracker singleton with unified flush cadence (`5s` / `20` events) for commands, components, metrics, and alerts.
- `_run_ready_runtime_services()` now owns both usage tracker startup (`start_usage_tracker()`) and usage JSONL prune-loop registration (`task_monitor.create("usage_jsonl_prune", ...)`).
- Usage observability startup removed from `full_startup_sequence()`.
- Focused lifecycle tests added to assert shared singleton, preserved flush settings, and runtime-services ownership boundary.
- Startup runbook and Phase 6 task-pack/deferred optimisation docs updated to reflect Phase 6C status.

**Validation**:

- All tests pass (1546 passed, 2 skipped).
- All validation scripts pass (architecture boundaries, deferred items, select tests, smoke imports, command registration).
- Pre-commit hooks pass.
- Codex Security diff review completed (no findings).
- Production smoke logs confirmed usage tracker startup in `ready_runtime_services` phase.

**Next Steps**:

Continue with the next Phase 6 task when identified, or proceed to other architectural optimisation work as prioritized.
