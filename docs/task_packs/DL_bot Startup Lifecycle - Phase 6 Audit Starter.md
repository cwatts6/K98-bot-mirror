# DL_bot Startup Lifecycle - Phase 6 Audit Starter

## 1. Task Header

- Task name: `DL_bot startup/lifecycle separation - Phase 6 audit`
- Date: `2026-05-26`
- Last updated: `2026-05-27`
- Owner/context: `Follow-up after Phase 5 upload-routing consolidation completed and Phase 6A/6B startup lifecycle boundaries were pushed to production`
- Task type: `deferred optimisation batch`
- One-pass approved: `no`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

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
- `docs/task_packs/DL_bot Upload Routing - Phase 5 Remaining Upload Fast Paths Starter.md`
- `docs/task_packs/DL_bot Upload Routing - Phase 5D Fallback Queue Route Starter.md`

Use `docs/reference/runbook_diagnostics.md` if the audit needs deeper diagnostics, telemetry,
offload registry, queue recovery, watchdog, or log-backup context. Use `docs/reference/ENV_REFERENCE.md`
if environment-variable ownership or runtime configuration validation becomes part of the design.

SQL validation is not expected for the first Phase 6 audit unless the review unexpectedly reaches
SQL-backed cache, import, export, report, or ProcConfig contracts. If it does, validate relevant
schema, procedure, view, index, and `ProcConfig` details against:

`C:\K98-bot-SQL-Server`

## 3. Objective

Perform a full audit of `DL_bot.py` and `bot_instance.py` startup/lifecycle responsibilities after
Phase 5 upload routing has been separated. Produce a careful target ownership model and PR-sized
implementation plan before any code changes.

Phase 6 should separate process entry, bot construction, command/event registration, startup
sequence, task supervision, queue worker lifecycle, graceful shutdown, singleton/runtime files, and
restart-safe state concerns without changing upload-route behaviour.

## 4. Background

Phase 5 upload-routing consolidation is complete:

- Phase 5A extracted MGE results and KVK Honor routes.
- Phase 5B extracted inventory upload-first and weekly activity routes.
- Phase 5C extracted Rally Forts routing.
- Phase 5D extracted main monitored-channel fallback queueing.

Phase 6A startup lifecycle boundary is complete:

- PR 117 (`codex/dlbot-phase-6-startup-lifecycle-1`) added `core/startup_lifecycle.py`.
- `bot_instance.py:on_ready()` now delegates the initial loop/console bootstrap through
  `run_startup_phases([StartupPhase("ready_runtime_bootstrap", ...)])`.
- Smoke testing on 2026-05-27 confirmed the expected `ready_runtime_bootstrap` phase started,
  installed the global asyncio exception handler, completed, and then allowed normal heartbeat,
  health dashboard, command-cache, scheduler, queue worker, rehydration, and full startup logs to
  continue.
- The PR was merged and pushed to production.

Phase 6B runtime services extraction is complete:

- PR 119 (`codex/dlbot-phase-6b-runtime-services`) added the named
  `ready_runtime_services` phase after `ready_runtime_bootstrap`.
- `bot_instance.py:on_ready()` now delegates heartbeat, health dashboard, offload monitor,
  `PIL.Image.show()` safety patch, lock-file cleanup, usage tracker startup, daily summary,
  activity tracking, UTC clock, and member-count status loops through `run_startup_phases()`.
- Smoke testing on 2026-05-27 confirmed the expected `ready_runtime_services` phase started,
  started the runtime services, completed, and then allowed command cache, event cache,
  rehydration, schedulers, queue workers, and `full_startup_sequence()` to continue.
- The PR was merged and pushed to production.
- Usage tracker ownership remains a deliberate follow-up because usage tracking is started in the
  runtime services phase and later startup/prune-loop behaviour remains in `full_startup_sequence()`.

`DL_bot.py` is now much closer to listener/delegation ownership for uploads, but startup and
lifecycle concerns remain spread across `DL_bot.py`, `bot_instance.py`, `bot_loader.py`,
`bot_helpers.py`, startup gates, singleton locks, background task monitors, queue workers, and
shutdown handlers. Phase 6 should audit these boundaries before proposing code movement.

## 5. Scope

### In Scope

- Audit `DL_bot.py` process entry, logging bootstrap, environment checks, singleton lock handling,
  command registration, event listener ownership, signal handling, graceful shutdown, and
  `bot.run()` flow.
- Audit `bot_instance.py` bot construction, event registration, `on_ready()`, `full_startup_sequence()`,
  task monitor usage, cache warming, view/handler rehydration, scheduler startup, queue worker
  startup, live queue rehydration, and shutdown hooks.
- Audit `bot_loader.py`, `bot_startup_gate.py`, `boot_safety.py`, `startup_utils.py`,
  `singleton_lock.py`, `bot_helpers.py`, `utils.py`, `logging_setup.py`, and `constants.py` only
  as needed to map lifecycle ownership.
- Map runtime state that must survive restart: singleton locks, PID files, shutdown markers,
  command cache, live queue cache, view/event/reminder trackers, offload registry, and scheduler
  state.
- Identify duplicate or unclear ownership between process-level startup, bot instance startup, and
  helper modules.
- Identify a safe Phase 6 first PR slice after the audit. The first implementation slice should be
  smaller than the full lifecycle redesign.
- Define focused tests and validation gates before implementation.
- Capture out-of-scope findings structurally.

### Out of Scope

- No implementation during Step 1 audit.
- No broad rewrite of `DL_bot.py` or `bot_instance.py` in one PR.
- No upload-route behaviour changes.
- No importer, workbook, SQL, Google Sheets, ProcConfig, or processing-pipeline contract changes.
- No command-surface consolidation.
- No deployment/promotion action without a separate promotion check.
- No destructive lock, PID, cache, or persisted-state cleanup without explicit approval.

## 6. Source Deferred Items

```md
### Deferred Optimisation
- Area: `DL_bot.py`, `bot_instance.py` startup and lifecycle
- Type: architecture
- Description: Startup and lifecycle responsibilities remain spread across `DL_bot.py` and `bot_instance.py`, including interpreter/startup checks, bot construction/import wiring, event registration, singleton/runtime concerns, signal/shutdown handling, task supervision, queue worker startup, live queue rehydration, cache warming, scheduler startup, and lifecycle coordination for the wider bot. Phase 5 completed upload-route separation, so lifecycle ownership can now be audited independently.
- Suggested Fix: Start Phase 6 from `docs/task_packs/DL_bot Startup Lifecycle - Phase 6 Audit Starter.md`. Audit `DL_bot.py`, `bot_instance.py`, `bot_loader.py`, `bot_startup_gate.py`, `boot_safety.py`, `startup_utils.py`, `singleton_lock.py`, `bot_helpers.py`, `utils.py`, and startup/shutdown runbooks before proposing any implementation. Define a target ownership model for process entry, bot construction, command registration, event registration, startup sequencing, task supervision, queue worker lifecycle, graceful shutdown, singleton/runtime files, and restart-safe state. Stop for approval before code changes.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5 upload routing is complete, smoke tested, closed, and production-pushed; proceed with audit/design before implementation.
```

## 7. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Mandatory before implementation; Phase 6 is architecture-sensitive lifecycle work. |
| `k98-discord-command-feature` | use | Startup/event registration, persistent views, rehydration, and scheduler startup affect Discord runtime behaviour. |
| `k98-sql-validation` | use if needed | Only if the audit reaches SQL-backed cache/import/export/ProcConfig contracts. |
| `k98-test-selection` | use | Required before validation; combine `scripts/select_tests.py` with lifecycle risk-based tests. |
| `k98-deferred-optimisation-capture` | use | Capture out-of-scope lifecycle, queue, task, logging, or persistence findings structurally. |
| `k98-pr-review` | use | Required before PR handoff because startup/lifecycle changes are high blast-radius. |
| `k98-promotion-check` | use before promotion only | Required before production promotion, bot-machine pull/restart, or production PR creation. |
| `codex-security:security-scan` | use before PR handoff if code changes | Startup, secrets/config, file handling, network calls, Discord interactions, and restart-sensitive persistence are security-sensitive surfaces. |

## 8. Mandatory Workflow

1. Audit / scope review, then stop for approval.
2. Architecture validation and target ownership model, then stop for approval.
3. PR-sized implementation plan, then stop for approval.
4. Implementation only after approval.
5. Validation and final review.
6. Codex Security review for code changes, or documented skip reason for docs-only work.

Do not proceed in one pass.

## 9. Audit Requirements

Review and map:

- process entry and import-time side effects
- logging bootstrap and file/queue logging ownership
- environment and interpreter/startup checks
- singleton lock acquisition/release and PID/runtime files
- bot construction and `bot_loader.py` ownership
- command registration and secondary command surface gating
- Discord event registration and `on_ready()` ownership
- startup gate/idempotency behaviour
- cache warming and cache failure handling
- persistent view and message rehydration
- queue worker startup, channel queue ownership, and live queue rehydration
- scheduler startup for Ark, MGE, calendar/events, reminders, subscriptions, maintenance, and UTC clock
- task monitor / background task supervision
- graceful shutdown, signal handling, cancellation, and logging flush order
- restart markers, crash recovery, and admin startup/shutdown notifications
- tests that currently cover startup, registration, scheduler startup, live queue persistence, and singleton locks

Produce these Step 1 outputs:

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

## 10. Architecture Targets

| Concern | Target |
|---|---|
| Process entry, signal wiring, `bot.run()` | `DL_bot.py` or a small process-entry module after approval |
| Bot construction singleton | `bot_loader.py` / `bot_instance.py` with one clear owner |
| Startup sequencing | service/helper boundary with idempotency and task ownership explicit |
| Event registration | one clear event-owner module; avoid duplicate registration paths |
| Queue worker lifecycle | one boundary that starts workers, rehydrates live queue state, and documents ownership |
| Task supervision | `TaskMonitor` or equivalent central lifecycle owner |
| Shutdown | one coordinated path for cancellation, state flush, locks, markers, and logging shutdown |
| Runtime files | `constants.py` paths plus focused helpers for atomic state writes |
| Tests | focused lifecycle tests in `tests/`, plus smoke/import/registration validators |

## 11. Likely Files

### Review

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
- `command_regenerate.py`
- `scripts/smoke_imports.py`
- `scripts/validate_command_registration.py`
- `docs/reference/runbook_startup.md`
- `docs/reference/runbook_shutdown.md`
- `docs/reference/singleton_lock.md`
- `tests/test_command_registration_smoke.py`
- `tests/test_domain_registrars_no_legacy_register_commands.py`
- `tests/test_mge_startup_hook_invoked.py`
- `tests/test_mge_rehydrate_and_regression.py`
- `tests/test_live_queue_persistence.py`
- `tests/test_utils_live_queue.py`
- `tests/test_singleton_lock_Version2.py`
- `tests/test_maintenance_suite.py`

### Modify

To be decided after Step 1 approval.

Likely first-slice candidates after audit:

- `DL_bot.py`
- `bot_instance.py`
- one small lifecycle helper module if the audit proves a clean extraction
- focused lifecycle tests
- startup/shutdown runbook notes

### Create

To be decided after Step 1 approval.

Possible candidates:

- `core/lifecycle.py`
- `core/startup_sequence.py`
- `core/shutdown.py`
- `tests/test_startup_lifecycle.py`

Do not create new lifecycle modules until the ownership model is approved.

## 12. Implementation Requirements

- Preserve production startup, shutdown, and command registration behaviour unless an explicit
  behaviour change is approved.
- Keep upload-route behaviour unchanged.
- Avoid moving large blocks without tests.
- Make idempotency and duplicate-start prevention explicit.
- Keep persistent/restart-sensitive state safe.
- Use existing helpers before adding new ones.
- Keep long-running or blocking cleanup bounded or offloaded.
- Preserve logging and improve it only where the audit finds ambiguity.
- Capture larger queue/lifecycle/task-supervision debt structurally if it exceeds the approved
  first PR.

## 13. Refactor Decisions

Initial classification before audit:

| Issue | Decision | Reason |
|---|---|---|
| Upload-route consolidation | not applicable | Phase 5 is complete; do not reopen routing in Phase 6. |
| Process entry and singleton lock ownership | audit first | High-impact startup path; define target ownership before edits. |
| Bot construction and event registration ownership | audit first | Current ownership is spread across `bot_loader.py`, `bot_instance.py`, and `DL_bot.py`. |
| Initial `on_ready()` runtime bootstrap boundary | complete | Phase 6A moved loop exception handler setup and console-handler cleanup behind `ready_runtime_bootstrap`, preserving startup order and adding named phase logs. |
| Runtime services/observability startup | complete | Phase 6B moved heartbeat, health dashboard, offload monitor, PIL safety patch, lock cleanup, usage tracker, daily summary, activity listeners, and status-channel loops behind `ready_runtime_services`, preserving startup order and smoke-tested behaviour. |
| Usage tracker lifecycle ownership | next recommended slice | Usage tracking now has clearer phase attribution but still has split ownership between `ready_runtime_services`, `full_startup_sequence()`, and shutdown. Audit and consolidate this before broader `full_startup_sequence()` extraction. |
| `on_ready()` / `full_startup_sequence()` remaining responsibilities | audit first | Continue extracting in small slices; do not move command sync, event rehydration, schedulers, queue workers, startup notifications, and shutdown together. |
| Queue worker startup and live queue rehydration | audit first | Restart-sensitive; must preserve worker handoff and live queue persistence. |
| Task monitor/scheduler startup | audit first | Multiple subsystems depend on startup order and duplicate prevention. |
| Graceful shutdown and signal handling | audit first | High blast radius; may be separate PR from startup extraction. |
| SQL/importer contracts | not applicable unless discovered | Phase 6 should avoid SQL/importer contract changes. |

Final decisions should be updated after each Phase 6 sub-phase.

## 14. Testing Requirements

Consider and document:

- happy path startup
- repeated `on_ready()` / startup gate idempotency
- command registration smoke
- persistent view or scheduler startup paths touched
- queue worker startup and live queue rehydration
- shutdown/cancellation/state persistence where touched
- singleton lock acquisition/release
- smoke imports without runtime side effects
- command-registration duplicate warnings
- log-noise and production operational log boundaries when running broad tests

Baseline audit/design-only commands:

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

Implementation validation should be selected after scope approval. Likely commands include:

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

## 15. Acceptance Criteria

- [ ] Phase 6 audit/scope packet is completed before implementation.
- [ ] Current startup, shutdown, task, queue, and persistence ownership is mapped.
- [ ] Target lifecycle ownership model is approved before code changes.
- [ ] First implementation slice is PR-sized and approved.
- [ ] Upload-route behaviour remains unchanged.
- [ ] Startup and shutdown remain idempotent and restart-safe.
- [ ] Queue worker lifecycle and live queue persistence remain safe.
- [ ] Command registration and duplicate-surface guardrails remain intact.
- [ ] Tests are added/updated or clear skip reasons are documented.
- [ ] Quality gates are run or documented.
- [ ] Codex Security review is run before PR handoff for code changes, or skipped only for
  documentation-only work with a reason.
- [ ] Deferred optimisations are captured structurally.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. Helpers Reused
7. Refactor Findings
8. Test Plan
9. AI Review Gates
10. Deployment Steps
11. Deferred Optimisations

For Step 1 audit only, include:

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

## 17. PR Summary Template

```md
## Summary

- Audit and separate DL_bot startup/lifecycle ownership after Phase 5 upload-route completion.
- Preserve runtime behaviour while moving only the approved lifecycle slice.

## Changes

- Map current startup, shutdown, task supervision, queue worker, and restart-state ownership.
- Implement the approved PR-sized lifecycle boundary after audit approval.

## Tests

- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- focused lifecycle pytest commands selected during audit
- broader repo gates as required by the approved implementation scope

## AI Review Gates

- Codex Security: run before PR handoff for code changes; skip only for docs-only work with reason.

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- Risk: medium-high; startup/lifecycle changes can affect bot availability, task duplication,
  restart safety, and shutdown behaviour.
- Rollback: revert the lifecycle PR and restart from the last known-good production branch.
```

## 18. Required Stop Point

Stop after the Phase 6 audit/scope packet.

Do not implement startup extraction, move event registration, alter singleton/runtime file
ownership, change queue worker lifecycle, alter shutdown behaviour, or open a PR until the audit
packet, target architecture, and first implementation scope have each been approved.
