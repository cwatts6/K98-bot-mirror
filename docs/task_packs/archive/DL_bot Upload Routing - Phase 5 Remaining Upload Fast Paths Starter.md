# DL_bot Upload Routing - Phase 5 Remaining Upload Fast Paths Starter

We are starting Phase 5 of the DL_bot upload-routing optimisation programme after:

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
- Phase 5A extracted the MGE results and KVK Honor routes into `upload_routes/mge_results_route.py`
  and `upload_routes/honor_route.py`, added shared route helpers in `upload_routes/common.py`, was
  smoke tested successfully on 2026-05-26, deployed to production, and closed.
- Phase 5B extracted inventory upload-first routing and weekly activity ingest into
  `upload_routes/inventory_route.py` and `upload_routes/weekly_activity_route.py`, was smoke tested
  successfully on 2026-05-26 with inventory and alliance weekly uploads, deployed to production,
  and closed.
- Phase 5C extracted Rally Forts ingest into `upload_routes/rally_forts_route.py`, was smoke
  tested successfully, merged, deployed to production, and pushed to production.
- Phase 5D extracted main monitored-channel fallback queueing into
  `upload_routes/fallback_queue_route.py`, was smoke tested successfully on 2026-05-26, closed,
  pushed to production, and completed Phase 5 upload-routing consolidation.

## Completion Note

Status: Phase 5A complete in PR 113 (`codex/dlbot-upload-routing-phase-5a`), smoke tested
successfully on 2026-05-26, deployed to production, and closed.

Delivered behaviour:

- `DL_bot.py` delegates MGE results auto-import through `handle_mge_results_upload()`.
- `DL_bot.py` delegates KVK Honor upload ingest through `handle_honor_upload()`.
- `upload_routes/common.py` provides shared notify-channel fallback, source/uploader embed fields,
  and best-effort task scheduling for reuse by later Phase 5 sub-phases.
- The MGE importer remains lazily loaded inside the route handler so MGE import dependency failures
  cannot block bot startup or unrelated message routes.
- SQL headroom preflight runs before workbook reads in the new MGE and Honor routes to avoid
  unnecessary attachment I/O when imports will abort.
- Current Discord output, importer contracts, SQL preflight behaviour, Honor stats refresh,
  background log-backup scheduling, route order, and fall-through behaviour were preserved.

Validation evidence included:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_mge_results_upload_route.py tests/test_honor_upload_route.py tests/test_dl_bot_mge_auto_import.py
.\.venv\Scripts\python.exe -m pytest -q tests/test_mge_results_import.py tests/test_mge_results_import_service.py tests/test_honor_importer.py
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Observed full-suite result: `1498 passed, 2 skipped`. Pytest log-noise validation confirmed
production operational logs were unchanged.

Production smoke evidence confirmed the Honor route passed SQL preflight, parsed and ingested
`1198_honor.xlsx` for `KVK_NO=15`, created `ScanID=40` with `93` rows, and scheduled a successful
background log-backup trigger.

Phase 5B inventory and weekly activity route extraction was completed in PR 114. Its starter packet
is retained for delivery history:
`docs/task_packs/DL_bot Upload Routing - Phase 5B Inventory and Weekly Activity Route Starter.md`.

## Phase 5B Completion Note

Status: Phase 5B complete in PR 114 (`codex/dlbot-upload-routing-phase-5b`), smoke tested
successfully on 2026-05-26 with inventory and alliance weekly uploads, deployed to production, and
closed.

Delivered behaviour:

- `DL_bot.py` delegates inventory upload-first handling through `handle_inventory_upload()`.
- `DL_bot.py` delegates weekly activity ingest through `handle_weekly_activity_upload()`.
- `upload_routes/inventory_route.py` wraps the existing
  `ui.views.inventory_views.handle_inventory_upload_message()` contract without moving inventory
  parsing, OCR/vision, pending session, materials, or SQL/service internals.
- `upload_routes/weekly_activity_route.py` preserves accepted filename matching
  (`1198_alliance_activity.xlsx`), notify-channel fallback, file-read/preflight order, importer
  arguments, duplicate skip output, success/error embeds, exception shielding, and best-effort
  background log-backup scheduling.
- Focused route tests cover inventory delegation/error handling and weekly activity matching,
  non-matching fall-through, SQL preflight abort, success, duplicate skip, importer exception,
  Discord error-notification failure, and notify fallback.

Validation evidence included:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_inventory_upload_route.py tests/test_weekly_activity_upload_route.py tests/test_inventory_upload_flow.py
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Observed full-suite result: `1511 passed, 2 skipped`. Pytest log-noise validation confirmed
production operational logs were unchanged.

Phase 5C Rally Forts upload-route extraction was completed in PR 115. Its starter packet is
retained for delivery history:
`docs/task_packs/DL_bot Upload Routing - Phase 5C Rally Forts Route Starter.md`.

## Phase 5C Completion Note

Status: Phase 5C complete in PR 115 (`codex/dlbot-upload-routing-phase-5c`), smoke tested
successfully, merged, deployed to production, and pushed to production.

Delivered behaviour:

- `DL_bot.py` delegates Rally Forts upload handling through `handle_rally_forts_upload()`.
- `upload_routes/rally_forts_route.py` preserves daily and all-time Rally filename matching,
  local `LOG_DIR/downloads` staging, lazy `forts_ingest` import behaviour, SQL preflight order,
  offload arguments, per-file result aggregation, final Discord embed shape, and best-effort
  background log-backup scheduling.
- Disabled `FORT_RALLY_CHANNEL_ID=0` falls through without sending embeds, matching the existing
  disabled-channel convention.
- Rally upload filenames containing path separators are rejected before local save.
- `forts_ingest.py`, SQL objects, stored procedures, views, file formats, importer contracts, and
  worker queue ownership were not changed.

Validation evidence included:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_rally_forts_upload_route.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_rally_forts_upload_route.py tests\test_weekly_activity_upload_route.py tests\test_honor_upload_route.py tests\test_mge_results_upload_route.py
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Observed final full-suite result after review fixes: `1528 passed, 2 skipped`. Pytest log-noise
validation confirmed production operational logs were unchanged.

Phase 5D fallback queue route extraction was completed in PR 116. Its starter packet is retained
for delivery history:
`docs/task_packs/DL_bot Upload Routing - Phase 5D Fallback Queue Route Starter.md`.

## Phase 5D Completion Note

Status: Phase 5D complete in PR 116 (`codex/dlbot-upload-routing-phase-5d`), smoke tested
successfully on 2026-05-26 with a monitored-channel stats workbook upload, closed, pushed to
production, and confirmed in production logs.

Delivered behaviour:

- `DL_bot.py` delegates main monitored-channel fallback queue handling through
  `handle_fallback_queue_upload()`.
- `upload_routes/fallback_queue_route.py` preserves route order after inventory, player location,
  MGE results, PreKvK, Honor, weekly activity, Rally Forts, and KVK_ALL routes.
- Fallback accepted attachment extensions remain `.xlsx`, `.xls`, and `.csv`.
- Worker queue handoff through `channel_queues` is preserved, including current
  enqueue-once-per-accepted-attachment behaviour.
- `QueueFull` remains a logged drop with no user-facing Discord response.
- Live queue bookkeeping, queue embed updates, command fall-through, and best-effort background
  log-backup scheduling are preserved.
- Review fixes kept synchronous log-backup awaitable construction failures non-fatal and switched
  fallback live-queue appends to the shared `utils.live_queue_lock` async lock used by
  `update_live_queue_embed()` and processing pipeline updates.
- Worker ownership, `processing_pipeline.py`, importer execution, queue persistence semantics,
  SQL/importer contracts, and startup/lifecycle ownership were not changed.

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

## Phase 5 Completion Note

Status: Phase 5 complete. The remaining upload fast paths after Phase 4 now delegate through
focused `upload_routes` modules:

- MGE results: `upload_routes/mge_results_route.py`
- KVK Honor: `upload_routes/honor_route.py`
- Inventory upload-first: `upload_routes/inventory_route.py`
- Weekly activity: `upload_routes/weekly_activity_route.py`
- Rally Forts: `upload_routes/rally_forts_route.py`
- Main monitored-channel fallback queue: `upload_routes/fallback_queue_route.py`

`DL_bot.py` now keeps upload listener/event plumbing and delegates upload-route behaviour. Phase 6
is the next architecture batch and should audit startup/lifecycle ownership separately from upload
routing.

Phase 5 was the remaining fast-path upload-route consolidation slice. It used the proven
`upload_routes` pattern to reduce `DL_bot.py` listener responsibilities while preserving production
behaviour. This section is retained as delivery history.

## Goal

Audit and extract the remaining inline upload fast paths from `DL_bot.py` into focused route
modules or an approved shared upload-router boundary.

The desired end state is:

- `DL_bot.py` delegates remaining upload message handling and keeps upload listener/event plumbing.
- MGE results import, KVK Honour ingest, weekly activity ingest, inventory upload-first routing,
  Rally Forts ingest, and fallback monitored-channel queueing have clear route ownership after
  Phase 5D.
- Shared SQL preflight, offload dispatch, import embed rendering, and route-level structured
  logging are consolidated only where behaviour parity is safe and testable.
- Current Discord output, importer contracts, accepted filenames/extensions, side effects, fallback
  queue behaviour, and fall-through order are preserved unless an explicit behaviour change is
  approved.
- No new SQL schema changes are introduced in this phase.

Step 1 is an audit/design packet, not implementation. Stop before code changes until the route
classification and first PR scope are approved.

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
- `docs/task_packs/DL_bot Upload Routing - Phase 4 KVK_ALL Upload Route Starter.md`
- `docs/task_packs/DL_bot Upload Routing - Phase 5B Inventory and Weekly Activity Route Starter.md`
- `docs/task_packs/DL_bot Upload Routing - Phase 5C Rally Forts Route Starter.md`
- `docs/task_packs/DL_bot Upload Routing - Phase 5D Fallback Queue Route Starter.md`

Use `C:\K98-bot-SQL-Server` as the SQL source of truth for any importer, DAL, export, stored
procedure, view, or output-contract assumptions reviewed during this phase.

## Skills To Use

- `k98-architecture-scope`
- `k98-discord-command-feature`
- `k98-sql-validation`
- `k98-test-selection`
- `k98-deferred-optimisation-capture`
- `k98-pr-review` before any PR handoff
- `k98-promotion-check` only before production promotion/deployment

## Source Deferred Item

### Deferred Optimisation
- Area: `DL_bot.py` remaining fast-path upload routes
- Type: architecture
- Description: After Phase 5C, `DL_bot.py` still owns main monitored-channel fallback queue handling directly in the root listener. Player location, PreKvK, KVK_ALL, MGE results, KVK Honor, inventory upload-first, weekly activity ingest, and Rally Forts ingest now delegate through the `upload_routes` pattern.
- Suggested Fix: Complete Phase 5 with a final Phase 5D audit/scope pass for the main monitored-channel fallback queue route because it touches worker queue ownership, `channel_queues`, `live_queue`, and queue embed side effects.
- Impact: medium
- Risk: medium
- Dependencies: Player-location, PreKvK, validation-blocker, and KVK_ALL phases are complete and production smoke tested; preserve existing Discord output and importer contracts.

## Phase 5 Scope

In scope for Step 1 audit:

- Audit remaining inline upload-related branches in `DL_bot.py`.
- Map route order and fall-through behaviour.
- Classify each remaining path as fix-now, defer, or not applicable for the first Phase 5 PR.
- Identify shared helper candidates for SQL preflight, offload dispatch, notification-channel
  resolution, import result rendering, and route logging.
- Identify which route tests are required for behaviour parity.
- Validate SQL-facing assumptions against `C:\K98-bot-SQL-Server` when reviewing importer or DAL
  contracts.
- Capture out-of-scope findings structurally.

Likely remaining route candidate:

- None. Phase 5D completed the final remaining fallback queue route.

Out of scope until separately approved:

- Changing importer behaviour, workbook/file formats, or result contracts.
- Changing SQL schema, stored procedures, views, export result sets, or Google Sheets contracts.
- Broad `DL_bot.py` startup/lifecycle or `bot_instance.py` refactor.
- KVK_ALL schema modernisation, legacy SQL cleanup, or performance tuning.
- Rewriting the worker queue or processing pipeline beyond route-boundary dependency injection.
- Consolidating slash-command surfaces.

## Current Files To Review

Likely route/listener files:

- `DL_bot.py`
- `upload_routes/player_location_route.py`
- `upload_routes/prekvk_route.py`
- `upload_routes/kvk_all_route.py`
- `upload_routes/mge_results_route.py`
- `upload_routes/honor_route.py`
- `upload_routes/common.py`
- `upload_routes/__init__.py`

Likely importer/service/helper files:

- `mge/mge_results_import.py`
- `honor_importer.py`
- `weekly_activity_importer.py`
- `forts_ingest.py`
- `ui/views/inventory_views.py`
- `file_utils.py`
- `embed_utils.py`
- `bot_helpers.py`
- `processing_pipeline.py`
- `worker.py`
- `log_health.py`

Likely tests:

- `tests/test_dl_bot_mge_auto_import.py`
- `tests/test_mge_results_import.py`
- `tests/test_mge_results_import_service.py`
- `tests/test_honor_importer.py`
- `tests/test_weekly_activity_importer.py` if present
- `tests/test_inventory_*`
- `tests/test_processing_pipeline.py`
- `tests/test_live_queue_persistence.py`
- existing upload-route tests
- new focused route tests for selected Phase 5 slice

## Design Questions

- Should Phase 5D extract fallback monitored-channel queueing into a route module, or should the
  audit recommend leaving it in `DL_bot.py` until Phase 6 lifecycle/queue ownership work?
- Which shared dependency object or helper should be introduced without over-abstracting the route
  pattern proven by player-location, PreKvK, and KVK_ALL?
- Which queue side effects are identical enough to preserve inside a route module, and which
  should remain in `DL_bot.py` until Phase 6?
- Is any SQL-facing contract actually touched by Phase 5D? Current expectation: no.
- What is the minimal first PR that reduces listener complexity without creating a hard-to-review
  broad router rewrite?

## Step 1 Required Output

Phase 5 Step 1 must produce:

- Audit Summary
- Current Remaining Route Map
- Route Order And Fall-Through Map
- Importer / SQL Contract Map
- Discord Output Preservation Map
- Shared Helper Recommendation
- Recommended First PR Scope
- Test And Validation Strategy
- Deferred Optimisation Findings
- Approval Questions
- Explicit Stop Point

Do not write bot code, SQL, tests, or deployment scripts during Step 1.

## Validation Requirements

For audit/design-only work:

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

For implementation after approval, choose validation based on the selected Phase 5 route slice:

- focused new route tests
- relevant importer/service tests for selected routes
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pytest -q tests`

If live SQL integration is intentionally needed, document and validate the opt-in path:

```powershell
$env:RUN_DB_TESTS="1"
.\.venv\Scripts\python.exe -m pytest -q <selected live DB tests>
```

## Acceptance Criteria

- Remaining route responsibilities are mapped before implementation.
- The approved first Phase 5 PR keeps `DL_bot.py` thinner without changing route order or
  fall-through behaviour.
- Current Discord output and importer contracts are preserved.
- No new direct SQL is added to Discord listener/route layers.
- Shared helper extraction is used only where behaviour parity is clear and covered.
- Focused route tests cover matching, non-matching, preflight aborts, importer success/failure,
  exception rendering, side effects, and fall-through for the selected slice.
- Out-of-scope upload-router, lifecycle, SQL, or worker findings are captured structurally.

## Explicit Stop Point

Stop after the Phase 5 audit/design packet.

Do not implement route extraction, alter SQL, change upload routing behaviour, or open a PR until
the audit packet, route classification, and first implementation scope have each been approved.
