# Codex Chat Starter - DL_bot Phase 6E Command Lifecycle Admin Tooling

Use this starter to continue Phase 6 after Phase 6D command sync lifecycle ownership was merged,
smoke-tested, pushed to production, and marked complete.

## Copy/Paste Starter

Codex, continue Phase 6 of the DL_bot architecture optimisation programme with Phase 6E:
command lifecycle admin tooling convergence.

Phase 6A, 6B, 6C, and 6D are complete:

- PR 117 (`codex/dlbot-phase-6-startup-lifecycle-1`) was merged and pushed to production.
- PR 119 (`codex/dlbot-phase-6b-runtime-services`) was merged and pushed to production.
- PR 120 (`codex/dlbot-phase-6c-usage-tracker`) was merged and pushed to production.
- PR 121 (`codex/dlbot-phase-6d-command-lifecycle`) was merged and pushed to production.
- `core/startup_lifecycle.py` provides `StartupPhase` and `run_startup_phases()`.
- `core/command_lifecycle.py` now owns startup command signature/cache/sync mechanics.
- `bot_instance.py:on_ready()` delegates:
  - initial loop/console bootstrap through `ready_runtime_bootstrap`
  - runtime services/observability startup through `ready_runtime_services`
  - startup command signature/cache/sync through `ready_command_sync`
- Production smoke logs confirmed for Phase 6D:
  - unchanged-command startup loaded the command cache and skipped sync
  - changed-command startup detected `/summary` version `v1.04` to `v1.05`
  - scoped guild sync completed successfully
  - command cache updated after the changed path
  - the next restart returned to `commands_changed result: False`
  - reminder cache, event cache, rehydration, and scheduler startup continued afterward

This is review/scope first. Do not implement code changes until the Phase 6E scope, target
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
- `docs/task_packs/Codex Chat Starter - DL_bot Phase 6D Command Sync Cache.md`

## Phase 6E Objective

Converge admin command lifecycle tooling onto the Phase 6D command lifecycle owner while preserving
operator-facing Discord behaviour.

The startup path is already owned by `core/command_lifecycle.py`; Phase 6E should audit and, after
approval, reuse that lifecycle layer from:

- `/ops resync_commands`
- `/ops validate_command_cache`
- `/ops show_command_versions`

The current production-smoke-tested behaviour must be preserved:

- `/ops resync_commands` remains admin/notify-channel gated.
- `safe_defer(ctx, ephemeral=True)` remains in place.
- the resync operation lock remains in place.
- manual resync performs scoped `bot.sync_commands(guild_ids=[GUILD_ID])` with the existing admin
  timeout behaviour unless a different timeout is explicitly approved.
- command cache writes remain atomic for admin-triggered writes.
- admin embeds keep their existing success, timeout, failure, and validation semantics.
- command-version display keeps flattened grouped command names such as `/ops run_sql_proc` and
  `/mge leadership_board`.

Recommended target: keep `core/command_lifecycle.py` as the non-Discord owner of command inventory,
signature, cache, comparison, and sync mechanics. Keep `commands/admin_cmds.py` responsible for
permissions, deferral, operation lock, Discord embeds, and admin UX.

## In Scope

- Audit the relationship between:
  - `core/command_lifecycle.py`
  - `commands/admin_cmds.py:/ops resync_commands`
  - `commands/admin_cmds.py:/ops validate_command_cache`
  - `commands/admin_cmds.py:/ops show_command_versions`
  - `commands.command_inventory.flatten_application_commands()`
  - `bot_helpers.get_command_signature()`
  - `COMMAND_CACHE_FILE`
  - `file_utils.atomic_json_write()`
  - `bot.sync_commands()`
- Decide which reusable helpers belong in `core/command_lifecycle.py`.
- Preserve admin command presentation and permissions in `commands/admin_cmds.py`.
- Add or update focused tests proving startup and admin tooling use the same signature model.
- Capture broader command-surface consolidation as deferred work, not Phase 6E implementation.

## Out Of Scope

- Slash-command renaming, grouping, or retirement.
- Ark, stats, registry, inventory, calendar, or subscription command-surface migrations.
- Event cache refresh, reminder loading, view rehydration, scheduler registration, and MGE/Ark
  lifecycle extraction.
- Queue worker startup, live queue rehydration, or queue persistence changes.
- Startup command sync behaviour changes beyond preserving Phase 6D behaviour.
- Shutdown redesign.
- `DL_bot.py` process-entry changes.
- Upload-route behaviour changes.
- SQL/importer/workbook/Google Sheets/ProcConfig contract changes.
- Production promotion or bot-machine deployment without `k98-promotion-check`.

## Likely Files

Review:

- `core/command_lifecycle.py`
- `commands/admin_cmds.py`
- `bot_helpers.py`
- `commands/command_inventory.py`
- `constants.py`
- `file_utils.py`
- `tests/test_command_lifecycle.py`
- `tests/test_admin_command_cache_paths.py`
- `tests/test_command_signature_inventory.py`
- `tests/test_command_inventory.py`
- `tests/test_command_registration_smoke.py`
- `scripts/validate_command_registration.py`
- `docs/reference/deferred_optimisations.md`

Likely modify after approval:

- `core/command_lifecycle.py`
- `commands/admin_cmds.py`
- `tests/test_command_lifecycle.py`
- `tests/test_admin_command_cache_paths.py`
- possibly a focused admin command lifecycle test file if AST/source-shape tests are not enough

Do not create a new command-surface migration module in Phase 6E.

## Step 1 Required Output

- Audit Summary
- Current Admin Command Cache / Sync Tooling Map
- Current Phase 6D Command Lifecycle Boundary Map
- Proposed Phase 6E Ownership Model
- Behaviour Preservation Checklist
- Ownership Problems And Refactor Triggers
- Recommended Phase 6E Implementation Scope
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
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_lifecycle.py tests\test_admin_command_cache_paths.py tests\test_command_signature_inventory.py tests\test_command_inventory.py tests\test_command_registration_smoke.py tests\test_domain_registrars_no_legacy_register_commands.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security review should be run before PR handoff for code changes because Phase 6E touches
Discord admin commands, command sync behaviour, command cache files, runtime config, and
operator-triggered lifecycle actions.

## Expected Smoke / Manual Verification

After implementation and deployment, manually verify:

- normal startup still shows `ready_command_sync` and `commands_changed result: False` when command
  signatures are unchanged
- `/ops show_command_versions` still lists flattened grouped commands with versions
- `/ops validate_command_cache` still reports cache mismatches and missing/stale entries clearly
- `/ops resync_commands` still syncs scoped guild commands and updates the cache
- admin commands remain ephemeral and permission-gated
- no command-surface names changed

The smoke test should not show:

```text
[STARTUP] phase failed
[CRITICAL] Exception during on_ready
[COMMAND SYNC] Resync failed
[COMMAND SYNC] Timed out during sync
[WARN] Command sync timed out
[WARN] Command sync failed
```

Warnings about command sync should be investigated if they are new; timeout/failure paths may be
expected only when deliberately testing those paths.

## Deferred Item Link

This starter continues the command lifecycle admin tooling deferred optimisation in
`docs/reference/deferred_optimisations.md` after Phase 6D completed startup command sync lifecycle
ownership.
