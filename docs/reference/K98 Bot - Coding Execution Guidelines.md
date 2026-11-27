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

Operator instructions and commissioned profiles define permitted actions. The pinned SQL repository governs intended schema facts. Accepted observations identify the installed state at the time of collection. If intended and observed state disagree, retain both and resolve the discrepancy before dependent work.

Within the authorised scope, apply the feature specification, project engineering standards, testing standards, execution guidelines, refactor guidance and deferred framework to the task pack. Record the resolution of a material conflict.

Existing code patterns should be followed for consistency, but never used to justify keeping an
anti-pattern when the standards require improvement or deferred capture.

### Resource requirements must retain their scope

Record the environment, measurement, units, timing and original approval for each
resource gate. A qualification limit is not automatically a production contract.
For P02, **8 GiB available host memory applies before starting the isolated
development VM**. It is not an additional post-start reservation, a guest free-RAM
floor or a production SQL-host requirement. Production does not run this test VM.
The production disk reserve (8 GiB), log-use ceiling (below 70%) and version-store
ceiling (below 512 MiB) are separate checks and remain in force.

Before adding or interpreting a guard, trace abbreviated handover wording back to
the original requirement. Code and a passing test can both encode the same wrong
assumption. Do not ask the operator to free RAM, change SQL settings or lower a
threshold to satisfy an invented condition. Preserve observed values and withdrawn
interpretations, then correct the source and its exact release bindings through
review. The SQL repository's `docs/deployment-resource-scope.md` and
`tests/test_d4_release_runner.ps1` own the production-path regression; the Bot's
`tests/test_p02_d4_release.py` rejects the obsolete runner revision while retaining
the migration/profile identities. Any new production memory floor needs evidence
and explicit approval defining its scope.

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

### 3.2 Task approval and unattended DEV work

For unapproved work, review scope, architecture, risks and the implementation plan. Obtain the owner's decision before implementation. For an approved task, identify the exact profiles, actors, targets and effects that cover it. Approval for an explicit one-pass task includes its ordinary in-scope validation and corrections.

Within a commissioned DEV profile, build, deploy to DEV, test, inspect failures, correct, restart and retest unattended. Preserve failed attempts and reconcile unknown outcomes before retry. Pause when the work needs a different scope or security boundary, an unsafe destructive operation, an unresolved decision or production action. The commissioning owner controls first startup and new capabilities.

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
| SQL schema change | SQL repo `migrations/`, with matching expected-state references in `sql_schema/` |

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

- Deliver intentional changes as reviewed SQL-repository migrations. Update the corresponding `sql_schema/<schema>.<ObjectName>.<Type>.sql` expected-state reference where applicable.
- Record the exact migration set, Bot/SQL compatibility, native validation against the authorised target and rollback, restore or roll-forward plan.
- Include `SET ANSI_NULLS ON`.
- Include `SET QUOTED_IDENTIFIER ON`.
- Keep Python behaviour aligned to the SQL contract.
- Document migration order.
- Call out breaking-change risk.

### Comparing submitted SQL with stored procedure definitions

Do not compare a submitted `CREATE OR ALTER PROCEDURE` script with catalog text
using raw equality or an assumed single-space `CREATE PROCEDURE` header. SQL Server
catalog evidence in this project has contained `CREATE   PROCEDURE` (three spaces).
This has caused repeated false refusals. Use the tested header-only comparison in
`scripts/sql_module_definition.py` for new Python validation tooling, or prove an
equivalent implementation against `tests/test_sql_module_definition.py`.

Retain the complete raw expected and actual text and their hashes before deciding.
Normalize only the leading `CREATE`, `CREATE OR ALTER` or `ALTER` procedure keywords
and the whitespace separating those keywords. Compare the remaining object name,
signature, execution clause, comments, literals and body exactly. Do not collapse
whitespace throughout SQL, strip comments or accept an observed body merely because
it came from the server. Any transport line-ending normalization needs an explicit
policy and retained raw evidence; the shared helper does not change body newlines.
Validate schema/object identity, module type, `uses_ansi_nulls`,
`uses_quoted_identifier` and execution context separately. Missing, encrypted,
truncated or unsupported definitions must stop with useful evidence.

Regression coverage must include all three header forms, multiple spaces and tabs,
the observed three-space form, and rejection of changed names, signatures, bodies,
comments and string-literal whitespace. Use delimited identifiers for diagnostic
SQL aliases, including `[backup]`; prepare and check final accounting queries as
carefully as the test statements. A final reporting failure is not permission to
replay already completed work.

If Python code being changed contains SQL in a command or view layer, treat that as a refactor
checkpoint. Decide and state one of:

- extracted now
- safe to defer for this task
- not in scope because of explicit user constraint

Silently leaving it in place is not acceptable.

## 8. Command Layer Rules

All new commands live in `commands/<domain>_cmds.py`.

New admin, leadership, operator, diagnostic, and domain-maintenance command work should be
group-first. A new top-level slash command or command group requires explicit task approval,
operator rationale for why an existing group is unsuitable, an
`APPROVED_TOP_LEVEL_COMMANDS` update in `scripts/validate_command_registration.py`, and a matching
update to `docs/reference/canonical_command_reference.md`.

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

## 15. AI Review Gate

Before PR handoff, run or justify skipping this AI-assisted review gate:

- Codex Security review when security-sensitive surfaces are touched.

Security-sensitive surfaces include:

- permission checks or role boundaries
- Discord commands, views, modals, callbacks, or user-facing interaction flows
- SQL/data access, imports, exports, reports, or SQL-backed caches
- file handling, path handling, uploads, downloads, archives, or generated artifacts
- secrets, tokens, environment variables, runtime config, or deployment scripts
- network calls, webhooks, external integrations, or user-controlled input parsing
- restart-sensitive persistence, rehydration, scheduler state, or duplicate-action prevention

For documentation-only, comment-only, or purely mechanical changes, this gate may be skipped when
the skip is stated in the delivery output. If review reports actionable issues, fix only issues
within the approved scope unless the user approves expanding the task.

## 16. Output Format For Delivered Work

When delivering code or a task pack, provide:

1. summary
2. file manifest with exact paths
3. SQL changes separately
4. helpers reused
5. refactor findings in touched areas
6. test plan and commands run
7. deployment / migration order
8. Codex Security review status, including skip reason when not run
9. follow-on debt or deferred improvements

For documentation-only changes, state that no runtime code, SQL, helper reuse, or restart behaviour
changed.

## 17. Definition Of Done

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
- [ ] Codex Security review was run or explicitly skipped based on risk triggers
- [ ] deferred debt is captured using the Deferred Optimisation Framework format

## 18. Quality Gates

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

Add the AI-assisted review gate before PR handoff:

- Codex Security review for changes touching the security-sensitive surfaces listed in section 15.

If the gate is skipped, record the reason in the delivery output.

## 19. If Uncertain

When unsure:

1. Inspect the closest subsystem pattern.
2. Choose the least disruptive compliant design.
3. Surface uncertainty explicitly.
4. Avoid inventing new architecture.
5. Prefer extraction over expansion of legacy files.

If the user has not asked for code yet, stop at plan approval rather than guessing.

## 20. Operational access preflight

Before proposing commands, state machine, shell, actual identity/elevation, exact paths, operation and evidence prerequisites. Inspect installed restrictions; do not infer custody from Git cleanliness or an administrator account name. Use reviewed executable paths and validate PowerShell 5.1 examples. Diagnose before retrying or broadening access.

The [Windows ownership and access contract](Windows%20ownership%20and%20access%20contract.md)
is required reading for this work and defines the operation matrix and validation details.
