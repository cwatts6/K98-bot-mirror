# Codex Chat Starter - DL_bot Phase 6D Command Sync Cache

Status: complete. PR 121 (`codex/dlbot-phase-6d-command-lifecycle`) was merged, smoke-tested, and
pushed to production on 2026-05-27. This starter is retained as historical context for Phase 6D.

Use `docs/task_packs/Codex Chat Starter - DL_bot Phase 6E Command Lifecycle Admin Tooling.md` for
the next Phase 6 slice.

## Copy/Paste Starter

Codex, continue Phase 6 of the DL_bot architecture optimisation programme with Phase 6D:
command signature/cache/sync lifecycle ownership.

Phase 6A, 6B, and 6C are complete:

- PR 117 (`codex/dlbot-phase-6-startup-lifecycle-1`) was merged and pushed to production.
- PR 119 (`codex/dlbot-phase-6b-runtime-services`) was merged and pushed to production.
- PR 120 (`codex/dlbot-phase-6c-usage-tracker`) was merged and pushed to production.
- `core/startup_lifecycle.py` provides `StartupPhase` and `run_startup_phases()`.
- `bot_instance.py:on_ready()` now delegates:
  - initial loop/console bootstrap through `ready_runtime_bootstrap`
  - runtime services/observability startup through `ready_runtime_services`
- `ready_runtime_services` owns heartbeat, health dashboard, offload monitor, image-show safety,
  lock cleanup, shared usage tracker startup, usage JSONL pruning, daily summary, activity
  tracking, and server status channel loops.
- Production smoke logs confirmed:
  - `[STARTUP] phase started: ready_runtime_bootstrap`
  - `[STARTUP] phase completed: ready_runtime_bootstrap`
  - `[STARTUP] phase started: ready_runtime_services`
  - `[BOOT] Usage tracker started.`
  - `[MONITOR] Task started: usage_jsonl_prune`
  - `[BOOT] Usage JSONL prune loop started (retention=30 days).`
  - `[STARTUP] phase completed: ready_runtime_services`
  - command cache, event cache, rehydration, schedulers, queue workers, and
    `full_startup_sequence()` continued afterward.

This is review/scope first. Do not implement code changes until the Phase 6D scope, target
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

## Phase 6D Objective

Audit and extract command signature/cache/sync handling from the remaining `on_ready()` body into
an explicit lifecycle owner.

The current production-smoke-tested behaviour must be preserved:

- build the current flattened slash-command signature list
- load `COMMAND_CACHE_FILE`
- compare command signatures with `commands_changed()`
- when changed, perform scoped `bot.sync_commands(guild_ids=[GUILD_ID])` with the current timeout
  behaviour and telemetry on timeout
- save command signatures only after the changed-command path
- skip sync when signatures are unchanged
- log loaded slash commands in the same order/shape currently used for operator visibility

Recommended target: a named startup phase or helper that owns command cache/sync behaviour without
mixing it with event cache refresh, reminder loading, rehydration, schedulers, queue workers, or
`full_startup_sequence()`.

## In Scope

- Audit the relationship between:
  - `bot_instance.py:on_ready()`
  - `bot_helpers.commands_changed()`
  - `bot_helpers.load_command_signatures()`
  - `bot_helpers.save_command_signatures()`
  - `commands.command_inventory.flatten_application_commands()`
  - `bot_instance.py:get_command_signature()`
  - `COMMAND_CACHE_FILE`
  - `bot.sync_commands()`
  - command sync timeout telemetry via `emit_telemetry_event()`
- Decide whether command signature/cache/sync should become:
  - a dedicated named startup phase such as `ready_command_sync`
  - a focused helper called by `on_ready()` after `ready_runtime_services`
  - or another explicit ownership model that preserves startup order.
- Preserve command registration and command-cache behaviour.
- Preserve command-sync timeout/error behaviour and logs.
- Preserve startup order enough that event cache and later tasks do not begin until command cache
  handling has completed or intentionally skipped sync.
- Add or update focused lifecycle tests.
- Capture broader command-surface consolidation or validator output cleanup as deferred work.

## Out Of Scope

- Command surface consolidation or slash-command renaming.
- Event cache refresh, reminder loading, view rehydration, scheduler registration, and MGE/Ark
  lifecycle extraction.
- Queue worker startup, live queue rehydration, or queue persistence changes.
- Usage tracker lifecycle changes beyond preserving Phase 6C behaviour.
- Shutdown redesign.
- `DL_bot.py` process-entry changes.
- Upload-route behaviour changes.
- SQL/importer/workbook/Google Sheets/ProcConfig contract changes.
- Production promotion or bot-machine deployment without `k98-promotion-check`.

## Likely Files

Review:

- `bot_instance.py`
- `bot_helpers.py`
- `commands/command_inventory.py`
- `constants.py`
- `core/startup_lifecycle.py`
- `scripts/validate_command_registration.py`
- `scripts/smoke_imports.py`
- `tests/test_startup_lifecycle.py`
- `tests/test_command_registration_smoke.py`
- `tests/test_domain_registrars_no_legacy_register_commands.py`
- `docs/reference/runbook_startup.md`
- `docs/reference/runbook_shutdown.md`

Likely modify after approval:

- `bot_instance.py`
- `tests/test_startup_lifecycle.py`
- possibly a focused helper module only if the audit proves `bot_instance.py` is no longer the
  right owner for command cache/sync orchestration.

Do not create a new command lifecycle module unless the audit finds a clear boundary that
`core/startup_lifecycle.py` and a local helper cannot cover.

## Step 1 Required Output

- Audit Summary
- Current Command Sync / Cache Lifecycle Map
- Current Phase 6A/6B/6C Boundary Map
- Proposed Phase 6D Ownership Model
- Behaviour Preservation Checklist
- Ownership Problems And Refactor Triggers
- Recommended Phase 6D Implementation Scope
- Test And Validation Strategy
- Deferred Optimisation Findings
- Approval Questions
- Explicit Stop Point

## Audit / Design-Only Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

## Likely Implementation Validation After Approval

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_startup_lifecycle.py tests\test_command_registration_smoke.py tests\test_domain_registrars_no_legacy_register_commands.py tests\test_mge_startup_hook_invoked.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security review should be run before PR handoff for code changes because Phase 6 touches
startup, Discord command registration/sync behaviour, runtime config, telemetry, and
restart-sensitive lifecycle.

## Expected Smoke Log Signals

After implementation and deployment, expected startup logs should still include:

```text
[STARTUP] phase started: ready_runtime_bootstrap
[STARTUP] phase completed: ready_runtime_bootstrap
[STARTUP] phase started: ready_runtime_services
[BOOT] Usage tracker started.
[BOOT] Usage JSONL prune loop started (retention=30 days).
[STARTUP] phase completed: ready_runtime_services
[STARTUP] phase started: ready_command_sync
[STARTUP] phase completed: ready_command_sync
```

If the implementation uses a helper rather than a new named phase, smoke expectations should still
include the existing command-cache and command-sync lines:

```text
Bot is ready
Reading command cache file
Command cache loaded
commands_changed result: False
Slash commands unchanged - skipping sync and update.
Loaded slash commands:
```

The smoke test should not show:

```text
[STARTUP] phase failed
[CRITICAL] Exception during on_ready
[WARN] Command sync timed out
[WARN] Command sync failed
GUILD_ID not set; skipping scoped sync
GUILD_ID is not an integer; skipping scoped sync
```

Warnings about command sync should be investigated if they are new; they may be expected only when
the environment or command signatures intentionally force that path.

## Deferred Item Link

This starter continues the startup/lifecycle deferred optimisation in
`docs/reference/deferred_optimisations.md` after Phase 6C completed usage tracker ownership.
