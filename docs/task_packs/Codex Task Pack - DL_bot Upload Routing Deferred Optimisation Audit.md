# Codex Task Pack - DL_bot Upload Routing Deferred Optimisation Audit

## 1. Task Header

- Task name: `DL_bot upload-routing deferred optimisation audit`
- Date: `2026-05-15`
- Owner/context: `Post-PR 96 follow-up: import-locations-command-orchestration-cleanup deployed to production`
- Task type: `deferred optimisation batch`
- One-pass approved: `no`

## 2. Required Reading

Before implementation, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/deferred_optimisations.md`

Then follow the required reading order and conditional references defined by `docs/reference/README.md`.

For SQL-facing work or validation of SQL-backed imports, validate relevant schema, procedures, views, indexes, UDTs, and `ProcConfig` details against:

`C:\K98-bot-SQL-Server`

Also review current open GitHub issues in `K98-bot-mirror` that mention:

- `DL_bot.py`
- upload routing
- legacy listener
- import orchestration
- PreKvK
- KVK_ALL
- player location import
- local validation blockers

## 3. Objective

Audit all active DL_bot-related deferred optimisation items and current GitHub issues affecting upload routing, legacy listener behaviour, import orchestration, and local validation blockers.

Produce a safe, PR-sized first implementation slice before coding.

This is a defensive architecture polish task. Do not implement until the audit/scope packet, architecture direction, and implementation plan have each been approved.

## 4. Background

PR 96 (`import-locations-command-orchestration-cleanup`) was smoke tested successfully and deployed to production.

The `/import_locations` command cleanup is complete. This task is fresh work around `DL_bot.py` upload routing and related validation blockers.

Current `DL_bot.py` still contains two upload-related branches inside the root `on_message`
listener after Phase 5B: Rally Forts ingest and main monitored-channel fallback queueing. Player
location CSV import, PreKvK snapshot ingest, KVK_ALL import, MGE results import, KVK Honour ingest,
inventory upload-first routing, and weekly activity ingest have been extracted into the
`upload_routes` pattern.

The active deferred backlog identifies these DL_bot-specific architecture items:

- PreKvK upload routing still mixes filename matching, KVK lookup, offload dispatch, and Discord rendering.
- Player location CSV auto-import still couples `DL_bot.py` to `commands/location_cmds.py` refresh signalling.
- KVK_ALL upload routing was extracted in Phase 4 and no longer lives inline in `DL_bot.py`.
- Local validation previously had DB and non-DB environment blockers that affected safe PR
  validation; Phase 3 later audited these and closed them as a no-op after current `main` passed
  focused blocker tests, full pytest, and log-noise validation.

## 5. Scope

### In Scope

- Audit `DL_bot.py` upload-routing responsibilities.
- Audit active deferred optimisation items related to DL_bot upload routing.
- Audit current `K98-bot-mirror` GitHub issues related to DL_bot, upload routing, import orchestration, and validation blockers.
- Identify the safest first PR-sized slice.
- Recommend target module boundaries for upload routes/services.
- Classify each finding as:
  - fix now
  - defer
  - not applicable
- Produce an implementation plan only after audit/scope approval.
- Preserve current production behaviour, Discord output, importer contracts, offload behaviour, and auto-export behaviour.

### Out of Scope

- No implementation during Step 1.
- No broad rewrite of `DL_bot.py` in one PR.
- No changes to production SQL without a separately approved SQL task.
- No change to import file formats unless required to preserve current behaviour.
- No changes to unrelated command modules except where required to remove fragile DL_bot coupling.
- No continuation of `/import_locations` command cleanup.
- No restart/performance hardening beyond what is necessary for the first DL_bot routing slice.

## 6. Source Deferred Items

```md
### Deferred Optimisation
- Area: tests/stats_service.py, tests/targets_sql_cache_subproc.py, tests/prekvk_stats.py, tests/proc_config_import_phase2.py, tests/sheets_sync_flow.py
- Type: consistency
- Description: Several non-Ark unit tests still reach live SQL Server or connection construction when run in the Codex/local PR validation environment without the bot machine's ODBC setup.
- Suggested Fix: Add subsystem-specific DAL/service boundary patches or explicit integration markers, then gate live DB coverage behind RUN_DB_TESTS=1.
- Impact: high
- Risk: medium
- Dependencies: Resolved by Phase 3 no-op audit on 2026-05-20; focused tests and full suite passed without live DB opt-in.

### Deferred Optimisation
- Area: tests/test_dl_bot_mge_auto_import.py, tests/test_integration_end_to_end_fake_worker.py, tests/test_maintenance_suite.py
- Type: consistency
- Description: Full-suite validation in the Codex/local PR environment has non-DB environment blockers: DL_bot expects venv/Scripts/python.exe while the documented command uses .venv, and subprocess worker tests fail with WinError 5 in the sandbox.
- Suggested Fix: Make startup interpreter validation configurable for tests and mark subprocess worker tests with an environment capability gate when process spawning is unavailable.
- Impact: medium
- Risk: medium
- Dependencies: Resolved by Phase 3 no-op audit on 2026-05-20; `.venv` interpreter and subprocess-worker tests passed locally.

### Deferred Optimisation
- Area: `DL_bot.py` PreKvK upload routing
- Type: architecture
- Description: PreKvK upload routing still lives in the legacy root bot listener with filename matching, current-KVK lookup, offload dispatch, and Discord response rendering mixed together.
- Suggested Fix: Move PreKvK upload routing into a dedicated route/service module and leave `DL_bot.py` responsible only for delegating the Discord event.
- Impact: medium
- Risk: medium
- Dependencies: PreKvK diagnostics result model should remain stable after the import-history rollout.

### Deferred Optimisation
- Area: `DL_bot.py` player location CSV auto-import, location refresh signalling
- Type: architecture
- Description: The player location auto-import flow in `DL_bot.py` now reaches directly into `commands/location_cmds.py` for `signal_location_refresh_complete`, so the legacy root bot listener depends on command-module internals for refresh-completion signalling.
- Suggested Fix: Move player-location auto-import orchestration into a dedicated route/service boundary and centralise location refresh signalling behind a shared importable helper.
- Impact: medium
- Risk: medium
- Dependencies: Preserve current player location auto-import Discord output and scanner/import behaviour.

### Deferred Optimisation
- Area: `DL_bot.py` KVK_ALL upload routing
- Type: architecture
- Description: KVK_ALL upload routing still lives in the legacy root bot listener with attachment filtering, offload dispatch, import result handling, Discord rendering, and export scheduling mixed together.
- Suggested Fix: Move KVK_ALL upload orchestration into a dedicated service or route module in a later phase, leaving `DL_bot.py` responsible for event delegation and Discord response plumbing.
- Impact: medium
- Risk: medium
- Dependencies: Resolved by Phase 4 in PR 110 (`codex/kvk-all-upload-route`); KVK_ALL now delegates to `upload_routes/kvk_all_route.py` and preserves existing Discord output and auto-export behaviour.
```

7. Codex Skills To Use
Skill	Decision	Notes
k98-architecture-scope	use	Mandatory before implementation. This is architecture-sensitive DL_bot routing work.
k98-discord-command-feature	use	Upload handling affects Discord message/listener flows and user-facing embeds.
k98-sql-validation	use	PreKvK, player locations, KVK_ALL, and validation blockers depend on SQL-backed import paths.
k98-test-selection	use	Required before validation, especially because this task includes local test-environment blockers.
k98-deferred-optimisation-capture	use	This task is explicitly a deferred optimisation audit and may discover further out-of-scope debt.
k98-pr-review	use	Required before PR handoff because this touches critical bot startup/import routing.
k98-promotion-check	use	Required before production promotion or bot-machine deployment.
8. Mandatory Workflow
Audit / scope review, then stop for approval.
Architecture validation, then stop for approval.
Implementation plan, then stop for approval.
Implementation after approval.
Validation and final review.

Do not proceed in one pass.

9. Audit Requirements

Review:

DL_bot.py root listener responsibilities.
Upload-route branching order and fall-through behaviour.
Importer contracts and result shapes.
Discord embed/output parity.
Offload behaviour and process/thread fallback.
SQL preflight checks.
Auto-export scheduling.
Cache warming and refresh signalling.
Startup interpreter validation.
Subprocess/worker test blockers.
GitHub issues related to this area.
Existing tests that cover DL_bot upload routes.

Map likely:

commands
services
route modules
repositories/DAL modules
SQL objects/contracts
caches
persisted state
restart implications
conditional reference docs
validation gates
10. Architecture Targets
Concern	Target
Root listener	DL_bot.py delegates only
Upload route detection	dedicated upload routing module
PreKvK orchestration	dedicated route/service module
Player location auto-import	dedicated route/service module
Location refresh signalling	shared helper, not command internals
KVK_ALL orchestration	later dedicated route/service module unless first slice proves safe
Shared offload/preflight	reuse existing helpers where safe
Discord rendering	route-level response helper or existing embed helper
SQL validation	SQL repo contracts checked before implementation
Tests	focused route/service tests plus selected regression tests
11. Likely Files
Review
DL_bot.py
commands/location_cmds.py
location_importer.py
prekvk_importer.py
kvk_all_importer.py
file_utils.py
embed_utils.py
stats_alerts/kvk_meta.py
stats_alerts/interface.py
tests/test_dl_bot_mge_auto_import.py
tests/test_integration_end_to_end_fake_worker.py
tests/test_maintenance_suite.py
tests/prekvk_stats.py
tests/sheets_sync_flow.py
docs/reference/deferred_optimisations.md
current relevant GitHub issues
Modify

To be decided after Step 1 approval.

Likely first-slice candidates:

DL_bot.py
new or existing upload route/service module
shared location refresh helper
focused tests
Create

To be decided after Step 1 approval.

Likely candidates:

upload_routes/
upload_routes/prekvk_route.py
upload_routes/player_location_route.py
services/location_refresh_signal.py
focused route tests
12. Implementation Requirements
Keep DL_bot.py thin.
Preserve upload route order and fall-through behaviour.
Preserve existing Discord output unless intentionally approved.
Preserve importer input/output contracts.
Preserve SQL preflight behaviour.
Preserve auto-export behaviour.
Preserve cache warm/refresh behaviour.
Avoid command-module internal coupling.
Avoid direct SQL in Discord command/view/listener layers.
Add tests before or alongside route extraction.
Keep first implementation slice small enough for safe PR review.
Capture all out-of-scope findings structurally.
13. Refactor Decisions

Initial classification before audit:

Issue	Decision	Reason
PreKvK route extraction	likely fix now	Medium-impact, clear boundary, contained route.
Player location route extraction and refresh signal helper	likely fix now	Removes fragile command-module coupling.
KVK_ALL route extraction	likely defer to phase 4	Higher blast radius due to multi-attachment import and auto-export scheduling.
Local DB test blockers	likely partial fix now	Needed only where it blocks validating the selected first slice.
Subprocess worker blockers	likely defer or capability-gate	Should not widen first routing PR unless validation is blocked.
SQL legacy PreKvK phase objects	defer to Phase 2B	Separate SQL cleanup audit/design task; do not mix destructive SQL cleanup into the route-extraction PR.
New PreKvK report/embed	defer to Phase 2C	Separate user-facing reporting task after the route boundary is stable.

Final decisions must be updated after Step 1 audit.

## 13A. Approved Phase Direction

The Step 1 audit, architecture direction, and Phase 1 implementation plan were approved after
review. The approved end-state direction is an incremental `upload_routes` pattern rather than
one-off route modules.

Phase breakdown:

1. **Phase 1 - Player location auto-import route**
   - Introduce `upload_routes/`.
   - Move the `scan_1198.csv` auto-import path out of the inline `DL_bot.py` listener branch.
   - Move location refresh signalling out of `commands/location_cmds.py` into a shared service.
   - Preserve current Discord output, SQL preflight, `load_staging_and_replace`, profile-cache
     warm, background log backup scheduling, and handled/fall-through behaviour.
2. **Phase 2A - PreKvK upload route extraction**
   - Extract filename detection, current-KVK lookup, offload dispatch, result rendering, duplicate
     handling, and stats-embed refresh behind the same route contract.
   - Preserve the existing Discord output and importer metadata contract except for the approved
     duplicate-skip side-effect change: duplicate skips should send the skipped embed but should
     not schedule a background log backup or refresh the stats embed.
   - Keep SQL schema cleanup and new PreKvK report/embed work out of this PR.
3. **Phase 2B - PreKvK SQL cleanup audit and design**
   - Audit dependencies on legacy SQL phase objects before proposing any SQL cleanup:
     `dbo.PreKvk_Phases`, `dbo.fn_PreKvkPhaseDelta`, and KVK-specific PreKvK phase views.
   - Validate production SQL/report/manual workflow dependencies in `C:\K98-bot-SQL-Server`.
   - Stop for approval before any SQL object replacement, retirement, or destructive cleanup.
4. **Phase 2C - New PreKvK report/embed**
   - Design and implement a dedicated PreKvK report/embed after the route extraction is stable.
   - Reuse the direct-stage PreKvK data path where possible and avoid changing upload routing
     behaviour in the reporting PR.
   - Define command/channel surface, permissions, limits, empty-data behaviour, and mobile-safe
     Discord output before implementation.
5. **Phase 3 - Local validation blockers**
   - Completed as a no-op on 2026-05-20 after the listed blockers no longer reproduced on current
     `main`.
   - Validation evidence: focused DB-facing blocker tests passed (`28 passed`), focused non-DB
     environment blocker tests passed (`20 passed`), full pytest passed (`1461 passed, 2 skipped`),
     and pytest log-noise validation passed with production operational logs unchanged.
6. **Phase 4 - KVK_ALL upload route**
   - Completed in PR 110 (`codex/kvk-all-upload-route`) and smoke tested successfully on
     2026-05-26.
   - Extracted the higher-risk multi-attachment KVK_ALL route into
     `upload_routes/kvk_all_route.py` after smaller routes proved the pattern.
   - Preserved structured importer failures, health output, link button, and auto-export
     scheduling.
   - Starter packet: `docs/task_packs/DL_bot Upload Routing - Phase 4 KVK_ALL Upload Route Starter.md`
7. **Phase 5 - Remaining upload fast-path consolidation**
   - Completed after Phase 4.
   - Phase 5A completed MGE results and KVK Honor route extraction in PR 113
     (`codex/dlbot-upload-routing-phase-5a`), smoke tested successfully on 2026-05-26, deployed
     to production, and closed.
   - Phase 5B completed inventory upload-first and weekly activity route extraction in PR 114
     (`codex/dlbot-upload-routing-phase-5b`), smoke tested successfully on 2026-05-26 with
     inventory and alliance weekly uploads, deployed to production, and closed.
   - Phase 5C completed Rally Forts route extraction in PR 115
     (`codex/dlbot-upload-routing-phase-5c`), smoke tested successfully, merged, deployed to
     production, and pushed to production.
   - Phase 5D completed main monitored-channel fallback queue extraction in PR 116
     (`codex/dlbot-upload-routing-phase-5d`), smoke tested successfully on 2026-05-26, closed,
     pushed to production, and confirmed in production logs.
   - Phase 5 is complete: MGE results, KVK Honor, inventory upload-first, weekly activity, Rally
     Forts, and fallback monitored-channel queueing now delegate through focused `upload_routes`
     modules.
   - Starter packet: `docs/task_packs/DL_bot Upload Routing - Phase 5 Remaining Upload Fast Paths Starter.md`
8. **Phase 6 - Startup/lifecycle separation**
   - Active architecture batch after Phase 5 completion.
   - Phase 6A completed the first named startup lifecycle boundary in PR 117
     (`codex/dlbot-phase-6-startup-lifecycle-1`), routing initial `on_ready()` runtime bootstrap
     through `ready_runtime_bootstrap`.
   - Phase 6B completed runtime services extraction in PR 119
     (`codex/dlbot-phase-6b-runtime-services`), routing heartbeat, health dashboard, offload
     monitor, lock cleanup, usage tracker startup, daily summary, activity tracking, and status
     channel loops through `ready_runtime_services`.
   - Phase 6C completed usage tracker lifecycle ownership in PR 120
     (`codex/dlbot-phase-6c-usage-tracker`), consolidating command/component/metric/alert usage
     logging onto the shared `usage_tracker.py` singleton and moving usage JSONL prune startup
     into `ready_runtime_services`.
   - Remaining work: command sync/cache extraction, event cache and rehydration boundaries,
     scheduler/task ownership, queue worker lifecycle, shutdown, and restart-safe state coordination.
   - Current starter packet: `docs/task_packs/Codex Chat Starter - DL_bot Phase 6D Command Sync Cache.md`

Phase 2A delivery notes:

- PreKvK upload routing is extracted into the `upload_routes` pattern with `DL_bot.py` retaining
  listener/delegation responsibility.
- Duplicate skips intentionally preserve the skipped embed but do not schedule background log
  backup or stats-embed refresh.
- PR 98 (`dlbot-prekvk-upload-route`) was smoke tested successfully and pushed to production.
- Phase 2B SQL cleanup and Phase 2C report/embed work remain separate approval-gated follow-ons.

Phase 2B starter:

- `docs/task_packs/DL_bot Upload Routing - Phase 2B PreKvK SQL Cleanup Audit Statement.md`
- Phase 2B is audit/design only until explicitly approved for SQL changes.
- It must validate dependencies on `dbo.PreKvk_Phases`, `dbo.fn_PreKvkPhaseDelta`, and
  KVK-specific PreKvK phase views against `C:\K98-bot-SQL-Server` before proposing cleanup.

Phase 3 delivery notes:

- Phase 3 local validation blockers were audited on current `main` and closed as a no-op.
- No bot code, SQL, tests, deployment scripts, or upload-routing behaviour changed.
- The two validation-blocker deferred items were removed from the active backlog after the focused
  blocker reproductions, full test suite, and log-noise validation all passed under `.venv`.

Phase 4 delivery notes:

- KVK_ALL upload routing is extracted into the `upload_routes` pattern with `DL_bot.py` retaining
  listener/delegation responsibility.
- The route preserves accepted `.xlsx`, `.xls`, and `.csv` attachment filtering, no-file warning
  output, per-attachment continuation, SQL preflight behaviour, structured importer failure
  rendering, success/warning embeds, branding thumbnail, Google Sheet link button, and non-blocking
  auto-export scheduling.
- The SQL preflight review fix intentionally relies on `ensure_sql_headroom_or_notify()` for the
  user-facing abort notification and does not emit a duplicate route-level abort embed.
- PR 110 (`codex/kvk-all-upload-route`) was smoke tested successfully and promoted to production.
- Phase 5 remaining fast-path consolidation was the next active upload-routing programme slice and
  has since completed.

Phase 5A delivery notes:

- MGE results upload routing is extracted into `upload_routes/mge_results_route.py`.
- KVK Honor upload routing is extracted into `upload_routes/honor_route.py`.
- `upload_routes/common.py` now provides shared notify-channel fallback, source/uploader embed
  field construction, and best-effort task scheduling for later route slices.
- The MGE importer remains lazily loaded inside the route handler to preserve startup resilience.
- The MGE and Honor routes run SQL headroom preflight before workbook reads.
- Focused route tests cover matching, non-matching, SQL preflight aborts, importer success/failure,
  exception rendering, side effects, report summary fields, Honor test-mode handling, and Honor
  stats-refresh best-effort behaviour.
- PR 113 (`codex/dlbot-upload-routing-phase-5a`) was smoke tested successfully, deployed to
  production, and closed.
- Phase 5B inventory and weekly activity route extraction was the next active slice.

Phase 5B delivery notes:

- Inventory upload-first routing is extracted into `upload_routes/inventory_route.py`.
- Weekly activity upload routing is extracted into `upload_routes/weekly_activity_route.py`.
- `DL_bot.py` now delegates both through the `upload_routes` pattern while preserving route order,
  fall-through behaviour, inventory service/view contracts, weekly accepted filename matching,
  weekly SQL preflight/importer arguments, duplicate/success/error embeds, notify fallback, and
  best-effort log-backup scheduling.
- Focused route tests cover inventory delegation/error handling and weekly activity matching,
  non-matching fall-through, SQL preflight abort, success, duplicate skip, importer exception,
  Discord error-notification failure, and notify fallback.
- PR 114 (`codex/dlbot-upload-routing-phase-5b`) was smoke tested successfully with inventory and
  alliance weekly uploads, deployed to production, and closed.
- Phase 5C Rally Forts route extraction was the next active slice and has since completed.

Phase 5C delivery notes:

- Rally Forts upload routing is extracted into `upload_routes/rally_forts_route.py`.
- `DL_bot.py` delegates Rally Forts upload handling through `handle_rally_forts_upload()`.
- The route preserves daily/all-time filename matching, local download staging under
  `LOG_DIR/downloads`, lazy importer loading, SQL preflight handoff, offload dispatch, result
  aggregation, Discord output, disabled-channel fall-through, unsafe filename rejection, and
  best-effort log-backup scheduling.
- PR 115 (`codex/dlbot-upload-routing-phase-5c`) was smoke tested successfully, merged, deployed
  to production, and pushed to production.
- Phase 5D fallback queue route extraction was the next active slice and has since completed.

Phase 5D delivery notes:

- Main monitored-channel fallback queue handling is extracted into
  `upload_routes/fallback_queue_route.py`.
- `DL_bot.py` delegates fallback queueing through `handle_fallback_queue_upload()` after all
  specific upload routes and before `bot.process_commands(message)`, preserving route order and
  command fall-through.
- The route preserves `.xlsx/.xls/.csv` fallback attachment filtering, `channel_queues` handoff,
  current enqueue-once-per-accepted-attachment behaviour, `QueueFull` drop logging, live queue
  bookkeeping, queue embed updates, shared `utils.live_queue_lock` usage, and best-effort
  log-backup scheduling.
- PR 116 (`codex/dlbot-upload-routing-phase-5d`) was smoke tested successfully on 2026-05-26,
  closed, pushed to production, and confirmed in production logs.
- Phase 5 upload-routing consolidation is complete. Phase 6 startup/lifecycle separation is the
  next active architecture batch.

14. Testing Requirements

Consider and document:

happy path
negative path
regression
permission/channel boundary
restart/persistence
cache safety
format/output shape
local validation environment capability

Baseline commands:

.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py

Focused tests to identify during Step 1:

.\.venv\Scripts\python.exe -m pytest -q tests -k "dl_bot or prekvk or location"

Broader checks where practical:

.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py

If live SQL tests are required, gate with:

$env:RUN_DB_TESTS="1"
.\.venv\Scripts\python.exe -m pytest -q <selected-db-tests>
15. Acceptance Criteria
 Step 1 audit identifies all active DL_bot-related deferred items and relevant GitHub issues.
 Affected routes and responsibilities in DL_bot.py are mapped.
 First PR-sized slice is recommended and justified.
 Architecture direction is approved before implementation planning.
 Implementation plan is approved before coding.
 DL_bot.py is made thinner only within approved scope.
 Existing production behaviour is preserved.
 No new direct SQL exists in commands, views, or listener layers.
 Location refresh signalling no longer depends on command-module internals if included in first slice.
 Tests are added/updated or exceptions documented.
 Validation blockers are fixed, gated, or explicitly deferred.
 Out-of-scope findings are captured structurally.
16. Required Delivery Output

Use this delivery shape:

Summary
File Manifest
New Files
Modified Files
SQL Changes
Helpers Reused
Refactor Findings
Test Plan
Deployment Steps
Deferred Optimisations

For Step 1 audit only, include:

Audit Summary
Current Route Map
Deferred Item Map
GitHub Issue Map
Risk / Blast Radius
Recommended Phase Breakdown
Recommended First PR Slice
Approval Questions
Explicit Stop Point
17. PR Summary Template
## Summary

- <summary item>

## Changes

- <change item>

## Tests

- <test command or verification>

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- <risk and rollback note>
18. Required Stop Point

Stop after Step 1 with an audit/scope packet.

Do not write code.

Do not modify files.

Do not create a branch implementation plan until the audit/scope packet is approved.
