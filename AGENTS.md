# Codex Repository Instructions

## Required Reading

Before beginning repo work, read the current versions of these core documents:

- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/k98 Bot - Deferred Optimisation Framework.md`

Read additional reference docs only when they apply to the task. The index in
`docs/reference/README.md` defines which references are always required and which are
background, operational, promotion, domain, or template-support material.

## Working Rules

- Step 1 must always be review/scope only unless explicitly told otherwise.
- Keep changes PR-sized and focused.
- Avoid embedded SQL in command modules and views.
- Prefer service and DAL layers for business logic and persistence.
- Preserve existing behaviour unless explicitly changing it.
- Run targeted tests and lint where practical.
- Capture deferred optimisation items clearly using the required structure.

### Review & Validation Rules

- When tests fail:
  - Fix only if related to the task.
  - Otherwise document the failure and do not expand scope.
- Before PR, run or justify skipping:
  - `python scripts/validate_architecture_boundaries.py`
  - `python scripts/validate_deferred_items.py`
  - `python scripts/select_tests.py`

## Repository / Promotion Model

- `origin` is the scrubbed Codex mirror: `K98-bot-mirror`.
- `production` is the private production repository: `K98-bot`.
- Codex should create branches and PRs against `K98-bot-mirror`.
- Production promotion happens only after local validation.
- Production changes are promoted by pushing the same branch to the `production` remote and opening a PR into `K98-bot/main`.
- The bot machine must deploy only from `K98-bot/main`, never from `K98-bot-mirror`.

Use `docs/reference/Promotion Guide.md` only for promotion/deployment tasks.

## SQL Validation Source

The authoritative SQL schema and stored procedures are stored in:

`C:\K98-bot-SQL-Server`

Codex must validate all SQL-facing implementation details against that SQL repo before
implementation:

- table names
- column names
- stored procedures
- indexes
- views
- `ProcConfig` usage
- staging/output table structure

Do not infer schema purely from Python usage when SQL definitions exist in the SQL repo.

If schema ambiguity exists:

1. Search the SQL repo first.
2. Report missing objects explicitly.
3. Do not guess column names.

Useful SQL repo searches:

```powershell
rg "CREATE TABLE.*STAGING_STATS" C:\K98-bot-SQL-Server
rg "ProcConfig" C:\K98-bot-SQL-Server
rg "EXCEL_FOR_KVK" C:\K98-bot-SQL-Server
rg "GovernorID" C:\K98-bot-SQL-Server
```
