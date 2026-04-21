# K98 Bot — Standard Development Initiation Statement

> **Purpose:** Paste this at the start of every AI coding session to establish context
> and workflow. It is a **workflow prompt**, not a standalone reference.

---

## Context

This project uses two repositories:

| Repo | Purpose |
|------|---------|
| `cwatts6/K98-bot-mirror` | Python Discord bot — commands, services, UI, schedulers, caches |
| `cwatts6/K98-bot-SQL-Server` | SQL Server schema — tables, views, stored procedures (`sql_schema/`) |

**Deployment model:** All code is deployed locally first. 
You have full repository access for reference but do **not** create a PR. 
Provide complete files and I will validate, test, and create PRs manually.

---

## Required Reading

Before beginning implementation, review these attached materials **in order**:

1. **Feature Specification**  or **Task overview**
2. **Project Engineering Standards** — `K98 Bot — Project Engineering Standards.md`
3. **Codex Execution Guidelines** — `codex_execution_guidelines.md`

The engineering standards define the architecture and rules.
The execution guidelines define how to implement within that architecture.
This document defines the **workflow** you must follow.

> If any document conflicts, follow the priority chain in the Execution Guidelines §1.

---

## Workflow

### Step 1 — Review Scope

**🛑 STOP after this step — wait for my confirmation before proceeding.**

Carefully review the feature specification and supporting documentation.

Confirm you understand:

- [ ] Scope of the feature
- [ ] Affected subsystems and existing modules
- [ ] Required SQL schema changes (tables, SPs, views)
- [ ] Command and UI components
- [ ] Background processes or schedulers
- [ ] Cache implications
- [ ] Restart/persistence requirements
- [ ] Which existing helpers/patterns apply (check the Execution Guidelines §3 helper table)

If anything is unclear or inconsistent:
- Ask clarifying questions
- Propose improvements or simplifications
- Flag any conflicts with engineering standards

**Do not proceed until scope is confirmed.**

---

### Step 2 — Validate Against Architecture

**🛑 STOP after this step — confirm alignment before proceeding.**

Ensure the design aligns with the target architecture:

| Element | Must go in | Not allowed in |
|---------|-----------|----------------|
| New slash commands | `commands/<domain>_cmds.py` | Legacy root modules, `cogs/` |
| UI views/modals | `ui/views/` | Root-level `*_ui.py` files |
| Business logic / services | Subsystem package or `<domain>_service.py` | Command or UI layers |
| Repository / data access | Subsystem package or dedicated module | Command or UI layers |
| Shared core utilities | `core/` | New root-level helpers |
| Subsystem features | `event_calendar/`, `stats_alerts/`, `ark/` | New root-level monoliths |
| SQL schema objects | `sql_schema/<schema>.<Name>.<Type>.sql` (SQL repo) | Inline in Python code |
| Tests | `tests/test_<module>.py` | Untested |
| Scripts/CLI tools | `scripts/` | Root level |

**If the feature would violate architecture standards, propose a compliant structure.**

---

### Step 3 — Confirm Implementation Plan

**🛑 STOP after this step — get plan approval before writing code.**

Provide a short implementation outline:

- [ ] New modules to create (with exact file paths)
- [ ] Existing modules to modify
- [ ] SQL schema objects to create/modify
- [ ] Commands and UI elements (with decorator plan: `@versioned`, `@safe_command`, `@track_usage`)
- [ ] Services required
- [ ] Existing helpers to reuse (cite specific functions)
- [ ] Caching strategy
- [ ] Logging points (key actions to log)
- [ ] Restart safety approach
- [ ] Test plan

**Confirm the plan before writing any code.**

---

## Implementation Requirements

All code must meet the standards defined in the **Engineering Standards** and
**Execution Guidelines**. Key non-negotiable requirements:

### Architecture
- New code goes in target architecture directories — never expand legacy root modules
- Search existing helpers before creating new ones (see Execution Guidelines §3)
- Use exact existing filenames — do not "correct" known typos (`decoraters.py`, etc.)

### Commands
- Use `@versioned()`, `@safe_command`, `@track_usage()` decorators
- Call `safe_defer(ctx)` for deferred responses
- Keep commands thin — delegate to services

### Quality
- Module-level loggers: `logger = logging.getLogger(__name__)`
- **Prohibited:** `logging.basicConfig()`, bare `print()`, `except: pass`
- UTC timestamps only: `datetime.now(UTC)` — never `datetime.utcnow()`
- Use `fmt_short()` from `embed_utils` for datetime display
- Docstrings on all new public functions
- Type hints on all new public function signatures

### Persistence & Safety
- Critical state must be persisted to SQL (not in-memory only)
- Background tasks must have cancellation handling
- Destructive operations require confirmation prompts
- Follow `graceful_shutdown.py` patterns for shutdown safety

### Tooling
Code must pass all quality gates before delivery:
```bash
python -m black --check .
python -m ruff check .
python -m pyright
python -m pytest -q
```

---

## Output Format

When delivering implementation, provide:

1. **File manifest** — list of new and modified files with paths
2. **SQL changes** — separate files with `sql_schema/` naming convention
3. **Python code** — complete file contents (not diffs/patches)
4. **Helpers reused** — confirm which existing helpers were used instead of recreated
5. **Configuration changes** — if any `.env`, config, or `pyproject.toml` updates needed
6. **Testing steps** — specific commands to validate the feature
7. **Deployment notes** — migration order if SQL changes are involved (SQL first, then Python)

> Avoid partial implementations. Deliver complete, production-ready code.

---

## Goal

Deliver a **complete, production-ready implementation** that:

- ✅ Follows engineering standards and target architecture
- ✅ Integrates cleanly with existing modules and patterns
- ✅ Is restart-safe with SQL-persisted state
- ✅ Is observable via structured logging
- ✅ Passes all tooling gates (Black, Ruff, Pyright, pytest)
- ✅ Can be safely deployed and tested locally
- ✅ Includes tests for critical behaviour
