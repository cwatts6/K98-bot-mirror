# K98 Bot — Project Engineering Standards

> **Living document** — revised 2026-04-21  
> Canonical location: keep alongside the codebase in `docs/` or project root.

---

## 1. Purpose

This is the **architecture and engineering contract** for the K98 bot ecosystem.

It defines:

- where code belongs
- how responsibilities are separated
- what must be avoided during refactors
- how Python and SQL changes are delivered
- what “production-ready” means in this project

Use this document with:

1. the task or feature specification
2. `K98 Bot — Coding Execution Guidelines.md`
3. `K98 Bot — Standard Development Initiation Statement.md`
4. `K98 Bot — Testing Standards.md`
5. `K98 Bot — Skills & Refactor Triggers.md`

When documents conflict, follow the priority chain in the execution guidelines.

---

## 2. Repositories

| Repo | Purpose | Primary language |
|------|---------|------------------|
| `cwatts6/K98-bot-mirror` | Discord bot application | Python |
| `cwatts6/K98-bot-SQL-Server` | SQL Server schema, views, procedures, functions | TSQL |

---

## 3. Architecture Overview

### 3.1 Current state

The bot is in transition from a **legacy flat-root layout** to a **target modular architecture**.

The repo root is the application root. There is **no `bot/` wrapper directory**.

### 3.2 Target architecture

New code must go into target directories.

| Area | Location | Notes |
|------|----------|-------|
| Slash commands | `commands/` | One command module per domain |
| Shared low-level utilities | `core/` | Reusable non-domain helpers |
| Discord views/modals | `ui/views/` | Interaction layer only |
| Ark subsystem | `ark/` | Domain logic, DAL, services |
| Event calendar subsystem | `event_calendar/` | Scheduler, cache, reminders |
| Stats alerts subsystem | `stats_alerts/` | Stats generation and delivery |
| Operational scripts | `scripts/` | Diagnostics, validation, tooling |
| Tests | `tests/` | `pytest` suite |
| Embedded Python-side SQL | `sql/` | Only when SQL is intentionally embedded |
| Documentation | `docs/` | Runbooks, standards, task support |
| Runtime config | `config/` | JSON and related config files |

### 3.3 Legacy root modules

These legacy modules may still be modified when needed, but they must **not be expanded as the long-term home for new domain logic**:

- `DL_bot.py`
- `Commands.py`
- `gsheet_module.py`
- `file_utils.py`
- `embed_utils.py`
- `bot_helpers.py`
- `processing_pipeline.py`
- `event_scheduler.py`
- `proc_config_import.py`

**Rule:** if a task touches one of these files, use the change as a chance to **extract logic outward** into the target architecture where practical.

### 3.4 Refactor expectation when touching code

When modifying an area, do not limit review to the exact lines changed.

You must also assess whether the change should include:

- extracting business logic out of a command or view
- removing direct SQL from command files
- moving reusable helpers out of legacy modules
- deleting dead code or unreachable flow branches
- consolidating duplicate logic
- improving naming, validation, and logging consistency
- replacing ad hoc JSON-only persistence with SQL-backed persistence where the state is critical

This does **not** mean every task becomes a full rewrite. It means obvious structural debt in the touched area should be surfaced and, when in scope, corrected rather than preserved.

---

## 4. Module Placement Rules

| Scenario | Correct location | Avoid |
|----------|------------------|-------|
| New slash command group | `commands/<domain>_cmds.py` | `cogs/`, legacy root modules |
| New view or modal | `ui/views/<name>.py` | root-level UI helpers |
| New service/business logic | subsystem package or `<domain>_service.py` | commands, views |
| New repository/data access layer | subsystem package or repository module | commands, views |
| New shared utility | `core/` | new root-level helper files |
| SQL schema changes | SQL repo `sql_schema/<schema>.<Object>.<Type>.sql` | inline migration SQL in Python |
| Tests | `tests/test_<module>.py` | untested delivery |
| Operational tooling | `scripts/` | root |
| Documentation | `docs/` | ad hoc notes in task packs only |

---

## 5. Responsibility Boundaries

### 5.1 Commands

Commands should:

- validate inputs
- perform permission checks
- defer safely where appropriate
- call service functions
- render Discord responses

Commands should not:

- contain business rules
- execute direct SQL
- own multi-step orchestration
- be the only place a feature can be exercised

### 5.2 Services

Services own:

- domain validation
- orchestration
- rule enforcement
- repository coordination
- cache coordination
- audit and outcome logging

Services must not depend on Discord types such as `ctx`, `Interaction`, `discord.Message`, or view classes.

### 5.3 Views

Views own:

- buttons
- dropdowns
- modals
- interaction routing
- response safety patterns

Views must not contain domain business logic.

### 5.4 Repositories / DAL

Data access code owns:

- SQL execution
- row mapping
- persistence contracts
- transaction boundaries where relevant

Repository code should avoid Discord concerns and avoid embedding domain presentation logic.

---

## 6. SQL Standards

### 6.1 Location

SQL schema changes belong in the SQL repo using the naming convention:

`sql_schema/<schema>.<ObjectName>.<Type>.sql`

Examples:

- `dbo.MGE_Events.Table.sql`
- `dbo.usp_CommandUsage_Snapshot.StoredProcedure.sql`
- `KVK.vw_FightingDataset.View.sql`

### 6.2 SQL authoring rules

- Use `dbo` for general objects and `KVK` for KVK-specific objects unless the schema already dictates otherwise.
- Include `SET ANSI_NULLS ON` and `SET QUOTED_IDENTIFIER ON`.
- Keep Python aligned to the live database contract.
- Document migration order and rollback considerations for risky changes.
- Avoid destructive changes unless explicitly required.
- Do not leave schema drift implied only in Python comments.

### 6.3 Python-side SQL discipline

Embedded SQL in Python is allowed only when it is truly operational or query-local.

When touching Python modules, actively check for SQL that should be moved out of:

- command modules
- views
- unrelated helper modules

**Strong preference:** SQL should sit in repository/data-access modules, or in the SQL repo when it is a schema object.

---

## 7. Helper Reuse and Duplicate Logic

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
- `core/interaction_safety.py`

Duplicate helpers are a review blocker unless the existing helper is clearly unsuitable and the replacement is part of an intentional consolidation.

If a better helper already exists but is awkwardly placed, prefer **reusing first** and plan extraction or relocation as part of the refactor.

---

## 8. Refactor Rules for Existing Areas

When working in an existing module, assess and note:

1. **Direct SQL in commands or views**
2. **Business logic in the interaction layer**
3. **Duplicate helpers**
4. **Dead feature flow from older iterations**
5. **JSON-only persistence for critical state**
6. **Hidden coupling across modules**
7. **Missing tests around changed behaviour**
8. **Inconsistent logging or error handling**

At minimum, the task output should explicitly state whether any of the above were found and whether they were fixed, deferred, or out of scope.

---

## 9. Logging, Errors, and Time

### 9.1 Logging

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

### 9.2 Error handling

- No silent failure
- No swallowed exception without explanation
- Validation errors should be explicit and user-safe
- Operational failures should be logged with enough context to debug

### 9.3 Time

- Persist UTC only
- Use `from datetime import UTC, datetime`
- Use `datetime.now(UTC)`
- Convert to display format only at the rendering layer
- Use `fmt_short()` from `embed_utils.py` for Discord-facing datetime display where appropriate

---

## 10. Persistence and Restart Safety

Critical state must survive restart.

Examples:

- event and signup state
- registry state
- published message IDs
- reminder/task state
- confirmation or completion flags
- anything needed to rehydrate Discord views or avoid duplicate posts

In-memory-only state is not acceptable for critical workflows.

JSON cache/state files may be used as supplementary or transitional storage, but not as the sole authority for critical operational state unless the feature is explicitly designed that way and documented.

---

## 11. Testing Baseline

Every production change should be accompanied by a testing decision.

Minimum expectation for changed behaviour:

- service-level happy path test
- at least one negative-path test
- regression coverage for the changed bug or behaviour
- permission boundary test when applicable
- restart/persistence test when applicable

See `K98 Bot — Testing Standards.md` for the full policy.

---

## 12. Known Filename and Schema Quirks

Use these exact names unless doing a coordinated migration:

- `decoraters.py`
- `docs/REVEIW_HELPERS.md`
- `dbo.ALL_STATS_FOR_DASHBAORD`

Do not “fix” these by accident in isolated task work.

---

## 13. Definition of Good Engineering Output

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

---

## 14. Quick Review Checklist

Before marking work complete, confirm:

- [ ] New code is in target directories
- [ ] Legacy modules were not expanded unnecessarily
- [ ] Commands remain thin
- [ ] Services own business logic
- [ ] No new direct SQL in commands or views
- [ ] Existing embedded SQL in touched areas was reviewed for extraction
- [ ] Helper reuse was checked
- [ ] Critical state is persisted safely
- [ ] Logging is adequate
- [ ] UTC handling is correct
- [ ] Tests were added or updated appropriately
- [ ] Any deferred debt in the touched area is explicitly called out

---

## 15. Companion Documents

Read alongside this document:

- `K98 Bot — Coding Execution Guidelines.md`
- `K98 Bot — Standard Development Initiation Statement.md`
- `K98 Bot — Testing Standards.md`
- `K98 Bot — Skills & Refactor Triggers.md`
