# DL_bot Startup Lifecycle - Phase 6 Audit Starter

## 1. Task Header

- Task name: `DL_bot startup/lifecycle separation - Phase 6 audit`
- Date: `2026-05-26`
- Last updated: `2026-05-28`
- Owner/context: `Follow-up after Phase 5 upload-routing consolidation completed and Phase 6A/6B/6C/6D/6E/6F/6G/6H/6I/6J lifecycle boundaries were pushed to production`
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
- `docs/reference/runbook_diagnostics.md`
- `docs/task_packs/Codex Task Pack - DL_bot Upload Routing Deferred Optimisation Audit.md`
- `docs/task_packs/Codex Chat Starter - DL_bot Phase 6H Queue Worker Lifecycle.md`
- `docs/task_packs/Codex Chat Starter - DL_bot Phase 6I Shutdown Recovery Coordination.md`
- `docs/task_packs/Codex Chat Starter - DL_bot Phase 6J Graceful Restart Shutdown Operations.md`
- `docs/task_packs/Codex Chat Starter - DL_bot Phase 6K Queue Persistence Hardening.md`

Use `docs/reference/ENV_REFERENCE.md` if environment-variable ownership or runtime configuration
validation becomes part of the design.

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
- Usage tracker ownership remained a deliberate follow-up because usage tracking was started in the
  runtime services phase and later startup/prune-loop behaviour remained in `full_startup_sequence()`.

Phase 6C usage tracker lifecycle ownership is complete:

- PR 120 (`codex/dlbot-phase-6c-usage-tracker`) consolidated command, component, metric, and alert
  usage logging onto the shared `usage_tracker.py` singleton.
- `_run_ready_runtime_services()` now owns usage tracker startup and `usage_jsonl_prune` TaskMonitor
  registration.
- `full_startup_sequence()` no longer owns usage observability startup.
- Production smoke testing on 2026-05-27 confirmed usage tracker startup, prune-loop scheduling,
  command/component SQL flushes, and startup sequence continuity.
- The PR was merged and pushed to production.

Phase 6D command sync lifecycle ownership is complete:

- PR 121 (`codex/dlbot-phase-6d-command-lifecycle`) added `core/command_lifecycle.py` and the
  named `ready_command_sync` phase.
- `bot_instance.py:on_ready()` now delegates startup command signature inventory, command-cache
  load/compare/save, scoped sync, timeout telemetry, and loaded-command logging through
  `core.command_lifecycle.run_ready_command_sync()`.
- Production smoke testing on 2026-05-27 confirmed the unchanged-command path, a changed-command
  `/summary` version bump path with successful scoped guild sync and cache update, and a follow-up
  restart returning to `commands_changed result: False`.
- The PR was merged and pushed to production.

Phase 6E command lifecycle admin tooling convergence is complete:

- PR 122 (`codex/dlbot-phase-6e-command-admin-tooling`) reused `core/command_lifecycle.py` from
  `/ops resync_commands`, `/ops validate_command_cache`, and `/ops show_command_versions`.
- `commands/admin_cmds.py` still owns admin permissions, notify-channel gating, ephemeral deferral,
  operation locking, and Discord embeds.
- `core.command_lifecycle` now owns shared command signature sorting, version-line rendering,
  manual scoped sync result handling, atomic command-cache updates, and cache validation logic.
- Production smoke testing on 2026-05-28 confirmed `show_command_versions`,
  `validate_command_cache`, and `resync_commands` loaded and executed, usage telemetry flushed
  normally, and manual command sync logged `[COMMAND SYNC] Slash commands successfully resynced.`
- The PR was merged and pushed to production.

Phase 6F event cache, reminder loading, and rehydration boundary is complete:

- PR 123 (`codex/dlbot-phase-6f-event-rehydration`) added
  `core/event_rehydration_lifecycle.py`.
- `bot_instance.py:on_ready()` now routes event cache/reminder/view rehydration through
  `ready_event_cache_rehydration`, `ready_view_rehydration`, and
  `ready_pinned_calendar_rehydration`.
- The current event-dependent scheduler bundle was deliberately preserved as a compatibility path
  and deferred to Phase 6G for scheduler/task-supervision ownership.
- Production smoke testing on 2026-05-28 confirmed clean startup phase logs, active reminder
  rehydration, event cache load/refresh, tracked view rehydration scheduling, pinned calendar
  rehydration scheduling, Ark/MGE scheduler continuation, `full_startup_sequence()` completion,
  reminder cleanup, daily pinned calendar refresh startup, and calendar reminder loop startup.
- No startup phase failure, event cache failure, tracked-view scheduling failure, pinned-calendar
  scheduling failure, or `on_ready()` critical exception was observed.
- The PR was merged and pushed to production.

Phase 6G scheduler and task-supervision boundary is complete:

- PR 124 (`codex/dlbot-phase-6g-scheduler-lifecycle`) added `core/scheduler_lifecycle.py`.
- `core/scheduler_lifecycle.py` owns scheduler/task registration ordering, readiness gating,
  `TaskMonitor` registration, duplicate-prevention checks, and best-effort logging.
- `bot_instance.py:on_ready()` delegates event-dependent schedulers through
  `ready_event_scheduler_tasks`, the long-running event cache refresh loop through
  `ready_event_cache_refresh_loop`, Ark/MGE schedulers through `ready_domain_scheduler_tasks`, and
  calendar schedulers through `ready_calendar_scheduler_tasks`.
- `reminder_cleanup` deliberately remains at its existing point after `full_startup_sequence()` and
  before pinned calendar rehydration.
- Review feedback restored `refresh_event_cache_task.start()` to its previous position before
  tracked view rehydration via the dedicated `ready_event_cache_refresh_loop` phase and changed Ark
  scheduler registration failure logging to `logger.exception()` for traceback parity.
- Production smoke testing on 2026-05-28 confirmed all Phase 6G lifecycle phases ran in order,
  event-dependent schedulers started after event readiness, `refresh_event_cache_task` armed before
  tracked view rehydration, Ark and MGE schedulers started and ticked, `full_startup_sequence()`
  completed, reminder cleanup started, pinned calendar rehydration completed, daily pinned calendar
  refresh started, and the calendar reminder loop armed.
- No startup phase failure, `on_ready()` critical exception, scheduler registration failure,
  pinned-calendar scheduling failure, or calendar reminder loop failure was observed.
- The PR was merged and pushed to production.

Phase 6H queue worker/live queue lifecycle is complete:

- PR 125 (`codex/dlbot-phase-6h-queue-lifecycle`) added `core/queue_lifecycle.py`.
- `core/queue_lifecycle.py` owns queue worker registration, live queue recovery, best-effort queue
  embed refresh, queue cleanup startup, connection watchdog startup, ordering, logging, and
  `TaskMonitor` duplicate-prevention preservation.
- `bot_instance.py:full_startup_sequence()` delegates queue startup through the named
  `ready_queue_lifecycle` phase at the existing point after restart/log initialization and before
  CrystalTech startup.
- Focused tests cover worker registration ordering, live queue load before embed refresh,
  best-effort embed refresh failure behavior, and duplicate-prevention delegation through
  `TaskMonitor.create()`.
- Production smoke testing on 2026-05-28 confirmed the queue lifecycle phase ran after
  `ready_domain_scheduler_tasks`, queue workers started for the configured monitored channels, live
  queue state loaded before embed refresh, queue cleanup and connection watchdog started once,
  `full_startup_sequence()` completed, reminder cleanup started, pinned calendar rehydration
  completed, and calendar scheduler tasks armed.
- No startup phase failure, `on_ready()` critical exception, queue embed refresh failure,
  `queue_worker` monitor crash, `queue_cleanup` crash, or `connection_watchdog` crash was observed.
- The PR was merged and pushed to production.
- Shutdown coordination was completed next in Phase 6I.

Phase 6I shutdown and recovery coordination is complete:

- PR 126 (`codex/dlbot-phase-6i-shutdown-recovery`) was merged and pushed to production.
- `DL_bot.py` signal shutdown now calls bot-side graceful teardown before `bot.close()`.
- `bot_instance.py` waits briefly for configured `channel_queues`, including in-flight
  `queue.join()` work, persists live queue state through `save_live_queue()`, cancels supervised
  `TaskMonitor` tasks, cancels reminder registries, writes shutdown heartbeat, stops usage
  tracking, and quiesces logging.
- Focused tests cover shutdown ordering, queue drain before `TaskMonitor.stop()`, zero-`qsize()`
  in-flight queue work, and signal teardown ordering.
- Production `/ops force_restart` smoke confirmed the restart flag path, restart recovery,
  `ready_queue_lifecycle`, queue worker startup, queue cleanup, connection watchdog startup,
  `full_startup_sequence()`, reminder cleanup, pinned calendar rehydration, and calendar scheduler
  startup continued normally.
- The production smoke did not produce a reliable in-process graceful shutdown log trail because
  `/ops force_restart` remains a break-glass termination-oriented path. Phase 6I is closed with
  this documented residual risk: the graceful teardown implementation may need rework if the next
  slice exposes a defect while making it directly smoke-testable.

Phase 6J graceful restart and shutdown operations hardening is complete:

- PR 127 (`codex/dlbot-phase-6j-graceful-restart-starter`) was merged and pushed to production.
- `/ops graceful_restart` is now the cooperative restart path that intentionally exercises Phase 6I
  graceful teardown before restart.
- `/ops restart_bot` was removed rather than kept as an overlapping restart route.
- `/ops force_restart` remains the break-glass path for stuck or looping bot states.
- `core/restart_operations.py` owns shared restart marker writing and cooperative restart
  invocation.
- `graceful_shutdown.py` now requests cooperative shutdown first with a configurable timeout
  defaulting to 15 seconds before falling back to external termination.
- Production smoke on 2026-05-28 confirmed queue drain/state flush/task cancellation, usage tracker
  stop, watchdog restart, and startup return through Phase 6 lifecycle logs.
- The smoke log did not include a literal `[SHUTDOWN] Logging quiesced` line; this is expected
  because `quiesce_logging()` is currently silent.

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
| Usage tracker lifecycle ownership | complete | Phase 6C consolidated command/component/metric/alert usage logging onto the shared `usage_tracker.py` singleton and moved usage JSONL pruning into `ready_runtime_services`, preserving startup order and smoke-tested behaviour. |
| Command signature/cache/sync ownership | complete | Phase 6D moved startup command signature/cache/sync handling into `core/command_lifecycle.py` and `ready_command_sync`, preserving cache, scoped sync, timeout telemetry, and loaded-command logging behaviour. |
| Command lifecycle admin tooling convergence | complete | Phase 6E reused `core/command_lifecycle.py` from `/ops resync_commands`, `/ops validate_command_cache`, and `/ops show_command_versions` while preserving admin permissions, embeds, timeout behaviour, and operator-facing summaries. |
| Event cache, reminder loading, and rehydration boundary | complete | Phase 6F separated event cache load/refresh, active reminder loading, event-dependent view rehydration, tracked view rehydration, and pinned calendar view rehydration from the remaining `on_ready()` body with explicit ordering and startup phase logs. Scheduler ownership inside the existing event-dependent bundle was deliberately deferred to Phase 6G. |
| Scheduler and task-supervision boundary | complete | Phase 6G separated scheduler/task registration from the remaining `on_ready()` body and the previous event-dependent bundle while preserving startup order, readiness gates, best-effort behavior, and `TaskMonitor` duplicate prevention. |
| `on_ready()` / `full_startup_sequence()` remaining responsibilities | audit first | Continue extracting in small slices; do not move cache warming, startup notifications, shutdown, and process entry together. |
| Queue worker startup and live queue rehydration | complete | Phase 6H extracted queue worker registration, live queue recovery, best-effort queue embed refresh, queue cleanup startup, and connection watchdog startup into `core/queue_lifecycle.py` and `ready_queue_lifecycle` while preserving ordering and `TaskMonitor` duplicate prevention. PR 125 was smoke tested, merged, and pushed to production. |
| Task monitor/scheduler startup | audit first | Multiple subsystems depend on startup order and duplicate prevention. |
| Graceful shutdown and signal handling | audit first | High blast radius; may be separate PR from startup extraction. |
| SQL/importer contracts | not applicable unless discovered | Phase 6 should avoid SQL/importer contract changes. |

Final decisions should be updated after each Phase 6 sub-phase.

## 13.1 Remaining Phase 6 Slices

Current recommended order after Phase 6J:

1. Phase 6I shutdown and recovery coordination: complete in PR 126 and pushed to production.
   Local validation passed and restart recovery smoke passed, but in-process graceful shutdown logs
   could not be categorically exercised from the current operator paths.
2. Phase 6J graceful restart and shutdown operations hardening: add `/ops graceful_restart`,
   remove `/ops restart_bot`, preserve `/ops force_restart` as break-glass, and update
   `graceful_shutdown.py` so scheduled machine restarts first request cooperative teardown with a
   configurable 15-second default fallback. Complete in PR 127 and pushed to production; smoke
   proved Phase 6I shutdown logs in production.
3. Optional Phase 6K queue persistence hardening slice: harden live queue load/apply semantics,
   atomic save verification, stale metadata handling, and restart/state-flush tests now that the
   cooperative restart path is proven.
4. Final process-entry and bot-construction cleanup: only after the smaller runtime lifecycle
   slices are stable, graceful restart/shutdown operations are smoke-tested, and the optional queue
   persistence hardening decision is made. Review whether `DL_bot.py`, `bot_loader.py`, and
   `bot_instance.py` need a clearer final ownership split.

The wider command-surface migration/renaming programme is deliberately separate from Phase 6.

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
