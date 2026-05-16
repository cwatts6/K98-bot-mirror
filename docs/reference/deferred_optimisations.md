# Deferred Optimisations

Active deferred optimisation items are staged here before they are grouped, scored, or promoted
to GitHub issues/task packs.

Resolved historical notes were moved to `archive/deferred_optimisations_resolved.md`.

Last reviewed during the DL_bot upload-routing Phase 1 work. PR 96
(`import-locations-command-orchestration-cleanup`) was smoke tested successfully and deployed to
production. The governor fuzzy/name/partial-ID lookup standardisation item, profile/location
profile-cache lookup item, `/import_locations` command orchestration item, and DL_bot player
location auto-import route/signal coupling item are complete or being completed by the Phase 1
upload-route PR; the remaining active backlog is listed below.

The next coherent major architecture batch should be scoped as fresh work around `DL_bot.py`
upload routing and related test-environment blockers, not as a continuation of the
`/import_locations` command cleanup. Start that task with a new audit/scope pass and review
both this backlog and the current `K98-bot-mirror` GitHub issues list.

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
- Area: `DL_bot.py` PreKvK upload routing
- Type: architecture
- Description: PreKvK upload routing still lives in the legacy root bot listener with filename matching, current-KVK lookup, offload dispatch, and Discord response rendering mixed together.
- Suggested Fix: Move PreKvK upload routing into a dedicated route/service module and leave `DL_bot.py` responsible only for delegating the Discord event.
- Impact: medium
- Risk: medium
- Dependencies: PreKvK diagnostics result model should remain stable after the import-history rollout.

### Deferred Optimisation
- Area: SQL repo legacy PreKvK phase objects
- Type: cleanup
- Description: `dbo.PreKvk_Phases`, `dbo.fn_PreKvkPhaseDelta`, and KVK-specific phase views still represent the old scan-window delta model even though Python reporting now uses direct stage columns.
- Suggested Fix: Audit production SQL/report dependencies, then replace with direct-stage equivalents or retire the legacy objects in a separate SQL cleanup task.
- Impact: medium
- Risk: medium
- Dependencies: Confirm no production reports or manual SQL workflows still depend on scan-window phase objects.

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
