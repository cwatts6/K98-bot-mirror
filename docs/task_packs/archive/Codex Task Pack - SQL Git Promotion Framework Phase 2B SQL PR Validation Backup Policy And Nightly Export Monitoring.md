# Codex Task Pack - SQL Git Promotion Framework Phase 2B SQL PR Validation Backup Policy And Nightly Export Monitoring

## 1. Task Header

- Task name: SQL Git Promotion Framework Phase 2B SQL PR Validation, Backup Policy, and Nightly Export Monitoring
- Date: 2026-06-03
- Owner/context: K98 SQL Repository Modernisation Initiative, following completed Phase 1 and Phase 2A
- Task type: tooling / documentation / operational resilience / DevOps
- One-pass approved: no
- Primary repository: `C:\K98-bot-SQL-Server`
- Production SQL Server: `MINI_AMD`
- Production database: `ROK_TRACKER`

## 1A. Delivery Status Update - 2026-06-03

**Status:** Complete, merged, deployed, and operator-validated.

Phase 2B has been delivered in the SQL repository through PRs #11, #12, and #13. The completed
delivery includes:

- SQL PR validation workflow in `.github/workflows/sql-validation.yml`.
- CI execution of `deploy/Validate-SqlRepo.ps1`.
- PowerShell parser validation for deployment scripts.
- committed-file credential-pattern scanning.
- documentation path sanity checks.
- scripted proof that the nightly export wrapper does not normally push directly to `main`.
- SQLFluff 4.2.1 advisory validation for migration and rollback scripts using the `tsql` dialect.
- explicit backup policy configuration via `deploy/sql_deploy_config.example.json` and optional
  ignored local `deploy/sql_deploy_config.json`.
- configurable backup readiness thresholds with deliberate warning-only differential backup policy.
- `deploy/Test-NightlyExportHealth.ps1` for bounded-tail export log and scheduled-task health
  checks.
- failure-only Discord alerts from `deploy/Invoke-NightlyProdSchemaExport.ps1` using
  `SQL_SCHEMA_DISCORD_WEBHOOK_URL`.
- ADR 003 documenting SQL CI, backup policy, and export monitoring decisions.
- SQL Promotion Guide and SQL Release Checklist updates for CI, backup policy, nightly export
  health checks, and failure-only Discord alert configuration.

Operational validation completed on the SQL operations machine:

- SQL repo validation completed successfully.
- nightly export health check completed successfully.
- manual schema export completed without error.
- Discord webhook payload test completed successfully.
- failure-only alert environment variable setup was confirmed for operational use.

No runtime SQL schema objects were changed by Phase 2B.

### Optional Validators Deferred From Phase 2B

SQLFluff is now included. The following remain optional later-phase validators rather than missing
Phase 2B work:

- SqlPackage / DACPAC structural validation, after tool installation, artifact handling, and target
  environment policy are agreed.
- tSQLt tests, after a DEV or UAT SQL Server exists; do not install tSQLt objects in Production
  for PR validation.
- TSQLLint, only as a fallback if SQLFluff proves unsuitable.

## 2. Required Reading

Before implementation, read the current repository instructions and indexed core standards:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow the required reading order and conditional references defined by
`docs/reference/README.md`. Do not add every reference document to the task by default.

SQL source of truth:

```text
C:\K98-bot-SQL-Server
```

Additional SQL repo references:

- `docs/SQL_PROMOTION_GUIDE.md`
- `docs/SQL_RELEASE_CHECKLIST.md`
- `docs/SQL_DATA_MIGRATION_GUARDRAILS.md`
- `docs/adr/001-git-first-sql-deployment.md`
- `docs/adr/002-sql-emergency-hotfix-and-rollback-standards.md`
- `migrations/README.md`
- `migrations/rollback/README.md`
- `deploy/Validate-SqlRepo.ps1`
- `deploy/Test-SqlBackupReadiness.ps1`
- `deploy/Invoke-NightlyProdSchemaExport.ps1`
- `deploy/Install-NightlySchemaExportTask.ps1`
- `deploy/Invoke-DriftCheck.ps1`
- `deploy/SqlDeploy.Common.ps1`
- `.github/` if it exists

## 3. Objective

Deliver the next maturity layer for the SQL Git-first deployment programme after the emergency
hotfix path has been proven.

The outcome should make unsafe SQL PRs harder to merge, make backup-threshold warnings deliberate
rather than noisy, and make failed nightly schema export easier to notice and act on.

## 4. Background

Phase 1 delivered the baseline Git-first SQL deployment framework:

- reviewed SQL PRs
- migration-based deployment
- migration and deployment history tables
- backup readiness checks
- drift export/check tooling
- safe nightly export branch workflow
- structured JSONL logs

Phase 2A delivered and rehearsed emergency readiness:

- hotfix report template and evidence convention
- rollback-script template and rollback classification
- data migration guardrails
- validation enhancements for rollback/data-safety metadata
- controlled Production rehearsal using `dbo.SqlHotfixRehearsal`
- post-rehearsal guide/checklist/template hardening

Remaining high-value risks:

1. SQL PR validation is still mostly local/manual.
2. The differential-backup age threshold produced expected warnings during rehearsal, but the
   policy is not yet explicit/configurable.
3. Nightly export has structured logs, but no monitor or notification path yet.

## 5. Scope

### In Scope

- Add GitHub Actions validation for SQL repo PRs.
- Add CI checks for:
  - migration naming/header validation
  - rollback/data-safety metadata validation
  - dangerous SQL pattern warnings through existing validator
  - PowerShell parser validation for deployment scripts
  - secrets/credential-pattern scanning where practical
  - documentation link/path sanity where practical
- Decide and document whether SQL PRs should require drift/snapshot consistency evidence.
- Add backup threshold policy or configuration, with special attention to the current
  differential-backup warning.
- Add scheduled-task monitoring or notification for failed `K98 SQL Nightly Schema Export`.
- Add CI or scripted evidence that nightly exports cannot push directly to `main`.
- Update SQL promotion docs/checklists for the new validation and monitoring expectations.
- Keep structured log outputs free of secrets.

### Out of Scope

- Full CI/CD deployment.
- Automated production deployment approvals.
- Automatic SQL deployment from GitHub Actions.
- Flyway or Liquibase adoption.
- DEV/UAT environment design.
- Automatic rollback generation.
- Automatic production hotfix reconciliation.
- Query Store baseline comparison.
- Broad drift report redesign beyond small path/link/readability improvements needed for CI.
- Bot command or runtime feature work.

## 6. Source Deferred Items

Not a deferred optimisation batch. This task comes from the SQL programme backlog after Phase 1 and
Phase 2A completion.

## 7. Codex Skills To Use

### Skill Decisions

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | use | Required before implementation; scope CI/tooling, docs, SQL/persistence implications, and approval checkpoints. |
| `k98-discord-command-feature` | not applicable | No Discord command, view, modal, or command registration changes expected. |
| `k98-sql-validation` | use | SQL repo validation, backup policy, drift/export, deployment tooling, and schema evidence are SQL-facing. |
| `k98-test-selection` | use | Select SQL repo validation, PowerShell parsing, CI dry runs, and bot-repo skip justifications. |
| `k98-deferred-optimisation-capture` | use if needed | Capture out-of-scope monitoring, drift, or environment maturity items found during audit. |
| `k98-pr-review` | use | Required before merge/handoff to confirm validation, docs, operational safety, and deferred items. |
| `k98-promotion-check` | use if deployment/production scheduling changes are touched | Required before changing scheduled task behavior or production operational monitoring. |
| `codex-security:security-scan` | use | CI, secrets scanning, deployment scripts, logs, scheduled tasks, and SQL/data access are security-sensitive. |

## 8. Mandatory Workflow

Default workflow:

1. Audit / scope review, then stop for approval.
2. Architecture and tooling design, then stop for approval.
3. Implementation plan, then stop for approval.
4. Implementation after approval.
5. Validation and final review.
6. Codex Security review because this touches deployment, logs, CI, secrets scanning, and SQL access.

Proceed in one pass only if the owner explicitly approves it.

## 9. Audit Requirements

Audit the SQL repo for:

- existing `.github/workflows/` configuration
- existing PowerShell parsing or validation commands
- existing secret-scanning patterns
- current `Validate-SqlRepo.ps1` warnings/errors and exit-code behavior
- current `Test-SqlBackupReadiness.ps1` threshold parameters and warning/error behavior
- current `Invoke-NightlyProdSchemaExport.ps1` log fields and failure behavior
- current scheduled task install script behavior
- whether logs contain enough event fields for monitoring
- whether export scripts can still push directly to `main` under any normal path
- whether drift/snapshot consistency can be checked cheaply in PR validation
- documentation paths and commands that CI should verify

Map likely affected files:

- `.github/workflows/*.yml`
- `deploy/Validate-SqlRepo.ps1`
- `deploy/Test-SqlBackupReadiness.ps1`
- `deploy/Invoke-NightlyProdSchemaExport.ps1`
- `deploy/Install-NightlySchemaExportTask.ps1`
- `deploy/Export-ProdSchemaSnapshot.ps1`
- `deploy/SqlDeploy.Common.ps1`
- `deploy/sql_deploy_config.example.json` if config is introduced
- `docs/SQL_PROMOTION_GUIDE.md`
- `docs/SQL_RELEASE_CHECKLIST.md`
- `docs/adr/*.md` if a new ADR is needed
- `README.md` or repo-level docs if CI badge/instructions are added

## 10. Architecture Targets

| Concern | Target |
|---|---|
| GitHub Actions CI | SQL repo `.github/workflows/` |
| SQL validation logic | Prefer extending existing `deploy/Validate-SqlRepo.ps1` over duplicating logic in YAML |
| PowerShell parser validation | SQL repo CI script or workflow step |
| Backup policy | SQL repo docs plus lightweight config if practical |
| Nightly export monitoring | SQL repo `deploy/` scripts and logs; optional GitHub issue/notification task if approved |
| Documentation | SQL repo `docs/` |
| SQL schema | SQL repo `sql_schema/schema.Object.Type.sql` naming convention |

## 11. Likely Files

### Review

- `C:\K98-bot-SQL-Server\.github\`
- `C:\K98-bot-SQL-Server\deploy\`
- `C:\K98-bot-SQL-Server\docs\`
- `C:\K98-bot-SQL-Server\logs\`
- `C:\K98-bot-SQL-Server\reports\`
- `C:\K98-bot-SQL-Server\migrations\`

### Modify

- `C:\K98-bot-SQL-Server\deploy\Validate-SqlRepo.ps1`
- `C:\K98-bot-SQL-Server\deploy\Test-SqlBackupReadiness.ps1`
- `C:\K98-bot-SQL-Server\deploy\Invoke-NightlyProdSchemaExport.ps1`
- `C:\K98-bot-SQL-Server\docs\SQL_PROMOTION_GUIDE.md`
- `C:\K98-bot-SQL-Server\docs\SQL_RELEASE_CHECKLIST.md`

### Create

- `C:\K98-bot-SQL-Server\.github\workflows\sql-validation.yml`
- `C:\K98-bot-SQL-Server\deploy\sql_deploy_config.example.json` if config support is approved
- optional `C:\K98-bot-SQL-Server\deploy\Test-NightlyExportHealth.ps1`
- optional `C:\K98-bot-SQL-Server\docs\adr\003-sql-ci-backup-policy-and-export-monitoring.md`

## 12. Implementation Requirements

- Prefer one authoritative validator: CI should call repo scripts instead of reimplementing checks in YAML.
- Keep CI read-only with respect to Production SQL.
- Do not require live `MINI_AMD` connectivity in normal PR CI.
- Use warning/failure levels deliberately. CI should fail on structural repo issues, invalid
  metadata, parser errors, and secret patterns; live backup warnings should not block PR CI unless
  explicitly designed as policy.
- Keep secrets out of workflow files, logs, config examples, and reports.
- Preserve Windows Auth production assumptions.
- Keep nightly export monitoring separate from deployment automation.
- Document how an operator should respond to a failed nightly export.
- If adding config support, keep defaults compatible with current production behavior.

### Command Surface Governance

Not applicable. This task should not change bot slash commands, command groups, command decorators,
command registration helpers, or Discord interaction flows.

## 13. Refactor Decisions

Classify each issue found during audit:

| Issue | Decision | Reason |
|---|---|---|
| Direct SQL in bot commands/views | not applicable | Expected scope is SQL repo tooling/docs only. |
| Duplicate validation logic in CI | fix now if found | CI should call existing scripts rather than fork logic. |
| Backup threshold noise | fix now | Rehearsal showed differential-age warning needs explicit policy/config. |
| Nightly export failure visibility | fix now or scope tightly | Main operational gap selected for Phase 2B. |
| Full deployment automation | defer | Out of scope for this phase. |
| DEV/UAT environment design | defer | Phase 3 environment maturity item. |

Deferred items must use the structured format from
`docs/reference/K98 Bot - Deferred Optimisation Framework.md`.

## 14. Testing Requirements

Consider each category and either cover it or explain why it does not apply:

- happy path: CI workflow/script validation succeeds on current SQL repo
- negative path: parser/metadata/secrets checks fail on a controlled fixture or reviewed logic path
- regression: existing `deploy/Validate-SqlRepo.ps1` still succeeds on current repo
- permission boundary: no live Production SQL credentials required in PR CI
- restart/persistence: not applicable unless scheduled task/monitoring state is changed
- cache safety: not applicable unless generated artifacts or log state are changed
- format/output shape: workflow logs, JSONL logs, and monitoring output are reviewable and non-secret

Suggested validation commands from SQL repo root:

```powershell
.\deploy\Validate-SqlRepo.ps1
```

PowerShell parser validation for changed scripts:

```powershell
$scripts = @(
  "deploy\Validate-SqlRepo.ps1",
  "deploy\Test-SqlBackupReadiness.ps1",
  "deploy\Invoke-NightlyProdSchemaExport.ps1"
)
foreach ($script in $scripts) {
  if (Test-Path $script) {
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
      (Resolve-Path $script),
      [ref]$tokens,
      [ref]$errors
    ) | Out-Null
    if ($errors.Count -gt 0) {
      $errors | ForEach-Object { Write-Host $_.Message }
      exit 1
    }
  }
}
```

If GitHub Actions are added, validate via:

- local review of workflow syntax where practical
- GitHub PR checks after push
- `gh pr checks` only if GitHub CLI is available, otherwise GitHub UI/connector evidence

Bot repo runtime tests are not required unless bot files are changed.

Before PR handoff, include the AI-assisted review gate decision:

- Codex Security review required because CI, deployment scripts, logs, secrets scanning, and SQL
  operational tooling are security-sensitive.

## 15. Acceptance Criteria

- [ ] Scope is complete and no out-of-scope deployment automation was mixed in.
- [ ] SQL PR CI exists or a clear implementation blocker is documented.
- [ ] CI runs the existing SQL repo validator.
- [ ] CI includes PowerShell parser validation for deployment scripts.
- [ ] CI includes practical secret/credential-pattern scanning.
- [ ] Backup threshold policy is explicit and either documented or configurable.
- [ ] Differential-backup warning behavior is deliberate and documented.
- [ ] Nightly export monitoring or notification path exists, or a precise owner-approved minimum
  monitor is documented.
- [ ] CI or a script proves nightly export cannot normally push directly to `main`.
- [ ] SQL Promotion Guide and Release Checklist include the new PR validation, backup policy, and
  monitoring steps.
- [ ] No live Production SQL credentials are required for PR validation.
- [ ] No secrets are added to workflows, docs, templates, examples, logs, or reports.
- [ ] Quality gates were run or documented.
- [ ] Codex Security review was run or explicitly skipped with a justified reason.
- [ ] Deferred optimisations are captured structurally.

## 16. Required Delivery Output

Use this delivery shape:

1. Summary
2. File Manifest
3. New Files
4. Modified Files
5. SQL Changes
6. Helpers Reused
7. Refactor Findings
8. Test Plan
9. AI Review Gates
10. Deployment Steps
11. Deferred Optimisations

For documentation/tooling-only work, state whether runtime SQL objects changed. If no runtime SQL
objects changed, state that explicitly.

## 17. PR Summary Template

```md
## Summary

- Add SQL PR validation and monitoring guardrails for Phase 2B.

## Changes

- SQL PR validation workflow, backup policy/configuration, nightly export monitoring, and
  documentation updates.

## Tests

- `.\deploy\Validate-SqlRepo.ps1`
- PowerShell parser validation and GitHub PR check evidence, when available.

## AI Review Gates

- Codex Security: required before PR handoff because CI, deployment scripts, logs, secrets
  scanning, and SQL operational tooling are security-sensitive.

## Deferred Optimisations

- None, or structured deferred items.

## Risk / Rollback

- No runtime SQL object changes expected.
- Roll back by reverting workflow/script/doc changes.
```
