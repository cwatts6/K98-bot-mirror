# DL_bot Upload Routing - Phase 5B Inventory and Weekly Activity Route Starter

We are starting Phase 5B of the DL_bot upload-routing optimisation programme after:

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

Phase 5B is the next small upload-routing slice. It should keep using the proven `upload_routes`
pattern and the new `upload_routes/common.py` helpers where the behaviour matches, without forcing
a broad router framework before rally and fallback queueing are scoped.

## Goal

Extract or wrap the next two lower-risk remaining upload paths from `DL_bot.py`:

- Inventory upload-first routing currently delegated inline to
  `ui.views.inventory_views.handle_inventory_upload_message`.
- Weekly activity upload ingest currently implemented inline in `DL_bot.py`.

The desired end state is:

- `DL_bot.py` delegates inventory upload-first handling through an `upload_routes` route module for
  route-order consistency while preserving the existing inventory service/view behaviour.
- `DL_bot.py` delegates weekly activity ingest through an `upload_routes` route module while
  preserving accepted filename matching, SQL preflight behaviour, importer contract, duplicate-skip
  output, success/error embeds, log-backup scheduling, and fall-through behaviour.
- `upload_routes/common.py` is reused for notify-channel fallback, source/uploader embed fields, and
  best-effort task scheduling where appropriate.
- New shared helpers are introduced only when the Phase 5B route contracts prove identical enough to
  test. Do not create a generic upload-router abstraction in this phase.
- No SQL schema, stored procedure, view, file-format, or importer-contract changes are introduced.

Step 1 is an audit/design packet, not implementation. Stop before code changes until the Phase 5B
route classification and first implementation scope are approved.

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

Use `C:\K98-bot-SQL-Server` as the SQL source of truth for weekly activity table, view, index, and
output-contract assumptions reviewed during this phase.

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
- Description: After Phase 5A, `DL_bot.py` still owns weekly activity ingest, rally forts ingest, inventory upload-first routing, and fallback monitored-channel queue handling directly in the root listener. MGE results import and KVK Honor ingest now delegate through `upload_routes/mge_results_route.py` and `upload_routes/honor_route.py`, but the remaining inline routes still contain repeated preflight/offload/rendering/logging and queue-bookkeeping patterns.
- Suggested Fix: Continue Phase 5 with small sub-phases that consolidate the remaining fast paths into the `upload_routes` pattern. Phase 5B should wrap inventory upload-first routing for route-order consistency and extract weekly activity ingest into a focused route module. Reuse `upload_routes/common.py` where the contract is already identical, add shared helpers only when behaviour parity is clear and covered, and avoid changing importer contracts, Discord output, route order, or fallback queue behaviour.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5A is complete and production smoke tested; preserve existing inventory and weekly activity user-facing behaviour.

## Phase 5B Scope

In scope for Step 1 audit:

- Audit the current inventory upload-first branch in `DL_bot.py`.
- Audit `ui.views.inventory_views.handle_inventory_upload_message` only enough to confirm its route
  contract and side effects; do not refactor inventory service/view internals in this phase.
- Audit the current weekly activity branch in `DL_bot.py`.
- Map route order and fall-through behaviour before and after the planned extraction.
- Validate weekly activity SQL-facing assumptions against `C:\K98-bot-SQL-Server`.
- Identify which shared helpers from `upload_routes/common.py` should be reused.
- Identify focused route tests required for behaviour parity.
- Capture out-of-scope findings structurally.

Likely Phase 5B route candidates:

- `upload_routes/inventory_route.py`
- `upload_routes/weekly_activity_route.py`

Out of scope until separately approved:

- Changing inventory parsing, OCR/vision flows, pending session behaviour, materials multi-screenshot
  behaviour, or inventory SQL/service contracts.
- Moving business logic out of `ui.views.inventory_views.py`; Phase 5B may wrap the existing handler
  but should not redesign the inventory interaction flow.
- Changing weekly activity workbook format, parser rules, importer result contract, duplicate
  detection, SQL tables, views, indexes, or Google Sheets/reporting consumers.
- Extracting rally forts upload routing.
- Extracting main monitored-channel fallback queueing.
- Rewriting `channel_queues`, `live_queue`, `processing_pipeline.py`, or worker process ownership.
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
- `upload_routes/__init__.py`

Likely inventory files:

- `ui/views/inventory_views.py`
- `inventory/` package files as needed for route contract confirmation
- `tests/test_inventory_upload_flow.py`
- `tests/test_inventory_views.py`
- `tests/test_inventory_*`

Likely weekly activity files:

- `weekly_activity_importer.py`
- `file_utils.py`
- `embed_utils.py`
- `log_health.py`
- `tests/test_weekly_activity_importer.py` if present
- nearby weekly/activity tests discovered by `rg`

Likely SQL repo objects to validate:

- `dbo.AllianceActivitySnapshotHeader`
- `dbo.AllianceActivitySnapshotRow`
- `dbo.AllianceActivityDelta`
- `dbo.AllianceActivityDaily`
- `dbo.vAllianceActivitySnapshots`
- `dbo.vAllianceActivity_DailyDelta`
- `dbo.vAllianceActivity_WeeklyDelta`
- `dbo.vAllianceActivity_WeeklyCumulative`
- `dbo.vWeekly_AllianceActivity`
- related indexes and constraints on the tables above

## Design Questions

- Should Phase 5B create a very thin inventory route wrapper around
  `handle_inventory_upload_message()` without moving inventory logic, or should inventory remain
  inline until a dedicated inventory service/view audit is scheduled?
- Should the weekly activity route use the same dependency-object pattern as MGE/Honor/PreKvK, with
  injected `send_embed`, `ensure_sql_headroom_or_notify`, `offload_callable`, and
  `trigger_log_backup_background`?
- Should weekly activity notify-channel fallback use `resolve_notify_channel()` from
  `upload_routes/common.py`, preserving current fallback to the source channel when notify lookup
  fails?
- Should duplicate weekly activity uploads keep the current minimal embed with only
  `Status: Duplicate detected for this week. Skipped.`, or should richer source/uploader fields be
  deferred to preserve exact output?
- Which repeated route behaviours are now mature enough for shared helpers, and which should remain
  route-local until rally/fallback queue extraction proves the broader contract?
- What is the minimal route test surface that proves inventory and weekly activity behaviour parity
  without duplicating inventory-service and importer tests?

## Step 1 Required Output

Phase 5B Step 1 must produce:

- Audit Summary
- Current Inventory Route Map
- Current Weekly Activity Route Map
- Route Order And Fall-Through Map
- Weekly Activity SQL Contract Map
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

For implementation after approval, choose validation based on the approved Phase 5B route slice:

- focused new inventory route tests
- focused new weekly activity route tests
- relevant existing inventory upload tests
- relevant existing weekly activity importer tests
- `.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py`
- `.\.venv\Scripts\python.exe scripts\validate_deferred_items.py`
- `.\.venv\Scripts\python.exe scripts\select_tests.py`
- `.\.venv\Scripts\python.exe scripts\smoke_imports.py`
- `.\.venv\Scripts\python.exe scripts\validate_command_registration.py`
- `.\.venv\Scripts\python.exe -m pre_commit run -a`
- `.\.venv\Scripts\python.exe -m pytest -q tests`
- `.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py` when running full-suite or
  deployment-oriented validation

If live SQL integration is intentionally needed, document and validate the opt-in path:

```powershell
$env:RUN_DB_TESTS="1"
.\.venv\Scripts\python.exe -m pytest -q <selected live DB tests>
```

## Acceptance Criteria

- Inventory upload-first route handling is delegated through the approved `upload_routes` boundary
  or explicitly deferred with a structured reason.
- Weekly activity upload ingest is delegated through the approved `upload_routes` boundary within
  the approved scope.
- `DL_bot.py` route order and fall-through behaviour are preserved.
- Inventory user-facing behaviour and inventory service/view contracts are preserved.
- Weekly activity accepted filename matching remains `1198_alliance_activity.xlsx`.
- Weekly activity SQL preflight, importer call arguments, duplicate-skip output, success/error
  embeds, and log-backup scheduling are preserved.
- No new direct SQL is added to Discord listener/route layers.
- `upload_routes/common.py` is reused where behaviour parity is clear and covered.
- Out-of-scope rally, fallback queue, inventory internals, SQL, lifecycle, or worker findings are
  captured structurally.

## Explicit Stop Point

Stop after the Phase 5B audit/design packet.

Do not implement route extraction, alter SQL, change upload routing behaviour, or open a PR until
the audit packet, route classification, and first implementation scope have each been approved.
