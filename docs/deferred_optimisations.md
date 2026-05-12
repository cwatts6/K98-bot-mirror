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
- Area: `commands/stats_cmds.py` `/my_stats_export`
- Type: architecture
- Description: The non-KVK `/my_stats_export` path still contains direct SQL for `vDaily_PlayerExport` inside the command handler.
- Suggested Fix: Extract daily stats export data access into a stats export DAL/service and leave the command responsible only for permission, defer, file-send, and response flow.
- Impact: medium
- Risk: medium
- Dependencies: Future stats command cleanup; preserve existing Excel/CSV/Google Sheets-compatible output copy and file workflow.

### Deferred Optimisation
- Area: `DL_bot.py` KVK_ALL upload routing
- Type: architecture
- Description: KVK_ALL upload routing still lives in the legacy root bot listener with attachment filtering, offload dispatch, import result handling, Discord rendering, and export scheduling mixed together.
- Suggested Fix: Move KVK_ALL upload orchestration into a dedicated service or route module in a later phase, leaving `DL_bot.py` responsible for event delegation and Discord response plumbing.
- Impact: medium
- Risk: medium
- Dependencies: Preserve existing Discord output and auto-export behaviour; broader restart/performance hardening remains assigned to Phase 9.

### Deferred Optimisation
- Area: `mge/mge_signup_service.py`
- Type: consistency
- Description: MGE signup governor lookup still reads the registry through the legacy registry shape instead of the newer `registry_service.get_user_accounts()` service boundary. This remains aligned with GitHub issues #29 and #32 and is not required for MGE reminder refresh or commander administration.
- Suggested Fix: Move MGE signup account resolution onto `registry_service.get_user_accounts()` in a focused service-consolidation pass, preserving existing self-service/admin-add behaviour and tests.
- Impact: medium
- Risk: medium
- Dependencies: Coordinate with the broader Service Layer Consolidation Pack so stats and MGE registry-service alignment are handled together.

### Deferred Optimisation
- Area: `mge/mge_publish_service.py`
- Type: architecture
- Description: MGE publish orchestration still mixes domain publish state transitions with Discord message IO. The current task reused that existing boundary for award reminder refresh to avoid splitting publish/repost behaviour mid-feature, with explicit architecture-check allowances on the pre-existing Discord-aware service surface.
- Suggested Fix: Extract Discord message fetch/edit/send operations into a dedicated interaction adapter or UI orchestration module, leaving `mge_publish_service.py` to produce publish/reminder intents and persist outcomes through DAL calls.
- Impact: high
- Risk: medium
- Dependencies: Requires careful regression coverage for publish, republish, reminder refresh, unpublish, award DM, and board refresh behaviours.
