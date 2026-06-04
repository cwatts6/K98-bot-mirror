# Codex Task Pack – SQL Git Promotion & Deployment Framework

**Task Name:** SQL Git Promotion & Deployment Framework  
**Date:** 2026-06-02  
**Owner/Context:** K98 SQL Repository Modernisation Initiative  
**Task Type:** Tooling / Architecture / DevOps / Documentation  
**Priority:** High  
**Risk Level:** High  
**One-Pass Approved:** No  

---

## 0. Programme Status Update - 2026-06-03

**Status:** Phase 1, Phase 2A, and Phase 2B delivered, merged, deployed, and operationally
validated.

This task pack originally defined the first major programme to move
`C:\K98-bot-SQL-Server` from a passive Production-to-Git schema snapshot repository into a
Git-first SQL deployment workflow. That first programme increment is complete. The follow-on
emergency-readiness phase has also been completed and rehearsed, and Phase 2B has now added SQL
PR validation, explicit backup policy, and nightly export monitoring/notification.

### Delivered In SQL Repo

Repository:

```text
C:\K98-bot-SQL-Server
```

Merged SQL repo PRs / commits:

- PR #4 merged `codex/sql-git-promotion-framework` into `main` at `61d3f03`.
- Follow-up drift snapshot reconciliation landed at `36f316b`.
- PR #5 / #6 merged `codex/sql-safe-nightly-export` into `main`; final verified `main` commit is
  `d298348`.
- PR #7 merged `codex/sql-emergency-readiness-hotfix-rollback` into `main`.
- PR #8 merged `codex/sql-hotfix-rehearsal-dry-run` into `main`.
- PR #9 merged `codex/sql-hotfix-rehearsal-reconcile` into `main`.
- PR #10 merged `codex/sql-hotfix-guide-rehearsal-alignment` into `main`.
- PR #11 merged `codex/sql-phase-2b-validation-monitoring` into `main`.
- PR #12 merged `codex/sql-nightly-health-cleanup-warning` into `main`.
- PR #13 merged `codex/sql-nightly-export-discord-alert` into `main`.

Delivered files and capabilities:

- `migrations/`
  - migration naming convention and authoring README
  - rollback folder guidance, rollback script template, rollback classification, and data-safety
    metadata
  - bootstrap migrations for:
    - `dbo.SchemaMigrationHistory`
    - `dbo.DeploymentRunHistory`
  - controlled rehearsal reconciliation migration:
    - `20260603_001_reconcile_sql_hotfix_rehearsal_table`
- `deploy/`
  - `Deploy-SqlMigration.ps1`
  - `Validate-SqlRepo.ps1`
  - `Test-SqlBackupReadiness.ps1`
  - `Export-ProdSchemaSnapshot.ps1`
  - `Compare-ProdSchema.ps1`
  - `Invoke-DriftCheck.ps1`
  - `New-SqlMigration.ps1`
  - `SqlDeploy.Common.ps1`
  - `Invoke-NightlyProdSchemaExport.ps1`
  - `Install-NightlySchemaExportTask.ps1`
  - `Test-NightlyExportHealth.ps1`
  - `sql_deploy_config.example.json`
- `.github/workflows/`
  - `sql-validation.yml`
- `.sqlfluff`
  - SQLFluff 4.2.1 advisory lint configuration for migration and rollback scripts
- `docs/`
  - `SQL_PROMOTION_GUIDE.md`
  - `SQL_RELEASE_CHECKLIST.md`
  - `adr/001-git-first-sql-deployment.md`
  - `adr/002-sql-emergency-hotfix-and-rollback-standards.md`
  - `adr/003-sql-ci-backup-policy-and-export-monitoring.md`
  - `SQL_DATA_MIGRATION_GUARDRAILS.md`
- `reports/hotfix/`
  - hotfix evidence folder convention
  - incident report template
  - rehearsal dry-run evidence
- structured log locations:
  - `logs/deployment.jsonl`
  - `logs/export.jsonl`
  - `logs/drift.jsonl`
  - `logs/validation.jsonl`
- drift report location:
  - `reports/drift_report_YYYYMMDD_HHMMSS.md`
- generated/export working area:
  - `exports/`

### Production Environment Confirmed

- SQL Server host: `MINI_AMD`
- Database: `ROK_TRACKER`
- SQL auth model: Windows Auth only
- SQL connectivity requires `TrustServerCertificate`
- Deployment machine: bot machine / RDP session on `MINI_AMD`
- Bot-machine shell bootstrap before SQL operations:

```powershell
cd C:\discord_file_downloader
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
.\dev.ps1
```

- Backup folder: `C:\sql_backup`
- Backup model: full, differential, and log backups, with external backup copy cadence every
  15 minutes.

### Production Validation Evidence

Validation completed on `MINI_AMD`:

- `deploy/Validate-SqlRepo.ps1`: succeeded
- `deploy/Test-SqlBackupReadiness.ps1`: succeeded
- `deploy/Deploy-SqlMigration.ps1 -ValidationOnly`: succeeded and detected 2 pending bootstrap
  migrations
- real `deploy/Deploy-SqlMigration.ps1`: succeeded
- `dbo.SchemaMigrationHistory`: both bootstrap migrations recorded as `Applied`
- `dbo.DeploymentRunHistory`: deployment recorded as `Succeeded`
- `deploy/Invoke-DriftCheck.ps1`: completed
- initial drift report showed only the two newly deployed history tables; snapshots were
  reconciled
- final drift check was clean

Nightly export replacement validation:

- old scheduled task `K98 SQL Schema Export` was disabled
- new scheduled task `K98 SQL Nightly Schema Export` was installed
- manual task run completed with `LastTaskResult : 0`
- new task exported to `export/prod-schema-*`
- SQL repo returned to clean `main`
- nightly export no longer pushes snapshots directly to `main`

Emergency-readiness validation:

- hotfix report template and evidence folder were created under `reports/hotfix/`
- rollback script template and conventions were added under `migrations/rollback/`
- data migration guardrails were added
- SQL repo validation now checks rollback/data-safety metadata and matching rollback headers
- controlled emergency hotfix rehearsal was executed against Production using isolated table
  `dbo.SqlHotfixRehearsal`
- drift check detected the expected added table and no unexpected drift
- reconciliation PR added migration, rollback script, and schema snapshot
- post-reconciliation drift check was clean
- deployment from `main` recorded the idempotent reconciliation migration in
  `dbo.SchemaMigrationHistory`
- final `Deploy-SqlMigration.ps1 -ValidationOnly` reported zero pending migrations
- post-rehearsal guide/checklist/template updates were merged after review feedback

Phase 2B validation and monitoring evidence:

- SQL PR GitHub Actions validation was added and runs read-only with respect to Production SQL.
- SQLFluff 4.2.1 is available locally and included as an advisory `tsql` migration/rollback lint
  gate.
- SqlPackage / DACPAC, tSQLt, and TSQLLint were explicitly reviewed and deferred as optional later
  validators.
- backup thresholds are explicit and configurable, with differential backup age warning-only under
  the current policy.
- nightly export health monitoring checks recent structured export logs and scheduled task result.
- stale cleanup-warning handling was hardened so old cleanup failures do not warn after a later
  successful finish event.
- failure-only Discord alerts were restored for nightly export and cleanup failures using
  `SQL_SCHEMA_DISCORD_WEBHOOK_URL`.
- manual schema export completed without error.
- Discord webhook payload test completed successfully.

### Security / Review Evidence

- Codex Security diff review was run for the initial deployment framework.
- No reportable security findings remained.
- Review feedback was addressed:
  - `Invoke-Sqlcmd` execution uses `-AbortOnError`
  - check constraints are scoped by `parent_object_id`
  - validator requires `exports/`
  - UPDATE/DELETE warnings scan per `GO` batch
  - nightly wrapper uses `powershell.exe -NoProfile`
  - disabling the old scheduled task fails fast without `-OldTaskName`
  - docs no longer hardcode a real Windows username in credential examples

### Current Operating Model

The SQL repo is now operated as:

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

Production exports are now:

```text
Production SQL
     ->
timestamped export/prod-schema-* branch
     ->
reviewable drift evidence
     ->
PR reconciliation only when needed
```

Emergency SQL hotfixes are now operated as:

```text
Hotfix report
     ->
backup readiness
     ->
minimum direct Production SQL
     ->
post-change validation
     ->
drift check
     ->
Git reconciliation PR
     ->
clean drift check
     ->
idempotent migration deployment from main
     ->
SchemaMigrationHistory recorded
     ->
final pending migration count 0
```

### Not Yet Delivered / Next Programme Phase

The following are deliberately **next phase** items, not missing work from the completed Phase 1,
Phase 2A, and Phase 2B framework:

- Improve drift reports so expected SMO formatting noise is easier to distinguish from real drift.
- Add optional deployment manifest enforcement if `deploy_manifest.example.json` proves useful.
- Add DEV/UAT SQL environment design if/when infrastructure is available.
- Consider Flyway or Liquibase only after the native workflow has several clean production cycles.
- Build monitoring-agent consumption over JSONL logs.
- Add SQL performance/regression validation such as Query Store baseline comparison.
- Add SqlPackage / DACPAC structural validation when tool installation, artifact policy, and target
  environment policy are approved.
- Add tSQLt tests only after a DEV or UAT SQL Server exists; do not install tSQLt objects in
  Production for PR validation.
- Keep TSQLLint as an optional fallback only if SQLFluff proves unsuitable.

### Current Recommendation

Treat this task pack as **completed for Phase 1, Phase 2A, and Phase 2B**. Use it as historical
context and as the launch point for the next task pack:

```text
SQL Git Promotion Framework - Phase 2C Drift Quality And Optional Manifest Enforcement
```

Recommended next selection from the remaining list:

1. Improve drift reports so expected SMO formatting noise is easier to distinguish from real drift.
2. Pilot optional deployment manifest enforcement for higher-risk SQL changes.
3. Keep SqlPackage / DACPAC and tSQLt as later environment-maturity tracks unless a DEV/UAT SQL
   target is available first.

Rationale: Phase 2B now prevents unsafe SQL PRs and closes the nightly-export alerting blind spot.
The next highest leverage step is improving the quality of drift evidence and making deployment
intent explicit for higher-risk changes without introducing full CI/CD deployment.

---

## 1. Required Reading

Before implementation, read:

- `AGENTS.md`
- `README-DEV.md`
- `docs/reference/README.md`

Then follow all linked references required by the repository.

Additional mandatory references:

- Current Bot Promotion Guide, used as the design standard for SQL promotion workflow documentation.
- Current SQL schema export tooling.
- Existing SQL repository structure.
- Any existing deployment scripts in:
  - `scripts/`
  - `deploy/`
  - SQL repo root
- Current deferred optimisation standards, if present.
- Current security / secrets handling standards, if present.

Validation source:

```text
C:\K98-bot-SQL-Server
```

Production runtime context:

- SQL Server: SQL Server 2022.
- Database: `ROK_TRACKER`.
- Current repository: `K98-bot-SQL-Server`.
- Current workflow includes Production → Git schema export using `Export-SqlSchemaAndPush.ps1`.

Codex must confirm any environment details that are not directly discoverable before proposing implementation.

---

## 2. Objective

Transform the SQL repository from a passive schema backup repository into a fully governed Git-first deployment workflow that mirrors the operational maturity of the K98 Bot promotion process.

The completed solution must:

- Support PR-driven SQL development.
- Support controlled Git → Production SQL deployments.
- Preserve Production → Git schema exports as a drift-detection and recovery mechanism.
- Eliminate the risk of production schema exports overwriting active development work.
- Introduce a formal SQL promotion guide with step-by-step instructions, rollback procedures, troubleshooting, and operational guardrails.
- Add backup validation before production deployment.
- Add structured deployment, export, and drift logs suitable for future monitoring agents.
- Add SQL validation tooling equivalent in purpose to bot-side linting / smoke validation.
- Add a documented emergency hotfix workflow for direct production changes.
- Add architecture decision records so the Git-first SQL model is clear and maintainable long term.

---

## 3. Background

Current state:

```text
Production SQL Server
        ↓
Export-SqlSchemaAndPush.ps1
        ↓
Git Repository
```

The SQL repository currently acts primarily as a schema snapshot.

### Problem 1 — Git Is Not the Authoritative Deployment Source

Developers may modify SQL directly in Production, and the next export may overwrite or confuse Git history.

This creates risk because Git records what Production became, not necessarily what was intentionally reviewed and promoted.

### Problem 2 — No Controlled Deployment Process Exists

Current deployment resembles:

```text
Edit SQL
Copy/Paste into SSMS
Run manually
Hope it worked
```

There is no SQL equivalent to the bot process:

```text
Mirror PR
Production PR
Promotion
Validation
Rollback
```

### Problem 3 — No SQL Promotion Guide Exists

The bot workflow is highly repeatable because the process is documented and standardised.

The SQL repository currently relies too heavily on tribal knowledge.

### Problem 4 — Production Export Can Clash With Active Development

The current export process is useful as a recovery and audit mechanism, but it must not behave like an uncontrolled source-of-truth sync into `main`.

Exports should create reviewable drift evidence, not silently overwrite active development branches.

### Problem 5 — Future Agent Monitoring Needs Better Signals

The long-term K98 platform direction includes agents that can monitor logs, detect issues, highlight optimisation opportunities, and identify operational risk.

The SQL promotion framework should therefore produce structured logs from day one.

---

## 4. Environment Model

Codex must explicitly document the current and target SQL environment model.

Current assumed model:

```text
Local SQL Repo
        ↓
GitHub SQL Repo
        ↓
Production SQL Server
        ↓
Production Schema Export
        ↓
GitHub SQL Repo / Drift Branch
```

Codex must confirm and document:

| Environment | Purpose | Notes |
|---|---|---|
| Local SQL repo | Development and script execution | `C:\K98-bot-SQL-Server` |
| GitHub SQL repo | Source of truth | PR-driven workflow |
| Production SQL Server | Runtime database | `ROK_TRACKER` |
| Production export branch | Drift evidence / recovery snapshot | Must not directly overwrite `main` |

Even if there is no DEV or UAT SQL database today, the design must leave a clear path to add them later without rewriting the framework.

---

## 5. Scope

### In Scope

#### Repository Governance

- Convert SQL repository into a Git-first workflow.
- Introduce migration-based deployment process.
- Introduce production deployment tooling.
- Introduce drift detection workflow.
- Introduce documented branch and promotion rules.

#### Export Process

Review current:

```text
Export-SqlSchemaAndPush.ps1
```

and redesign it so production exports are safe, reviewable, and cannot overwrite active development work.

#### Deployment Process

Create:

```text
Git
 ↓
Deploy Script
 ↓
Production SQL
```

workflow.

#### Documentation

Create:

```text
docs/SQL_PROMOTION_GUIDE.md
```

Equivalent in quality and detail to the bot promotion guide.

Also create:

```text
docs/SQL_RELEASE_CHECKLIST.md
docs/adr/001-git-first-sql-deployment.md
```

#### Safety Controls

Add deployment guardrails, including branch checks, dirty tree checks, backup checks, migration history, and drift review.

#### Migration Tracking

Introduce migration history tracking and deployment run history.

#### Validation

Add SQL repository validation tooling that can be run before PR review and before deployment.

#### Structured Logging

Create structured log outputs for deployment, export, drift, and validation operations.

---

### Out of Scope — Phase 2

The following are not required in this task, but the design should not block them later:

- Automated CI/CD deployment.
- GitHub Actions deployment.
- Azure DevOps pipelines.
- Flyway / Liquibase migration tooling.
- Multiple SQL environments such as DEV / UAT / PROD.
- Automated schema drift remediation.

### Out of Scope — Phase 3

- Fully automated rollback generation.
- Fully automated production hotfix reconciliation.
- Production deployment approvals through GitHub Actions.
- Real-time SQL agent monitoring dashboard.

---

## 6. Codex Skills To Use

| Skill | Decision | Notes |
|---|---|---|
| `k98-architecture-scope` | Use | Major workflow and architecture change |
| `k98-sql-validation` | Use | Core SQL task |
| `k98-test-selection` | Use | Deployment validation required |
| `k98-pr-review` | Use | Required before merge |
| `k98-promotion-check` | Use | Required before deployment |
| `codex-security:security-scan` | Use | Deployment and database access tooling |

Codex should also use any project-standard documentation, deferred optimisation, or promotion skills available in the repo.

---

## 7. Mandatory Workflow

This task must be delivered in controlled stages.

### Stage 1 — Audit Current SQL Repository

Audit current state and stop for approval.

Must include:

- Repository structure.
- Current export script behaviour.
- Current Git branch and sync risks.
- Existing deployment scripts, if any.
- Existing docs.
- Current SQL object layout.
- Current gaps against the bot promotion standard.

### Stage 2 — Design Proposed Workflow

Design target workflow and stop for approval.

Must include:

- Git-first promotion model.
- Branch model.
- Deployment flow.
- Export / drift flow.
- Emergency hotfix flow.
- Interaction with bot promotion.
- Initial backup and recovery model.

### Stage 3 — Design Migration Framework

Design migration framework and stop for approval.

Must include:

- Migration naming standard.
- Migration folder layout.
- Migration metadata.
- Migration history table.
- Deployment run history table.
- Roll-forward and rollback expectations.
- Idempotency expectations.

### Stage 4 — Implement Scripts and Documentation

Implement approved scripts, documentation, and guardrails.

### Stage 5 — Validate Workflow

Validate the full workflow using safe test migrations / dry-run modes where possible.

### Stage 6 — Final Review

Produce final review output including risks, validation evidence, and future enhancements.

---

## 8. Audit Requirements

Codex must audit the following.

### Repository Structure

Review:

```text
sql_schema/
scripts/
exports/
deploy/
docs/
logs/
```

and identify:

- Current strengths.
- Weaknesses.
- Missing folders.
- Ambiguous ownership.
- Files that should move.
- Files that should remain read-only snapshots.
- Files that should become deployable migrations.

### Current Export Script

Review:

```text
Export-SqlSchemaAndPush.ps1
```

and document:

- Risks.
- Limitations.
- Missing guardrails.
- Opportunities.
- Current branch assumptions.
- Current push behaviour.
- Risk of overwriting Git changes.
- Whether User Defined Table Types and other dependency objects are exported correctly.

### Promotion Gaps

Identify missing:

- Deployment process.
- Validation process.
- Backup validation.
- Rollback process.
- Migration tracking.
- Deployment run tracking.
- Drift review process.
- Emergency hotfix reconciliation.
- SQL promotion guide.
- Structured deployment logs.

### Security and Secrets Review

Audit:

- How SQL connection details are handled.
- Whether credentials are hardcoded.
- Whether scripts rely on Windows Auth, SQL Auth, or environment variables.
- Whether logs risk exposing secrets.
- Whether deployment scripts can be safely committed.

---

## 9. Target Architecture

### Repository Layout

Target structure:

```text
K98-bot-SQL-Server
│
├─ sql_schema/
│  ├─ tables/
│  ├─ views/
│  ├─ stored_procedures/
│  ├─ functions/
│  ├─ types/
│  └─ indexes/
│
├─ migrations/
│  ├─ 20260602_001_example.sql
│  ├─ 20260602_002_example.sql
│  └─ README.md
│
├─ deploy/
│  ├─ Deploy-SqlMigration.ps1
│  ├─ Export-ProdSchemaSnapshot.ps1
│  ├─ Compare-ProdSchema.ps1
│  ├─ Invoke-DriftCheck.ps1
│  ├─ Validate-SqlRepo.ps1
│  ├─ Test-SqlBackupReadiness.ps1
│  └─ New-SqlMigration.ps1
│
├─ docs/
│  ├─ SQL_PROMOTION_GUIDE.md
│  ├─ SQL_RELEASE_CHECKLIST.md
│  └─ adr/
│     └─ 001-git-first-sql-deployment.md
│
├─ logs/
│  ├─ deployment.jsonl
│  ├─ drift.jsonl
│  ├─ export.jsonl
│  └─ validation.jsonl
│
└─ deploy_manifest.example.json
```

Codex may adjust exact folder names to match the current repo, but must explain any deviation.

---

## 10. Deployment Model

### Source of Truth

```text
Git
```

Git becomes authoritative for intentional SQL changes.

### Deployment Source

```text
migrations/
```

Migrations become deployable code.

### Schema Snapshots

```text
sql_schema/
```

Schema snapshots become:

- Reference material.
- Audit evidence.
- Drift detection source.
- Recovery support.

They must not be treated as the primary deployment mechanism.

### Production Export

Production export remains available, but changes role:

```text
Production SQL
        ↓
Export Snapshot
        ↓
Dedicated Drift / Export Branch
        ↓
Review
        ↓
Reconcile if required
```

Exports must not directly push to `main`.

---

## 11. Migration Framework Requirements

### Migration Naming Standard

Use a sortable naming convention:

```text
YYYYMMDD_NNN_short_description.sql
```

Example:

```text
20260602_001_add_schema_migration_history.sql
```

### Migration Header Standard

Each migration must include a header similar to:

```sql
/*
MigrationId: 20260602_001_add_schema_migration_history
Purpose: Add schema migration history tracking table
Author: cwatts
CreatedUtc: 2026-06-02
RequiresBackup: Yes
RiskLevel: Low | Medium | High
Rollback: Manual | Included | Not Possible
RelatedBotPR: optional
RelatedSQLPR: optional
*/
```

### Migration Behaviour

Migrations should be:

- Reviewable.
- Small enough to understand.
- Ordered.
- Logged.
- Applied once.
- Preferably idempotent where safe.
- Explicit about rollback limitations.

Codex must document when idempotency is expected and when it is not appropriate.

---

## 12. Required Deliverables

### Deliverable 1 — Migration Framework

Create the migration folder structure, naming standard, metadata standard, and authoring guidance.

### Deliverable 2 — Migration History Table

Create a migration history table.

Example:

```sql
CREATE TABLE dbo.SchemaMigrationHistory
(
    MigrationId NVARCHAR(255) NOT NULL PRIMARY KEY,
    AppliedAtUtc DATETIME2(0) NOT NULL,
    AppliedBy NVARCHAR(255) NULL,
    GitCommit NVARCHAR(40) NULL,
    BranchName NVARCHAR(255) NULL,
    Status NVARCHAR(50) NOT NULL,
    ErrorMessage NVARCHAR(MAX) NULL,
    Checksum NVARCHAR(128) NULL,
    DurationMs INT NULL
);
```

Codex may improve the schema but must explain the final design.

### Deliverable 3 — Deployment Run History Table

Create a deployment run history table.

Example:

```sql
CREATE TABLE dbo.DeploymentRunHistory
(
    DeploymentId UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
    StartedAtUtc DATETIME2(0) NOT NULL,
    FinishedAtUtc DATETIME2(0) NULL,
    StartedBy NVARCHAR(255) NULL,
    GitCommit NVARCHAR(40) NULL,
    BranchName NVARCHAR(255) NULL,
    MigrationCount INT NOT NULL DEFAULT 0,
    Status NVARCHAR(50) NOT NULL,
    ErrorMessage NVARCHAR(MAX) NULL,
    DurationSeconds INT NULL
);
```

Codex may improve the schema but must explain the final design.

### Deliverable 4 — Production Deployment Script

Create:

```text
deploy/Deploy-SqlMigration.ps1
```

Capabilities:

- Validate branch.
- Validate working tree.
- Validate migration naming.
- Validate migration has not already been applied.
- Validate SQL connection.
- Validate recent backup readiness.
- Execute migration.
- Log execution.
- Update migration history.
- Update deployment run history.
- Stop on failure.
- Support dry-run / validation-only mode if practical.
- Produce structured JSONL logs.

### Deliverable 5 — Backup Readiness Script

Create:

```text
deploy/Test-SqlBackupReadiness.ps1
```

The script should check and report:

- Last full backup time.
- Last differential backup time, if applicable.
- Last log backup time, if applicable.
- Database recovery model.
- Backup age versus configured threshold.
- Whether deployment should proceed.

If exact production backup policy is unknown, Codex must document assumptions and make thresholds configurable.

### Deliverable 6 — Drift Export Script

Refactor:

```text
Export-SqlSchemaAndPush.ps1
```

into:

```text
deploy/Export-ProdSchemaSnapshot.ps1
```

Requirements:

- Must not push directly to `main`.
- Must support dedicated export branch.
- Must support drift review.
- Must support dry-run mode if practical.
- Must log structured export output.
- Must clearly distinguish snapshot output from migration scripts.
- Must protect active development work.

### Deliverable 7 — Schema Comparison Tooling

Create:

```text
deploy/Compare-ProdSchema.ps1
```

The tool should compare current repo schema snapshots against newly exported production snapshots and generate a readable drift report.

Expected output:

```text
reports/drift_report_YYYYMMDD_HHMMSS.md
```

The report should summarise:

- Added objects.
- Removed objects.
- Modified objects.
- Object types affected.
- Whether drift appears expected or unexpected.
- Recommended next action.

### Deliverable 8 — Drift Check Tooling

Create:

```text
deploy/Invoke-DriftCheck.ps1
```

This should orchestrate export + comparison + report generation.

### Deliverable 9 — SQL Repo Validation Script

Create:

```text
deploy/Validate-SqlRepo.ps1
```

Validation should include, where practical:

- Migration naming checks.
- Duplicate migration ID checks.
- Basic SQL parse / syntax validation where possible.
- Duplicate object file checks.
- Missing required folders.
- Missing migration headers.
- Potential unresolved dependency warnings.
- Dangerous operation warnings, such as `DROP TABLE`, `TRUNCATE TABLE`, large `UPDATE` without `WHERE`, or destructive `ALTER` patterns.
- Secrets scanning for connection strings or passwords.

This does not need to be perfect, but it must provide a useful pre-PR and pre-deployment safety layer.

### Deliverable 10 — Deployment Manifest

Create an example deployment manifest:

```text
deploy_manifest.example.json
```

Example structure:

```json
{
  "migration": "20260602_001_add_schema_migration_history",
  "description": "Add SQL migration tracking table",
  "author": "cwatts",
  "requires_backup": true,
  "risk_level": "Low",
  "related_bot_pr": null,
  "related_sql_pr": null,
  "validation_required": [
    "deploy/Validate-SqlRepo.ps1",
    "manual smoke test"
  ]
}
```

Codex should decide whether this remains an example only or becomes an optional deployment input.

### Deliverable 11 — SQL Promotion Guide

Create:

```text
docs/SQL_PROMOTION_GUIDE.md
```

Requirements are detailed in Section 13.

### Deliverable 12 — SQL Release Checklist

Create:

```text
docs/SQL_RELEASE_CHECKLIST.md
```

This should be a concise tick-box operational checklist for real deployments.

### Deliverable 13 — Architecture Decision Record

Create:

```text
docs/adr/001-git-first-sql-deployment.md
```

Must document:

- Decision.
- Context.
- Options considered.
- Why Git becomes authoritative.
- Why migrations are used for deployment.
- Why snapshots remain for drift detection and recovery.
- Why direct production changes are discouraged.
- Consequences and follow-up work.

### Deliverable 14 — Structured Logging

Ensure deployment/export/drift/validation scripts write structured logs suitable for future monitoring agents:

```text
logs/deployment.jsonl
logs/drift.jsonl
logs/export.jsonl
logs/validation.jsonl
```

Each log event should include, where applicable:

- Timestamp UTC.
- Script name.
- Operation.
- Status.
- Branch.
- Git commit.
- Operator.
- Database.
- Migration ID.
- Duration.
- Error message.
- Recommended action.

Logs must not expose secrets.

---

## 13. SQL Promotion Guide Requirements

Create:

```text
docs/SQL_PROMOTION_GUIDE.md
```

The guide must be modelled after the Bot Promotion Guide and detailed enough that the owner can follow it without remembering the process.

### Required Sections

#### Purpose

Explain:

- Git-first deployment.
- Migration-based promotion.
- Drift detection.
- Export snapshots.
- Backup validation.
- Interaction with bot promotion.

#### Environment Model

Document:

- Local repo.
- GitHub repo.
- Production SQL Server.
- Production export branch.
- Future DEV/UAT extension path.

#### Standard Process

Document each step with exact commands:

1. Confirm current branch.
2. Pull latest SQL repo state.
3. Create SQL feature branch.
4. Create migration.
5. Run SQL validation.
6. Review migration manually.
7. Open PR.
8. Merge PR after review.
9. Sync local repo with merged `main`.
10. Confirm backup readiness.
11. Deploy migration.
12. Run smoke tests.
13. Run drift export.
14. Compare schema.
15. Record validation notes.
16. Cleanup branches.

#### Required Commands

Provide exact commands for:

- Branch creation.
- Migration creation.
- Validation.
- Backup readiness check.
- Deployment.
- Export.
- Drift review.
- Log review.
- Cleanup.
- Branch sync repair.

#### Pre-Deployment Checklist

Include a checklist covering:

- Git branch is correct.
- Working tree is clean.
- PR is approved / merged.
- Backup readiness confirmed.
- Migration reviewed.
- Rollback approach understood.
- Bot dependency order understood.
- Smoke tests prepared.

#### Post-Deployment Checklist

Include:

- Migration history checked.
- Deployment run history checked.
- Bot smoke tests run if relevant.
- Drift export run.
- Drift report reviewed.
- Logs reviewed.
- Branches cleaned up.

#### Troubleshooting

Must include:

- Dirty working tree.
- Failed migration.
- Partial migration.
- Export run on wrong branch.
- Production hotfix.
- Unexpected drift.
- Branch sync issues.
- SQL connection failure.
- Backup readiness failure.
- Migration already applied.
- Migration history corruption.
- Deployment log missing or malformed.
- Drift report unclear.

#### Rollback Procedures

Document:

- Failed deployment before any SQL change.
- Failed deployment after partial SQL change.
- Failed deployment after successful SQL change but failed bot validation.
- Schema recovery.
- Hotfix recovery.
- Restore-from-backup decision points.

The guide must be explicit that not every SQL migration can be safely auto-rolled back.

#### Emergency Production Hotfix Workflow

Document a specific emergency process for cases where Production must be changed directly in SSMS.

Must include:

1. Record reason for emergency hotfix.
2. Take or confirm backup.
3. Apply minimum safe production change.
4. Export production snapshot immediately after.
5. Create hotfix migration in Git that matches Production.
6. Open PR.
7. Merge PR.
8. Run drift check to confirm Git and Production are reconciled.
9. Record final notes.

#### Interaction With Bot Promotion

Document deployment order when:

- Bot changes require SQL changes.
- SQL changes require bot changes.
- SQL and bot changes must be deployed together.
- SQL changes are backward compatible.
- SQL changes are breaking.

Include examples.

---

## 14. Safety Guardrails

Implement the following.

### Branch Protection

Deployment should refuse unsafe branches by default.

Examples:

- Refuse deployment from unapproved feature branches unless explicitly allowed.
- Prefer deployment from `main` after PR merge.
- Require explicit override flags for exceptional cases.

### Dirty Tree Protection

Refuse deployment if:

```powershell
git status --porcelain
```

is not clean.

### Backup Protection

Deployment must check backup readiness before applying production changes.

If backup information is unavailable, deployment must warn clearly and require an explicit override.

### Export Protection

Refuse export directly into:

```text
main
```

unless an explicit override is provided and documented.

Default export target should be a dedicated branch, for example:

```text
export/prod-schema-YYYYMMDD-HHMMSS
```

### Migration Tracking

Require migration history update for every applied migration.

### Deployment Run Tracking

Require deployment run history update for every deployment attempt, including failed attempts.

### Error Handling

Fail safely.

No partial success reporting.

A deployment must never report success unless all required steps completed successfully.

### Secrets Protection

Scripts and logs must not expose:

- Passwords.
- Connection strings with credentials.
- Access tokens.
- Service account secrets.

---

## 15. Testing Requirements

Validate the following.

### Happy Path

- Migration deploys successfully.
- Migration history is updated.
- Deployment run history is updated.
- Structured logs are written.

### Failed Migration

- Migration failure is detected.
- Deployment stops.
- Error is logged.
- History reflects failure.
- Rollback guidance is available.

### Backup Readiness

- Script reports recent backup information.
- Deployment blocks or warns when backup threshold is not met.

### Drift Detection

- Unexpected schema change is identified.
- Drift report is generated.
- Drift logs are written.

### Export Protection

- Export is blocked on `main` by default.
- Export branch workflow works.

### Validation Script

- Invalid migration naming is detected.
- Missing headers are detected.
- Dangerous SQL patterns are warned.
- Structured validation logs are written.

### Promotion Workflow

- Full end-to-end process is documented and tested as far as safely possible.

### Hotfix Workflow

- Emergency hotfix reconciliation process is documented and dry-run validated where practical.

---

## 16. Acceptance Criteria

- [x] Git becomes the controlled deployment source.
- [x] SQL migrations can be deployed from repository to production.
- [x] Production schema export no longer overwrites development work.
- [x] Dedicated drift-detection workflow exists.
- [x] Migration history table implemented.
- [x] Deployment run history table implemented.
- [x] Deployment tooling created.
- [x] Backup readiness check created.
- [x] Export tooling refactored.
- [x] Schema comparison tooling created.
- [x] SQL validation tooling created.
- [x] Structured JSONL logs created for deployment, export, drift, and validation.
- [x] SQL Promotion Guide created.
- [x] SQL Promotion Guide includes rollback and troubleshooting procedures.
- [x] SQL Promotion Guide includes emergency production hotfix workflow.
- [x] SQL Release Checklist created.
- [x] ADR created for Git-first SQL deployment decision.
- [x] SQL Promotion Guide is comparable in quality and detail to the Bot Promotion Guide.
- [x] Guardrails prevent accidental deployment mistakes.
- [x] Full workflow documented and validated.
- [x] Existing production schema export capability remains available as a safety mechanism.
- [x] Final output includes clear future enhancements and deferred optimisations.

Phase 1 acceptance status: complete as of 2026-06-02.
Phase 2A emergency-readiness status: complete as of 2026-06-03.
Phase 2B SQL validation, backup policy, and nightly export monitoring status: complete as of
2026-06-03.
Remaining programme work is tracked in Section 0, "Not Yet Delivered / Next Programme Phase", and
Section 19.

---

## 17. Required Delivery Output

Codex final delivery must include:

- Audit findings.
- Proposed architecture.
- Environment model.
- Repository changes.
- New scripts.
- Modified scripts.
- Migration framework.
- Migration history table.
- Deployment run history table.
- Backup readiness approach.
- SQL validation approach.
- Structured logging approach.
- Drift detection approach.
- SQL Promotion Guide.
- SQL Release Checklist.
- ADR.
- Validation results.
- Security review findings.
- Deployment recommendations.
- Emergency hotfix guidance.
- Future enhancements.
- Deferred optimisations.

---

## 18. Information Codex Must Confirm or Request

Before implementation, Codex must confirm or clearly document assumptions for:

### SQL Connection Model

- Windows Authentication or SQL Authentication.
- Server name.
- Database name.
- Whether deployment is run from the bot machine, dev machine, or another admin workstation.
- Whether credentials are stored in environment variables, local profile, Windows Credential Manager, or another approved mechanism.

### Backup Policy

- Full backup frequency.
- Differential backup frequency, if used.
- Log backup frequency, if used.
- Backup retention period.
- Expected maximum age of backup before deployment.
- Whether deployment scripts can query `msdb` backup history.

### Production Change Frequency

- Typical number of SQL changes per week / month.
- Whether emergency direct-production edits are common or rare.
- Whether most SQL changes are stored procedure changes, table changes, index changes, or config data changes.

### Bot Dependency Model

- Which bot features depend on SQL schema changes.
- Whether SQL migrations must usually be deployed before bot releases.
- Whether backward-compatible SQL changes are expected.

### Repo and Branch Model

- Whether SQL repo uses only `main` today.
- Whether production branches are required like the bot repo.
- Whether export branches should be automatically created.

---

## 19. Future Enhancements / Deferred Optimisations

The following items should be promoted into future task packs now that Phase 1, Phase 2A, and
Phase 2B are stable in Production.

### Completed Phase 2B - SQL PR Validation, Backup Policy, And Nightly Export Monitoring

- GitHub Actions validation for SQL repo PRs was added.
- automated migration validation, PowerShell parser checks, credential-pattern scanning,
  documentation sanity checks, and nightly main-branch protection proof were added.
- SQLFluff was added as an advisory migration/rollback linter.
- scheduled-task monitoring for `K98 SQL Nightly Schema Export` was added.
- failure-only Discord notification was restored for nightly export and cleanup failures.
- backup policy thresholds are explicit and configurable.
- generated drift/snapshot consistency was reviewed and left as a future drift-quality phase rather
  than a Phase 2B blocker.

### Phase 2C - Drift Quality And Optional Manifest Enforcement

- Improve drift reports so expected SMO formatting noise is easier to separate from real schema drift.
- Add optional deployment manifest enforcement if the example manifest becomes operationally useful.

### Phase 3 - Environment And Platform Maturity

- Add DEV / UAT SQL environment design.
- Add automated deployment approval workflow.
- Add automatic drift dashboard.
- Add deployment monitoring agent over JSONL logs.
- Add SQL performance regression checks.
- Add Query Store baseline comparison after deployment.
- Add automatic documentation generation from migration metadata.
- Expand data migration safety framework for larger backfills and destructive data changes if real
  migrations expose gaps beyond the Phase 2A guardrails.
- Expand rollback tooling only after reviewed manual rollback scripts have several clean
  production cycles.
- Evaluate Flyway or Liquibase only after the native process has several clean production cycles.

---

## 20. Success Definition

At completion, the SQL repository should operate using the same principles as the bot repositories:

```text
Feature Branch
     ↓
PR Review
     ↓
Merge
     ↓
Backup Readiness Check
     ↓
Controlled Promotion
     ↓
Production Validation
     ↓
Drift Verification
     ↓
Structured Logging
     ↓
Cleanup
```

while still preserving a Production → Git export path for recovery, auditing, and schema drift detection:

```text
Production SQL
     ↓
Export Snapshot
     ↓
Drift Branch
     ↓
Review
     ↓
Reconcile if Required
```

The final outcome should be a safe, repeatable, documented SQL deployment framework that supports current production needs and prepares the SQL platform for future automation, monitoring agents, and multi-environment maturity.
