# K98 Bot - Coding Execution Guidelines

> Version 2.1. Canonical repo copy: `docs/reference/K98 Bot - Coding Execution Guidelines.md`.

## 1. Purpose

This document tells AI coding agents how to execute work safely and consistently in the K98 bot
ecosystem. It governs agent behaviour. `K98 Bot - Project Engineering Standards.md` governs
system architecture.

It covers:

- reading order
- review-first workflow
- implementation order
- refactor expectations while touching code
- output expectations
- quality gates
- uncertainty handling

## 2. Mandatory Reading Order

Before implementation, read in this order:

1. Feature specification, issue, user request, or task pack.
2. `README-DEV.md`.
3. `docs/reference/README.md`.
4. `docs/reference/K98 Bot - Project Engineering Standards.md`.
5. `docs/reference/K98 Bot - Coding Execution Guidelines.md`.
6. `docs/reference/K98 Bot - Testing Standards.md`.
7. `docs/reference/K98 Bot - Skills & Refactor Triggers.md`.
8. `docs/reference/K98 Bot - Deferred Optimisation Framework.md`.
9. Conditional references from `docs/reference/README.md` when relevant.

Do not read every reference document by default. Use the reference index to choose domain,
operational, promotion, or template documents only when the task calls for them.

### Conflict Resolution

Use this priority order:

1. Live SQL schema / SQL repo contract
2. Feature specification or explicit user instruction
3. Project engineering standards
4. Testing standards
5. Coding execution guidelines
6. Skills and refactor triggers
7. Deferred optimisation framework
8. Task pack
9. Existing code patterns

Existing code patterns should be followed for consistency, but never used to justify keeping an
anti-pattern when the standards require improvement or deferred capture.

## 3. Mandatory Working Method

### 3.1 Review First

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
- relevant reference docs beyond the required core set

Step 1 is review/scope only unless the user explicitly says to proceed in one pass or has already
approved implementation.

### 3.2 Stop-And-Confirm Workflow

Default workflow:

1. Review scope.
2. Stop for confirmation.
3. Validate architecture and proposed design.
4. Stop for confirmation.
5. Present implementation plan.
6. Stop for confirmation.
7. Code only after approval.

If the user explicitly asks for a full draft/update of standards documents, a complete task pack,
or a one-pass implementation, proceed within that approved scope.

### 3.3 No Line-Only Edits Mindset

Do not treat a task as only the exact requested diff. When touching an area, check whether the
touched module still contains:

- direct SQL in command/view layers
- business logic in command/view layers
- dead code from previous feature iterations
- duplicate helpers
- weak validation
- missing logging
- missing tests
- fragile restart/persistence behaviour

If issues are found, fix them when they are in scope, low risk, and in the touched area. Otherwise
capture them with the Deferred Optimisation Framework format.

## 4. Architecture-Aware Delivery

The repo contains both a legacy flat-root layout and target modular architecture. There is no
`bot/` wrapper directory.

Target placement:

| Feature element | Target location |
|----------------|-----------------|
| Slash command | `commands/<domain>_cmds.py` |
| Service / business logic | subsystem package or `<domain>_service.py` |
| Repository / DAL | subsystem package or repository module |
| View / modal | `ui/views/<name>.py` |
| Shared low-level utility | `core/` or existing helper modules |
| Operational tooling | `scripts/` |
| Tests | `tests/` |
| Embedded Python SQL | `sql/` when justified |
| SQL schema object | SQL repo `sql_schema/<schema>.<Object>.<Type>.sql` |

Do not add new long-term domain logic to major legacy root modules. If a legacy file must be
touched, prefer extracting new logic to the target architecture and importing it back.

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

- state which helpers were reused
- state when a new helper was necessary
- state if a duplicate or near-duplicate helper was discovered and what happened to it

For helper-heavy work, consult `docs/reference/REVIEW_HELPERS.md`.

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

## 7. SQL Change Rules

SQL changes belong in the SQL Server repo.

Required SQL rules:

- Use `sql_schema/<schema>.<ObjectName>.<Type>.sql`.
- Include `SET ANSI_NULLS ON`.
- Include `SET QUOTED_IDENTIFIER ON`.
- Keep Python behaviour aligned to the SQL contract.
- Document migration order.
- Call out breaking-change risk.

If Python code being changed contains SQL in a command or view layer, treat that as a refactor
checkpoint. Decide and state one of:

- extracted now
- safe to defer for this task
- not in scope because of explicit user constraint

Silently leaving it in place is not acceptable.

## 8. Command Layer Rules

All new commands live in `commands/<domain>_cmds.py`.

Commands must:

- use `@versioned()`, `@safe_command`, and `@track_usage()` where the local command pattern requires them
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

## 9. Service Layer Rules

Services own domain orchestration:

- validation
- rule enforcement
- repository calls
- cache coordination
- audit logging
- cross-module orchestration

Services must not use Discord objects.

## 10. View Layer Rules

Views live in `ui/views/`.

Views may contain:

- buttons
- selects
- modals
- interaction wiring
- response sequencing

Views must use `core/interaction_safety.py` patterns, call services, and avoid business logic.

## 11. Restart, Persistence, And State Safety

Critical state must survive restart. Do not design stateful features that rely solely on:

- process memory
- view instance state
- temporary files
- non-authoritative JSON files

When applicable, consider:

- SQL-persisted state
- message/view rehydration
- deduplication of reminders/posts
- cancellation handling for background tasks
- restart-safe recovery paths

If a task changes a stateful area, the output must state how restart safety was verified or why
no change was required.

## 12. Logging And Observability

Use module-specific loggers:

```python
import logging

logger = logging.getLogger(__name__)
```

Do not use:

- `logging.basicConfig()`
- bare `print()`
- `except: pass`

Log key decisions and outcomes with identifiers and UTC timestamps where relevant. When debugging
or auditing an area, assess whether the current log points explain failures end to end.

## 13. Time Standard

- Persist UTC only.
- Use `from datetime import UTC, datetime`.
- Use `datetime.now(UTC)`.
- Use `fmt_short()` only at display time.
- Never persist local time.

## 14. Testing Execution Rules

Every meaningful change requires a test decision.

Minimum expectation:

- happy path test
- negative path test
- regression test for the changed behaviour or bug
- permission boundary test when applicable
- restart/persistence test when applicable

Additional rules:

- Update existing tests if the implementation changes expected behaviour.
- Review nearby tests when refactoring an area.
- If no tests are added, explicitly justify why.
- Do not rely solely on smoke imports for behavioural coverage.

See `K98 Bot - Testing Standards.md` for the fuller matrix.

## 15. Output Format For Delivered Work

When delivering code or a task pack, provide:

1. summary
2. file manifest with exact paths
3. SQL changes separately
4. helpers reused
5. refactor findings in touched areas
6. test plan and commands run
7. deployment / migration order
8. follow-on debt or deferred improvements

For documentation-only changes, state that no runtime code, SQL, helper reuse, or restart behaviour
changed.

## 16. Definition Of Done

A task is done only when:

- [ ] engineering standards were followed
- [ ] architecture placement is correct
- [ ] commands are thin where commands were touched
- [ ] services own business logic where service logic was touched
- [ ] no new direct SQL was added to commands/views
- [ ] touched areas were checked for existing embedded SQL and duplication
- [ ] helper reuse was verified where helpers were touched
- [ ] logging is adequate
- [ ] UTC handling is correct
- [ ] restart safety is preserved
- [ ] tests were added, updated, or explicitly ruled out
- [ ] quality gates were considered
- [ ] deferred debt is captured using the Deferred Optimisation Framework format

## 17. Quality Gates

Run or recommend these before completion:

```powershell
python scripts/validate_architecture_boundaries.py
python scripts/validate_deferred_items.py
python scripts/select_tests.py
python -m pytest -q tests
python scripts/smoke_imports.py
python scripts/validate_command_registration.py
```

For SQL-heavy, configuration-heavy, or domain-specific tasks, also include targeted validation
commands relevant to the subsystem.

## 18. If Uncertain

When unsure:

1. Inspect the closest subsystem pattern.
2. Choose the least disruptive compliant design.
3. Surface uncertainty explicitly.
4. Avoid inventing new architecture.
5. Prefer extraction over expansion of legacy files.

If the user has not asked for code yet, stop at plan approval rather than guessing.
