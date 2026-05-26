# DL_bot Upload Routing - Phase 5C Rally Forts Route Starter

We are starting Phase 5C of the DL_bot upload-routing optimisation programme after:

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

Phase 5C is the next small upload-routing slice. It should keep using the proven `upload_routes`
pattern and `upload_routes/common.py` helpers where behaviour matches. Do not pull the main
monitored-channel fallback queue into this phase unless explicitly approved after the audit packet.

## Goal

Extract Rally Forts XLSX auto-ingest from `DL_bot.py` into a focused route module while preserving
production behaviour.

The desired end state is:

- `DL_bot.py` delegates Rally Forts upload handling through an `upload_routes` route module.
- Route order and fall-through behaviour are preserved.
- Accepted file matching is preserved:
  - daily: `Rally_data_DD-MM-YYYY.xlsx`
  - all-time: `Rally[_\s]?data.*all[\s_]?time.*\.xlsx`
- Local download staging under `LOG_DIR/downloads` is preserved unless a safer equivalent is
  explicitly approved.
- Lazy import behaviour for `forts_ingest` is preserved so missing optional dependencies do not
  crash startup.
- SQL preflight behaviour, offload dispatch, per-file result aggregation, skip/error rendering,
  final Discord embed shape, and best-effort log-backup scheduling are preserved.
- No SQL schema, stored procedure, view, file-format, importer-contract, or worker queue changes
  are introduced.

Step 1 is an audit/design packet, not implementation. Stop before code changes until the Phase 5C
route classification and implementation scope are approved.

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

Use `C:\K98-bot-SQL-Server` as the SQL source of truth for Rally Forts table, staging table, view,
stored procedure, index, and output-contract assumptions reviewed during this phase.

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
- Description: After Phase 5B, `DL_bot.py` still owns Rally Forts ingest and main monitored-channel fallback queue handling directly in the root listener. Player location, PreKvK, KVK_ALL, MGE results, KVK Honor, inventory upload-first, and weekly activity ingest now delegate through the `upload_routes` pattern, but the remaining inline routes still contain route-specific preflight/offload/rendering/logging and queue-bookkeeping patterns.
- Suggested Fix: Continue Phase 5 with small sub-phases that consolidate the remaining fast paths into the `upload_routes` pattern. Phase 5C should extract Rally Forts ingest into a focused route module while preserving filename matching, local download staging, importer contracts, SQL preflight, per-file result aggregation, Discord output, and log-backup scheduling. Phase 5D should separately scope the main monitored-channel fallback queue route because it touches worker queue ownership, `channel_queues`, `live_queue`, and queue embed side effects.
- Impact: medium
- Risk: medium
- Dependencies: Phase 5B is complete, smoke tested, deployed, and production-pushed; preserve Rally Forts user-facing behaviour and importer contracts.

## Phase 5C Scope

In scope for Step 1 audit:

- Audit the current Rally Forts branch in `DL_bot.py`.
- Audit `is_rally_daily()` and `is_rally_alltime()` route matching.
- Audit `forts_ingest.import_rally_daily_xlsx()` and `forts_ingest.import_rally_alltime_xlsx()`
  only enough to confirm route contract, local-path contract, SQL objects, result shape, and
  side effects.
- Map route order and fall-through behaviour before and after the planned extraction.
- Validate Rally Forts SQL-facing assumptions against `C:\K98-bot-SQL-Server`.
- Identify which shared helpers from `upload_routes/common.py` should be reused.
- Identify focused route tests required for behaviour parity.
- Capture out-of-scope findings structurally.

Likely Phase 5C route candidate:

- `upload_routes/rally_forts_route.py`

Out of scope until separately approved:

- Extracting main monitored-channel fallback queueing.
- Rewriting `channel_queues`, `live_queue`, `processing_pipeline.py`, or worker process ownership.
- Changing Rally workbook formats, parser rules, importer result contracts, duplicate detection,
  SQL tables, staging tables, stored procedures, views, indexes, or export/reporting consumers.
- Moving Rally importer SQL access out of `forts_ingest.py`.
- Changing local file download retention, naming, or cleanup semantics unless needed for parity.
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
- `upload_routes/__init__.py`

Likely Rally files:

- `forts_ingest.py`
- `file_utils.py`
- `embed_utils.py`
- `log_health.py`
- `tests/test_file_utils.py`
- `tests/test_file_utils_build_cmd.py`
- nearby Rally/Forts tests discovered by `rg`

Likely SQL repo objects to validate:

- `dbo.stg_RallyDaily`
- `dbo.stg_RallyAllTime`
- `dbo.cur_RallyDaily`
- `dbo.cur_RallyTotals_Base`
- `dbo.IngestionLog`
- `dbo.sp_Import_Rally_Daily`
- `dbo.sp_Import_Rally_AllTime`
- `dbo.v_RallyDaily_Latest`
- `dbo.v_RallyTotals_Current`
- `dbo.vFortsCompleted_WeekToDate`
- `dbo.sp_Rebuild_RALLY_EXPORT`
- related indexes and constraints on the tables above

## Design Questions

- Should Phase 5C move `is_rally_daily()` and `is_rally_alltime()` into the new Rally route module
  as route-local helpers?
- Should the route preserve local download staging exactly with `att.save(local_path)`, or should
  download path handling be dependency-injected for tests while keeping the production path the
  same?
- Should Rally notify-channel fallback use `resolve_notify_channel()` from
  `upload_routes/common.py`, preserving current fallback to the source channel when notify lookup
  fails?
- Should per-success log-backup scheduling use `schedule_best_effort()` from
  `upload_routes/common.py`?
- Should import failure and final embed send failures be swallowed or logged in exactly the same
  way as the inline branch?
- What route tests prove behaviour parity without adding live SQL or filesystem-heavy integration
  coverage?
- Should Phase 5D be required? Current recommendation: yes. Phase 5D should be the final
  upload-routing sub-phase and should focus only on the main monitored-channel fallback queue route.

## Step 1 Required Output

Phase 5C Step 1 must produce:

- Audit Summary
- Current Rally Forts Route Map
- Route Order And Fall-Through Map
- Rally SQL Contract Map
- Discord Output Preservation Map
- Local Download / File Handling Map
- Shared Helper Recommendation
- Recommended First PR Scope
- Test And Validation Strategy
- Deferred Optimisation Findings
- Phase 5D Recommendation
- Approval Questions
- Explicit Stop Point

Do not write bot code, SQL, tests, or deployment scripts during Step 1.

## Validation Requirements

For audit/design-only work:

```powershell
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

For implementation after approval, choose validation based on the approved Phase 5C route slice:

- focused new Rally Forts route tests
- relevant existing file/path helper tests
- relevant `forts_ingest` tests if present or added with SQL mocked/faked
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

- Rally Forts upload handling is delegated through the approved `upload_routes` boundary.
- `DL_bot.py` route order and fall-through behaviour are preserved.
- Daily and all-time Rally filename matching remains unchanged.
- Local download staging behaviour is preserved.
- Lazy import failure handling is preserved.
- SQL preflight, offload arguments, importer result handling, skip/error aggregation, final embed
  content, and best-effort log-backup scheduling are preserved.
- No new direct SQL is added to Discord listener/route layers.
- `upload_routes/common.py` is reused where behaviour parity is clear and covered.
- Out-of-scope fallback queue, SQL, lifecycle, worker, or importer-internal findings are captured
  structurally.
- The implementation packet explicitly states whether Phase 5D remains required. Current expected
  answer: yes, Phase 5D is required for fallback monitored-channel queueing and should be the final
  upload-routing sub-phase.

## Explicit Stop Point

Stop after the Phase 5C audit/design packet.

Do not implement route extraction, alter SQL, change upload routing behaviour, or open a PR until
the audit packet, route classification, and first implementation scope have each been approved.
