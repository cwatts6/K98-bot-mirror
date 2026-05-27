# Codex Chat Starter - DL_bot Phase 6B Runtime Services

Use this starter to continue Phase 6 after Phase 6A startup lifecycle boundary was merged,
smoke-tested, pushed to production, and marked complete.

## Copy/Paste Starter

Codex, continue Phase 6 of the DL_bot architecture optimisation programme with Phase 6B:
`on_ready()` runtime services and observability startup extraction.

Phase 6A is complete:

- PR 117 (`codex/dlbot-phase-6-startup-lifecycle-1`) was merged and pushed to production.
- `core/startup_lifecycle.py` now provides `StartupPhase` and `run_startup_phases()`.
- `bot_instance.py:on_ready()` now delegates the initial loop/console bootstrap through the
  named `ready_runtime_bootstrap` phase.
- Production smoke logs confirmed:
  - `[STARTUP] phase started: ready_runtime_bootstrap`
  - `[BOOT] Global asyncio exception handler installed on running loop.`
  - `[STARTUP] phase completed: ready_runtime_bootstrap`
  - normal heartbeat, health dashboard, command-cache, scheduler, queue worker, rehydration, and
    full startup logs continued afterward.

This is review/scope first. Do not implement code changes until the Phase 6B scope, target
phase boundary, and first PR-sized implementation plan have each been approved.

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

## Phase 6B Objective

Extract the next contiguous `bot_instance.py:on_ready()` startup block into a named lifecycle phase
using the Phase 6A `core.startup_lifecycle` pattern.

Recommended target phase:

`ready_runtime_services`

This phase should cover only the runtime services and observability startup block that currently
follows `ready_runtime_bootstrap`, including:

- heartbeat task startup
- health dashboard task startup
- offload monitor startup
- `PIL.Image.show()` safety patch
- old lock-file cleanup
- usage tracker startup
- daily summary loop startup
- activity schema/listener startup when activity tracking is enabled
- UTC clock status channel loop startup
- member-count status channel loop startup

The implementation should preserve startup order and behaviour.

## Out Of Scope

- `DL_bot.py` process-entry changes.
- Upload-route behaviour changes.
- Command sync/cache extraction.
- Command-surface consolidation.
- Event cache refresh, reminder loading, view rehydration, scheduler registration, and MGE/Ark
  lifecycle extraction.
- Queue worker startup, live queue rehydration, or queue persistence changes.
- Shutdown, signal handling, singleton lock, PID, marker, or logging-shutdown changes.
- SQL/importer/workbook/Google Sheets/ProcConfig contract changes.
- Production promotion or bot-machine deployment without `k98-promotion-check`.

## Likely Files

Review:

- `bot_instance.py`
- `core/startup_lifecycle.py`
- `tests/test_startup_lifecycle.py`
- `docs/reference/runbook_startup.md`
- `docs/reference/runbook_shutdown.md`
- `docs/reference/singleton_lock.md`

Likely modify after approval:

- `bot_instance.py`
- `tests/test_startup_lifecycle.py`

Do not create a new lifecycle module unless the audit finds `core/startup_lifecycle.py` is no
longer sufficient.

## Step 1 Required Output

- Audit Summary
- Current Phase 6A Boundary Map
- Proposed Phase 6B Runtime Services Map
- Behaviour Preservation Checklist
- Ownership Problems And Refactor Triggers
- Recommended Phase 6B Implementation Scope
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
.\.venv\Scripts\python.exe -m pytest -q tests\test_startup_lifecycle.py tests\test_mge_startup_hook_invoked.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security review should be run before PR handoff for code changes because Phase 6 touches
startup, file handling, network calls, Discord runtime behaviour, and restart-sensitive
persistence.

## Expected Smoke Log Signals

After implementation and deployment, expected startup logs should include:

```text
[STARTUP] phase started: ready_runtime_bootstrap
[STARTUP] phase completed: ready_runtime_bootstrap
[STARTUP] phase started: ready_runtime_services
[BOOT] Heartbeat loop started
[BOOT] Health dashboard task started
[BOOT] Offload monitor scheduled via TaskMonitor
[BOOT] Usage tracker started.
[BOOT] daily_summary loop started
[BOOT] Server activity tracking initialized
[BOOT] UTC clock status channel loop started
[BOOT] Member count status channel loop started
[STARTUP] phase completed: ready_runtime_services
```

The smoke test should not show:

```text
[STARTUP] phase failed: ready_runtime_services
[CRITICAL] Exception during on_ready
```

## Deferred Item Link

This starter continues the startup/lifecycle deferred optimisation in
`docs/reference/deferred_optimisations.md`.
