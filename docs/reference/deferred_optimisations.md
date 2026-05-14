# Deferred Optimisations

Active deferred optimisation items are staged here before they are grouped, scored, or promoted
to GitHub issues/task packs.

Resolved historical notes were moved to `archive/deferred_optimisations_resolved.md`.

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
- Area: `ark/registration_flow.py`, `account_picker.py`, `services/governor_account_service.py`
- Type: consistency
- Description: Ark registration flows still load raw registry account dictionaries, build governor select options through the legacy account picker path, and resolve governor names from local account dictionaries. The flow also has Ark-specific signup, ban, roster, active-match, and persistent-message behaviour, so it should not be migrated opportunistically with registry command/view work even after the registry command/view summary migration.
- Suggested Fix: Audit Ark self-service join/sub/leave/switch account lookup and governor-name resolution for safe reuse of `AccountResolutionSummary`. Migrate only after confirming Ark signup behaviour, ban enforcement, roster filtering, active signup detection, and persistent registration-message refresh remain unchanged.
- Impact: medium
- Risk: medium
- Dependencies: Registry command/view direct migration complete; preserve Ark signup behaviour and focused Ark regression coverage.

### Deferred Optimisation
- Area: `services/governor_account_service.py`, `services/stats_account_service.py`, `inventory/inventory_service.py`, `mge/mge_signup_service.py`, `ark/registration_flow.py`, `account_picker.py`
- Type: cleanup
- Description: Compatibility adapters and duplicate local account classification/linked-governor/registered-governor shaping remain necessary while Ark consumers are still pending migration. Removing them now would risk breaking public shapes used by stats, inventory, MGE, telemetry, registry compatibility imports, and Ark tests.
- Suggested Fix: After Ark account-resolution migration has focused regression coverage, remove obsolete `AccountLookup`-only pathways and any duplicate local classification or option-shaping helpers that no longer have external callers.
- Impact: medium
- Risk: medium
- Dependencies: Telemetry/KVK and registry command/view surfaces migrated to `AccountResolutionSummary`; Ark migration and focused regression coverage still pending. Preserve coverage for stats export, inventory permissions, MGE signup, telemetry/KVK pickers, registry flows, and Ark signup before cleanup.
