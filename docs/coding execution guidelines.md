# K98 Bot — Codex Execution Guidelines

> **Version:** 1.1 — updated 2026-03-11  
> **Companion to:** `K98 Bot — Project Engineering Standards.md` (authoritative)

---

## Purpose

This document instructs AI coding agents (Codex / ChatGPT / Copilot / automation tools)
how to safely generate code for the K98 Discord bot ecosystem.

Use alongside:

- **`K98 Bot — Project Engineering Standards.md`** — defines *how the system works*
- **Feature specifications** — define *what to build*
- **Codex task packs** — define *specific task scope*

This document defines **how the AI should implement tasks within that system**.

---

## 1  Mandatory Reading Order

Before implementing any task, read in this order:

1. `K98 Bot — Project Engineering Standards.md`
2. The feature specification document
3. This execution guidelines document
4. The Codex task pack (if provided)

### Conflict Resolution

| Priority | Source | Wins when… |
|----------|--------|------------|
| 1 | SQL schema (SQL Server repo) | Python must always conform to the DB contract |
| 2 | Feature specification | Defines *what* to build — overrides implementation defaults |
| 3 | Engineering standards | Defines *how* — overrides agent preferences |
| 4 | This execution guidelines doc | Defines *agent workflow* |
| 5 | Codex task pack | Scoped instructions for a specific task |
| 6 | Existing code patterns | Follow for consistency, but don't copy anti-patterns |

> **Key rule:** Never ignore engineering standards unless the feature spec *explicitly* overrides
> them and documents the deviation.

---

## 2  Architecture Awareness

### 2.1  Two architectures coexist

The repository has a **flat-root legacy layout** and a **target modular architecture**.
There is **no `bot/` wrapper directory** — the repo root IS the application root.

### 2.2  Target architecture directories (use for new code)

| Directory | Purpose | Example |
|-----------|---------|---------|
| `commands/` | Slash command groups | `commands/stats_cmds.py` |
| `core/` | Shared low-level utilities | `core/interaction_safety.py` |
| `ui/views/` | Discord UI components | `ui/views/ark_signup_view.py` |
| `event_calendar/` | Calendar subsystem package | `event_calendar/scheduler.py` |
| `stats_alerts/` | Stats alert subsystem | `stats_alerts/db.py` |
| `ark/` | Ark of Osiris subsystem | `ark/match_service.py` |
| `scripts/` | CLI & operational tools | `scripts/collect_diagnostics.py` |
| `tests/` | pytest test suite | `tests/test_calendar_engine.py` |
| `sql/` | Embedded SQL (Python-side) | `sql/calendar_schema.sql` |
| `docs/` | Documentation & runbooks | `docs/runbook_startup.md` |
| `config/` | Runtime config files | `config/sheet_config.json` |

### 2.3  Legacy root modules (do NOT expand)

These large root-level files are legacy. Never add new functionality to them:

- `DL_bot.py` (~61KB), `gsheet_module.py` (~121KB), `file_utils.py` (~80KB)
- `embed_utils.py` (~73KB), `bot_instance.py` (~79KB), `event_scheduler.py` (~51KB)
- `processing_pipeline.py` (~41KB), `proc_config_import.py` (~50KB)
- `Commands.py`, `cogs/commands.py` (legacy command bridge)

If you must touch a legacy module: extract the new logic into a target-architecture
package and import it back.

### 2.4  Known filename quirks

AI agents must use these **exact** filenames — do not "correct" them:

- `decoraters.py` — misspelled (not "decorators"), used across many imports
- `docs/REVEIW_HELPERS.md` — misspelled (not "REVIEW")
- `dbo.ALL_STATS_FOR_DASHBAORD` — SQL table typo; a corrected version also exists

---

## 3  Helper Reuse (Check Before Creating)

Before creating ANY new helper function, search these files first:

| File | Contains |
|------|----------|
| `file_utils.py` | SQL connection helpers, file I/O, data transforms |
| `utils.py` | General utility functions |
| `embed_utils.py` | Embed builders, `fmt_short()` for datetime formatting |
| `bot_helpers.py` | Bot-specific helpers |
| `constants.py` | Shared constants, channel IDs, role IDs |
| `process_utils.py` | Process management utilities |
| `governor_registry.py` | Governor lookup/registration |
| `account_picker.py` | Multi-account selection UI |
| `logging_setup.py` | Logging configuration |
| `target_utils.py` | Target/objective utilities |
| `admin_helpers.py` | Admin operation helpers |
| `core/interaction_safety.py` | Discord interaction safety wrappers |

> **Rule:** Duplicating an existing helper is a review blocker.

---

## 4  Feature Implementation Workflow

### Step 1 — Understand the domain

Determine: subsystem, command group, services, DB schema, UI components, caching needs.

### Step 2 — Map feature to modules

| Feature element | Target location |
|-----------------|-----------------|
| SQL schema objects | `sql_schema/<schema>.<Name>.<Type>.sql` (SQL Server repo) |
| Service / business logic | Subsystem package or `<domain>_service.py` |
| Repository / data access | Subsystem package or dedicated repository module |
| Slash command | `commands/<domain>_cmds.py` |
| Discord UI views | `ui/views/<name>.py` |
| Background/scheduled tasks | Subsystem package |
| Shared utilities | `core/<name>.py` |
| Tests | `tests/test_<module>.py` |

### Step 3 — Implementation order

1. Database schema (SQL Server repo)
2. Repository / data access layer
3. Service layer
4. Command interface
5. UI views
6. Caching layer
7. Tests

> **Never implement command logic before the service layer exists.**

---

## 5  SQL Change Rules

SQL changes go in the SQL Server repo: `cwatts6/K98-bot-SQL-Server`.

**File format:** `sql_schema/<schema>.<ObjectName>.<Type>.sql`

| Type | Example |
|------|---------|
| Table | `dbo.MGE_Events.Table.sql` |
| Stored Procedure | `KVK.sp_KVK_AllPlayers_Ingest.StoredProcedure.sql` |
| View | `KVK.vw_FightingDataset.View.sql` |
| Function | `dbo.fn_ExampleFunc.UserDefinedFunction.sql` |

**Guidelines:**
- Use `dbo` for general objects, `KVK` for KVK-specific objects
- Include `SET ANSI_NULLS ON` / `SET QUOTED_IDENTIFIER ON` headers
- Never inline schema changes inside Python code
- Avoid destructive migrations unless explicitly required
- Document migration order and breaking-change risk

---

## 6  Command Implementation Rules

All new commands live in `commands/<domain>_cmds.py`.

**Commands MUST:**
- Use standard decorators: `@versioned()`, `@safe_command`, `@track_usage()`
- Call `safe_defer(ctx)` for deferred responses
- Perform permission checks
- Validate arguments
- Call service functions
- Return Discord responses

**Commands MUST NOT:**
- Contain business logic
- Execute SQL directly
- Implement complex multi-step workflows

**Example pattern (from engineering standards):**
```python
@bot.slash_command(
    name="next_kvk_event",
    description="Show the next upcoming KVK events",
    guild_ids=[GUILD_ID],
)
@versioned("v1.04")
@safe_command
@track_usage()
async def next_kvk_event(ctx):
    logger.info("[COMMAND] /next_kvk_event used")
    await safe_defer(ctx, ephemeral=False)
    # ... call service, render response
```

---

## 7  Service Layer Rules

Services contain business logic and domain orchestration.

**Responsibilities:** validation, rule enforcement, orchestration, repository calls,
audit logging, cache coordination.

**Services MUST NOT** depend on Discord-specific objects (no `ctx`, `Interaction`,
`discord.Message` etc.).

---

## 8  UI View Rules

Discord UI elements live in `ui/views/`.

Views may contain: buttons, dropdowns, modals, interaction wiring.

Views must: call services, avoid business logic, handle interaction responses safely
using patterns from `core/interaction_safety.py`.

---

## 9  Restart & Persistence Safety

Critical state **must** survive bot restarts via SQL persistence:

- Events, signups, roster assignments, published lists
- Message/view IDs for rehydration (see `rehydrate_views.py`)
- Scheduler tasks (see `reminder_task_registry.py`)
- Subscription and registry state

**AI agents MUST NOT** implement stateful features using only in-memory variables.

**Shutdown requirements:**
- Background tasks must have explicit cancellation handling
- Use `graceful_shutdown.py` patterns
- No silent task loss

---

## 10  Logging Requirements

**Use module-specific loggers:**
```python
import logging
logger = logging.getLogger(__name__)
```

**Prohibited:** `logging.basicConfig()` — enforced by pre-commit hook. Will be rejected.

**Prohibited:** Bare `print()` in production modules — enforced by tests.

**Required log fields for key actions:**
```python
logger.info(
    "event_create",
    extra={
        "actor_id": actor_id,
        "event_id": event_id,
        "outcome": "success",
        "ts_utc": datetime.now(UTC).isoformat(),
    },
)
```

Never suppress exceptions silently (`except: pass` is prohibited).

---

## 11  Time & Timezone Standard

- **Persist UTC timestamps only** — never store local timezone values
- Use `datetime.now(UTC)` (not `datetime.utcnow()`)
- Convert for display only in the rendering layer
- Use `fmt_short()` from `embed_utils.py` for Discord-facing datetime formatting

---

## 12  Public vs Leadership Data

Public messages MUST NOT expose:
- Priority requests, leadership notes
- Evaluation metrics, internal reasoning

Leadership review boards may show full detail. Use ephemeral responses for sensitive
or admin outcomes.

---

## 13  Caching Rules

SQL Server is always the **source of truth**. Caches are performance optimisations only.

Cache safety pattern:
1. Fetch from SQL (authoritative source)
2. Validate the payload
3. Write to temp file
4. Atomic replace of live cache
5. Never overwrite a valid cache with empty/invalid data

---

## 14  Attachment Handling

Store metadata rather than downloading:
```python
{
    "discord_url": str,
    "filename": str,
    "content_type": str,
    "size": int,
}
```
Attachments should always be optional.

---

## 15  Destructive Operations

Operations that delete or reset data MUST require explicit confirmation.

Examples: switching modes, clearing signups, resetting rosters, purging data.

AI agents must always implement a confirmation prompt (button or modal).

---

## 16  Tooling & Quality Gates

### 16.1  Required tools (from `pyproject.toml`)

| Tool | Key settings |
|------|-------------|
| **Black** | `line-length = 100`, `target-version = ["py311"]`, exclude `old_discord_bot_package` |
| **Ruff** | `line-length = 100`, `target-version = "py311"`, `fix = true`, `unsafe-fixes = false`, select `E,F,W,I,B,UP,RUF` |
| **Pyright** | `pythonVersion = "3.11"`, `typeCheckingMode = "basic"` |

### 16.2  Pre-commit hooks (`.pre-commit-config.yaml`)

These run automatically and will reject non-conforming code:
- Trailing whitespace / end-of-file fixes
- Ruff lint
- Black format
- **Gitleaks** secret scanning (`--staged --redact`)
- Pyright type checking
- **`forbid-logging-basicconfig`** — rejects any `logging.basicConfig()` call

### 16.3  Validation commands (run before marking task complete)

```bash
python -m black --check .
python -m ruff check .
python -m pyright
python -m pytest -q
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
```

---

## 17  Testing Requirements

- **Framework:** pytest (configured in `pyproject.toml`)
- **Location:** `tests/` directory
- **Fixtures:** `tests/conftest.py`

Every new feature should include:
- Validation logic tests
- Service behaviour tests (happy + error paths)
- At least one **negative-path** test
- At least one **permission boundary** test
- Restart safety verification for stateful features

Existing tests must not break. Run `pytest` before marking complete.

---

## 18  Code Quality Expectations

Generated code must:
- Follow project naming conventions (see engineering standards §3)
- Include docstrings for new public functions and classes
- Use type hints on all new public functions
- Avoid duplicate helpers (check §3 of this doc first)
- Match existing architecture patterns
- Use `from datetime import UTC, datetime` (not `import datetime`)

**Do NOT:**
- Introduce new frameworks or dependencies unless specified
- Add new root-level modules when a target directory exists
- Invent new architectural patterns without justification

---

## 19  Definition of Done

A task is complete only when:

- [ ] Code follows engineering standards
- [ ] Modules placed in target architecture directories
- [ ] Standard decorators used on commands (`@versioned`, `@safe_command`, `@track_usage`)
- [ ] Structured logging added (module-level logger, no `basicConfig`, no bare `print`)
- [ ] UTC time standard followed
- [ ] Restart/persistence safety implemented for stateful features
- [ ] SQL changes in SQL Server repo with correct naming
- [ ] All quality gates pass (black, ruff, pyright, pytest)
- [ ] No legacy architecture violations
- [ ] Helper reuse verified (no duplication)
- [ ] Tests added and passing
- [ ] Commands work end-to-end

---

## 20  If Uncertain

When the specification is ambiguous:

1. Search the repository for similar implementations
2. Follow the closest existing subsystem pattern
3. Choose the **least disruptive** design
4. Check `docs/helpers_project_standards.md` for conventions
5. Prefer extracting to a target-architecture package over adding to legacy

Never invent a new architecture pattern without explicit justification.

---

## Appendix: Key File Quick Reference

| Need | File | Import |
|------|------|--------|
| Logger setup | `logging_setup.py` | `import logging; logger = logging.getLogger(__name__)` |
| Safe interaction | `core/interaction_safety.py` | `from core.interaction_safety import ...` |
| Command decorators | `decoraters.py` | `from decoraters import versioned, safe_command, track_usage` |
| Safe defer | `decoraters.py` or `bot_helpers.py` | `from bot_helpers import safe_defer` |
| Datetime formatting | `embed_utils.py` | `from embed_utils import fmt_short` |
| Constants | `constants.py` | `from constants import GUILD_ID, ...` |
| Bot config | `bot_config.py` | `from bot_config import ...` |
| View rehydration | `rehydrate_views.py` | Pattern for persistent Discord views |
| Graceful shutdown | `graceful_shutdown.py` | Shutdown orchestration patterns |
| ProcConfig (SQL config) | `proc_config_import.py` | SQL-backed key/value configuration |

---

*This document should be included in every Codex task pack context.*
