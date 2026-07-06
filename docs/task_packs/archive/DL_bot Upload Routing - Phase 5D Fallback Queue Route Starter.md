# DL_bot Upload Routing - Phase 5D Fallback Queue Route Starter

We are starting Phase 5D of the DL_bot upload-routing optimisation programme after:

- Phase 1 player-location upload routing was smoke tested successfully and pushed to production.
- Phase 2A PreKvK upload route extraction was smoke tested successfully and pushed to production.
- Phase 2B PreKvK SQL compatibility cleanup was deployed, smoke tested successfully, and pushed to
  production.
- Phase 2C delivered the public read-only `/prekvk report` image report, was smoke tested
  successfully, and pushed to production.
- Phase 2D refactored the scheduled PreKvK stats-alert path onto the Phase 2C report service
  architecture, was smoke tested successfully, and pushed to production.
- Phase 3 local validation blockers were audited and closed as a no-op after the focused blocker
  tests, full suite, and log-noise validation all passed under `.venv`.
- Phase 4 extracted the KVK_ALL route into `upload_routes/kvk_all_route.py`, was smoke tested
  successfully on 2026-05-26, and was pushed to production.
- Phase 5A extracted MGE results and KVK Honor upload routing into
  `upload_routes/mge_results_route.py` and `upload_routes/honor_route.py`, added
  `upload_routes/common.py`, was smoke tested successfully on 2026-05-26, deployed to production,
  and closed.
- Phase 5B extracted inventory upload-first routing and weekly activity ingest into
  `upload_routes/inventory_route.py` and `upload_routes/weekly_activity_route.py`, was smoke tested
  successfully on 2026-05-26 with inventory and alliance weekly uploads, deployed to production,
  and closed.
- Phase 5C extracted Rally Forts ingest into `upload_routes/rally_forts_route.py`, was smoke
  tested successfully, merged, deployed to production, and pushed to production.

Phase 5D was the final upload-routing sub-phase before Phase 6 startup/lifecycle separation. It
was intentionally more sensitive than the previous upload-route slices because the remaining inline
path owned queue handoff, live queue bookkeeping, and queue embed side effects.

## Completion Note

Status: Phase 5D complete in PR 116 (`codex/dlbot-upload-routing-phase-5d`), smoke tested
successfully on 2026-05-26 with a monitored-channel stats workbook upload, closed, pushed to
production, and confirmed in production logs.

Delivered behaviour:

- `DL_bot.py` delegates main monitored-channel fallback queue handling through
  `handle_fallback_queue_upload()`.
- `upload_routes/fallback_queue_route.py` owns monitored-channel fallback matching, supported
  attachment filtering, worker queue handoff, live queue job append, queue embed update, and
  best-effort log-backup scheduling.
- Route order and command fall-through are preserved after all specific fast-path upload routes.
- Accepted fallback attachments remain `.xlsx`, `.xls`, and `.csv`.
- Existing worker queue handoff through `channel_queues` is preserved.
- Existing `QueueFull` behaviour is preserved as a logged drop with no user-facing Discord embed.
- Existing `live_queue["jobs"]` bookkeeping and `update_live_queue_embed()` side effects are
  preserved while using the shared `utils.live_queue_lock` async lock.
- Existing best-effort log-backup scheduling for queued imports is preserved, including non-fatal
  handling for both awaitable construction failures and task scheduling failures.
- No worker-process, `processing_pipeline.py`, queue persistence, SQL/importer, or lifecycle
  ownership changes were introduced.

Validation evidence included:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_fallback_queue_route.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_fallback_queue_route.py tests\test_live_queue_persistence.py tests\test_utils_live_queue.py tests\test_processing_pipeline.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_fallback_queue_route.py tests\test_utils_live_queue.py tests\test_live_queue_persistence.py tests\test_processing_pipeline.py
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Observed full-suite result before final review fixes: `1539 passed, 2 skipped`. Pytest log-noise
validation confirmed production operational logs were unchanged.

Production smoke evidence confirmed a monitored-channel workbook upload was recognized by
`upload_routes.fallback_queue_route`, enqueued for the worker, triggered a successful background
log-backup request, and completed the downstream processing pipeline through Excel processing,
archive, SQL procedure, export, ProcConfig import, cache refresh, and final success summary.

Phase 5 upload-routing consolidation is now complete. Phase 6 remains required for
startup/lifecycle separation and should audit `DL_bot.py`, `bot_instance.py`, startup/shutdown
runbooks, task supervision, singleton/runtime concerns, queue worker lifecycle, live queue
rehydration, scheduler startup, and restart-safe state separately from upload routing.

## Goal

Audit and, if approved, extract the main monitored-channel fallback queue route from `DL_bot.py`
into a focused upload-route boundary while preserving production behaviour.

The desired end state is:

- `DL_bot.py` keeps listener/event plumbing and delegates monitored-channel fallback queueing
  through an approved boundary.
- Route order and fall-through behaviour are preserved after all specific fast-path upload routes.
- Accepted fallback attachments remain unchanged: `.xlsx`, `.xls`, and `.csv`.
- Existing worker queue handoff through `channel_queues` is preserved.
- Existing `QueueFull` behaviour is preserved.
- Existing `live_queue["jobs"]` bookkeeping and `update_live_queue_embed()` side effects are
  preserved.
- Existing best-effort log-backup scheduling for queued imports is preserved.
- No worker-process, `processing_pipeline.py`, queue persistence, SQL/importer, or lifecycle
  ownership changes are introduced unless explicitly approved after the audit packet.

Step 1 was completed before implementation. This starter is retained for delivery history.

## Required Reading

Before audit work, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`
- `docs/reference/deferred_optimisations.md`
- `docs/task_packs/Codex Task Pack - DL_bot Upload Routing Deferred Optimisation Audit.md`
- `docs/task_packs/DL_bot Upload Routing - Phase 5 Remaining Upload Fast Paths Starter.md`
- `docs/task_packs/DL_bot Upload Routing - Phase 5C Rally Forts Route Starter.md`

Use `docs/reference/runbook_diagnostics.md` only if the audit needs deeper diagnostics, telemetry,
offload, queue recovery, or log-backup context. Use `docs/reference/runbook_startup.md`,
`docs/reference/runbook_shutdown.md`, and `docs/reference/singleton_lock.md` only if the audit
discovers startup, shutdown, or lifecycle implications that cannot be classified without them.

## Skills To Use

- `k98-architecture-scope`
- `k98-discord-command-feature`
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review` before any PR handoff
- `k98-promotion-check` only before production promotion/deployment

Use `k98-sql-validation` only if the audit unexpectedly reaches SQL-facing importer contracts.
The intended Phase 5D route boundary should not change SQL objects.

## Source Deferred Item

### Deferred Optimisation
- Area: `DL_bot.py` remaining fast-path upload routes
- Type: architecture
- Description: After Phase 5C, `DL_bot.py` still owns the main monitored-channel fallback queue handling directly in the root listener. Player location, PreKvK, KVK_ALL, MGE results, KVK Honor, inventory upload-first, weekly activity ingest, and Rally Forts ingest now delegate through the `upload_routes` pattern, but the fallback queue path still mixes monitored-channel matching, worker queue handoff, `live_queue` bookkeeping, queue embed updates, and best-effort log-backup scheduling in the listener.
- Suggested Fix: Complete Phase 5 with a final Phase 5D audit/scope pass for the main monitored-channel fallback queue route. Extract the fallback queue path into a focused `upload_routes` boundary only if the audit confirms route-order, queue ownership, `channel_queues`, `live_queue`, queue embed, worker handoff, and background log-backup side effects can be preserved with focused tests. Keep broader worker/lifecycle ownership and `processing_pipeline.py` refactors out of Phase 5D unless explicitly approved.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5C is complete, smoke tested, merged, deployed, and production-pushed.

## Phase 5D Scope

In scope for Step 1 audit:

- Audit the current main monitored-channel fallback branch in `DL_bot.py`.
- Map exact route order after inventory, player location, MGE results, PreKvK, Honor, weekly
  activity, Rally Forts, and KVK_ALL routes.
- Audit `CHANNEL_IDS` matching and disabled/empty configuration behaviour.
- Audit `bot_helpers.channel_queues` construction and queue lookup expectations.
- Audit `QueueFull` handling and message drop logging.
- Audit `live_queue["jobs"]` mutation, `LIVE_QUEUE_LOCK`, and `update_live_queue_embed()` calls.
- Audit `trigger_log_backup_background()` scheduling after successful queue handoff.
- Identify whether a thin `upload_routes/fallback_queue_route.py` can preserve behaviour without
  moving worker ownership.
- Identify focused route tests required for behaviour parity.
- Capture worker/lifecycle/persistence findings structurally when they exceed the approved route
  boundary.

Likely Phase 5D route candidate:

- `upload_routes/fallback_queue_route.py`

Out of scope until separately approved:

- Rewriting `channel_queues` ownership or worker startup.
- Rewriting `processing_pipeline.py`, importer execution, or worker process orchestration.
- Changing queue size, retry, duplicate enqueue, or drop semantics.
- Changing live queue persistence in `utils.py`.
- Changing queue embed content or persistence semantics unless required for parity.
- Changing monitored-channel config semantics.
- Changing SQL schema, importers, workbook/file formats, or downstream processing contracts.
- Broad `DL_bot.py` startup/lifecycle or `bot_instance.py` refactor.

## Current Files To Review

Likely route/listener files:

- `DL_bot.py`
- `upload_routes/common.py`
- `upload_routes/player_location_route.py`
- `upload_routes/prekvk_route.py`
- `upload_routes/kvk_all_route.py`
- `upload_routes/mge_results_route.py`
- `upload_routes/honor_route.py`
- `upload_routes/inventory_route.py`
- `upload_routes/weekly_activity_route.py`
- `upload_routes/rally_forts_route.py`
- `upload_routes/__init__.py`

Likely queue/worker/helper files:

- `bot_config.py`
- `bot_helpers.py`
- `utils.py`
- `processing_pipeline.py`
- `file_utils.py`
- `log_health.py`

Likely tests:

- `tests/test_processing_pipeline.py`
- `tests/test_live_queue_persistence.py`
- `tests/test_utils_live_queue.py`
- `tests/test_offload_callable_integration.py`
- `tests/test_offload_monitor_once.py`
- `tests/test_offload_registry_rotation.py`
- `tests/test_offload_serialization.py`
- `tests/test_maintenance_suite.py`
- existing upload-route tests
- new focused fallback queue route tests if implementation is approved

## Design Questions

- Should Phase 5D extract fallback queueing into `upload_routes/fallback_queue_route.py`, or should
  the audit recommend leaving this path inline until Phase 6 because queue/lifecycle ownership is
  too tightly coupled?
- If extracted, should the route receive `channel_queues`, `live_queue`, `LIVE_QUEUE_LOCK`,
  `update_live_queue_embed`, and `trigger_log_backup_background` through a dependency dataclass?
- Should the route return `True` when a monitored-channel message has attachments but no supported
  `.xlsx/.xls/.csv` file, preserving the current listener behaviour of processing commands after
  the branch?
- Should queue embed update failures remain logged and non-fatal exactly as today?
- Should `QueueFull` remain a logged drop with no user-facing Discord embed?
- Should live queue bookkeeping continue to append once per accepted attachment even though the
  message is enqueued once per accepted attachment under current behaviour?
- What focused tests prove parity without invoking real worker processes?
- Should Phase 6 begin immediately after Phase 5D, or should a short phase-end cleanup PR update
  docs/backlog first?

## Step 1 Required Output

Phase 5D Step 1 must produce:

- Audit Summary
- Current Fallback Queue Route Map
- Route Order And Fall-Through Map
- Queue / Worker Handoff Map
- Live Queue / Queue Embed Side-Effect Map
- Local File / Attachment Filtering Map
- Shared Helper Recommendation
- Recommended First PR Scope
- Test And Validation Strategy
- Deferred Optimisation Findings
- Phase 6 Recommendation
- Approval Questions
- Explicit Stop Point

Step 1 output was completed before implementation.

## Validation Requirements

For audit/design-only work, the expected checks were:

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

For implementation after approval, validation was selected from:

- focused new fallback queue route tests
- relevant existing queue/live-queue tests
- relevant existing processing pipeline smoke/regression tests where practical
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pre_commit run -a`
- `.\.venv\Scripts\python.exe -m pytest -q tests`
- `.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py` when running full-suite or
  deployment-oriented validation

## Acceptance Criteria

- Fallback monitored-channel queue handling is either delegated through an approved boundary or
  explicitly kept inline with a documented reason.
- `DL_bot.py` route order and fall-through behaviour are preserved.
- Accepted fallback attachment extensions remain `.xlsx`, `.xls`, and `.csv`.
- Worker queue handoff through `channel_queues` is preserved.
- `QueueFull` handling is preserved.
- `live_queue` bookkeeping and queue embed update side effects are preserved.
- Best-effort log-backup scheduling after queued imports is preserved.
- No new direct SQL is added to Discord listener/route layers.
- No worker/lifecycle/startup refactor is bundled into the route extraction.
- Out-of-scope worker, lifecycle, persistence, queue-embed, SQL, or processing-pipeline findings
  are captured structurally.
- The implementation packet explicitly states whether Phase 6 remains required. Current expected
  answer: yes, Phase 6 is required for startup/lifecycle separation after Phase 5D.

## Explicit Stop Point

Completed. Do not reopen Phase 5D. Use
`docs/task_packs/DL_bot Startup Lifecycle - Phase 6 Audit Starter.md` for startup/lifecycle
separation and broader queue ownership audits.
