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

Phase 5B inventory and weekly activity route extraction is now the next active upload-routing
programme slice. Starter packet:
`docs/task_packs/DL_bot Upload Routing - Phase 5B Inventory and Weekly Activity Route Starter.md`.

Phase 5 is the remaining fast-path upload-route consolidation slice. It should use the proven
`upload_routes` pattern to reduce `DL_bot.py` listener responsibilities while preserving production
behaviour.

## Goal

Audit and extract the remaining inline upload fast paths from `DL_bot.py` into focused route
modules or an approved shared upload-router boundary.

The desired end state is:

- `DL_bot.py` delegates remaining upload message handling and keeps only listener/event plumbing.
- MGE results import and KVK Honour ingest have clear route ownership after Phase 5A. Weekly
  activity ingest, rally forts ingest, inventory upload-first routing, and fallback monitored-channel
  queueing remain to be extracted in later Phase 5 sub-phases.
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
- Description: After Phase 5A, `DL_bot.py` still owns weekly activity ingest, rally forts ingest, inventory upload-first routing, and fallback monitored-channel queue handling directly in the root listener, with repeated preflight/offload/rendering/logging patterns. MGE results import and KVK Honor ingest now delegate through the `upload_routes` pattern.
- Suggested Fix: Continue Phase 5 in small sub-phases, starting with inventory upload-first routing and weekly activity ingest in Phase 5B. Reuse `upload_routes/common.py` where behaviour parity is clear and covered, and only add new shared helpers when later routes prove the same contract.
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

Likely remaining route candidates:

- Inventory upload-first route currently delegated to `ui.views.inventory_views.handle_inventory_upload_message`.
- Weekly activity ingest route.
- Rally forts XLSX auto-ingest route.
- Main monitored-channel fallback queue route.

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

- Should Phase 5 extract all remaining fast paths in one PR, or split into smaller route families
  such as MGE/Honor/Weekly first, Rally second, fallback queue last?
- Should inventory upload-first remain delegated to `ui.views.inventory_views` for this phase, or
  should a thin `upload_routes/inventory_route.py` wrap that existing handler for route-order
  consistency?
- Which shared dependency object or helper should be introduced without over-abstracting the route
  pattern proven by player-location, PreKvK, and KVK_ALL?
- Which repeated embed-rendering patterns are identical enough to consolidate safely, and which
  should remain route-local to preserve exact Discord output?
- Should fallback monitored-channel queueing become a route module, or should it remain at the end
  of `DL_bot.py` until Phase 6 lifecycle/queue ownership is scoped?
- Which SQL contracts need source-of-truth validation before implementation, and which are already
  covered by existing tests?
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
