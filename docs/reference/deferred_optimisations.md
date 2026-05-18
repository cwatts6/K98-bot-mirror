# Deferred Optimisations

Active deferred optimisation items are staged here before they are grouped, scored, or promoted
to GitHub issues/task packs.

Resolved historical notes were moved to `archive/deferred_optimisations_resolved.md`.

Last reviewed after the DL_bot upload-routing Phase 2B production SQL cleanup. PR 96
(`import-locations-command-orchestration-cleanup`) was smoke tested successfully and deployed to
production. PR 97 (`dlbot-player-location-upload-route`) was smoke tested successfully and
promoted to production. The governor fuzzy/name/partial-ID lookup standardisation item,
profile/location profile-cache lookup item, `/import_locations` command orchestration item, DL_bot
player location auto-import route/signal coupling item, and DL_bot PreKvK upload route extraction
item from PR 98 (`dlbot-prekvk-upload-route`) are complete, smoke tested successfully, and
promoted to production. Phase 2B PreKvK SQL compatibility cleanup was deployed and smoke tested
successfully; the remaining active backlog is listed below.

The next coherent major architecture batch should be scoped as fresh work around `DL_bot.py`
upload routing and related test-environment blockers, not as a continuation of the
`/import_locations` command cleanup. Start that task with a new audit/scope pass and review
both this backlog and the current `K98-bot-mirror` GitHub issues list.

### Deferred Optimisation
- Area: `commands/`, `scripts/validate_command_registration.py`
- Type: architecture
- Description: The primary Discord application-command set is currently at the 100 top-level command limit. Phase 2C avoided the limit by grouping PreKvK commands under `/prekvk`, but future standalone slash commands can still break startup sync with Discord error 30032 unless command surface consolidation is planned before new command work.
- Suggested Fix: Run a command-surface balancing audit before the next command-heavy feature. Group related commands by domain where user experience allows, identify stale/low-use admin commands for consolidation or retirement, update docs for renamed paths, and keep `scripts/validate_command_registration.py` enforcing the 100-command ceiling in PR validation.
- Impact: high
- Risk: medium
- Dependencies: Coordinate with bot operators before renaming public command paths; preserve admin-only permission checks when commands move into groups.

### Deferred Optimisation
- Area: tests/stats_service.py, tests/targets_sql_cache_subproc.py, tests/prekvk_stats.py, tests/proc_config_import_phase2.py, tests/sheets_sync_flow.py
- Type: consistency
- Description: Several non-Ark unit tests still reach live SQL Server or connection construction when run in the Codex/local PR validation environment without the bot machine's ODBC setup.
- Suggested Fix: Add subsystem-specific DAL/service boundary patches or explicit integration markers, then gate live DB coverage behind RUN_DB_TESTS=1.
- Impact: high
- Risk: medium
- Dependencies: Agreement on which non-Ark tests should remain live DB integration coverage.

### Deferred Optimisation
- Area: tests/test_dl_bot_mge_auto_import.py, tests/test_integration_end_to_end_fake_worker.py, tests/test_maintenance_suite.py
- Type: consistency
- Description: Full-suite validation in the Codex/local PR environment has non-DB environment blockers: DL_bot expects venv/Scripts/python.exe while the documented command uses .venv, and subprocess worker tests fail with WinError 5 in the sandbox.
- Suggested Fix: Make startup interpreter validation configurable for tests and mark subprocess worker tests with an environment capability gate when process spawning is unavailable.
- Impact: medium
- Risk: medium
- Dependencies: Local validation environment contract for venv naming and subprocess permissions.

### Deferred Optimisation
- Area: SQL repo legacy PreKvK phase object retirement
- Type: cleanup
- Description: After Phase 2B compatibility wrappers remove active scan-window logic, `dbo.PreKvk_Phases` and any compatibility-only phase objects may remain as unused legacy SQL surface.
- Suggested Fix: Run a later Option C retirement audit after at least one production cycle, re-check live SQL dependencies and manual/report usage, then prepare a SQL-repo-only drop plan with rollback scripts if no consumers remain.
- Impact: low
- Risk: medium
- Dependencies: Phase 2B compatibility wrapper deployment completed and smoke tested; live dependency checks confirm no references beyond the objects being retired; production owner approves destructive SQL cleanup.

### Deferred Optimisation
- Area: `C:\K98-bot-SQL-Server` SQL development and deployment workflow
- Type: architecture
- Description: SQL schema changes can now be developed through Git PRs, but the existing production export routine can still overwrite Git-driven SQL changes because it syncs production schema back to the repository as the main routine.
- Suggested Fix: After the current upload-routing phase set is complete, use `C:\Users\cwatt\Downloads\sql_deploy_route_task_pack.md` to create a PR-based SQL promotion workflow with guarded deploy scripts, migration history, a safe production schema export branch, `migrations/` conventions, and `docs/SQL_PROMOTION_GUIDE.md`.
- Impact: high
- Risk: medium
- Dependencies: Complete the active DL_bot upload-routing phases first; preserve current production schema export as a drift/safety mechanism while preventing direct overwrite of `main`.

### Deferred Optimisation
- Area: `stats_alerts/prekvk_stats.py`, `stats_alerts/embeds/prekvk.py`
- Type: refactor
- Description: After the Phase 2C dedicated PreKvK report introduces the new report DAL/service/image-rendering architecture, the scheduled PreKvK stats-alert embed will still use its older helper/rendering path.
- Suggested Fix: Phase 2D should refactor the scheduled PreKvK stats-alert helper/embed to reuse the new PreKvK architecture while preserving scheduled-post behaviour, guard/state handling, and existing upload-refresh behaviour.
- Impact: medium
- Risk: medium
- Dependencies: Complete and validate Phase 2C dedicated report first; do not move on from the PreKvK report phase until Phase 2D is complete.

### Deferred Optimisation
- Area: `DL_bot.py` KVK_ALL upload routing
- Type: architecture
- Description: KVK_ALL upload routing still lives in the legacy root bot listener with attachment filtering, offload dispatch, import result handling, Discord rendering, and export scheduling mixed together.
- Suggested Fix: Move KVK_ALL upload orchestration into a dedicated service or route module in a later phase, leaving `DL_bot.py` responsible for event delegation and Discord response plumbing.
- Impact: medium
- Risk: medium
- Dependencies: Preserve existing Discord output and auto-export behaviour; broader restart/performance hardening remains assigned to the KVK_ALL modernisation programme.

### Deferred Optimisation
- Area: `DL_bot.py` remaining fast-path upload routes
- Type: architecture
- Description: After the first upload-route slices, `DL_bot.py` will still own MGE, honor, weekly activity, rally, inventory, and fallback queue handling directly in the root listener, with repeated preflight/offload/rendering/logging patterns.
- Suggested Fix: Phase 5 should consolidate the remaining fast paths into the `upload_routes` pattern, add shared SQL-preflight/offload handling where safe, centralise repeated import embed rendering, and add route-level structured logging without changing importer contracts or Discord output.
- Impact: medium
- Risk: medium
- Dependencies: Complete and validate the player-location, PreKvK, validation-blocker, and KVK_ALL phases first so the general router is based on proven route contracts.

### Deferred Optimisation
- Area: `DL_bot.py`, `bot_instance.py` startup and lifecycle
- Type: architecture
- Description: Startup and lifecycle responsibilities remain spread across DL_bot and bot_instance, including interpreter/startup checks, bot construction/import wiring, event registration, singleton/runtime concerns, and lifecycle coordination for the wider bot.
- Suggested Fix: Phase 6 should audit DL_bot and bot_instance together, define the target lifecycle ownership model, and separate startup/runtime wiring from upload routing after the fast-path router consolidation is complete.
- Impact: medium
- Risk: medium
- Dependencies: Defer until Phase 5 upload routing is complete so lifecycle changes are reviewed independently from upload-route behaviour.
