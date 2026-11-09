# Codex Task Pack – SQL Emergency Readiness, Hotfix Rehearsal & Rollback Standards

**Task Name:** SQL Emergency Readiness, Hotfix Rehearsal & Rollback Standards
**Programme:** SQL Git Promotion Framework – Phase 2A
**Date:** 2026-06-02
**Owner/Context:** K98 SQL Repository Modernisation Initiative
**Task Type:** Tooling / Documentation / Operational Resilience / DevOps
**Priority:** High
**Risk Level:** High
**One-Pass Approved:** No
**Primary Repository:** `C:\K98-bot-SQL-Server`
**Production SQL Server:** `MINI_AMD`
**Production Database:** `ROK_TRACKER`

---

## 0A. Completion Status Update - 2026-06-03

**Status:** Complete, merged, deployed, rehearsed, and post-rehearsal guide updates merged to
production SQL repo `main`.

Phase 2A delivered the emergency-readiness layer described by this task pack. The controlled
rehearsal was executed against Production using the deliberately isolated
`dbo.SqlHotfixRehearsal` table. The rehearsal left Git and Production reconciled and recorded the
reconciliation migration in `dbo.SchemaMigrationHistory`.

### Merged SQL Repo PRs / Commits

- PR #7 `Add SQL emergency readiness standards`
  - branch: `codex/sql-emergency-readiness-hotfix-rollback`
  - delivered hotfix reports, rollback standards, data guardrails, ADR 002, guide/checklist
    updates, and validation enhancements
- PR #8 `Record SQL hotfix rehearsal dry run`
  - branch: `codex/sql-hotfix-rehearsal-dry-run`
  - recorded the Codex-session authentication blocker and owner-run rehearsal steps
- PR #9 `Reconcile SQL hotfix rehearsal table`
  - branch: `codex/sql-hotfix-rehearsal-reconcile`
  - reconciled the production-created `dbo.SqlHotfixRehearsal` table through Git with migration,
    rollback script, and schema snapshot
- PR #10 `Align SQL hotfix guide with rehearsal`
  - branch: `codex/sql-hotfix-guide-rehearsal-alignment`
  - aligned the guide, checklist, and template with the exact pressure-tested flow

Final production SQL repo commit after Phase 2A rehearsal reconciliation:

```text
399ddfbbd221
```

### Delivered Files And Capabilities

Delivered in `C:\K98-bot-SQL-Server`:

- `reports/hotfix/README.md`
- `reports/hotfix/hotfix_template.md`
- `reports/hotfix/rehearsal_20260603_0736_sql_hotfix_rehearsal_table_dry_run.md`
- `docs/SQL_PROMOTION_GUIDE.md`
- `docs/SQL_RELEASE_CHECKLIST.md`
- `docs/SQL_DATA_MIGRATION_GUARDRAILS.md`
- `docs/adr/002-sql-emergency-hotfix-and-rollback-standards.md`
- `migrations/README.md`
- `migrations/rollback/README.md`
- `migrations/rollback/_rollback_template.sql`
- `deploy_manifest.example.json`
- `deploy/New-SqlMigration.ps1`
- `deploy/Validate-SqlRepo.ps1`
- `migrations/20260603_001_reconcile_sql_hotfix_rehearsal_table.sql`
- `migrations/rollback/20260603_001_reconcile_sql_hotfix_rehearsal_table_rollback.sql`
- `sql_schema/dbo.SqlHotfixRehearsal.Table.sql`

Validation and operational proof:

- Backup readiness succeeded on `MINI_AMD`.
- Direct production-style SQL created `dbo.SqlHotfixRehearsal`.
- Post-change validation confirmed the table existed and was empty.
- Drift check detected the expected added table and no unexpected drift.
- Git reconciliation PR added the migration, rollback script, and schema snapshot.
- Pre-deployment `Deploy-SqlMigration.ps1 -ValidationOnly` reported one pending migration.
- Drift check after Git reconciliation reported no schema drift.
- Real deployment from `main` applied the idempotent reconciliation migration.
- Final `Deploy-SqlMigration.ps1 -ValidationOnly` reported zero pending migrations.
- `dbo.SchemaMigrationHistory` recorded:

```text
MigrationId: 20260603_001_reconcile_sql_hotfix_rehearsal_table
Status: Applied
AppliedAtUtc: 2026-06-03 08:07:34
BranchName: main
GitCommit: 399ddfbbd221
```

### Lessons Captured

The rehearsal exposed guide gaps that were fixed before this phase was marked complete:

- report creation must copy `hotfix_template.md`, not start from a blank note
- report filename stamps must use UTC
- drift evidence should use `Invoke-DriftCheck.ps1` for the hotfix path
- clean drift after schema reconciliation does not replace deploying the idempotent migration to
  record migration history
- final closure requires both clean drift and pending migration count zero
- hotfix reports need fields for backup warnings, object pre-checks, schema snapshot, rollback
  script, deployment result, migration history, and post-deployment pending checks

### Phase 2A Verdict

The SQL repo is now ready for normal and emergency SQL operation under the documented native
Git-first workflow. Future SQL emergency work should use `docs/SQL_PROMOTION_GUIDE.md` and
`reports/hotfix/hotfix_template.md` as the operational source of truth.

---

## 0. Executive Summary

Phase 1 of the SQL Git Promotion & Deployment Framework is complete and production validated. The SQL repository now has migration-based deployment, deployment history, drift export/check tooling, backup readiness checks, structured logs, and a SQL Promotion Guide.

This Phase 2A task hardened the framework for emergency and recovery scenarios before broader automation or CI/CD is added.

The next operational risk is not the standard happy-path deployment. The next risk is:

```text
Production SQL issue occurs
    -> urgent direct production hotfix is needed
    -> Git and Production drift
    -> rollback confidence is unclear
    -> future SQL deployments become risky
```

This task delivered:

1. A formal SQL hotfix incident template.
2. A clear reports folder convention for hotfix evidence.
3. A controlled, non-destructive emergency hotfix rehearsal.
4. Rollback-script templates and conventions for safely reversible migrations.
5. Data migration guardrails for high-risk SQL changes.
6. Backup threshold configuration or documented threshold policy.
7. Detailed step-by-step updates to the SQL Promotion Guide so the owner can follow the process without relying on memory.

This task must be practical, operational, and evidence-driven. Do not over-automate. Do not introduce GitHub Actions, deployment approvals, Flyway/Liquibase, or DEV/UAT design in this phase unless they are already required by the existing repo and explicitly approved.

---

## 1. Relationship To Phase 1

Phase 1 delivered the baseline Git-first SQL deployment framework.

This task builds directly on the delivered Phase 1 files and operating model, including:

```text
deploy/Deploy-SqlMigration.ps1
deploy/Validate-SqlRepo.ps1
deploy/Test-SqlBackupReadiness.ps1
deploy/Export-ProdSchemaSnapshot.ps1
deploy/Compare-ProdSchema.ps1
deploy/Invoke-DriftCheck.ps1
deploy/New-SqlMigration.ps1
deploy/SqlDeploy.Common.ps1
docs/SQL_PROMOTION_GUIDE.md
docs/SQL_RELEASE_CHECKLIST.md
docs/adr/001-git-first-sql-deployment.md
migrations/
logs/
reports/
exports/
```

The Phase 1 operating model is:

```text
Feature branch
     ->
SQL PR
     ->
main
     ->
backup readiness
     ->
controlled migration deployment
     ->
deployment and migration history
     ->
drift export/check
     ->
clean main baseline
```

Production exports are now expected to behave as drift evidence:

```text
Production SQL
     ->
timestamped export/prod-schema-* branch
     ->
reviewable drift evidence
     ->
PR reconciliation only when needed
```

This Phase 2A task must preserve that model. Direct production SQL changes remain discouraged, but this task must recognise that emergency production hotfixes may be required and must be safely documented, rehearsed, exported, and reconciled back to Git.

---

## 2. Required Reading

Before implementation, Codex must read and follow:

```text
AGENTS.md
README-DEV.md
docs/reference/README.md
```

Then follow all linked reference documents required by the repository.

Additional required SQL repo files:

```text
docs/SQL_PROMOTION_GUIDE.md
docs/SQL_RELEASE_CHECKLIST.md
docs/adr/001-git-first-sql-deployment.md
migrations/README.md
deploy/Deploy-SqlMigration.ps1
deploy/Validate-SqlRepo.ps1
deploy/Test-SqlBackupReadiness.ps1
deploy/Export-ProdSchemaSnapshot.ps1
deploy/Compare-ProdSchema.ps1
deploy/Invoke-DriftCheck.ps1
deploy/New-SqlMigration.ps1
deploy/SqlDeploy.Common.ps1
```

Also inspect any existing:

```text
migrations/rollback/
reports/
reports/hotfix/
deploy_manifest.example.json
logs/*.jsonl
```

If files or folders already exist, extend and align them. Do not duplicate competing standards.

---

## 3. External Technical References

Use Microsoft documentation as the primary technical reference for SQL Server backup, restore, and transactional error handling decisions.

Relevant references:

- Microsoft Learn: SQL Server backup and restore strategies.
- Microsoft Learn: SQL Server recovery models.
- Microsoft Learn: `BACKUP` Transact-SQL.
- Microsoft Learn: `RESTORE` statement arguments, especially multi-step restore guidance.
- Microsoft Learn: `TRY...CATCH` Transact-SQL.
- Microsoft Learn: `XACT_STATE` Transact-SQL.
- Microsoft Learn: `SET XACT_ABORT` Transact-SQL.

Do not turn this task into a generic SQL Server theory exercise. Use the references only to justify practical repo standards and safe operational guidance.

---

## 4. Objective

Deliver a Phase 2A emergency-readiness layer for the SQL Git Promotion Framework.

The completed solution must make the following scenarios safe, documented, and repeatable:

1. A direct production SQL hotfix is needed because the normal PR route is too slow.
2. A direct production SQL hotfix has already happened and Git must be reconciled.
3. A SQL migration is reversible and needs a standard rollback script.
4. A SQL migration is not safely reversible and must declare forward-fix or restore-from-backup expectations.
5. A high-risk data migration requires preview, validation, and rollback/forward-fix planning.
6. Backup threshold warnings need to be clear, configurable or policy-documented, and not generate unnecessary deployment noise.
7. The SQL Promotion Guide must contain detailed, copy/paste-ready, step-by-step instructions for standard rollback, emergency hotfix, hotfix reconciliation, and rehearsal.

---

## 5. Non-Goals / Out Of Scope

Do not deliver the following in this phase unless a severe gap is discovered and approval is given:

- GitHub Actions SQL PR validation.
- Full CI/CD deployment.
- Automated production deployment approvals.
- Flyway or Liquibase adoption.
- DEV/UAT SQL environment design.
- Automatic rollback generation.
- Automatic production hotfix reconciliation.
- Query Store baseline comparison.
- Agent or dashboard monitoring over SQL JSONL logs.
- Broad refactor of the deployment framework unless required for the hotfix/rollback scope.

These are valuable later phases, but Phase 2A should remain focused on emergency readiness, guide quality, and reversible migration safety.

---

## 6. Codex Skills To Use

Use the repo’s available skills and standards. At minimum:

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | Use | Emergency workflow and repo convention changes |
| `k98-sql-validation` | Use | Core SQL migration and rollback safety task |
| `k98-test-selection` | Use | Select safe validation and rehearsal tests |
| `k98-pr-review` | Use | Required before merge |
| `k98-promotion-check` | Use | Required before production or rehearsal deployment |
| `codex-security:security-scan` | Use | Ensure logs/templates/scripts do not expose credentials |

If a skill is unavailable, document that and follow the matching reference docs manually.

---

## 7. Mandatory Delivery Approach

This task must be delivered in controlled stages. Stop for owner review after Stage 2 unless the owner has explicitly approved one-pass implementation.

### Stage 1 — Audit Current Phase 1 Assets

Audit current SQL repo state and document:

- Existing `docs/SQL_PROMOTION_GUIDE.md` hotfix content.
- Existing rollback guidance in `migrations/README.md` or `migrations/rollback/`.
- Existing `reports/` folder conventions.
- Existing deployment manifest behaviour.
- Current backup threshold configuration or embedded defaults.
- Current validation warnings for dangerous SQL patterns.
- Current structured logging fields in deployment/export/drift/validation scripts.
- Any existing support for hotfix evidence or rehearsal.

Output: short audit note in Codex response before implementation or in a temporary planning section.

### Stage 2 — Design Proposed Phase 2A Changes

Propose the final file/folder changes before implementation.

Must include:

- New or updated hotfix template location.
- New or updated rollback template location.
- New or updated data migration guardrail documentation location.
- Whether backup thresholds become configurable now or only documented.
- Exact controlled rehearsal design.
- Whether a tiny rehearsal database object is required.
- Whether the rehearsal should create a real migration.
- How rehearsal evidence will be recorded.
- Which SQL Promotion Guide sections will be added or rewritten.

Stop for approval unless one-pass approval is explicitly granted.

### Stage 3 — Implement Documentation And Templates

Implement approved documentation/templates.

Required outputs are listed in Section 10.

### Stage 4 — Implement Minimal Tooling Enhancements

Only implement tooling changes that directly support this phase.

Examples:

- Configurable backup threshold file.
- Validation checks for missing rollback classification.
- Validation checks for invalid rollback values.
- Validation warnings when `Rollback: Included` is declared but no rollback file exists.
- Validation warnings when destructive or high-risk data operations do not include a declared data safety plan.

Do not expand into full CI.

### Stage 5 — Rehearse Emergency Hotfix Workflow

Run a safe, controlled, non-destructive rehearsal.

The rehearsal must prove the process, not introduce operational risk.

Acceptable rehearsal options:

1. Add/update/remove an extended property on a dedicated rehearsal object.
2. Create and then reconcile a tiny dedicated metadata table such as `dbo.SqlHotfixRehearsal`.
3. Use a harmless stored procedure comment/extended property if object creation is considered unnecessary.

Preferred option:

```text
dbo.SqlHotfixRehearsal
```

Rationale: a dedicated object makes drift detection easy and avoids touching real bot business tables or stored procedures.

The final rehearsal must leave Git and Production reconciled.

### Stage 6 — Validate And Final Review

Run the repo’s relevant validation commands and produce final evidence.

Final response must include:

- Files changed.
- Commands run.
- Rehearsal evidence path.
- Validation result.
- Security review result.
- Any deferred follow-ups.

---

## 8. Target Repository Changes

Codex should implement or update the following structure, adjusting only if the existing repo layout requires it.

```text
K98-bot-SQL-Server
│
├─ docs/
│  ├─ SQL_PROMOTION_GUIDE.md                 # update with detailed step-by-step guide sections
│  ├─ SQL_RELEASE_CHECKLIST.md               # update with hotfix/rehearsal/rollback checks
│  ├─ SQL_HOTFIX_GUIDE.md                    # optional, only if guide becomes too large
│  ├─ SQL_DATA_MIGRATION_GUARDRAILS.md       # required unless folded into migrations/README.md
│  └─ adr/
│     └─ 002-sql-emergency-hotfix-and-rollback-standards.md
│
├─ migrations/
│  ├─ README.md                              # update rollback metadata standards
│  └─ rollback/
│     ├─ README.md                           # required rollback conventions
│     └─ _rollback_template.sql              # required template
│
├─ reports/
│  └─ hotfix/
│     ├─ README.md                           # required folder convention
│     ├─ hotfix_template.md                  # required incident template
│     └─ rehearsal_YYYYMMDD_HHMM_<short_name>.md  # created during validation/rehearsal
│
├─ deploy/
│  ├─ sql_deploy_config.example.json         # optional/required if thresholds are made configurable
│  ├─ Validate-SqlRepo.ps1                   # update if validation additions are approved
│  └─ Test-SqlBackupReadiness.ps1            # update if config support is approved
│
└─ deploy_manifest.example.json              # update if manifest fields now include rollback/data-safety fields
```

If Codex chooses not to add a separate `docs/SQL_HOTFIX_GUIDE.md`, then `docs/SQL_PROMOTION_GUIDE.md` must still contain all detailed step-by-step instructions listed in Section 11.

---

## 9. Required Design Decisions

Codex must make, document, and justify these decisions.

### Decision 1 — Hotfix Evidence Location

Preferred:

```text
reports/hotfix/
```

Reason: hotfixes are operational incidents with evidence, commands, timestamps, and follow-up notes. They should not be mixed into general docs.

### Decision 2 — Hotfix Template Location

Preferred:

```text
reports/hotfix/hotfix_template.md
```

Optional supporting guide:

```text
docs/SQL_HOTFIX_GUIDE.md
```

### Decision 3 — Rollback File Convention

Preferred:

```text
migrations/rollback/<MigrationId>_rollback.sql
```

Example:

```text
migrations/20260602_003_add_example_column.sql
migrations/rollback/20260602_003_add_example_column_rollback.sql
```

### Decision 4 — Rollback Classification

Allowed values:

```text
Rollback: Included
Rollback: Manual
Rollback: Forward Fix Only
Rollback: Not Possible
```

Meanings:

| Value | Meaning |
|---|---|
| `Included` | A matching rollback script exists and has been reviewed. |
| `Manual` | Rollback steps are known but require manual judgement. |
| `Forward Fix Only` | Do not roll back; correct with a new migration. |
| `Not Possible` | Change cannot safely be reversed without restore or bespoke recovery. |

### Decision 5 — Data Safety Classification

Add or document optional migration header fields:

```sql
DataChange: Yes | No
DataSafetyPlan: Not Required | Required | Included
EstimatedRowsAffected: optional
PreValidationQuery: optional
PostValidationQuery: optional
```

Codex may adjust names if the existing migration header standard suggests a better convention.

### Decision 6 — Rehearsal Object

Preferred safe rehearsal object:

```text
dbo.SqlHotfixRehearsal
```

The rehearsal must be deliberately isolated from bot runtime behaviour.

---

## 10. Required Deliverables

### Deliverable 1 — Hotfix Reports Folder Convention

Create or update:

```text
reports/hotfix/README.md
```

Must explain:

- What belongs in `reports/hotfix/`.
- Naming convention for hotfix incident reports.
- Naming convention for rehearsal reports.
- Required evidence to attach or reference.
- How to link related SQL PRs and bot PRs.
- How to record final reconciliation status.
- How to handle sensitive information.

Suggested report naming:

```text
reports/hotfix/hotfix_YYYYMMDD_HHMM_<short_description>.md
reports/hotfix/rehearsal_YYYYMMDD_HHMM_<short_description>.md
```

### Deliverable 2 — SQL Hotfix Incident Template

Create:

```text
reports/hotfix/hotfix_template.md
```

The template must include:

```text
# SQL Hotfix Incident Report

Hotfix ID:
Date/time UTC:
Operator:
Environment:
Server:
Database:
Related bot issue/PR:
Related SQL issue/PR:

## 1. Incident Summary
What happened?
What was the user/business impact?
Why was this urgent?

## 2. Decision To Bypass Standard SQL PR Flow
Why could the normal Git-first process not be followed first?
Who approved the emergency path?
What risk was accepted?

## 3. Backup Confirmation
Last full backup:
Last differential backup:
Last log backup:
Backup readiness command/output reference:
Any override used:

## 4. Production Change Applied
Exact SQL executed or script path:
Execution time UTC:
Rows affected:
Objects affected:
Transaction handling used:

## 5. Validation Performed
Pre-change validation:
Post-change validation:
Bot smoke test if relevant:
SQL smoke test:
User-visible confirmation:

## 6. Drift And Export Evidence
Export branch:
Drift report path:
Expected drift summary:
Unexpected drift summary:

## 7. Git Reconciliation
Migration created:
Rollback classification:
SQL PR:
Merge commit:
Deployment history check:
Final drift check result:

## 8. Rollback / Forward-Fix Notes
Could this change be rolled back?
Rollback script path if any:
Forward-fix plan if rollback is not safe:
Restore-from-backup decision point:

## 9. Final Status
Resolved / Partially resolved / Reverted / Monitoring:
Outstanding risks:
Follow-up tasks:
Deferred optimisations:
```

The template must be detailed enough that the owner can fill it in during a real incident.

### Deliverable 3 — Detailed SQL Promotion Guide Updates

Update:

```text
docs/SQL_PROMOTION_GUIDE.md
```

This is a major deliverable. The guide must contain very clear step-by-step instructions with exact commands.

At minimum add or rewrite these sections:

1. Emergency SQL hotfix decision tree.
2. Standard production hotfix workflow.
3. Already-applied production hotfix reconciliation workflow.
4. Controlled hotfix rehearsal workflow.
5. Rollback decision tree.
6. Reversible migration workflow.
7. Non-reversible migration workflow.
8. Forward-fix workflow.
9. Restore-from-backup escalation points.
10. Data migration safety workflow.
11. Backup threshold policy and override handling.
12. Post-hotfix drift verification.
13. Final incident report completion.

The guide must be written for practical use during stress. Avoid vague instructions like “check backups” unless followed by exact commands and what good/bad output looks like.

### Deliverable 4 — SQL Release Checklist Updates

Update:

```text
docs/SQL_RELEASE_CHECKLIST.md
```

Add checklist blocks for:

- Reversible migration review.
- Rollback file exists when required.
- Non-reversible migration acknowledgement.
- Data migration safety review.
- Emergency hotfix pre-checks.
- Emergency hotfix post-checks.
- Hotfix reconciliation checks.
- Drift evidence captured.
- Hotfix report completed.

### Deliverable 5 — Rollback README

Create or update:

```text
migrations/rollback/README.md
```

Must define:

- What rollback scripts are for.
- When rollback scripts are required.
- When rollback scripts must not be created because they would give false confidence.
- Naming convention.
- Header convention.
- Review requirements.
- Transaction handling expectations.
- Data-loss warning expectations.
- How rollback relates to restore-from-backup.
- How rollback relates to forward-fix.

### Deliverable 6 — Rollback Script Template

Create:

```text
migrations/rollback/_rollback_template.sql
```

Template must include a header such as:

```sql
/*
RollbackForMigrationId: YYYYMMDD_NNN_short_description
Purpose: Describe what this rollback reverses
Author: cwatts
CreatedUtc: YYYY-MM-DD
RiskLevel: Low | Medium | High
DataLossRisk: None | Low | Medium | High
RollbackType: Full | Partial | Manual Assist
RequiresBackup: Yes
PreRollbackValidation: Describe query/check
PostRollbackValidation: Describe query/check
RelatedSQLPR: optional

IMPORTANT:
- This script must be reviewed before use.
- This script must not be run blindly.
- Confirm backup readiness before execution.
*/

SET XACT_ABORT ON;
GO

BEGIN TRY
    BEGIN TRANSACTION;

    -- Pre-rollback validation here.
    -- Rollback statements here.
    -- Post-rollback validation here.

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
GO
```

Codex must adapt this to the repo’s existing SQL style if needed.

### Deliverable 7 — Migration Header Standard Update

Update `migrations/README.md` so future migrations include rollback and data safety metadata.

Suggested header:

```sql
/*
MigrationId: YYYYMMDD_NNN_short_description
Purpose: Short description
Author: cwatts
CreatedUtc: YYYY-MM-DD
RequiresBackup: Yes | No
RiskLevel: Low | Medium | High
Rollback: Included | Manual | Forward Fix Only | Not Possible
RollbackScript: migrations/rollback/YYYYMMDD_NNN_short_description_rollback.sql | N/A
DataChange: Yes | No
DataSafetyPlan: Not Required | Required | Included
EstimatedRowsAffected: optional
PreValidationQuery: optional
PostValidationQuery: optional
RelatedBotPR: optional
RelatedSQLPR: optional
*/
```

Document what each field means and when it is mandatory.

### Deliverable 8 — Data Migration Guardrails

Create:

```text
docs/SQL_DATA_MIGRATION_GUARDRAILS.md
```

Must include rules for:

- `UPDATE` statements.
- `DELETE` statements.
- `TRUNCATE` statements.
- `DROP` statements.
- large backfills.
- column type changes.
- column drops.
- table renames.
- index changes on large tables.
- config table changes that affect bot behaviour.

For high-risk data migrations, require:

```text
1. Purpose statement.
2. Row-count preview query.
3. Expected row-count range.
4. Transaction plan.
5. Locking/runtime risk note.
6. Backup confirmation.
7. Rollback or forward-fix plan.
8. Pre-validation query.
9. Post-validation query.
10. Bot impact assessment where relevant.
```

### Deliverable 9 — Backup Threshold Policy Or Config

Either update the docs to make backup thresholds explicit, or implement a simple config file if practical.

Preferred if practical:

```text
deploy/sql_deploy_config.example.json
```

Example:

```json
{
  "database": "ROK_TRACKER",
  "server": "MINI_AMD",
  "backup_thresholds": {
    "full_backup_max_age_hours": 24,
    "differential_backup_max_age_hours": 12,
    "log_backup_max_age_minutes": 60,
    "differential_backup_policy": "warn_only"
  },
  "hotfix": {
    "require_incident_report": true,
    "require_post_hotfix_drift_check": true
  }
}
```

If implementing config support is too invasive, document the thresholds clearly and defer script config support.

### Deliverable 10 — Validation Enhancements

Where practical, update:

```text
deploy/Validate-SqlRepo.ps1
```

Add warnings/errors for:

- Missing `Rollback:` field in migration headers.
- Invalid rollback classification.
- `Rollback: Included` but no matching rollback file.
- `DataChange: Yes` without `DataSafetyPlan:`.
- High-risk operations without data safety metadata.
- Rollback scripts that do not include `RollbackForMigrationId:`.

Keep validation useful but not brittle. Warnings are acceptable for this phase unless the repo standard already supports hard failures.

### Deliverable 11 — Controlled Hotfix Rehearsal Report

Create a rehearsal report under:

```text
reports/hotfix/rehearsal_YYYYMMDD_HHMM_<short_description>.md
```

The report must document:

- What was rehearsed.
- Why it was non-destructive.
- Backup readiness result.
- Exact SQL used for the direct production-style change.
- Drift export/check result.
- Reconciliation migration path.
- Rollback classification.
- Final validation.
- Final drift status.
- Lessons learned.

### Deliverable 12 — ADR For Emergency Hotfix And Rollback Standards

Create:

```text
docs/adr/002-sql-emergency-hotfix-and-rollback-standards.md
```

Must document:

- Context.
- Decision.
- Why direct production hotfixes remain discouraged.
- Why a formal emergency path is still needed.
- Why rollback scripts are optional but classification is mandatory.
- Why some changes should be forward-fix only.
- Why hotfix evidence is stored under `reports/hotfix/`.
- Consequences.
- Follow-up work.

---

## 11. Required Step-By-Step Guide Content

This section is deliberately detailed. Codex must use this as the minimum expected content for the SQL Promotion Guide updates.

### 11.1 Emergency Hotfix Decision Tree

Add a section that answers:

```text
Can this wait for the normal SQL PR workflow?
```

Guide text must include a decision tree similar to:

```text
1. Is production down, corrupting data, blocking a critical bot function, or producing materially wrong user output?
   - If no: use the normal SQL PR workflow.
   - If yes: continue.

2. Is there a safe workaround outside SQL?
   - If yes: apply workaround and create normal SQL PR.
   - If no: continue.

3. Is the required SQL change small, understood, and reversible or forward-fixable?
   - If no: stop and consider restore/escalation.
   - If yes: continue.

4. Has backup readiness been confirmed?
   - If no: run backup readiness check.
   - If backup check fails: decide whether to stop or explicitly record override.

5. Create or start the hotfix incident report.
6. Apply the minimum safe production change.
7. Validate.
8. Export/drift check.
9. Reconcile Git.
10. Complete incident report.
```

### 11.2 Standard Emergency Hotfix Workflow

Must include copy/paste commands, adjusted to actual script names and repo paths.

Minimum command pattern:

```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
.\dev.ps1

cd C:\K98-bot-SQL-Server
git status
git switch main
git pull --ff-only

.\deploy\Validate-SqlRepo.ps1
.\deploy\Test-SqlBackupReadiness.ps1
```

Then instructions for creating the hotfix report from the template:

```powershell
$stamp = Get-Date -Format "yyyyMMdd_HHmm"
Copy-Item .\reports\hotfix\hotfix_template.md ".\reports\hotfix\hotfix_${stamp}_short_description.md"
```

Then a safe SSMS / sqlcmd execution section:

```text
- Paste only the reviewed minimum SQL.
- Use an explicit transaction where safe.
- Capture rows affected.
- Capture errors.
- Do not make additional opportunistic changes.
```

Then post-hotfix commands:

```powershell
.\deploy\Invoke-DriftCheck.ps1
```

Then Git reconciliation commands:

```powershell
git switch -c codex/sql-hotfix-YYYYMMDD-short-description
.\deploy\New-SqlMigration.ps1 -Description "reconcile_hotfix_short_description"
```

Then validation and PR steps:

```powershell
.\deploy\Validate-SqlRepo.ps1
git status
git add .
git commit -m "Document and reconcile SQL hotfix"
git push -u origin codex/sql-hotfix-YYYYMMDD-short-description
```

### 11.3 Already-Applied Production Hotfix Reconciliation Workflow

Must cover the case where a change was made before the formal template was started.

Steps:

```text
1. Stop making further production changes.
2. Create a hotfix report immediately.
3. Record everything known: who, when, why, what SQL, affected object, validation.
4. Run backup readiness check for current state.
5. Run drift check.
6. Create Git branch.
7. Create reconciliation migration that matches current Production.
8. Do not re-run a migration that duplicates the already-applied production effect unless it is idempotent and safe.
9. Validate migration logic against SchemaMigrationHistory expectations.
10. Open PR.
11. Merge.
12. Run final drift check.
13. Complete the incident report.
```

### 11.4 Controlled Hotfix Rehearsal Workflow

Must include a step-by-step rehearsal with exact commands.

Minimum rehearsal:

```text
1. Create rehearsal report from template.
2. Confirm backup readiness.
3. Apply a non-destructive direct production-style change.
4. Run drift check and confirm expected drift.
5. Create Git reconciliation migration.
6. Validate repo.
7. Deploy reconciliation migration if needed or mark already reconciled if the migration represents the production state safely.
8. Run final drift check.
9. Complete rehearsal report.
```

If using `dbo.SqlHotfixRehearsal`, example SQL must be safe and isolated.

Example pattern:

```sql
IF OBJECT_ID(N'dbo.SqlHotfixRehearsal', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.SqlHotfixRehearsal
    (
        RehearsalId INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_SqlHotfixRehearsal PRIMARY KEY,
        CreatedAtUtc DATETIME2(0) NOT NULL CONSTRAINT DF_SqlHotfixRehearsal_CreatedAtUtc DEFAULT SYSUTCDATETIME(),
        Notes NVARCHAR(4000) NULL
    );
END;
```

Codex may choose a better non-destructive scenario after inspecting the repo.

### 11.5 Rollback Decision Tree

Guide must include:

```text
1. Did the migration fail before any SQL changed?
   - No rollback required; fix migration and redeploy.

2. Did the migration partially apply?
   - Stop.
   - Check transaction state and deployment logs.
   - Check SchemaMigrationHistory and DeploymentRunHistory.
   - Decide between manual rollback, forward fix, or restore.

3. Did the migration succeed but bot validation failed?
   - If backward-compatible: fix bot or forward-fix SQL.
   - If breaking: consider rollback script or restore depending on risk.

4. Is there a reviewed rollback script?
   - If yes: confirm backup, review script, execute carefully, validate.
   - If no: do not invent rollback under pressure; prefer forward-fix or restore decision.

5. Is data loss involved?
   - If yes: escalate restore-from-backup decision.
```

### 11.6 Reversible Migration Workflow

Must include:

```text
1. Migration declares `Rollback: Included`.
2. Matching rollback file exists.
3. Rollback file has `RollbackForMigrationId:` header.
4. Rollback script includes pre/post validation.
5. Rollback script is reviewed in the same PR.
6. Rollback script is not automatically run by deployment tooling.
7. Operator must manually choose rollback after checking backup readiness.
```

### 11.7 Non-Reversible Migration Workflow

Must include:

```text
1. Migration declares `Rollback: Forward Fix Only` or `Rollback: Not Possible`.
2. PR explains why rollback is unsafe.
3. Release checklist confirms this was reviewed.
4. Backup readiness is mandatory.
5. Post-deployment validation is mandatory.
6. Restore-from-backup decision point is documented.
```

### 11.8 Data Migration Safety Workflow

Must include:

```text
1. Run preview SELECT.
2. Confirm expected rows affected.
3. Confirm backup readiness.
4. Execute inside transaction where safe.
5. Capture rows affected.
6. Run post-validation query.
7. Record result in deployment or hotfix notes.
```

Example guide snippet:

```sql
-- Preview
SELECT COUNT(*) AS RowsToChange
FROM dbo.ExampleTable
WHERE ...;

-- Change
SET XACT_ABORT ON;
BEGIN TRY
    BEGIN TRANSACTION;

    UPDATE dbo.ExampleTable
    SET ExampleColumn = ...
    WHERE ...;

    SELECT @@ROWCOUNT AS RowsChanged;

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
```

### 11.9 Restore-From-Backup Escalation Points

Must clearly state that restore is an operational decision, not a casual rollback.

Include escalation points:

```text
- Data corruption suspected.
- Unknown number of rows changed.
- Destructive change applied without reliable rollback.
- Migration changed multiple dependent objects and failed mid-way.
- Bot is producing materially wrong output and forward fix is not immediately safe.
```

Must include a warning that restore strategy depends on recovery model and backup chain.

### 11.10 Hotfix Report Completion

Guide must require:

```text
- Fill in final status.
- Link PR/commit/migration.
- Link drift report.
- Confirm final drift clean or explain accepted drift.
- Record follow-up actions.
- Move any improvement ideas to deferred optimisations if appropriate.
```

---

## 12. Validation Requirements

Codex must validate the following.

### Documentation Validation

- All new docs are linked from either `docs/SQL_PROMOTION_GUIDE.md`, `docs/SQL_RELEASE_CHECKLIST.md`, `migrations/README.md`, or `reports/hotfix/README.md`.
- No contradictory rollback classifications exist.
- No guide section refers to scripts or paths that do not exist.
- Commands are copy/paste-ready for the known environment.

### Repo Validation

Run:

```powershell
.\deploy\Validate-SqlRepo.ps1
```

If validation fails due to existing unrelated issues, document the failure and separate it from this task’s changes.

### Backup Readiness Validation

Run, where safe:

```powershell
.\deploy\Test-SqlBackupReadiness.ps1
```

If unavailable in Codex environment, document that it must be run on `MINI_AMD` before production rehearsal.

### Rehearsal Validation

Run a safe rehearsal or provide exact rehearsal instructions if Codex cannot access the production SQL server.

The preferred output is an actual rehearsal report. If Codex cannot execute the production rehearsal, it must still create:

```text
reports/hotfix/rehearsal_DRY_RUN_YYYYMMDD_sql_hotfix_workflow.md
```

and clearly mark what remains for the owner to run on `MINI_AMD`.

### Drift Validation

Run, where safe:

```powershell
.\deploy\Invoke-DriftCheck.ps1
```

Final state must be one of:

```text
Clean drift check
Expected drift documented and reconciled
Unable to run in current environment; exact owner commands provided
```

### Security Validation

Run the repo’s security review process if available.

At minimum confirm:

- Hotfix reports do not require passwords or secrets.
- Templates warn against pasting secrets.
- Logs do not expose connection strings with credentials.
- Config examples do not contain real usernames, passwords, tokens, or private paths beyond already-documented repo/server names.

---

## 13. Acceptance Criteria

This task is complete when all of the following are true:

- [x] `reports/hotfix/README.md` exists and defines the hotfix evidence convention.
- [x] `reports/hotfix/hotfix_template.md` exists and is detailed enough for a real incident.
- [x] `docs/SQL_PROMOTION_GUIDE.md` contains detailed step-by-step instructions for emergency hotfix, hotfix reconciliation, controlled rehearsal, rollback, forward-fix, restore escalation, and data migration safety.
- [x] `docs/SQL_RELEASE_CHECKLIST.md` includes hotfix, rollback, and data-migration checks.
- [x] `migrations/rollback/README.md` exists and defines rollback conventions.
- [x] `migrations/rollback/_rollback_template.sql` exists.
- [x] `migrations/README.md` includes rollback classification and data safety metadata standards.
- [x] `docs/SQL_DATA_MIGRATION_GUARDRAILS.md` exists or equivalent content is included in an approved existing doc.
- [x] Backup threshold policy is either documented clearly or made configurable.
- [x] `deploy_manifest.example.json` is updated if rollback/data-safety metadata belongs there.
- [x] `Validate-SqlRepo.ps1` warns or fails appropriately for missing/invalid rollback metadata where practical.
- [x] A controlled non-destructive hotfix rehearsal is completed or a clearly marked dry-run rehearsal report is produced with exact owner-run steps.
- [x] Rehearsal evidence is stored under `reports/hotfix/`.
- [x] Final drift state is clean or clearly documented.
- [x] No real bot runtime behaviour is changed by the rehearsal.
- [x] No secrets are added to docs, templates, config, logs, or reports.
- [x] Final Codex response includes changed files, validation commands, validation outcomes, and any follow-up recommendations.

---

## 14. Required Final Codex Output

At the end of the task, Codex must provide:

```text
1. Summary of what changed.
2. Files created.
3. Files updated.
4. Any scripts changed and why.
5. Hotfix rehearsal scenario used.
6. Hotfix report path.
7. Rollback convention summary.
8. Data migration guardrail summary.
9. Backup threshold decision.
10. Validation commands run.
11. Validation results.
12. Security review result.
13. Production impact statement.
14. Follow-up tasks / deferred optimisations.
```

The final output must explicitly state whether the controlled hotfix rehearsal was actually executed against Production or whether it remains an owner-run step.

---

## 15. Suggested Implementation Order

Use this order unless the audit shows a better path.

```text
1. Inspect current SQL repo docs and scripts.
2. Confirm existing rollback folder state.
3. Confirm existing report folder state.
4. Update migrations/README.md with rollback/data metadata.
5. Add migrations/rollback/README.md.
6. Add migrations/rollback/_rollback_template.sql.
7. Add reports/hotfix/README.md.
8. Add reports/hotfix/hotfix_template.md.
9. Add docs/SQL_DATA_MIGRATION_GUARDRAILS.md.
10. Add ADR 002.
11. Update docs/SQL_PROMOTION_GUIDE.md with detailed step-by-step sections.
12. Update docs/SQL_RELEASE_CHECKLIST.md.
13. Update deploy_manifest.example.json if appropriate.
14. Add backup threshold config or document threshold policy.
15. Update Validate-SqlRepo.ps1 only if low-risk and practical.
16. Run validation.
17. Perform or document controlled hotfix rehearsal.
18. Run drift check if environment permits.
19. Produce final review.
```

---

## 16. Suggested Controlled Rehearsal Design

Preferred rehearsal name:

```text
sql_hotfix_rehearsal_metadata_object
```

Preferred SQL object:

```text
dbo.SqlHotfixRehearsal
```

Preferred direct-production-style change:

```sql
IF OBJECT_ID(N'dbo.SqlHotfixRehearsal', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.SqlHotfixRehearsal
    (
        RehearsalId INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_SqlHotfixRehearsal PRIMARY KEY,
        CreatedAtUtc DATETIME2(0) NOT NULL CONSTRAINT DF_SqlHotfixRehearsal_CreatedAtUtc DEFAULT SYSUTCDATETIME(),
        Notes NVARCHAR(4000) NULL
    );
END;
```

Alternative direct-production-style change if object creation is not desired:

```sql
EXEC sys.sp_addextendedproperty
    @name = N'K98_HotfixRehearsal',
    @value = N'Controlled SQL hotfix rehearsal metadata only',
    @level0type = N'SCHEMA', @level0name = N'dbo';
```

Codex must choose the safest option after inspecting the repo.

The rehearsal must verify:

```text
Production-style direct SQL change detected by drift check
-> Git reconciliation migration created
-> rollback classification assigned
-> final drift status clean or documented
-> rehearsal report completed
```

---

## 17. Deferred Follow-Ups Not To Solve Here

Create deferred optimisation entries if appropriate, but do not implement these now:

- GitHub Actions SQL validation.
- Scheduled-task monitoring for nightly export.
- Bot or agent alerting for failed SQL export.
- Query Store regression comparison.
- Automated drift dashboard.
- DEV/UAT SQL environment design.
- Full automated rollback orchestration.
- Flyway/Liquibase evaluation.

---

## 18. Success Definition

At completion, the SQL repo should be ready for both normal and emergency SQL operations:

```text
Normal path:
Feature branch -> PR -> main -> backup check -> deploy -> validate -> drift check
```

```text
Emergency path:
Hotfix report -> backup check -> minimum production change -> validate -> drift check -> Git reconciliation PR -> final drift check -> completed incident record
```

```text
Rollback path:
Rollback classification -> reviewed rollback script if included -> backup check -> manual rollback or forward-fix decision -> validation -> documented outcome
```

The owner should be able to open the SQL Promotion Guide during a stressful production SQL issue and follow it step by step without relying on memory.
