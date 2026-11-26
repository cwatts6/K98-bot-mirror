# Codex Repository Instructions

## Required Reading

Before beginning repo work, read the current versions of these core documents:

- `README-DEV.md`
- `docs/reference/README.md`
- `docs/reference/K98 Bot - Project Engineering Standards.md`
- `docs/reference/K98 Bot - Coding Execution Guidelines.md`
- `docs/reference/K98 Bot - Testing Standards.md`
- `docs/reference/K98 Bot - Skills & Refactor Triggers.md`
- `docs/reference/K98 Bot - Deferred Optimisation Framework.md`

Read additional reference docs only when they apply to the task. The index in
`docs/reference/README.md` defines which references are always required and which are
background, operational, promotion, domain, or template-support material.

## Working Rules

- Start unapproved work with review and scope. For an approved task, verify the required DEV capabilities against the commissioning handoff. Carry out routine edit, DEV deploy, test, diagnosis, correction, restart and retest within that scope. Pause for a new boundary, an unsafe destructive action, unresolved ambiguity or a production decision.
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
- Run or justify skipping a Codex Security review when a change touches security-sensitive
  surfaces such as permissions, Discord interactions, SQL/data access, file handling,
  secrets/config, deployment, network calls, user-controlled input, or restart-sensitive
  persistence.

## Codex Security Review Routing

- Use `k98-security-review-routing` to make the security-review decision before invoking Codex Security.
- For a pull request, commit, branch range, or working-tree patch, use `$codex-security:security-diff-scan` when review is required, or record a precise documented skip.
<!-- codex-security-routing: allow-standard reason="defines the explicit-only standard codebase audit boundary" -->
<!-- codex-security-routing: allow-deep reason="defines the explicit-only deep codebase audit boundary" -->
- Do not use `$codex-security:security-scan` or `$codex-security:deep-security-scan` as a routine task-completion, PR, promotion, or deployment gate.
- A standard codebase scan requires an explicit operator request for a repository-wide or scoped-folder audit.
- A deep scan requires an explicit operator request for a deep, exhaustive, or multi-pass audit. It must not be used for a PR or Git diff.
- Before starting a routine scan, confirm `Scan type: Changes`, the intended base/head or uncommitted patch, and that Deep scan is off. Stop and correct setup if it shows `Codebase` or a whole-repository target.
- Treat root and nested `SECURITY.md` files as threat-model, invariant, reportability, exclusion, and severity context. They do not select or launch a scan.
- Triage captured findings with `$codex-security:triage-finding`; do not start discovery again merely to reproduce known findings.
- Remediate one accepted finding, or one tightly related root-cause family, with `$codex-security:fix-finding`, then review the resulting Git diff.
- Bot and SQL repositories have separate Git histories and require separate diff targets and normally separate security reviews.
- Run or justify skipping `python scripts/validate_codex_security_routing.py` before PR handoff.

## Repository / Promotion Model

- `origin` is the scrubbed Codex mirror: `K98-bot-mirror`.
- `production` is the private production repository: `K98-bot`.
- Codex should create branches and PRs against `K98-bot-mirror`.
- With authorised repository access, automation can apply the validated mirror file delta on a branch based on private `production/main`, open the private PR and prepare its final head for merge. Preserve private-only files and separate review evidence for both histories.
- Private merge requires its own decision. It triggers a mirror scrub that closes open mirror PRs, including unmerged work. Preserve and reconcile all affected work using the [private merge and scrub procedure](docs/reference/Promotion%20Guide.md#private-merge-and-mirror-scrub).
- Production promotion and execution require a separate human decision on the private-main release, SQL pairing, window and recovery plan.
- The bot machine must deploy only from `K98-bot/main`, never from `K98-bot-mirror`.

Use the [Promotion Guide](docs/reference/Promotion%20Guide.md) for private PR preparation, merge, promotion and deployment tasks.

## SQL Validation Source

Validate intended SQL schema and stored procedures against an authorised checkout of `cwatts6/K98-bot-SQL-Server` at the SQL commit pinned in the task. `C:\K98-bot-SQL-Server` is one local example.

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

Run these example searches from the root of that verified SQL checkout:

```powershell
rg "CREATE TABLE.*STAGING_STATS" .
rg "ProcConfig" .
rg "EXCEL_FOR_KVK" .
rg "GovernorID" .
```
