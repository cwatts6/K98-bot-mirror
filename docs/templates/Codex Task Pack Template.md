# Codex Task Pack Template

> Canonical template for K98 bot Codex work.
> Replace all angle-bracket placeholders before use.

Use this file for new feature work, bug fixes, refactor batches, and deferred optimisation packs.
Do not use archived templates as active guidance.

## 1. Task Header

- Task name: `<short descriptive name>`
- Date: `<YYYY-MM-DD>`
- Owner/context: `<requester, issue, PR, incident, or source>`
- Task type: `<feature | bug fix | refactor | deferred optimisation batch | docs | tooling>`
- One-pass approved: `<yes | no>`

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by
`docs/reference/README.md`. Do not add every reference document to a task pack by default.

For SQL-facing work, validate schema, procedure, view, index, and `ProcConfig` details against:

`C:\K98-bot-SQL-Server`

## 3. Objective

<Describe the outcome in 2-4 lines. State the user-visible or engineering result first, then the
implementation direction only where it helps clarify scope.>

## 4. Background

<Summarise relevant context, links, prior PRs, incidents, current behaviour, or deferred items.>

## 5. Scope

### In Scope

- `<specific file, module, behaviour, workflow, or documentation change>`
- `<specific validation or migration work to include>`

### Out Of Scope

- `<explicitly excluded work>`
- `<related optimisation that should be deferred unless separately approved>`

## 6. Source Deferred Items

Use this section only when the task comes from deferred optimisation capture. Delete it when it
does not apply.

```md
### Deferred Optimisation
- Area:
- Type: performance | architecture | cleanup | refactor | consistency
- Description:
- Suggested Fix:
- Impact: low | medium | high
- Risk: low | medium | high
- Dependencies:
```

## 7. Mandatory Workflow

Default workflow:

1. Audit / scope review, then stop for approval.
2. Architecture validation, then stop for approval.
3. Implementation plan, then stop for approval.
4. Implementation after approval.
5. Validation and final review.

Proceed in one pass only when the user explicitly approves it.

## 8. Audit Requirements

Review the touched area for:

- direct SQL in commands or views
- business logic in interaction layers
- duplicate helpers or near-duplicates
- dead code from prior iterations
- weak validation or logging
- cache and persistence safety
- restart safety
- test coverage gaps

Map the likely:

- commands
- services
- repositories / DAL modules
- SQL objects or contracts
- views or modals
- caches or persisted state
- restart implications
- conditional reference docs

## 9. Architecture Targets

| Concern | Target |
|---|---|
| Slash commands | `commands/<domain>_cmds.py` |
| Views / modals | `ui/views/` |
| Services / business logic | subsystem package or `<domain>_service.py` |
| Repository / DAL | subsystem package or repository module |
| Shared helpers | `core/` or existing helper modules |
| Operational tooling | `scripts/` |
| Documentation | `docs/` |
| SQL schema | SQL repo `sql_schema/<schema>.<Object>.<Type>.sql` |
| Tests | `tests/` |

## 10. Likely Files

### Review

- `<path>`

### Modify

- `<path>`

### Create

- `<path or none>`

## 11. Implementation Requirements

- Keep commands and views thin.
- Move business logic into services.
- Move data access into repository/DAL code.
- Avoid new direct SQL in commands or views.
- Reuse existing helpers where practical.
- Preserve restart safety.
- Add or improve meaningful logging where operational paths are touched.
- Add or update tests unless the change is documentation-only or tooling-only.
- Capture new out-of-scope findings as deferred optimisations.

## 12. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| `<issue>` | `fix now | defer | not applicable` | `<short reason>` |

Deferred items must use the structured format from
`docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 13. Testing Requirements

Consider each category and either cover it or explain why it does not apply:

- happy path
- negative path
- regression
- permission boundary
- restart/persistence
- cache safety
- format/output shape

Suggested baseline commands:

```powershell
.\.venv\Scripts\python.exe scripts\validate_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\validate_deferred_items.py
.\.venv\Scripts\python.exe scripts\select_tests.py
```

Add focused pytest commands for the subsystem under change. For broader or runtime changes, also
consider:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

## 14. Acceptance Criteria

- [ ] Scope is complete and no out-of-scope work was mixed in.
- [ ] Correct architecture/layer ownership is preserved.
- [ ] No new direct SQL exists in commands or views.
- [ ] Helper reuse was checked and documented.
- [ ] Logging is adequate for changed operational paths.
- [ ] Restart safety is preserved or explicitly not applicable.
- [ ] Tests were added/updated or a clear testing exception is documented.
- [ ] Quality gates were run or documented.
- [ ] Deferred optimisations are captured structurally.

## 15. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. Helpers Reused
7. Refactor Findings
8. Test Plan
9. Deployment Steps
10. Deferred Optimisations

For documentation-only work, state that no runtime code, SQL, helper reuse, or restart behaviour
changed.

## 16. PR Summary Template

```md
## Summary

- <summary item>

## Changes

- <change item>

## Tests

- <test command or verification>

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- <risk and rollback note>
```
