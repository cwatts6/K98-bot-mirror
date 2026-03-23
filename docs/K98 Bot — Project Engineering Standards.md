# K98 Bot — Project Engineering Standards

> **Living document** — updated 2026-03-11  
> Canonical location: keep alongside the codebase in `docs/` or project root.

---

## 1  Repositories

| Repo | Purpose | Primary language |
|------|---------|-----------------|
| [`K98-bot-mirror`](https://github.com/cwatts6/K98-bot-mirror) | Discord bot — Python application | Python 99.4% |
| [`K98-bot-SQL-Server`](https://github.com/cwatts6/K98-bot-SQL-Server) | SQL Server schema & stored procedures | TSQL 97.5 %, PLpgSQL 2.5 % |

---

## 2  Architecture Overview

### 2.1  Current state (legacy + target)

The codebase is transitioning from a **flat-root monolith** to a **modular package structure**.

**Legacy code** lives at the repository root as standalone `.py` files. **New modules** MUST be delivered
into the target package directories listed below. Legacy modules will be refactored into the target
layout incrementally.

### 2.2  Target directory layout (`K98-bot-mirror`)

> ⚠️ There is **no `bot/` wrapper directory**. The repo root IS the application root.

```
K98-bot-mirror/                  # ← repo root = application root
│
├── run_bot.py                   # Entry point (start here)
├── bot_instance.py              # Bot singleton / core loop
├── bot_config.py                # Runtime configuration
├── bot_loader.py                # Extension loader
├── bot_startup_gate.py          # Startup readiness gate
├── constants.py                 # Shared constants
├── decoraters.py                # Custom decorators (legacy filename)
├── graceful_shutdown.py         # Shutdown orchestration
├── logging_setup.py             # Logging configuration
├── singleton_lock.py            # Single-instance lock
│
├── commands/                    # ★ Slash-command modules (target arch)
│   ├── __init__.py
│   ├── admin_cmds.py
│   ├── ark_cmds.py
│   ├── calendar_cmds.py
│   ├── events_cmds.py
│   ├── location_cmds.py
│   ├── registry_cmds.py
│   ├── stats_cmds.py
│   └── subscriptions_cmds.py
│
├── core/                        # ★ Shared core utilities (target arch)
│   ├── __init__.py
│   └── interaction_safety.py
│
├── ui/                          # ★ Discord UI components (target arch)
│   ├── __init__.py
│   └── views/
│
├── event_calendar/              # ★ Calendar subsystem package (target arch)
│   ├── __init__.py
│   ├── event_generator.py
│   ├── scheduler.py
│   ├── reminders.py
│   ├── reminder_prefs.py
│   ├── reminder_state.py
│   ├── runtime_cache.py
│   ├── cache_contract.py
│   ├── cache_publisher.py
│   ├── pinned_embed.py
│   ├── datetime_utils.py
│   ├── reminder_metrics.py
│   ├── reminder_prefs_store.py
│   └── reminder_types.py
│
├── stats_alerts/                # ★ Stats alert subsystem (target arch)
│   ├── __init__.py
│   ├── db.py
│   ├── allkingdoms.py
│   ├── formatters.py
│   ├── guard.py
│   ├── honors.py
│   ├── interface.py
│   ├── kvk_meta.py
│   ├── prekvk_stats.py
│   └── embeds/
│
├── ark/                         # ★ Ark of Osiris subsystem
├── cogs/                        # Legacy bridge cog (being replaced by commands/)
│   └── commands.py
│
├── scripts/                     # CLI & operational tools
│   ├── callable_worker.py
│   ├── collect_diagnostics.py
│   ├── config_self_test.py
│   ├── offload_admin.py
│   ├── offload_monitor.py
│   ├── smoke_imports.py
│   └── validate_command_registration.py
│
├── tests/                       # pytest test suite (100+ files)
│   └── conftest.py
│
├── sql/                         # Embedded SQL (calendar schema, test queries)
├── config/                      # Runtime config files (crystaltech JSON, SP configs)
├── docs/                        # Project documentation & runbooks
│   ├── ENV_REFERENCE.md
│   ├── OPERATIONS.md
│   ├── runbook_startup.md
│   ├── runbook_shutdown.md
│   ├── runbook_diagnostics.md
│   ├── runbook_devops.md
│   └── ...
├── assets/                      # Static assets (images, etc.)
│
├── pyproject.toml               # Project metadata, tool config, dependencies
├── requirements.txt             # Pip dependencies (loose)
├── requirements-freeze.txt      # Pip dependencies (pinned)
├── .pre-commit-config.yaml      # Pre-commit hooks
├── .gitleaks.toml               # Secret scanning config
├── .gitignore
├── .publishignore
│
│  ── Legacy root-level modules (to be refactored) ──
├── DL_bot.py                    # Legacy monolith (~61KB)
├── Commands.py                  # Legacy command dispatch
├── gsheet_module.py             # Google Sheets integration (~121KB)
├── file_utils.py                # File I/O utilities (~80KB)
├── embed_utils.py               # Embed builders (~72KB)
├── bot_helpers.py               # Miscellaneous helpers
├── processing_pipeline.py       # Data processing pipeline
├── event_scheduler.py           # Legacy event scheduler
├── ... (50+ additional legacy modules)
```

### 2.3  SQL Server layout (`K98-bot-SQL-Server`)

```
K98-bot-SQL-Server/
└── sql_schema/
    ├── README.md
    │
    │  ── Schemas ──
    ├── dbo.*                    # Primary schema (tables, SPs, functions)
    └── KVK.*                    # KVK-specific schema
        ├── KVK.KVK_AllPlayers_Raw.Table.sql
        ├── KVK.KVK_Windows.Table.sql
        ├── KVK.sp_KVK_AllPlayers_Ingest.StoredProcedure.sql
        ├── KVK.sp_KVK_Recompute_Windows.StoredProcedure.sql
        ├── KVK.vw_FightingDataset.View.sql
        └── ... (~150+ schema objects)
```

**Naming convention:** `<schema>.<ObjectName>.<Type>.sql`  
Types: `Table`, `StoredProcedure`, `View`, `UserDefinedFunction`

---

## 3  Module Placement Rules

| Scenario | Location | Example |
|----------|----------|---------|
| New slash command group | `commands/<domain>_cmds.py` | `commands/calendar_cmds.py` |
| New Discord UI view/modal | `ui/views/<name>.py` | `ui/views/ark_signup_view.py` |
| New self-contained subsystem | New package dir at root | `event_calendar/`, `stats_alerts/` |
| Shared low-level utility | `core/<name>.py` | `core/interaction_safety.py` |
| Operational/CLI script | `scripts/<name>.py` | `scripts/collect_diagnostics.py` |
| SQL schema change | `sql_schema/<schema>.<Name>.<Type>.sql` (SQL Server repo) | `dbo.IMPORT_STAGING_PROC.StoredProcedure.sql` |
| Embedded SQL (Python-side) | `sql/<name>.sql` | `sql/calendar_schema.sql` |
| Tests | `tests/test_<module>.py` | `tests/test_calendar_engine.py` |
| Documentation | `docs/<name>.md` | `docs/runbook_startup.md` |

**Legacy modules at root** should NOT be extended. If you must touch a legacy module, prefer extracting
the new logic into a target-architecture package and importing back.

---

## 4  Coding Standards

### 4.1  Python

- **Version:** 3.11+ (check `pyproject.toml` for current target)
- **Formatter:** Configured via `pyproject.toml` (Ruff/Black — check `[tool.ruff]` or `[tool.black]`)
- **Linter:** Ruff (configured in `pyproject.toml`)
- **Pre-commit:** `.pre-commit-config.yaml` — run `pre-commit install` after cloning
  - Includes: gitleaks (secret scanning), formatting, linting hooks
- **Type hints:** Preferred on all new public functions
- **Docstrings:** Required for new public functions and classes
- **Logging:** Use `logging_setup.py` — never use bare `print()` in production modules
  - See: `tests/test_no_prints_in_cache_modules.py` (enforced by test)
- **Async:** Bot commands and Discord event handlers are `async`. Use `await` for I/O.
- **Error handling:** Wrap Discord interactions with `core/interaction_safety.py` patterns
  - See: [`core/interaction_safety.py`](https://github.com/cwatts6/K98-bot-mirror/blob/main/core/interaction_safety.py)

### 4.2  SQL (TSQL)

- **Schemas:** Use `dbo` for general objects, `KVK` for KVK-specific objects
- **Naming:** PascalCase for tables/SPs, prefix SPs with `sp_` within `KVK` schema
- **File naming:** `<schema>.<ObjectName>.<Type>.sql`
- **Always include** `SET ANSI_NULLS ON` / `SET QUOTED_IDENTIFIER ON` headers

### 4.3  File naming conventions

| Type | Convention | Example |
|------|-----------|---------|
| Command modules | `<domain>_cmds.py` | `stats_cmds.py` |
| Embed builders | `embed_<name>.py` | `embed_my_stats.py` |
| Importers | `<domain>_importer.py` | `honor_importer.py` |
| Services | `<domain>_service.py` | `stats_service.py`, `crystaltech_service.py` |
| Cache modules | `<domain>_cache.py` | `player_stats_cache.py`, `profile_cache.py` |
| UI modules | `<domain>_ui.py` | `kvk_ui.py`, `crystaltech_ui.py` |
| Views | `<domain>_view.py` | `kvk_history_view.py`, `honor_rankings_view.py` |
| Helpers | `<domain>_helpers.py` | `bot_helpers.py`, `admin_helpers.py` |
| Config | `<domain>_config.py` | `bot_config.py`, `crystaltech_config.py` |
| Tests | `test_<module_or_feature>.py` | `test_calendar_engine.py` |

---

## 5  Testing

- **Framework:** pytest
- **Config:** `pyproject.toml` `[tool.pytest.ini_options]`
- **Location:** `tests/` directory
- **Run:** `pytest` from repo root
- **Coverage areas:** Commands, views, importers, pipeline, calendar, ark, file utils, embeds, etc.
- **Smoke tests exist for:**
  - Import validation: `scripts/smoke_imports.py`
  - Command registration: `scripts/validate_command_registration.py`
  - UI imports: `tests/test_ui_imports.py`
  - No-print enforcement: `tests/test_no_prints_in_cache_modules.py`

### Practical references:
- [`tests/conftest.py`](https://github.com/cwatts6/K98-bot-mirror/blob/main/tests/conftest.py) — shared fixtures
- [`tests/test_interaction_safety.py`](https://github.com/cwatts6/K98-bot-mirror/blob/main/tests/test_interaction_safety.py) — example of testing core module
- [`tests/test_processing_pipeline.py`](https://github.com/cwatts6/K98-bot-mirror/blob/main/tests/test_processing_pipeline.py) — pipeline testing pattern

---

## 6  Configuration & Environment

- **Environment variables:** Documented in [`docs/ENV_REFERENCE.md`](https://github.com/cwatts6/K98-bot-mirror/blob/main/docs/ENV_REFERENCE.md)
- **Bot config:** `bot_config.py` — runtime settings loaded from env / config files
- **ProcConfig:** `proc_config_import.py` — SQL Server-backed process configuration (key/value store)
  - Schema: `dbo.ProcConfig` table
  - Audit: `dbo.ProcConfig_AuditLog` table
- **Crystaltech paths:** `config/crystaltech_paths.v1.json`
- **Secrets:** Never committed. `.gitleaks.toml` configured for scanning. `.gitignore` excludes `.env` files.
- **Config self-test:** `scripts/config_self_test.py` — validates config on startup

---

## 7  Branching & PR Workflow

- **Default branch:** `main`
- **Feature branches:** Create from `main`, PR back to `main`
- **Pre-commit hooks:** Must pass before push (gitleaks, formatting, linting)
- **Review:** All PRs reviewed before merge
- **Test gate:** `pytest` must pass

---

## 8  Operations & Runbooks

Operational documentation lives in `docs/`:

| Runbook | Purpose | Link |
|---------|---------|------|
| `runbook_startup.md` | Bot startup procedure | [View](https://github.com/cwatts6/K98-bot-mirror/blob/main/docs/runbook_startup.md) |
| `runbook_shutdown.md` | Graceful shutdown procedure | [View](https://github.com/cwatts6/K98-bot-mirror/blob/main/docs/runbook_shutdown.md) |
| `runbook_diagnostics.md` | Troubleshooting & diagnostics | [View](https://github.com/cwatts6/K98-bot-mirror/blob/main/docs/runbook_diagnostics.md) |
| `runbook_devops.md` | DevOps procedures | [View](https://github.com/cwatts6/K98-bot-mirror/blob/main/docs/runbook_devops.md) |
| `OPERATIONS.md` | Day-to-day operations | [View](https://github.com/cwatts6/K98-bot-mirror/blob/main/docs/OPERATIONS.md) |
| `singleton_lock.md` | Single-instance lock design | [View](https://github.com/cwatts6/K98-bot-mirror/blob/main/docs/singleton_lock.md) |

**Key operational scripts:**

| Script | Purpose |
|--------|---------|
| `start-bot-after-sql.ps1` | Start bot after SQL Server is ready |
| `rotate-logs.ps1` | Log rotation |
| `dev.ps1` | Local development helper |
| `scripts/collect_diagnostics.py` | Collect runtime diagnostics |
| `scripts/offload_monitor.py` | Monitor offload queue |

---

## 9  Key Subsystems Reference

| Subsystem | Package / Files | Notes |
|-----------|----------------|-------|
| **Bot core** | `run_bot.py`, `bot_instance.py`, `bot_config.py`, `bot_loader.py` | Entry point + singleton |
| **Commands** | `commands/` package | Target architecture — all new commands here |
| **Event calendar** | `event_calendar/` package | Full subsystem: generator, reminders, cache, scheduler |
| **Stats alerts** | `stats_alerts/` package | Kingdom summaries, honors, pre-KVK alerts |
| **Ark of Osiris** | `ark/` directory | Match management, signups, bans |
| **UI views** | `ui/views/` | Discord UI components |
| **Data pipeline** | `processing_pipeline.py` (legacy root) | Stats ingestion pipeline |
| **Google Sheets** | `gsheet_module.py` (legacy root) | Sheets read/write integration |
| **SQL connectivity** | `file_utils.py` (legacy root) | Includes SQL connection helpers |
| **KVK tracking** | `kvk_*.py` files + `KVK` SQL schema | Multi-file subsystem spanning both repos |
| **Graceful shutdown** | `graceful_shutdown.py` | Coordinated async shutdown |
| **View rehydration** | `rehydrate_views.py` | Persistent Discord views across restarts |
| **CrystalTech** | `crystaltech_*.py` files | Config-driven technology paths |

---

## 10  Legacy Migration Tracker

The following large root-level files are candidates for decomposition into the target architecture:

| File | Size | Migration target |
|------|------|-----------------|
| `gsheet_module.py` | ~121 KB | Extract to `services/gsheet/` or `integrations/gsheet/` |
| `bot_instance.py` | ~79 KB | Extract subsystem hooks to respective packages |
| `file_utils.py` | ~80 KB | Extract SQL helpers to `core/db.py`, file I/O to `core/file_io.py` |
| `embed_utils.py` | ~73 KB | Extract by domain to `commands/` or `ui/embeds/` |
| `DL_bot.py` | ~61 KB | Legacy monolith — functionality migrated to `commands/` |
| `event_scheduler.py` | ~51 KB | Consolidate into `event_calendar/` |
| `proc_config_import.py` | ~50 KB | Extract to `core/proc_config/` |

> **Rule:** Do not add new functionality to these files. Extract, import back if needed, and plan
> eventual deletion behind a feature flag or version gate.

---

## 11  Known Issues & Quirks

1. **`decoraters.py`** — filename is misspelled ("decoraters" vs "decorators"). Do not rename without
   a coordinated find-and-replace across all imports.
2. **`dbo.ALL_STATS_FOR_DASHBAORD`** — SQL table name typo ("DASHBAORD" vs "DASHBOARD"). A corrected
   `dbo.ALL_STATS_FOR_DASHBOARD` table also exists. Both are live — check which is referenced before modifying.
3. **`docs/REVEIW_HELPERS.md`** — filename typo ("REVEIW" vs "REVIEW").
4. **Config file copies** — `config/` contains multiple `crystaltech_paths.v1*.json` variants
   (Copy, archive1, broken, old, out, path6, highinf). Clean up unused variants when safe.
5. **`cogs/commands.py`** — Legacy bridge to the old command system. Being replaced by `commands/` package.
   Do not add new commands here.

---

## 12  Quick-Start Checklist

```bash
# 1. Clone
git clone <repo-url> && cd K98-bot-mirror

# 2. Create virtual environment
python -m venv .venv && .venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install pre-commit hooks
pre-commit install

# 5. Run config self-test
python scripts/config_self_test.py

# 6. Run smoke imports
python scripts/smoke_imports.py

# 7. Run tests
pytest

# 8. Start bot (after SQL Server is running)
# Option A: Direct
python run_bot.py
# Option B: Via PowerShell script (waits for SQL)
.\start-bot-after-sql.ps1
```

---

## Appendix A  Useful links

- **Bot repo:** https://github.com/cwatts6/K98-bot-mirror
- **SQL repo:** https://github.com/cwatts6/K98-bot-SQL-Server
- **Dev README:** [`README-DEV.md`](https://github.com/cwatts6/K98-bot-mirror/blob/main/README-DEV.md)
- **Env reference:** [`docs/ENV_REFERENCE.md`](https://github.com/cwatts6/K98-bot-mirror/blob/main/docs/ENV_REFERENCE.md)
- **Operations guide:** [`docs/OPERATIONS.md`](https://github.com/cwatts6/K98-bot-mirror/blob/main/docs/OPERATIONS.md)
- **Helpers standards:** [`docs/helpers_project_standards.md`](https://github.com/cwatts6/K98-bot-mirror/blob/main/docs/helpers_project_standards.md)
