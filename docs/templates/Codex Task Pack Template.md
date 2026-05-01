# Codex Task Pack - <Task Name>

> Task pack version: 1.0
> Date: <YYYY-MM-DD>
> Owner/context: <requester, issue, or source>

## Required Reading

Read and follow the current versions of:

- `README-DEV.md`
- `docs/K98 Bot — Project Engineering Standards.md`
- `docs/K98 Bot — Coding Execution Guidelines.md`
- `docs/K98 Bot — Standard Development Initiation Statement.md`
- `docs/K98 Bot — Testing Standards.md`
- `docs/K98 Bot — Skills & Refactor Triggers.md`
- `docs/k98 Bot — Deferred Optimisation Framework.md`
- `docs/K98 Bot Deferred Optimisation Scoring Model.md`
- `docs/K98 Bot Codex Task Pack Generator.md`
- `docs/K98 Code Prompt.md`

## Objective

<Describe the outcome in 2-4 lines. State the user-visible or engineering result, not the implementation first.>

## Background

<Summarise relevant context, links, prior PRs, deferred items, incidents, or current behaviour.>

## Scope

### In Scope

- <Specific file, module, behaviour, or workflow to change>
- <Specific validation or docs work to include>

### Out of Scope

- <Explicitly excluded work>
- <Related optimisation that should be deferred unless separately approved>

## Source Deferred Items

Use this section when the task pack comes from deferred optimisation capture. Delete if not applicable.

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

## Mandatory Workflow

Follow `docs/K98 Code Prompt.md`.

Stop for approval after:

1. Audit / scope review
2. Architecture validation
3. Implementation plan

Do not code until approval unless the user explicitly requests a one-pass implementation.

## Audit Requirements

Review the touched area for:

- direct SQL in commands/views
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
- views/modals
- caches or persisted state
- restart implications

## Target Architecture

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

## Likely Files To Review

- `<path>`

## Likely Files To Modify

- `<path>`

## Implementation Requirements

- Keep commands and views thin.
- Move business logic into services.
- Move data access into repository/DAL code.
- Avoid new direct SQL in commands or views.
- Reuse existing helpers where practical.
- Preserve restart safety.
- Add or improve meaningful logging where the task touches operational paths.
- Add or update tests unless the change is documentation-only or tooling-only.
- Capture new out-of-scope findings as deferred optimisations.

## Testing Requirements

Consider each category and either cover it or explain why it does not apply:

- happy path
- negative path
- regression
- permission boundary
- restart/persistence
- cache safety
- format/output shape

Suggested commands:

```powershell
.\.venv\Scripts\python.exe -m pre_commit run -a
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\smoke_imports.py
.\.venv\Scripts\python.exe scripts\validate_command_registration.py
```

Add focused pytest commands for the subsystem under change.

## Acceptance Criteria

- [ ] Scope is complete and no out-of-scope work was mixed in.
- [ ] Correct architecture/layer ownership is preserved.
- [ ] No new direct SQL exists in commands/views.
- [ ] Helper reuse was checked and documented.
- [ ] Logging is adequate for changed operational paths.
- [ ] Restart safety is preserved or explicitly not applicable.
- [ ] Tests were added/updated or a clear testing exception is documented.
- [ ] Quality gates were run or documented.
- [ ] Deferred optimisations are captured structurally.

## Required Output

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

## PR Summary Template

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
