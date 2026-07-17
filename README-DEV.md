# Developer Quickstart

## Core Reference Contract

Before repo work, read `AGENTS.md` and the indexed core docs in
`docs/reference/README.md`. That index separates must-read standards from background,
domain, promotion, and operations references so routine work does not require reading the
entire `docs/reference` folder.

## Current GovernorOS Programme

GovernorOS v2 Phase 5B Premium Inventory Report Backdrops and Visual Alignment is complete.
Operator smoke and final visual acceptance passed on 2026-07-13 across the premium Resources,
Speedups, Materials, and honest no-data reports. The shared 1400x980 renderer uses the approved
report-specific production backdrops, restored item icons, the invoking player's best-effort
Discord avatar, fitted typography, up to six genuine upload-date labels, and density-aware markers
for every plotted upload. The 2800x1960 masters remain source-only. Private direct `/me` reports
and the then-live legacy `/myinventory` route shared that visual refresh. Phase 5F subsequently
retires the legacy route while preserving the accepted renderer, data, calculations, controls,
exports, filenames, fallback, and attachment lifecycle. The completed Phase 5B task pack and
starter are archived.

Phase 5C Premium Accounts Summary Card is complete and operator accepted in mirror PR #221 and
production PR #528. `/me accounts` resolves every linked registry entry through set-based Kingdom
1198 and canonical Inventory reads, renders the approved 1702x924 avatar-enabled portfolio card as
a standalone private attachment, preserves the guided Manage workflow, and adds a private,
avatar-enabled paginated Overview/Combat/Economy Account Summary with VIP, compact power, KP
Loss/Tanking Score, percentage-labelled Tanking, Conduct in Economy, UTC date-times, and a complete
formula-safe CSV. The main roster uses a larger two-column governor-tile grid with prominent Power
values and no duplicate Main-governor header line. Same-payload fallbacks, author gates, graceful
timeouts, attachment replacement, and stream cleanup are retained; no SQL schema, registry,
ownership, direct Inventory, or existing export contract changed. The completed Phase 5C task pack
and starter are archived.

Phase 5D Premium Reminders Summary Card is complete and operator accepted in mirror PR #222 and
production PR #529 after final smoke on 2026-07-15. `/me reminders` now provides the private,
avatar-enabled 1702x924 ACTIVE/REVIEW/OFF card, truthful coverage hero, friendly KVK/Calendar
summaries, deterministic insight, duplicate-safe identity, page-relevant navigation without the
deprecated Inventory button, aligned state support, a full UTC footer, same-payload fallback, and
graceful timeout. Manage refresh and all existing reminder behavior remain intact. The completed
Phase 5D task pack and starter are archived.

Phase 5D.1 Authoritative Next Scheduled Alert Projection is complete and operator accepted in
mirror PR #223 and production PR #530 after final Discord smoke on 2026-07-15. The Reminders hero
now selects the deterministic earliest future KVK or Calendar candidate through narrow pure
eligibility shared with live dispatch, distinguishes healthy `NO UPCOMING ALERT` from request-level
`SCHEDULE UNAVAILABLE`, and performs no jobs, DMs, acknowledgements, refreshes, network calls, or
writes. The default KVK snapshot uses the same injected UTC clock as the projection, and the final
card makes the authoritative event start date-time prominent in bold gold. Existing reminder,
tracker, rehydration, retry, command, Calendar, persistence, and DM contracts remain unchanged apart
from the separately authorised KVK at-start eligibility correction. The completed task pack and
starter are archived.

Phase 5E Premium Preferences Summary Card is complete, operator accepted, merged in mirror PR #224
and production PR #531, and deployed on 2026-07-16. `/me preferences` is now the private Discord-
user-level Personal Settings centre with the invoking user's top-left avatar on an approved
1702x924 standalone card, DST-aware local-time context, regional-profile coverage, truthful
Inventory privacy copy, deterministic insight, one in-place `Manage settings` journey, and a same-
payload fallback. `Update VIP` now belongs to the existing
Manage Accounts task selector and explicitly resolves a currently linked governor before the
unchanged VIP service rechecks access and writes. Profile saves use a narrow atomic field-specific
DAL upsert so concurrent edits to different fields do not overwrite one another. No SQL repository
object, schema, migration, procedure, view, index, data, default, or preference meaning changed.
The completed Phase 5E task pack and starter are archived.

GovernorOS v2 Phase 5F supersedes Phase 5E's Inventory-privacy ownership and the proposed Premium
Inventory Summary Card. The implementation retires `/me inventory`, `/myinventory`, and
`/inventory_preferences` together; removes public Inventory reporting, combined `All` viewing, the
visibility model/service/DAL, the orphaned legacy controller, and the old summary backdrop; and
simplifies Personal Settings to regional profile plus derived `LOCAL`/`UTC` context. It preserves
the selected-governor dashboard, `/me resources`, `/me speedups`, `/me materials`, and their private
report-page Excel/CSV/Google Sheets exports. At the accepted Phase 5F checkpoint, `/me exports`
contained only the Stats export journey;
the legacy combined/all-governor Inventory export and `/export_inventory` are retired. `/inventory
import` and `/inventory audit` remain. `dbo.InventoryReportPreference` and existing rows remain
untouched for rollback; there is no SQL deployment in Phase 5F.

Phase 5F is complete and operator accepted after final Discord smoke on 2026-07-16. Mirror PR #225
contains the accepted implementation, and production-branch commit `89f7da16` carries the promoted
patch. The completed task pack and chat starter are archived under `docs/task_packs/archive/`.

GovernorOS v2 Phase 5G Account Data Export Consolidation is implemented on its working branch and
is in validation/review before operator smoke and promotion. It removes `/me exports` and
`/my_stats_export`, removes every Exports navigation surface, and makes
`/me accounts -> Account Summary -> Download data` the canonical all-linked personal-data journey.

`Download data` offers a default Account-Summary-first formatted workbook (`.xlsx`), the exact
current Account Summary snapshot (`.csv`), or raw Stats history (`.csv`) for 30/60/90/180/360 days.
The phase also corrects every identified Stats export issue: exact inclusive N-day windows, filtered
`ALL_DAILY`, actual written row counts/date bounds, selected-window Forts semantics, shared formula
safety, separate Stats/Inventory freshness, truthful generated time, and one honest Excel/Google
Sheets-compatible workbook option. The top-level command surface is 38, `/me` has seven grouped
subcommands, and `/inventory` remains at two. The three selected-governor Inventory report-page
exports remain unchanged. `/my_stats` remains unchanged; redesign and migration are Phase 6.

Active Phase 5G records:

- `docs/task_packs/Codex Task Pack - Player Self-Service Command Centre v2 Phase 5G Account Data Export Consolidation.md`
- `docs/task_packs/Codex Chat Starter - Player Self-Service Command Centre v2 Phase 5G Account Data Export Consolidation.md`

## Quality Automation

Run before committing:

```powershell
python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py
python scripts/select_tests.py

pre-commit run -a
pytest -q tests
python scripts/analyse_pytest_log_noise.py
```

Before PR handoff, make and record the security-review decision with
`k98-security-review-routing` when the change touches permissions, Discord interactions,
SQL/data access, file handling, secrets/config, dependencies, deployment, network calls,
user-controlled input, subprocesses, or restart-sensitive persistence.

- Routine Git-backed changes: run `$codex-security:security-diff-scan` or record a precise skip.
- Standard or deep codebase scans: only after an explicit operator request for that audit.
- Confirm `Scan type: Changes`, the correct base/head, and Deep off for routine reviews.
- Run or justify skipping `python scripts/validate_codex_security_routing.py`.

`pytest` runs are isolated from production operational log files. Expected negative-path logs
remain visible through pytest output and `caplog`; when a saved audit artifact is needed, capture
the run explicitly, for example:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests 2>&1 | Tee-Object -FilePath .codex_pytest_audit.log
```

Use `python scripts/analyse_pytest_log_noise.py` to verify that pytest did not write to
`logs/log.txt`, `logs/error_log.txt`, `logs/crash.log`, or `logs/telemetry_log.jsonl`.

When a full-suite run feels slow, capture durations with the audit artifact so the next
optimisation task has actionable timing evidence:

```powershell
.\.venv\Scripts\python.exe -m pytest -vv tests --durations=30 --durations-min=1.0 2>&1 | Tee-Object -FilePath .codex_pytest_audit.log
```

Optional: for fast local searches, place `rg.exe` at `C:\discord_file_downloader\tools\rg.exe`.
`dev.ps1` adds `tools\` to `PATH` when that binary exists.

## Windows Setup (per new PowerShell session)
```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
.\dev.ps1
pre-commit autoupdate
pre-commit install --install-hooks
pre-commit run --all-files
pre-commit run --all-files
git switch main
git switch -c feat/

git add -A
git status
pre-commit run -a
git add -A

pre-commit run -a
git commit -m "feat: short summary of the change"

git push -u origin feat/my-topic # = what it is

cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
.\dev.ps1
git switch main
git pull
Git-CleanupMerged
.\venv\Scripts\python.exe -m pip install -r requirements.txt
pre-commit run -a


1. **Load local dev environment**
# === Session bootstrap (paste this as-is) ===
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Create venv if missing, then activate
if (-not (Test-Path .\venv\Scripts\Activate.ps1)) {
  py -m venv venv
}
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Dot-source local dev env (pre-commit cache, UTF-8, etc.)
. .\dev.ps1

# Ensure hooks are installed
pre-commit autoupdate
pre-commit install --install-hooks

# Quick sanity: run all hooks across repo
pre-commit run --all-files
# === end bootstrap ===


cd C:\discord_file_downloader
.\venv\Scripts\Activate
pytest -q tests/test_kvk_personal_views.py -vv
pytest -q tests/test_kvk_personal_service.py -vv
pytest -q tests/test_mykvkstats.py -vv
pytest -q tests/test_mykvktargets.py -vv


pytest -q tests/test_usage_tracker.py -vv
pytest -q tests/test_command_usage_dal.py -vv
pytest -q tests/test_mge_dm_followup.py -vv
pytest -q tests/test_mge_priority_rank_map.py -vv
pytest -q tests/test_mge_public_signup_embed.py -vv
pytest -q tests/test_mge_review_service.py -vv
pytest -q tests/test_mge_signup_config.py -vv
pytest -q tests/test_mge_signup_service.py -vv
pytest -q tests/test_mge_simplified_flow_service.py -vv
pytest -q tests/test_mge_simplified_signup_form_view.py -vv
pytest -q tests/test_mge_content_renderer.py -vv
pytest -q tests/test_mge_publish_service.py -vv
pytest -q tests/test_mge_embed_field_limits.py -vv
pytest -q tests/test_mge_embed_manager.py -vv
pytest -q tests/test_mge_simplified_leadership_service.py -vv

pytest -q tests/test_mge_rules_service.py tests/test_mge_rules_edit_view.py -vv
pytest -q tests/test_mge_signup_service.py tests/test_ark_registration_flow.py -vv

pytest -q tests/test_registry_io.py -vv
pytest -q tests/test_registry_io_xlsx.py -vv
pytest -q tests/test_registry_io_error_roundtrip.py -vv
pytest -q tests/test_registry_service.py -vv
pytest -q tests/test_registry_governor_registry.py -vv
pytest -q tests/test_registry_dal.py -vv
pytest -q tests/test_registry_views_smoke.py -vv


pytest tests/test_mge_simplified_leadership_admin_add.py -vv
pytest tests/test_mge_embed_manager.py -vv 
pytest tests/test_mge_simplified_flow_service.py -vv
pytest tests/test_mge_leadership_dal.py -vv 
pytest tests/test_mge_publish_service.py -vv
pytest tests/test_mge_simplified_leadership_view.py -vv 
pytest tests/test_mge_simplified_leadership_service.py -vv 
pytest tests/test_mge_simplified_signup_view.py -vv
pytest tests/test_mge_public_signup_embed.py -vv
pytest tests/test_mge_xlsx_parser.py -vv
pytest tests/test_mge_results_import.py -vv
pytest tests/test_dl_bot_mge_auto_import.py -vv
pytest tests/test_mge_results_import_service.py -vv
pytest tests/test_mge_results_overwrite_confirm_view.py -vv
pytest tests/test_mge_startup_wiring.py -vv 
pytest tests/test_mge_permissions.py -vv 
pytest tests/test_mge_rehydrate_and_regression.py -vv 
pytest tests/test_mge_startup_hook_invoked.py -vv
pytest tests/test_mge_simplified_flow_service.py -vv
pytest tests/test_mge_completion_service.py -vv 
pytest tests/test_mge_report_service.py -vv 
pytest tests/test_mge_admin_completion_view.py -vv 
pytest tests/test_mge_scheduler_completion.py -vv 
pytest tests/test_mge_rules_edit_view.py -vv
pytest tests/test_mge_rules_service.py -vv
pytest tests/test_mge_event_service_rules_regression.py -vv
pytest tests/test_mge_roster_rank_waitlist_notes.py -vv
pytest tests/test_mge_roster_permissions.py -vv
pytest tests/test_mge_roster_service.py -vv
pytest tests/test_mge_roster_delete_undo_audit.py -vv
pytest tests/test_mge_cache.py -vv
pytest tests/test_mge_event_service.py -vv
pytest tests/test_mge_scheduler.py -vv
pytest tests/test_mge_open_mode_switch.py -vv 
pytest tests/test_mge_signup_views.py -vv
pytest tests/test_mge_signup_service.py -vv
pytest tests/test_mge_dm_followup.py -vv
pytest tests/test_mge_summary_service.py -vv 
pytest tests/test_mge_review_service.py -vv
pytest tests/test_mge_leadership_board_view.py -vv
pytest tests/test_mge_cmds_register.py -vv

pytest tests/test_calendar_reminder_metrics.py -vv
pytest tests/test_calendar_reminder_prefs.py -vv 
pytest tests/test_calendar_datetime_utils_usage.py -vv
pytest tests/test_calendar_view_pagination.py -vv 
pytest tests/test_calendar_engine.py -vv 
pytest tests/test_calendar_reminders_dispatch.py -vv 
pytest tests/test_calendar_reminders.py -vv 
pytest tests/test_calendar_views.py -vv 
pytest tests/test_calendar_pinned_embed.py -vv
pytest tests/test_calendar_pipeline.py -vv 
pytest tests/test_calendar_commands.py -vv 
pytest tests/test_event_generator_sourcekind_mapping.py -vv 
pytest tests/test_constants.py -vv 
pytest tests/test_event_calendar_datetime_utils.py -vv
pytest tests/test_calendar_cache_contract.py -vv 
pytest tests/test_calendar_schema_contract.py -vv 
pytest tests/test_calendar_service.py -vv
pytest tests/test_sheets_sync_flow.py -vv 
pytest tests/test_sheets_sync_parsers.py -vv
pytest tests/test_admin_calendar_commands_task3.py -vv 
pytest tests/test_calendar_service_telemetry_task3.py -vv 
pytest tests/test_calendar_publish_cache.py -vv 
pytest tests/test_event_generator.py -vv 
pytest tests/test_calendar_scheduler.py -vv 
pytest tests/test_calendar_runtime_cache.py -vv
pytest tests/test_calendar_status_embed_task4.py -vv

cd C:\discord_file_downloader
.\venv\Scripts\Activate
pytest tests/test_ark_reminder_phase_gh.py -vv
pytest tests/test_ark_cancel_match.py -vv
pytest tests/test_ark_cancel_match_view.py -vv
pytest tests/test_ark_cancel_dm.py -vv
pytest tests/test_ark_team_publish_mention.py -vv
pytest tests/test_ark_reminder_phase_c.py -vv
pytest tests/test_ark_reminder_phase_bd.py -vv
pytest tests/test_ark_reminder_reschedule.py -vv
pytest tests/test_ark_dal_team_workflow.py -vv
pytest tests/test_ark_confirm_publish_service.py -vv
pytest tests/test_ark_draft_service.py -vv 
pytest tests/test_ark_preference_commands.py -vv
pytest tests/test_ark_preference_service.py -vv 
pytest tests/test_ark_auto_create_service.py -vv 
pytest tests/test_ark_team_balancer.py -vv 
pytest tests/test_ark_team_state.py -vv 
pytest tests/test_ark_registration_messages.py -vv 
pytest tests/test_ark_confirmation_modal.py -vv 
pytest tests/test_ark_scheduler_post_start.py -vv
pytest tests/test_ark_dal_results.py -vv
pytest tests/test_ark_confirmation_view.py -vv
pytest tests/test_ark_fuzzy_select_view.py -vv 
pytest tests/test_ark_bans_enforcement.py -vv
pytest tests/test_ark_ban_utils.py -vv
pytest tests/test_ark_ban_commands.py -vv
pytest tests/test_ark_scheduler_status_gating.py -vv 
pytest tests/test_ark_scheduler_final_day_routing.py -vv 
pytest tests/test_ark_scheduler_grace_window.py -vv 
pytest tests/test_ark_scheduler_dm_failures.py -vv 
pytest tests/test_ark_reminder_prefs_command.py -vv 
pytest tests/test_ark_reminder_prefs.py -vv 
pytest tests/test_ark_reminder_prefs_view.py -vv
pytest tests/test_ark_reminder_state.py -vv 
pytest tests/test_ark_scheduler_reminders.py -vv
pytest tests/test_ark_confirmation_view.py -vv
pytest tests/test_ark_confirmation_embed.py -vv
pytest tests/test_ark_scheduler.py -vv
pytest tests/test_ark_confirmation_flow.py -vv
pytest tests/test_local_time_embed_title.py -vv
pytest tests/test_ark_admin_roster.py -vv
pytest tests/test_ark_registration_flow.py -vv
pytest tests/test_ark_embeds.py -vv
set RUN_CITYHALLLEVEL_TEST=1
pytest tests/test_cityhalllevel_cache.py -vv
pytest tests/test_ark_phase3a_create_match.py -vv
pytest tests/test_ark_phase3b_amend_match.py -vv
pytest tests/test_ark_registration_message_move.py -vv
pytest tests/test_ark_cancel_match.py -vv
pytest tests/test_ark_cancel_match_view.py -vv
pytest tests/test_rehydrate_views_and_localtime.py -vv
pytest tests/test_rehydrate_views.py -vv
pytest tests/test_rehydrate_sanitize_and_fileio.py -vv
pytest tests/test_kvk_helpers.py -vv
pytest tests/test_gsheet_module.py -vv
pytest tests/test_gsheet_sorting.py -vv
pytest tests/test_kvk_helpers.py -vv
pytest tests/test_gsheet_helpers.py -vv
pytest tests/test_ark_state_json_migration.py -vv

pytest tests/test_command_registration_smoke.py -vv
pytest tests/test_domain_registrars_no_legacy_register_commands.py -vv
pytest tests/test_commands_ui_helpers_present.py -vv 
pytest tests/test_admin_views_smoke.py -vv
pytest tests/test_subscription_views.py -vv
pytest tests/test_ui_imports.py -vv
pytest tests/test_events_views.py -vv
pytest tests/test_stats_views_smoke.py -vv
pytest tests/test_kvkrankingview.py -vv
pytest tests/test_registry_views_smoke.py -vv
pytest tests/test_location_views_smoke.py -vv
pytest tests/test_embed_utils_target_lookup_injection.py -vv


python -m py_compile Commands.py ui/views/admin_views.py ui/views/location_views.py ui/views/registry_views.py ui/views/stats_views.py tests/test_ui_imports.py

pytest tests/test_embed_utils_target_lookup_injection.py -vv
python -m py_compile embed_utils.py

python -m py_compile Commands.py ui/__init__.py ui/views/__init__.py ui/views/events_views.py command_regenerate.py tests/test_events_views.py
pytest tests/test_events_views.py -vv
python scripts/validate_command_registration.py
pytest tests/test_interaction_safety.py -vv

pytest tests/test_build_kvkrankings_embed.py -vv
pytest tests/test_kvkrankingview.py -vv

pytest -q tests/test_stats_service.py -vv
pytest -q tests/test_embed_my_stats.py -vv
pytest -q tests/test_stats_export.py -vv
pytest -q tests/test_my_stats_export_command.py -vv
pytest -q tests/test_stats_exporter_csv.py -vv

pytest -q tests/test_kvk_history_offload_and_utils.py

pytest -q tests/test_honor_importer.py
pytest -q tests/test_honor_rankings_view.py

pytest -q tests/test_crystaltech_service.py
pytest -q tests/test_account_picker.py
pytest -q tests/test_kvk_ui_rebuild_options.py

pytest -q tests/test_registry_io.py
pytest -q tests/test_registry_io_xlsx.py
pytest -q tests/test_registry_io_error_roundtrip.py

pytest -q tests/test_prekvk_stats.py
pytest -q tests/test_prekvk_embed.py
pytest -q tests/test_prekvk_importer.py

pytest -q tests/test_gsheet_module.py
pytest -q tests/test_event_data_loader.py
pytest -q tests/test_player_stats_cache.py
pytest -q tests/test_prekvk_importer.py
pytest -q tests/test_proc_config_import.py
pytest -q tests/test_proc_config_import_phase2.py
pytest -q tests/test_sheet_importer.py
pytest -q tests/test_proc_config_import_offload.py
pytest -q tests/test_gsheet_helpers.py

pytest -q tests/test_event_cache.py

pytest -q tests/test_maintenance_suite.py

pytest -q tests/test_player_stats_cache.py
pytest -q tests/test_prekvk_importer.py
pytest -q tests/test_proc_config_import.py
pytest -q tests/test_proc_config_import_phase2.py
pytest -q tests/test_sheet_importer.py
pytest -q tests/test_proc_config_import_offload.py
pytest -q tests/test_gsheet_helpers.py

pytest -q tests/test_process_utils.py
pytest -q tests/test_file_utils_lockinfo.py
pytest -q tests/test_file_utils_2.py
pytest -q tests/test_file_utils.py

pytest -q tests/test_file_utils_2.py
pytest -q tests/test_file_utils_build_cmd.py

pytest -q tests/test_no_prints_in_cache_modules.py


pytest -q tests/test_live_queue_persistence.py

pytest -q tests/test_processing_pipeline.py

tests/test_processing_pipeline.py
tests/test_live_queue_persistence.py


pytest -q tests/test_offload_callable_integration.py
pytest -q tests/test_worker_module.py

pytest -q tests/test_offload_monitor_once.py
pytest -q tests/test_offload_registry_rotation.py

pytest -q tests/test_offload_serialization.py


pytest -q tests/test_file_utils_build_cmd.py
pytest -q tests/test_maintenance_worker_truncation.py
pytest -q tests/test_no_prints_in_cache_modules.py
