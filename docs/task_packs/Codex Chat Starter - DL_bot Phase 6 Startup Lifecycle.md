# Codex Chat Starter - DL_bot Phase 6 Startup Lifecycle

Use this starter for historical Phase 6 kickoff context. Phase 6A was completed in PR 117
(`codex/dlbot-phase-6-startup-lifecycle-1`), and Phase 6B was completed in PR 119
(`codex/dlbot-phase-6b-runtime-services`). Both were smoke-tested on 2026-05-27, merged, and
pushed to production. For the next active slice, use
`docs/task_packs/Codex Chat Starter - DL_bot Phase 6C Usage Tracker Ownership.md`.

This original starter began Phase 6 after Phase 5 upload-routing consolidation was closed,
smoke-tested, pushed to production, and marked complete.

## Copy/Paste Starter

Codex, start Phase 6 of the DL_bot architecture optimisation programme: startup/lifecycle
separation.

This is audit/design work first. Do not implement code changes until the Phase 6 audit packet,
target lifecycle ownership model, and first PR-sized implementation scope have each been approved.

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
- `docs/task_packs/Codex Task Pack - DL_bot Upload Routing Deferred Optimisation Audit.md`
- `docs/task_packs/DL_bot Startup Lifecycle - Phase 6 Audit Starter.md`

Context:

- Phase 5 upload routing is complete.
- MGE results, KVK Honor, inventory upload-first, weekly activity, Rally Forts, and main
  monitored-channel fallback queueing now delegate through focused `upload_routes` modules.
- `DL_bot.py` is now much closer to upload listener/delegation ownership, so startup/lifecycle
  separation can be audited independently.

Phase 6 objective:

Audit `DL_bot.py` and `bot_instance.py` together and define the target ownership model for process
entry, bot construction, command registration, event registration, startup sequencing, task
supervision, queue worker lifecycle, graceful shutdown, singleton/runtime files, and restart-safe
state.

Likely files to review:

- `DL_bot.py`
- `bot_instance.py`
- `bot_loader.py`
- `bot_startup_gate.py`
- `boot_safety.py`
- `startup_utils.py`
- `singleton_lock.py`
- `bot_helpers.py`
- `utils.py`
- `logging_setup.py`
- `constants.py`
- `Commands.py`
- `docs/reference/runbook_startup.md`
- `docs/reference/runbook_shutdown.md`
- `docs/reference/singleton_lock.md`

Step 1 required output:

- Audit Summary
- Current Startup / Lifecycle Map
- Current Shutdown / Recovery Map
- Task Supervision And Scheduler Map
- Queue Worker / Live Queue Lifecycle Map
- Runtime State And Persistence Map
- Ownership Problems And Refactor Triggers
- Recommended Phase 6 Architecture Direction
- Recommended First PR Scope
- Test And Validation Strategy
- Deferred Optimisation Findings
- Approval Questions
- Explicit Stop Point

Out of scope until separately approved:

- Upload-route behaviour changes.
- Broad `DL_bot.py` or `bot_instance.py` rewrite in one PR.
- SQL/importer/workbook/Google Sheets/ProcConfig contract changes.
- Worker/process orchestration changes beyond the approved first lifecycle slice.
- Destructive lock, PID, cache, or persisted-state cleanup.
- Production promotion or bot-machine deployment without `k98-promotion-check`.

Audit/design-only validation:

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

Likely implementation validation after approval:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_command_registration_smoke.py tests\test_domain_registrars_no_legacy_register_commands.py tests\test_mge_startup_hook_invoked.py tests\test_mge_rehydrate_and_regression.py tests\test_live_queue_persistence.py tests\test_utils_live_queue.py tests\test_singleton_lock_Version2.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security review should be run before PR handoff for code changes because Phase 6 touches
startup, secrets/config, file handling, network calls, Discord runtime behaviour, and
restart-sensitive persistence.

## Deferred Item Link

This starter implements the startup/lifecycle deferred optimisation in
`docs/reference/deferred_optimisations.md`.
