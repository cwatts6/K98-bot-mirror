# DevOps Runbook

Purpose: summarize deployment, promotion, configuration, and maintenance guidance.

## Repository Model

- `origin` points to `K98-bot-mirror`, the scrubbed Codex mirror.
- `production` points to `K98-bot`, the private production repo.
- Codex branches and PRs should target the mirror first.
- Production deployment must come from `K98-bot/main`, not the mirror.

Use `Promotion Guide.md` for the detailed mirror-to-production process.

## Local Setup

```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
.\dev.ps1
```

Install or update dependencies when needed:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Quality Gates

For normal PR work:

```powershell
python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py
python scripts/select_tests.py
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
```

Run focused pytest commands for the touched subsystem. Use full `pytest -q tests` before
promotion or when the blast radius is broad.

## Runtime Configuration

Use `ENV_REFERENCE.md` for variable details. Common required/important values:

- `DISCORD_BOT_TOKEN`
- `WATCHDOG_RUN=1`
- `GUILD_ID`
- channel IDs from `bot_config.py`
- SQL/ODBC settings from `constants.py`

## Logs And State

Important runtime locations are configured in `constants.py` and `logging_setup.py`:

- `LOG_DIR`
- `DATA_DIR`
- `logs/log.txt`
- `logs/error_log.txt`
- `logs/crash.log`
- `logs/telemetry_log.jsonl`
- `QUEUE_CACHE_FILE`
- `LAST_SHUTDOWN_INFO`
- `BOT_LOCK_PATH`

Back up `DATA_DIR` and operational logs before risky deployment or migration work.

## Maintenance And Offloads

Operational scripts:

- `scripts/collect_diagnostics.py`
- `scripts/offload_admin.py`
- `scripts/offload_monitor.py`
- `scripts/maintenance_telemetry_audit.py`

Use offload tooling to inspect or cancel long-running isolated work when the registry has enough
context to do so safely.

## Production Promotion

Use the patch-based promotion flow in `Promotion Guide.md`. Do not push mirror branch history
directly to production.

Before promotion:

- mirror PR validation is clean
- SQL repo changes are committed/reviewed when applicable
- targeted tests and quality gates pass
- migration/deployment order is documented

After promotion:

- open production PR from the promoted branch
- merge mirror and production PRs in the intended order
- deploy only from `K98-bot/main`
