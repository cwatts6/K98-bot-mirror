# Developer Quickstart

## Windows Setup (per new PowerShell session)
```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
. .\dev.ps1
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

git switch main
git pull
Git-CleanupMerged


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
pytest tests/test_ark_scheduler_status_gating.py -v 
pytest tests/test_ark_scheduler_final_day_routing.py -v 
pytest tests/test_ark_scheduler_grace_window.py -v 
pytest tests/test_ark_scheduler_dm_failures.py -v 
pytest tests/test_ark_reminder_prefs_command.py -v 
pytest tests/test_ark_reminder_prefs.py -v 
pytest tests/test_ark_reminder_prefs_view.py -v
pytest tests/test_ark_reminder_state.py -v 
pytest tests/test_ark_scheduler_reminders.py -v
pytest tests/test_ark_confirmation_view.py -v
pytest tests/test_ark_confirmation_embed.py -v
pytest tests/test_ark_scheduler.py -v
pytest tests/test_ark_confirmation_flow.py -v
pytest tests/test_local_time_embed_title.py -v
pytest tests/tests_test_ark_admin_roster.py -v
pytest tests/test_ark_registration_flow.py -v
pytest tests/test_ark_embeds.py -v
set RUN_CITYHALLLEVEL_TEST=1
pytest tests/test_cityhalllevel_cache.py -v
pytest tests/test_ark_phase3a_create_match.py -v
pytest tests/test_ark_phase3b_amend_match.py -v
pytest tests/test_ark_registration_message_move.py -v
pytest tests/test_ark_cancel_match.py -v
pytest tests/test_ark_cancel_match_view.py -v
pytest tests/test_rehydrate_views_and_localtime.py -v
pytest tests/test_rehydrate_views.py -v
pytest tests/test_rehydrate_sanitize_and_fileio.py -v
pytest tests/test_kvk_helpers.py -v
pytest tests/test_gsheet_module.py -v
pytest tests/test_gsheet_sorting.py -v
pytest tests/test_kvk_helpers.py -v
pytest tests/test_gsheet_helpers.py -v

pytest tests/test_command_registration_smoke.py -v
pytest tests/test_domain_registrars_no_legacy_register_commands.py -v
pytest tests/test_commands_ui_helpers_present.py -v 
pytest tests/test_admin_views_smoke.py -v
pytest tests/test_subscription_views.py -v
pytest tests/test_ui_imports.py -v
pytest tests/test_events_views.py -v
pytest tests/test_stats_views_smoke.py -v
pytest tests/test_kvkrankingview.py -v
pytest tests/test_registry_views_smoke.py -v
pytest tests/test_location_views_smoke.py -v
pytest tests/test_embed_utils_target_lookup_injection.py -v


python -m py_compile Commands.py ui/views/admin_views.py ui/views/location_views.py ui/views/registry_views.py ui/views/stats_views.py tests/test_ui_imports.py

pytest tests/test_embed_utils_target_lookup_injection.py -v
python -m py_compile embed_utils.py

python -m py_compile Commands.py ui/__init__.py ui/views/__init__.py ui/views/events_views.py command_regenerate.py tests/test_events_views.py
pytest tests/test_events_views.py -v
python scripts/validate_command_registration.py
pytest tests/test_interaction_safety.py -v

pytest tests/test_build_kvkrankings_embed.py -v
pytest tests/test_kvkrankingview.py -v

pytest -q tests/test_stats_service.py -v
pytest -q tests/test_embed_my_stats.py -v
pytest -q tests/test_stats_export.py -v
pytest -q tests/test_my_stats_export_command.py -v
pytest -q tests/test_stats_exporter_csv.py -v

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
