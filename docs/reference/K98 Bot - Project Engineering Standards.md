# K98 Bot - Project Engineering Standards

> Living document. Canonical repo copy: `docs/reference/K98 Bot - Project Engineering Standards.md`.

## 1. Purpose

This is the architecture and engineering contract for the K98 bot ecosystem. It defines:

- where code belongs
- how responsibilities are separated
- how Python and SQL changes are delivered
- what must be checked when touching existing code
- what "production-ready" means for this project

Use this document with:

1. the task or feature specification
2. `K98 Bot - Coding Execution Guidelines.md`
3. `K98 Bot - Testing Standards.md`
4. `K98 Bot - Skills & Refactor Triggers.md`
5. `K98 Bot - Deferred Optimisation Framework.md`

When documents conflict, follow the priority chain in the execution guidelines.

## 2. Repositories

| Repo | Purpose | Primary language |
|------|---------|------------------|
| `cwatts6/K98-bot-mirror` | Scrubbed Codex mirror for bot application PRs | Python |
| `cwatts6/K98-bot` | Private production bot repository | Python |
| `cwatts6/K98-bot-SQL-Server` | Authoritative SQL Server schema, views, procedures, functions | T-SQL |

Local SQL source-of-truth path:

`C:\K98-bot-SQL-Server`

For SQL-facing work, validate against the SQL repo before implementation. Do not infer table,
column, procedure, view, index, `ProcConfig`, staging, or output-table contracts purely from
Python usage when SQL definitions exist.

## 3. Architecture Overview

The bot is in transition from a legacy flat-root layout to a modular architecture. The repo
root is the application root. There is no `bot/` wrapper directory.

### Target Locations

| Area | Location | Notes |
|------|----------|-------|
| Slash commands | `commands/` | One command module per domain |
| Shared low-level utilities | `core/` or existing helper modules | Prefer established helpers before adding new ones |
| Discord views/modals | `ui/views/` | Interaction layer only |
| Ark subsystem | `ark/` | Domain logic, DAL, services |
| Event calendar subsystem | `event_calendar/` | Scheduler, cache, reminders |
| MGE subsystem | `mge/` | Domain logic, DAL, services, reporting |
| Registry subsystem | `registry/` | Governor/account registry logic and DAL |
| Stats subsystem | `stats/`, `stats_alerts/`, `services/` | Stats data access, alerts, and orchestration |
| Operational scripts | `scripts/` | Diagnostics, validation, tooling |
| Tests | `tests/` | `pytest` suite |
| Embedded Python-side SQL | `sql/` when justified | Prefer DAL/repository modules for query execution |
| SQL schema objects | SQL repo `sql_schema/<schema>.<Object>.<Type>.sql` | Authoritative database contract |
| Documentation | `docs/` | Standards, references, runbooks, task support |
| Runtime config | `config/` | JSON and related config files |

### Legacy Root Modules

These root modules may still be modified when needed, but they must not be expanded as the
long-term home for new domain logic:

- `DL_bot.py`
- `Commands.py`
- `gsheet_module.py`
- `file_utils.py`
- `embed_utils.py`
- `bot_helpers.py`
- `processing_pipeline.py`
- `event_scheduler.py`
- `proc_config_import.py`

When a task touches one of these files, assess whether new logic should be extracted into the
target architecture and imported back.

## 4. Responsibility Boundaries

### Commands

Commands should:

- validate inputs
- perform permission checks
- defer safely where appropriate
- call service functions
- render Discord responses

Commands should not:

- contain business rules
- execute direct SQL
- own complex workflow orchestration
- be the only place a feature can be exercised

### Services

Services own:

- domain validation
- orchestration
- rule enforcement
- repository coordination
- cache coordination
- audit and outcome logging

Services must not depend on Discord types such as `ctx`, `Interaction`, `discord.Message`,
or view classes.

### Views

Views own:

- buttons
- dropdowns
- modals
- interaction routing
- response sequencing

Views must use safe interaction patterns and call services for business behaviour. They must
not contain domain business logic.

### Repositories / DAL

Data access code owns:

- SQL execution
- row mapping
- persistence contracts
- transaction boundaries where relevant

Repository code should avoid Discord concerns and presentation logic.

## 5. SQL Standards

SQL schema changes belong in the SQL repo using:

`sql_schema/<schema>.<ObjectName>.<Type>.sql`

Examples:

- `dbo.MGE_Events.Table.sql`
- `dbo.usp_CommandUsage_Snapshot.StoredProcedure.sql`
- `KVK.vw_FightingDataset.View.sql`

SQL authoring rules:

- Use `dbo` for general objects and `KVK` for KVK-specific objects unless the schema already dictates otherwise.
- Include `SET ANSI_NULLS ON`.
- Include `SET QUOTED_IDENTIFIER ON`.
- Keep Python aligned to the live SQL contract.
- Document migration order and rollback considerations for risky changes.
- Avoid destructive changes unless explicitly required.
- Do not leave schema drift implied only in Python comments.

Embedded SQL in Python is allowed only when it is truly operational or query-local. When touching
Python modules, actively check for SQL that should move out of command modules, views, or unrelated
helpers. Strong preference: query execution belongs in repository/data-access modules.

## 6. Helper Reuse And Duplicate Logic

Before creating a helper, search at least these:

- `file_utils.py`
- `utils.py`
- `embed_utils.py`
- `bot_helpers.py`
- `process_utils.py`
- `logging_setup.py`
- `admin_helpers.py`
- `target_utils.py`
- `governor_registry.py`
- `account_picker.py`
- `core/interaction_safety.py`

Duplicate helpers are a review blocker unless the existing helper is clearly unsuitable and the
replacement is part of an intentional consolidation. If a better helper exists but is awkwardly
placed, reuse first and capture relocation or cleanup as deferred work.

For helper-heavy changes, also consult `REVEIW_HELPERS.md`.

## 7. Refactor Review When Touching Code

When modifying an area, do not limit review to the exact changed lines. Assess whether the touched
area contains:

1. Direct SQL in commands or views
2. Business logic in the interaction layer
3. Duplicate helpers
4. Dead feature flow from older iterations
5. JSON-only persistence for critical state
6. Hidden coupling across modules
7. Missing tests around changed behaviour
8. Inconsistent logging or error handling

The task output should explicitly state whether these were found and whether they were fixed,
deferred, or out of scope. Deferred improvements must use the Deferred Optimisation Framework.

## 8. Logging, Errors, And Time

Use module-level loggers:

```python
import logging

logger = logging.getLogger(__name__)
```

Do not use:

- `logging.basicConfig()`
- bare `print()`
- `except: pass`

Key operations should log actor, object identifiers, outcome, and UTC timestamp where relevant.

Time rules:

- Persist UTC only.
- Use `from datetime import UTC, datetime`.
- Use `datetime.now(UTC)`.
- Convert to display format only at the rendering layer.
- Use `fmt_short()` from `embed_utils.py` for Discord-facing datetime display where appropriate.

## 9. Persistence And Restart Safety

Critical state must survive restart. Examples include:

- event and signup state
- registry state
- published message IDs
- reminder/task state
- confirmation or completion flags
- anything needed to rehydrate Discord views or avoid duplicate posts

In-memory-only state is not acceptable for critical workflows. JSON cache/state files may be used
as supplementary or transitional storage, but not as the sole authority for critical operational
state unless the feature is explicitly designed that way and documented.

## 10. Testing Baseline

Every production change requires a testing decision. Minimum expectation for changed behaviour:

- service-level happy path test
- at least one negative-path test
- regression coverage for the changed bug or behaviour
- permission boundary test when applicable
- restart/persistence test when applicable

See `K98 Bot - Testing Standards.md` for the full policy.

## 11. Known Filename And Schema Quirks

Use these exact names unless doing a coordinated migration:

- `decoraters.py`
- `docs/reference/REVEIW_HELPERS.md`
- `dbo.ALL_STATS_FOR_DASHBAORD`

Do not "fix" these by accident in isolated task work.

## 12. Definition Of Good Engineering Output

A good implementation in this project:

- fits the target architecture
- improves the touched area rather than preserving obvious debt
- avoids business logic in commands/views
- avoids direct SQL in commands/views
- uses existing helpers where possible
- includes sufficient tests
- preserves restart safety
- is observable through logging
- is locally deployable
- does not introduce speculative abstraction without need

## 13. Quick Review Checklist

Before marking work complete, confirm:

- [ ] New code is in target directories.
- [ ] Legacy modules were not expanded unnecessarily.
- [ ] Commands remain thin.
- [ ] Services own business logic.
- [ ] No new direct SQL was added to commands or views.
- [ ] Existing embedded SQL in touched areas was reviewed for extraction.
- [ ] Helper reuse was checked.
- [ ] Critical state is persisted safely.
- [ ] Logging is adequate.
- [ ] UTC handling is correct.
- [ ] Tests were added or updated appropriately.
- [ ] Any deferred debt in the touched area is explicitly called out.
