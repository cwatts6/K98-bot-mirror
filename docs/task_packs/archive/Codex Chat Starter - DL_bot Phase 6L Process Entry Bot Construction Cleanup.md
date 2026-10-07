# Codex Chat Starter - DL_bot Phase 6L Process Entry Bot Construction Cleanup

Status: complete. Phase 6L closed the DL_bot upload-routing and startup/lifecycle optimisation
programme. The approved final ownership model is:

- `DL_bot.py` remains process-entry, command-registration, signal, and message/upload listener
  owner.
- `bot_loader.py` remains the sole bot construction owner.
- `bot_instance.py` remains lifecycle event, startup phase, task-supervision, and bot-side
  graceful teardown owner.

The implementation intentionally stayed narrow: `DL_bot.py` now names child PID publication and
process signal registration through small helpers while preserving startup ordering, command
registration, event registration, shutdown/restart semantics, queue persistence, and upload-route
behavior. Startup/shutdown/diagnostics runbooks and deferred optimisation notes document the
post-Phase 6 state. Completed DL_bot task packs and chat starters are archived under
`docs/task_packs/archive/`. The next related programmes are command-surface migration,
queue-domain redesign, optional SQL-backed queue persistence, disabled secondary command-surface
cleanup, SQL deployment workflow, and pinned calendar tracker atomic-write hardening.

Historical starter content follows.

## Copy/Paste Starter

Codex, continue Phase 6 of the DL_bot architecture optimisation programme with Phase 6L:
process-entry and bot-construction cleanup.

Phase 6A through Phase 6K are complete:

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
- PR 128 (`codex/dlbot-phase-6k-queue-persistence`) was merged and pushed to production.
- Phase 6A-K separated startup phase orchestration, runtime services, usage tracker lifecycle,
  command lifecycle, event rehydration, scheduler startup, queue lifecycle, graceful shutdown,
  cooperative restart operations, and live queue persistence hardening behind stable boundaries.
- Phase 6K production smoke confirmed `/ops graceful_restart` still drains queues, persists live
  queue state, cancels supervised tasks, stops usage tracking, restarts through the watchdog, loads
  live queue state before embed refresh, recovers stale queue embed metadata, starts queue
  cleanup/watchdog once, and continues through `ready_calendar_scheduler_tasks`.

This is review/scope first. Do not implement code changes until the Phase 6L scope, final
process-entry/bot-construction target model, and first PR-sized implementation plan have each been
approved.

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
- `docs/task_packs/Codex Chat Starter - DL_bot Phase 6J Graceful Restart Shutdown Operations.md`
- `docs/task_packs/Codex Chat Starter - DL_bot Phase 6K Queue Persistence Hardening.md`

Use `docs/reference/ENV_REFERENCE.md` if environment-variable ownership or runtime configuration
validation becomes part of the design. SQL validation is not expected unless the audit unexpectedly
touches SQL-backed cache/import/export/report/ProcConfig contracts.

## Phase 6L Objective

Finish Phase 6 by auditing and tightening process-entry and bot-construction ownership now that
runtime startup phases, scheduler ownership, queue lifecycle, graceful shutdown, cooperative
restart, and live queue persistence have stable boundaries.

Explicit Phase 6L targets:

- Audit `DL_bot.py` process entry, environment/interpreter checks, logging bootstrap, singleton
  lock/PID handling, command registration import wiring, Discord client start, signal handling,
  shutdown marker handling, and `bot.run()` flow.
- Audit `bot_loader.py` and `bot_instance.py` construction/import ownership, including whether bot
  singleton creation, event registration, and startup hooks have one clear owner.
- Audit `bot_startup_gate.py`, `boot_safety.py`, `startup_utils.py`, `singleton_lock.py`,
  `logging_setup.py`, `constants.py`, and `command_regenerate.py` only as needed to map process
  entry and construction boundaries.
- Decide whether the final cleanup should be documentation-only, a narrow extraction, or a small
  naming/wrapper consolidation.
- Preserve Phase 6A-K runtime behavior, startup ordering, shutdown ordering, restart semantics,
  queue persistence, command registration behavior, and upload-route behavior.
- Add focused tests only where the approved implementation changes observable process-entry,
  construction, signal, singleton, or import-side-effect behavior.

## In Scope

- `DL_bot.py` process entry and signal wiring audit.
- `bot_loader.py` and `bot_instance.py` construction/import ownership audit.
- Startup gate, singleton lock, PID/runtime marker, logging bootstrap, and command registration
  import-path review.
- Focused cleanup that reduces duplicate ownership or clarifies naming without moving broad
  runtime behavior.
- Startup/shutdown/runbook and Phase 6 task-pack updates.
- Deferred optimisation updates for any remaining out-of-scope process-entry or construction debt.

## Out Of Scope

- Upload-route behavior changes.
- Queue worker processing behavior or queue persistence changes already completed in Phase 6K.
- Scheduler ownership changes already completed in Phase 6G.
- Restart command behavior already completed in Phase 6J.
- Broad command-surface migration or slash-command renaming.
- SQL/importer/workbook/Google Sheets/ProcConfig contract changes unless unexpectedly required by
  validation.
- Production promotion or bot-machine deployment without `k98-promotion-check`.
- Full queue domain redesign or SQL-backed queue persistence; those are separate deferred items.

## Likely Files

Review:

- `DL_bot.py`
- `bot_loader.py`
- `bot_instance.py`
- `bot_startup_gate.py`
- `boot_safety.py`
- `startup_utils.py`
- `singleton_lock.py`
- `logging_setup.py`
- `constants.py`
- `command_regenerate.py`
- `Commands.py`
- `run_bot.py`
- `tests/test_startup_lifecycle.py`
- `tests/test_singleton_lock_Version2.py`
- `tests/test_command_registration_smoke.py`
- `tests/test_domain_registrars_no_legacy_register_commands.py`
- `tests/test_process_utils.py`
- `tests/test_file_utils_lockinfo.py`
- `docs/reference/runbook_startup.md`
- `docs/reference/runbook_shutdown.md`
- `docs/reference/deferred_optimisations.md`

Likely modify after approval:

- `DL_bot.py` only if the audit proves a narrow process-entry cleanup is safe.
- `bot_loader.py` or `bot_instance.py` only if construction ownership needs a narrow adjustment.
- focused process-entry/startup/singleton/registration tests.
- startup/shutdown runbooks and Phase 6 task-pack docs.

Do not create a broad application container or rewrite process entry in one PR.

## Step 1 Required Output

- Audit Summary
- Current Process Entry Map
- Current Bot Construction And Import Ownership Map
- Current Signal / Shutdown / Restart Entry Map
- Singleton, PID, Runtime Marker, And Logging Bootstrap Map
- Command Registration And Event Registration Map
- Phase 6A-K Boundary Preservation Checklist
- Proposed Phase 6L Target Ownership Model
- Ownership Problems And Refactor Triggers
- Recommended Phase 6L Implementation Scope
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
.\.venv\Scripts\python.exe -m pytest -q tests\test_startup_lifecycle.py tests\test_singleton_lock_Version2.py tests\test_command_registration_smoke.py tests\test_domain_registrars_no_legacy_register_commands.py tests\test_process_utils.py tests\test_file_utils_lockinfo.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Codex Security review should be run before PR handoff for code changes because Phase 6L may touch
process entry, file-backed runtime state, signal handling, environment/config handling, Discord
startup, singleton locks, or restart-sensitive lifecycle behavior.

## Expected Smoke / Manual Verification

After implementation and deployment, manually verify:

- normal watchdog startup acquires singleton lock and writes PID as before
- all Phase 6 startup phases still run in order through `ready_calendar_scheduler_tasks`
- command registration cache behavior remains unchanged
- `/ops graceful_restart` still drains queues, persists live queue state, and restarts through the
  watchdog
- `/ops force_restart` remains available as break-glass
- startup notification and owner/admin diagnostics remain unchanged unless explicitly approved
- no duplicate bot construction, event registration, command registration, queue workers,
  scheduler tasks, or watchdog tasks appear after repeated ready/restart paths

## Remaining Phase 6 Slices

Recommended order after Phase 6K:

1. Final process-entry and bot-construction cleanup.

Phase 6 startup/lifecycle separation is closed after Phase 6L.
The wider command-surface migration/renaming programme, full queue domain redesign, SQL-backed
queue persistence, and pinned calendar tracker atomic-write hardening remain separate deferred
items.

## Deferred Item Links

This starter continues the active lifecycle deferred optimisation in
`docs/reference/deferred_optimisations.md`.

Carry forward, but do not implement unless separately approved:

- full queue domain redesign
- SQL-backed queue persistence
- pinned calendar tracker persistence hardening in `event_calendar/pinned_embed.py`
- wider command-surface migration/renaming programme
