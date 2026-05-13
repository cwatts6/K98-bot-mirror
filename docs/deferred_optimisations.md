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
- Dependencies: Preserve existing Discord output and auto-export behaviour; broader restart/performance hardening remains assigned to Phase 9.

## Recently Resolved

- Stats Commands Full Optimisation & Standardisation was implemented, merged, production promoted, and smoke-tested via PR #78.
- The following stats deferred items are closed and complete:
  - `commands/stats_cmds.py` no longer performs `/my_stats_export` SQL directly; export data access now lives in `stats/dal/stats_export_dal.py` and export orchestration lives in `services/stats_export_service.py`, resolving GitHub issue #46.
  - Stats account resolution now routes through `services/stats_account_service.py`, which delegates to the SQL-backed registry service boundary and removes stats command/service traversal of the legacy registry dict shape, resolving the stats scope of GitHub issues #27, #29, #31, and #32.
  - Stats-touched legacy registry view/account-selection paths were aligned with the current registry-service flow where touched by stats commands, resolving the stats scope of GitHub issue #28.
  - KVK admin/stat command flows touched by the stats cleanup were reviewed and aligned with the current service/DAL boundaries used by the deployed implementation, resolving GitHub issue #42 for the stats command batch.
  - Production deployment completed successfully and manual Discord command smoke tests passed after deployment.
- Telemetry Commands Full Optimisation & Standardisation was implemented, merged, production promoted, and smoke-tested via PR #76.
- The following telemetry deferred items are closed and complete:
  - `commands/telemetry_cmds.py` no longer imports or wraps the KVK DAL current-KVK resolver, resolving GitHub issue #26.
  - The telemetry scope of command-layer SQL separation is complete, resolving GitHub issue #33.
  - CrystalTech governor session locking is now restart-safe and service/DAL-backed, resolving GitHub issue #47.
  - `/mykvktargets` and `/mykvkcrystaltech` resolve linked accounts through `services/governor_account_service.py`, which delegates to `registry_service.get_user_accounts()`.
  - CrystalTech governor session locking now routes through `services/governor_session_lock_service.py` and `registry/dal/governor_session_lock_dal.py` with UTC expiry, release, refresh, contention, and cleanup support.
  - Player profile posting moved to `commands/player_profile_flow.py`.
  - CrystalTech interaction orchestration moved to `commands/crystaltech_flow.py`.
  - `account_picker.py`, `kvk_ui.py`, selected KVK personal views, selected registry views, and Ark registration account lookup were aligned away from direct registry dict traversal where touched.
  - Final deployed validation: `python -m pytest -q tests` reported 1306 passed and 8 skipped; command registration and import smoke validation passed; post-deploy Discord smoke testing was completed.
- The stats-related issues from the task pack are now resolved: #27, #28, #29, #31, #32, #42, and #46.
- MGE Process Polish Phase 2 was implemented, production deployed, and smoke-tested via PR #75.
- `mge/mge_signup_service.py` self-signup account resolution now uses `registry_service.get_user_accounts()` instead of the legacy registry dict shape. Admin-add reverse owner lookup remains on `get_discord_user_for_governor()`.
- `mge/mge_publish_service.py` no longer performs direct Discord message fetch/send/edit/delete/DM IO. Publish, republish, reminder refresh, unpublish, award DM, and board refresh paths now route Discord operations through `mge/mge_publish_discord_adapter.py`.
- The remaining open service-consolidation scope from GitHub issues #29 and #32 is stats-service registry alignment, not MGE.
