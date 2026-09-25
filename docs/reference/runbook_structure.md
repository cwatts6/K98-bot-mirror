# Repository Structure

Purpose: quick navigation map. Architecture rules live in
`K98 Bot - Project Engineering Standards.md`.

## Root Entrypoints And Legacy Modules

- `DL_bot.py` - process entrypoint, startup guards, signal wiring, upload fast paths
- `bot_instance.py` - bot object, on-ready lifecycle, background tasks
- `Commands.py` - legacy command registration bridge
- `command_regenerate.py` - command registration support
- `constants.py` - paths, SQL connection constants, runtime file locations
- `bot_config.py` - environment parsing and exported config values
- `logging_setup.py` - logging and telemetry setup
- `file_utils.py`, `utils.py`, `process_utils.py`, `bot_helpers.py` - shared helpers

## Target Architecture Directories

- `commands/` - slash command modules
- `services/` - cross-domain service modules
- `core/` - low-level cross-cutting helpers
- `ui/views/` - Discord views/modals
- `ark/` - Ark domain logic
- `event_calendar/` - event calendar sync, cache, reminders
- `mge/` - MGE services, DAL, cache, views support
- `registry/` - governor/account registry
- `stats/`, `stats_alerts/` - stats data access, embeds, alert/report helpers
- `prekvk/`, `kvk/`, `inventory/` - domain packages
- `scripts/` - validation, diagnostics, maintenance tooling
- `tests/` - pytest suite
- `docs/` - standards, references, task packs, runbooks

## SQL Repo

SQL schema and stored procedures are authoritative in:

`C:\K98-bot-SQL-Server`

Use the SQL repo to validate table names, columns, stored procedures, views, indexes, and
`ProcConfig` usage before SQL-facing Python changes.

## Onboarding Checks

```powershell
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
python scripts/select_tests.py
```
