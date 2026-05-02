# K98 Bot — Coding Execution Guidelines

> **Version:** 2.0 — revised 2026-04-21  
> **Companion to:** `K98 Bot — Project Engineering Standards.md` (authoritative)

---

## 1. Purpose

This document tells AI coding agents how to execute work safely and consistently in the K98 bot ecosystem.

It focuses on:

- reading order
- implementation workflow
- refactor expectations while touching code
- output format
- quality gates
- escalation of uncertainty
- what must be checked before code is considered done

This document governs **agent behaviour**. The engineering standards govern **system rules**.

---

## 2. Mandatory Reading Order

Read in this order before implementation:

1. feature specification or task overview
2. `K98 Bot — Project Engineering Standards.md`
3. `K98 Bot — Coding Execution Guidelines.md`
4. `K98 Bot — Standard Development Initiation Statement.md`
5. `K98 Bot — Testing Standards.md`
6. `K98 Bot — Skills & Refactor Triggers.md`
7. task pack, if one exists

### Conflict resolution

Use this priority order:

1. live SQL schema / SQL repo contract
2. feature specification
3. engineering standards
4. testing standards
5. execution guidelines
6. initiation statement
7. task pack
8. existing code patterns

Existing code patterns should be followed for consistency, but never used to justify keeping an anti-pattern.

---

## 3. Mandatory Working Method

### 3.1 Review first

Before coding, identify:

- affected subsystem(s)
- command(s)
- services
- repositories / DAL
- SQL schema implications
- cache implications
- restart/persistence implications
- views/modals
- logging points
- likely tests to add or update

### 3.2 Stop-and-confirm workflow

Default working flow:

1. review scope
2. stop for confirmation
3. validate architecture and proposed design
4. stop for confirmation
5. present implementation plan
6. stop for confirmation
7. code only after approval

If the user explicitly asks for a full draft/update of standards documents or a complete task pack in one pass, produce it directly.

### 3.3 No “line-only” edits mindset

Do not treat a task as only the exact requested diff.

When touching an area, check whether the touched module still contains:

- direct SQL in command/view layers
- business logic in command/view layers
- dead code from previous feature iterations
- duplicate helpers
- weak validation
- missing logging
- missing tests

If issues are found:

fix when in scope or the same module and low risk
otherwise capture using the Deferred Optimisation Framework format
ensure deferred items are structured and suitable for later batching

---

## 4. Architecture-Aware Delivery

### 4.1 Two architectures coexist

The repo contains both:

- a legacy flat-root layout
- a target modular architecture

There is no `bot/` wrapper directory.

### 4.2 Placement rules

| Feature element | Target location |
|----------------|-----------------|
| Slash command | `commands/<domain>_cmds.py` |
| Service / business logic | subsystem package or `<domain>_service.py` |
| Repository / DAL | subsystem package or repository module |
| View / modal | `ui/views/<name>.py` |
| Shared low-level utility | `core/` |
| Operational tooling | `scripts/` |
| Tests | `tests/` |
| Embedded Python SQL | `sql/` when justified |
| SQL schema object | SQL repo `sql_schema/<schema>.<Object>.<Type>.sql` |

### 4.3 Legacy files

Do not add new long-term domain logic to major legacy root modules.

If a legacy file must be touched, prefer:

1. extract new logic to the target architecture
2. import it back
3. reduce legacy responsibility over time

---

## 5. Helper Reuse Protocol

Before creating any helper, search and assess these first:

- `file_utils.py`
- `utils.py`
- `embed_utils.py`
- `bot_helpers.py`
- `constants.py`
- `process_utils.py`
- `governor_registry.py`
- `account_picker.py`
- `logging_setup.py`
- `target_utils.py`
- `admin_helpers.py`
- `core/interaction_safety.py`

Required output behaviour:

- explicitly state which helpers were reused
- explicitly state when a new helper was necessary
- explicitly state if a duplicate helper or near-duplicate was discovered and what was done about it

---

## 6. Feature Implementation Order

Default order:

1. SQL schema or SQL contract review
2. repository / DAL
3. service layer
4. command layer
5. view layer
6. cache updates
7. tests
8. documentation / runbook notes if needed

Never implement a command-first feature when the service layer does not yet exist.

---

## 7. SQL Change Rules

SQL changes belong in the SQL Server repo.

### Required rules

- Use `sql_schema/<schema>.<ObjectName>.<Type>.sql`
- Include `SET ANSI_NULLS ON`
- Include `SET QUOTED_IDENTIFIER ON`
- Keep Python behaviour aligned to the SQL contract
- Document migration order
- Call out breaking-change risk

### Additional refactor rule

If Python code being changed contains SQL in a command or view layer, treat that as a **refactor checkpoint**.

You must decide and state one of:

- extracted now
- safe to defer for this task
- not in scope because of explicit user constraint

Silently leaving it in place is not acceptable.

---

## 8. Command Layer Rules

All new commands live in `commands/<domain>_cmds.py`.

Commands must:

- use `@versioned()`, `@safe_command`, `@track_usage()`
- use `safe_defer(ctx)` when deferred response is needed
- validate inputs
- check permissions
- call service functions
- return Discord responses

Commands must not:

- contain business logic
- execute SQL directly
- own cache mutation logic except trivial service handoff
- implement complex workflow state machines

---

## 9. Service Layer Rules

Services own domain orchestration.

Services should contain:

- validation
- rule enforcement
- repository calls
- cache coordination
- audit logging
- cross-module orchestration

Services must not use Discord objects.

---

## 10. View Layer Rules

Views live in `ui/views/`.

Views may contain:

- buttons
- selects
- modals
- interaction wiring
- response sequencing

Views must:

- use `core/interaction_safety.py` patterns
- call services
- avoid business logic

---

## 11. Restart, Persistence, and State Safety

Critical state must survive restart.

AI agents must not design stateful features that rely solely on:

- process memory
- view instance state
- temporary files
- non-authoritative JSON files

Required considerations when applicable:

- SQL-persisted state
- message/view rehydration
- deduplication of reminders/posts
- cancellation handling for background tasks
- restart-safe recovery paths

If a task changes a stateful area, the output must state how restart safety was verified or why no change was required.

---

## 12. Logging and Observability

Use module-specific loggers:

```python
import logging
logger = logging.getLogger(__name__)
```

Do not use:

- `logging.basicConfig()`
- bare `print()`
- `except: pass`

Log key decisions and outcomes with identifiers and UTC timestamps where relevant.

When debugging or auditing an area, do not merely add logs. Also assess whether the current log points are sufficient to explain failures end-to-end.

---

## 13. Time Standard

- Persist UTC only
- Use `from datetime import UTC, datetime`
- Use `datetime.now(UTC)`
- Use `fmt_short()` only at display time
- Never persist local time

---

## 14. Testing Execution Rules

Every meaningful change requires a test decision.

### Minimum expectation

- happy path test
- negative path test
- regression test for the changed behaviour or bug
- permission boundary test when applicable
- restart/persistence test when applicable

### Additional rules

- update existing tests if the implementation changes expected behaviour
- review nearby tests when refactoring an area
- if no tests are added, explicitly justify why
- do not rely solely on smoke imports for behavioural coverage

See `K98 Bot — Testing Standards.md` for the fuller matrix.

---

## 15. Output Format for Delivered Work

When delivering code or a task pack, provide:

1. file manifest
2. exact file paths
3. SQL changes separately
4. helpers reused
5. refactor findings in touched areas
6. test plan
7. deployment / migration order
8. follow-on debt or deferred improvements

For coding tasks, provide complete files unless the user asked for a patch format.

---

## 16. Definition of Done

A task is done only when:

- [ ] engineering standards were followed
- [ ] architecture placement is correct
- [ ] commands are thin
- [ ] services own business logic
- [ ] no new direct SQL was added to commands/views
- [ ] touched areas were checked for existing embedded SQL and duplication
- [ ] helper reuse was verified
- [ ] logging is adequate
- [ ] UTC handling is correct
- [ ] restart safety is preserved
- [ ] tests were added or updated appropriately
- [ ] quality gates were considered
- [ ] deferred debt is captured using the Deferred Optimisation Framework format
- [ ] deferred items are suitable for grouping into optimisation batches

---

## 17. Quality Gates

Run or recommend these before completion:

```bash
python -m black --check .
python -m ruff check .
python -m pyright
python -m pytest -q
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
```

For SQL-heavy or configuration-heavy tasks, also include any targeted validation commands relevant to the subsystem.

---

## 18. If Uncertain

When unsure:

1. inspect the closest subsystem pattern
2. choose the least disruptive compliant design
3. surface uncertainty explicitly
4. avoid inventing new architecture
5. prefer extraction over expansion of legacy files

If the user has not asked for code yet, stop at plan approval rather than guessing.

---

## 19. Companion Documents

Use alongside:

- `K98 Bot — Project Engineering Standards.md`
- `K98 Bot — Standard Development Initiation Statement.md`
- `K98 Bot — Testing Standards.md`
- `K98 Bot — Skills & Refactor Triggers.md`
