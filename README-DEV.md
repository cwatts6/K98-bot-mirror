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
