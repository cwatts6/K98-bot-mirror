# Developer Quickstart

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
