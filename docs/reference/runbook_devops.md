# DevOps Runbook

Purpose: summarize deployment, promotion, configuration, and maintenance guidance.

## Repository Model

- `origin` points to `K98-bot-mirror`, the scrubbed Codex mirror.
- `production` points to `K98-bot`, the private production repo.
- Codex branches and PRs should target the mirror first.
- Production deployment must come from `K98-bot/main`, not the mirror.

Use `Promotion Guide.md` for the detailed mirror-to-production process.

## Protected S11 deployment — current process

Follow the [operator Promotion Guide](Promotion%20Guide.md) and
[S11 release contract](S11%20Deployment%20and%20Restart%20Contract.md).
The protected runtime pins source hashes and startup policy together. Runtime
patches therefore use the fixed `Update-K98.ps1` command, which automatically
prepares a reviewed release definition for `Deploy-K98Release.ps1`;
a manual pull in the live checkout is not a complete deployment. The runner asks
for `/ops graceful_restart`, verifies the old pair drained, then installs matching
source/policy and verifies one successor start. Ordinary restart uses installed
source and does not deploy a merged PR.

Batch compatible patches into one deployment if useful. A documentation/test-only
merge needs no bot deployment unless it changes installed operational material.
SQL steps are included only for required reviewed migrations. Never replay prior
cutover or recovery as a routine patch step. Routine preparation is automatic;
the operator does not build manifests, calculate hashes or edit commands. SQL,
dependency and configuration releases retain separately reviewed steps. The
updater still awaits native/live acceptance; consult the Promotion Guide status.

The setup/dependency commands below are development/initial-setup guidance, not
instructions to mutate the running protected installation. Production dependency
changes require explicit inclusion in the reviewed release.

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
python scripts/analyse_pytest_log_noise.py
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
```

Run focused pytest commands for the touched subsystem. Use full `pytest -q tests` before
promotion or when the blast radius is broad. Use `python scripts/analyse_pytest_log_noise.py`
when deployment validation needs proof that pytest did not write WARNING/ERROR records to
production operational logs.

For command-surface changes, `scripts/validate_command_registration.py` also enforces the approved
top-level command baseline. New top-level commands or command groups require operator approval,
an `APPROVED_TOP_LEVEL_COMMANDS` update, and a matching
`docs/reference/canonical_command_reference.md` update before promotion.

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

Pytest evidence is intentionally separate from these operational logs. Review test failures in
pytest output or an explicitly captured audit file, for example `.codex_pytest_audit.log`.

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
