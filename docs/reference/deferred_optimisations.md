# Deferred Optimisations

Active deferred optimisation items are staged here before they are grouped, scored, or promoted
to GitHub issues/task packs.

Resolved historical notes were moved to `archive/deferred_optimisations_resolved.md`.

Last reviewed after the slow-pytest optimisation production release. PR 107
(`pytest-log-delivery-docs`) resolved the high-impact pytest duration outliers found after the
pytest log-isolation production smoke audit, reducing the duration audit from `1450 passed, 2
skipped, 19 warnings in 638.91s` to `1450 passed, 2 skipped, 19 warnings in 54.86s`; it was smoke
tested successfully and deployed to production. PR 96
(`import-locations-command-orchestration-cleanup`) was smoke tested successfully and deployed to
production. PR 97 (`dlbot-player-location-upload-route`) was smoke tested successfully and
promoted to production. The governor fuzzy/name/partial-ID lookup standardisation item,
profile/location profile-cache lookup item, `/import_locations` command orchestration item, DL_bot
player location auto-import route/signal coupling item, and DL_bot PreKvK upload route extraction
item from PR 98 (`dlbot-prekvk-upload-route`) are complete, smoke tested successfully, and
promoted to production. Phase 2B PreKvK SQL compatibility cleanup was deployed and smoke tested
successfully. Phase 2C delivered the public read-only `/prekvk report` image report, was smoke
tested successfully, and was pushed to production. Phase 2D refactored the scheduled PreKvK
stats-alert path onto the Phase 2C report service architecture while preserving scheduled embed,
guard/state, and upload-refresh behaviour; it was smoke tested successfully and pushed to
production. Phase 3 local validation blockers were audited on 2026-05-20 and closed as a no-op:
the focused DB/non-DB blocker tests, full suite, and pytest log-noise validation all passed under
the documented `.venv` workflow without `RUN_DB_TESTS=1`. Phase 4 KVK_ALL upload-route extraction
is now the next upload-routing programme slice; the remaining active backlog is listed below.

The next coherent major architecture batch should be scoped as fresh work around `DL_bot.py`
upload routing, not as a continuation of the `/import_locations` command cleanup. Start that task
with a new audit/scope pass and review both this backlog and the current `K98-bot-mirror` GitHub
issues list.

### Deferred Optimisation
- Area: `tests/test_ark_preference_service.py`, `tests/test_ark_bans_enforcement.py`, `tests/test_lock_timeout.py`, `tests/test_calendar_service.py`, `tests/test_calendar_pipeline.py`, remaining slow full-suite pytest paths
- Type: performance
- Description: After PR 107 resolved the original slow pytest offenders, the new duration audit `C:\Users\cwatt\Downloads\.codex_pytest_audit-new.log` shows the remaining full-suite outliers are concentrated in Ark preference/ban negative paths, lock-timeout coverage, calendar failure-path retries, live queue persistence, maintenance subprocess timeout/success coverage, and one inventory vision import case. The slowest current timings are `tests/test_ark_preference_service.py::test_set_preference_rejects_unknown_governor` at 7.33s, `tests/test_ark_bans_enforcement.py::test_admin_add_allows_when_override_on` at 5.23s, `tests/test_lock_timeout.py::test_remove_view_tracker_entry_returns_false_when_locked` at 5.06s, `tests/test_lock_timeout.py::test_save_view_tracker_raises_on_lock` at 5.06s, `tests/test_calendar_service.py::test_refresh_full_stops_on_sync_failure` at 3.02s, and `tests/test_calendar_pipeline.py::test_pipeline_stops_on_sync_failure` at 3.01s.
- Suggested Fix: Start a fresh audit from `.codex_pytest_audit-new.log` and classify each remaining slow path as intentional timeout coverage, missing test boundary, live dependency leakage, retry/backoff, or genuine defect. Preserve lock-timeout and subprocess timeout coverage, but replace real multi-second waits with patched timeout constants, fake clocks, controlled retry policies, or explicit service/DAL boundary fakes where safe. Keep the scope separate from PR 107 and validate with `pytest -vv tests --durations=30 --durations-min=1.0`, focused subsystem tests, `scripts/analyse_pytest_log_noise.py`, and `python -m pytest -q tests`.
- Impact: medium
- Risk: medium
- Dependencies: Use the post-PR-107 audit baseline (`1450 passed, 2 skipped, 19 warnings in 54.86s`); preserve genuine timeout, subprocess, lock, negative-path, and log-noise coverage.

### Deferred Optimisation
- Area: `commands/`, `scripts/validate_command_registration.py`
- Type: architecture
- Description: Batch 1 of the command-surface balancing audit grouped admin-heavy `/ops` and `/mge` commands, reducing the primary Discord application-command set from 100 to 82 top-level commands. Future standalone slash commands can still erode this buffer and eventually break startup sync with Discord error 30032 unless additional command-surface consolidation remains planned.
- Suggested Fix: Continue the command-surface programme through the staged follow-up batches below. Group related commands by domain where user experience allows, identify stale/low-use admin commands for consolidation or retirement, update docs for renamed paths, and keep `scripts/validate_command_registration.py` enforcing the 100-command ceiling with a warning at 90+.
- Impact: high
- Risk: medium
- Dependencies: Batch 1 `/ops` and `/mge` grouping validation remains clean; coordinate with bot operators before renaming public command paths; preserve admin-only permission checks when commands move into groups.

### Deferred Optimisation
- Area: `commands/ark_cmds.py`, `docs/ark/`, Ark command tests
- Type: architecture
- Description: Ark still exposes many top-level commands (`/ark_create_match`, `/ark_force_announce`, `/ark_amend_match`, `/ark_cancel_match`, `/ark_set_preference`, `/ark_clear_preference`, `/ark_ban_add`, `/ark_ban_revoke`, `/ark_ban_list`, `/ark_set_result`, `/ark_generate_draft`, `/create_ark_team`, plus public `/ark_reminder_prefs` and `/ark_report_players`). These are a natural `/ark` command group and could recover another large block of top-level command headroom, but several docs and public/operator workflows reference the flat paths.
- Suggested Fix: Prepare a second command-surface migration batch that groups Ark commands under `/ark`, preserving `is_admin_or_leadership_only`, `channel_only`, public reminder/report behavior, autocomplete/options, and interaction responses. Coordinate operator communication for public path changes before implementation and update Ark docs/tests to the new paths.
- Impact: high
- Risk: medium
- Dependencies: Batch 1 `/ops` and `/mge` grouping deployed cleanly; operators approve public Ark path migration and announcement timing.

### Deferred Optimisation
- Area: `commands/stats_cmds.py`, `commands/registry_cmds.py`, `commands/inventory_cmds.py`, `commands/calendar_cmds.py`, `commands/subscriptions_cmds.py`, user-facing command docs/tests
- Type: architecture
- Description: Public/player-facing command domains still use many top-level paths that could be grouped later (`/kvk`, `/registry`, `/inventory`, `/calendar`, `/subscriptions`). These commands are more discoverability-sensitive than admin-only surfaces and include heavily documented player workflows, so moving them without coordination could confuse users even though it would reduce startup sync risk further.
- Suggested Fix: Scope a later public command-path migration with operator-approved UX rules, aliases/transition messaging if feasible, and focused docs/test updates. Prioritise admin-heavy subcommands inside each domain first, then evaluate whether player paths should remain flat for discoverability.
- Impact: medium
- Risk: medium
- Dependencies: Operator approval for public command rename policy; updated command reference/announcement plan; Batch 1 validation remains below the warning threshold.

### Deferred Optimisation
- Area: `cogs/commands.py`, `subscribe.py`, `scripts/validate_command_registration.py`, startup command audit docs
- Type: cleanup
- Description: Disabled secondary command surfaces still declare duplicate command names (`/summary`, `/weeksummary`, `/history`, `/failures`, `/ping`, `/subscribe`). The validator reports these duplicates, but the output does not clearly separate intentionally disabled legacy surfaces from active startup-sync risk.
- Suggested Fix: Decide whether to retire the disabled secondary cogs or enhance validator output to classify duplicates by active vs disabled registration path. If the files are retained, document the environment gating and keep duplicate warnings informational; if retired, remove or archive the dead command declarations with smoke/import coverage.
- Impact: medium
- Risk: low
- Dependencies: Confirm secondary cogs remain disabled by default in production and no operator workflow depends on loading them.

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
- Area: `DL_bot.py` KVK_ALL upload routing
- Type: architecture
- Description: KVK_ALL upload routing still lives in the legacy root bot listener with attachment filtering, offload dispatch, import result handling, Discord rendering, and export scheduling mixed together.
- Suggested Fix: Move KVK_ALL upload orchestration into a dedicated service or route module in a later phase, leaving `DL_bot.py` responsible for event delegation and Discord response plumbing.
- Impact: medium
- Risk: medium
- Dependencies: Start with `docs/task_packs/DL_bot Upload Routing - Phase 4 KVK_ALL Upload Route Starter.md`; preserve existing Discord output and auto-export behaviour; broader restart/performance hardening remains assigned to the KVK_ALL modernisation programme.

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
